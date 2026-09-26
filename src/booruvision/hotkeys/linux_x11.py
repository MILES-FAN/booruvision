"""X11 global hotkey via XGrabKey on the root window.

python-xlib connections are not thread-safe, so a single worker thread owns the
Display; other threads send it work through a queue and wake its select() loop
with a self-pipe.
"""

import logging
import os
import queue
import select
import threading
import time
from concurrent.futures import Future

from Xlib import XK, X, display, error

from booruvision.hotkeys.base import Hotkey, HotkeyBackend, HotkeyCallback, HotkeyError, Modifier

log = logging.getLogger(__name__)

_MODIFIER_MASKS = {
    Modifier.CTRL: X.ControlMask,
    Modifier.SHIFT: X.ShiftMask,
    Modifier.ALT: X.Mod1Mask,
    Modifier.META: X.Mod4Mask,
}
_RELEVANT_MASK = X.ControlMask | X.ShiftMask | X.Mod1Mask | X.Mod4Mask

# Grab once for every combination of lock modifiers, otherwise the hotkey stops
# working while CapsLock / NumLock (Mod2) / ScrollLock (Mod5) are on.
_LOCK_COMBINATIONS = [0, X.LockMask, X.Mod2Mask, X.Mod5Mask]
_LOCK_COMBINATIONS = sorted(
    {a | b | c for a in _LOCK_COMBINATIONS for b in _LOCK_COMBINATIONS for c in _LOCK_COMBINATIONS}
)

# Without detectable auto-repeat X sends Release/Press pairs while a key is held
_MIN_TRIGGER_INTERVAL = 0.3


class X11HotkeyBackend(HotkeyBackend):
    name = "x11"

    def __init__(self) -> None:
        super().__init__()
        self._display = display.Display()
        self._root = self._display.screen().root
        self._ops: queue.Queue = queue.Queue()
        self._wake_r, self._wake_w = os.pipe()
        self._grab: tuple[int, int] | None = None  # (keycode, modifier mask)
        self._callback: HotkeyCallback | None = None
        self._last_trigger = 0.0
        self._running = True
        self._thread = threading.Thread(target=self._run, name="hotkey-x11", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        fd = self._display.fileno()
        while self._running:
            readable, _, _ = select.select([fd, self._wake_r], [], [])
            if self._wake_r in readable:
                os.read(self._wake_r, 64)
                self._drain_ops()
            while self._display.pending_events():
                self._handle_event(self._display.next_event())

        self._ungrab()
        self._display.close()

    def _handle_event(self, event) -> None:
        if event.type != X.KeyPress or self._grab is None or self._callback is None:
            return
        keycode, mask = self._grab
        if event.detail != keycode or (event.state & _RELEVANT_MASK) != mask:
            return
        now = time.monotonic()
        if now - self._last_trigger < _MIN_TRIGGER_INTERVAL:
            return
        self._last_trigger = now
        try:
            self._callback()
        except Exception:
            log.exception("Hotkey callback failed")

    def _drain_ops(self) -> None:
        while True:
            try:
                fn, future = self._ops.get_nowait()
            except queue.Empty:
                return
            try:
                future.set_result(fn())
            except Exception as e:
                future.set_exception(e)

    def _call(self, fn):
        if not self._thread.is_alive():
            raise HotkeyError("Hotkey thread is not running")
        future: Future = Future()
        self._ops.put((fn, future))
        os.write(self._wake_w, b"x")
        return future.result(timeout=5)

    def _ungrab(self) -> None:
        if self._grab is None:
            return
        keycode, mask = self._grab
        for locks in _LOCK_COMBINATIONS:
            self._root.ungrab_key(keycode, mask | locks)
        self._display.sync()
        self._grab = None

    def register(self, hotkey: Hotkey, callback: HotkeyCallback) -> None:
        mask = 0
        for modifier in hotkey.modifiers:
            mask |= _MODIFIER_MASKS[modifier]

        def do_register():
            keysym = XK.string_to_keysym(hotkey.key.lower() if len(hotkey.key) == 1 else hotkey.key)
            keycode = self._display.keysym_to_keycode(keysym)
            if not keycode:
                raise HotkeyError(f"No keycode for {hotkey.key} in the current keyboard layout")

            self._ungrab()
            catcher = error.CatchError(error.BadAccess)
            for locks in _LOCK_COMBINATIONS:
                self._root.grab_key(
                    keycode, mask | locks, True, X.GrabModeAsync, X.GrabModeAsync, onerror=catcher
                )
            self._display.sync()
            if catcher.get_error():
                for locks in _LOCK_COMBINATIONS:
                    self._root.ungrab_key(keycode, mask | locks)
                self._display.sync()
                raise HotkeyError(f"{hotkey} is already grabbed by another application")

            self._grab = (keycode, mask)
            self._callback = callback

        self._call(do_register)
        log.info("Registered hotkey %s", hotkey)

    def unregister(self) -> None:
        def do_unregister():
            self._ungrab()
            self._callback = None

        self._call(do_unregister)

    def stop(self) -> None:
        if not self._thread.is_alive():
            return
        self._running = False
        os.write(self._wake_w, b"x")
        self._thread.join(timeout=2)
        os.close(self._wake_r)
        os.close(self._wake_w)
