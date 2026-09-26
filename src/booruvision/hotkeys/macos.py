"""macOS global hotkey via a listen-only CGEventTap.

The tap runs on its own thread with its own CFRunLoop, so it does not depend on
who owns the main thread (the Flet client, or the embedded Python in a built app).
Listening to key events requires the Input Monitoring permission.
"""

import logging
import threading

import Quartz

from booruvision.hotkeys.base import Hotkey, HotkeyBackend, HotkeyCallback, HotkeyError, Modifier
from booruvision.i18n import Msg

log = logging.getLogger(__name__)

# Virtual key codes (kVK_*) from Carbon HIToolbox/Events.h. These are positional
# (ANSI layout), so on non-QWERTY layouts the physical key is what matters.
_KEYCODES = {
    "A": 0x00, "S": 0x01, "D": 0x02, "F": 0x03, "H": 0x04, "G": 0x05, "Z": 0x06, "X": 0x07,
    "C": 0x08, "V": 0x09, "B": 0x0B, "Q": 0x0C, "W": 0x0D, "E": 0x0E, "R": 0x0F, "Y": 0x10,
    "T": 0x11, "1": 0x12, "2": 0x13, "3": 0x14, "4": 0x15, "6": 0x16, "5": 0x17, "9": 0x19,
    "7": 0x1A, "8": 0x1C, "0": 0x1D, "O": 0x1F, "U": 0x20, "I": 0x22, "P": 0x23, "L": 0x25,
    "J": 0x26, "K": 0x28, "N": 0x2D, "M": 0x2E,
    "F1": 0x7A, "F2": 0x78, "F3": 0x63, "F4": 0x76, "F5": 0x60, "F6": 0x61, "F7": 0x62,
    "F8": 0x64, "F9": 0x65, "F10": 0x6D, "F11": 0x67, "F12": 0x6F, "F13": 0x69, "F14": 0x6B,
    "F15": 0x71, "F16": 0x6A, "F17": 0x40, "F18": 0x4F, "F19": 0x50, "F20": 0x5A,
}  # fmt: skip

_MODIFIER_FLAGS = {
    Modifier.CTRL: Quartz.kCGEventFlagMaskControl,
    Modifier.SHIFT: Quartz.kCGEventFlagMaskShift,
    Modifier.ALT: Quartz.kCGEventFlagMaskAlternate,
    Modifier.META: Quartz.kCGEventFlagMaskCommand,
}
_RELEVANT_FLAGS = 0
for _flag in _MODIFIER_FLAGS.values():
    _RELEVANT_FLAGS |= _flag

PERMISSION_MESSAGE = Msg("hotkey.macos_permission")


class MacHotkeyBackend(HotkeyBackend):
    name = "macos"

    def __init__(self) -> None:
        super().__init__()
        # (keycode, flags, callback) swapped atomically; read from the tap thread
        self._binding: tuple[int, int, HotkeyCallback] | None = None
        self._thread: threading.Thread | None = None
        self._run_loop = None
        self._tap = None
        self._started = threading.Event()
        self._start_error: Msg | None = None
        # pyobjc must keep a reference to the Python callback for the tap's lifetime
        self._tap_callback = self._on_event

    def _on_event(self, proxy, event_type, event, refcon):
        if event_type in (Quartz.kCGEventTapDisabledByTimeout, Quartz.kCGEventTapDisabledByUserInput):
            Quartz.CGEventTapEnable(self._tap, True)
            return event

        binding = self._binding
        if binding is None or event_type != Quartz.kCGEventKeyDown:
            return event
        if Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventAutorepeat):
            return event

        keycode, flags, callback = binding
        if (
            Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode) == keycode
            and (Quartz.CGEventGetFlags(event) & _RELEVANT_FLAGS) == flags
        ):
            try:
                callback()
            except Exception:
                log.exception("Hotkey callback failed")
        return event

    def _run(self) -> None:
        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly,
            Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown),
            self._tap_callback,
            None,
        )
        if self._tap is None:
            self._start_error = PERMISSION_MESSAGE
            self._started.set()
            return

        source = Quartz.CFMachPortCreateRunLoopSource(None, self._tap, 0)
        self._run_loop = Quartz.CFRunLoopGetCurrent()
        Quartz.CFRunLoopAddSource(self._run_loop, source, Quartz.kCFRunLoopCommonModes)
        Quartz.CGEventTapEnable(self._tap, True)
        self._started.set()

        Quartz.CFRunLoopRun()

        Quartz.CFRunLoopRemoveSource(self._run_loop, source, Quartz.kCFRunLoopCommonModes)
        Quartz.CFMachPortInvalidate(self._tap)
        self._tap = None

    def _ensure_started(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        if not Quartz.CGPreflightListenEventAccess():
            # Shows the system prompt the first time; the grant applies after a restart
            Quartz.CGRequestListenEventAccess()
            self.status_message = PERMISSION_MESSAGE
        else:
            self.status_message = None

        self._started.clear()
        self._start_error = None
        self._thread = threading.Thread(target=self._run, name="hotkey-macos", daemon=True)
        self._thread.start()
        self._started.wait(timeout=5)
        if self._start_error:
            self.status_message = self._start_error
            raise HotkeyError(self._start_error)

    def register(self, hotkey: Hotkey, callback: HotkeyCallback) -> None:
        keycode = _KEYCODES.get(hotkey.key)
        if keycode is None:
            raise HotkeyError(Msg("hotkey.key_unsupported_macos", key=hotkey.key))
        flags = 0
        for modifier in hotkey.modifiers:
            flags |= _MODIFIER_FLAGS[modifier]

        self._ensure_started()
        self._binding = (keycode, flags, callback)
        log.info("Registered hotkey %s", hotkey)

    def unregister(self) -> None:
        self._binding = None

    def stop(self) -> None:
        self._binding = None
        if self._run_loop is not None:
            Quartz.CFRunLoopStop(self._run_loop)
            self._run_loop = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
