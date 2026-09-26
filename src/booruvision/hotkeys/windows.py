"""Windows global hotkey via RegisterHotKey.

RegisterHotKey(NULL, ...) posts WM_HOTKEY to the *registering thread's* message
queue, so registration and the GetMessage loop both live on one worker thread.
Other threads hand it work through a queue and wake it with PostThreadMessage.
"""

import ctypes
import logging
import queue
import threading
from concurrent.futures import Future
from ctypes import wintypes

from booruvision.hotkeys.base import Hotkey, HotkeyBackend, HotkeyCallback, HotkeyError, Modifier

log = logging.getLogger(__name__)

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.PeekMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
    wintypes.UINT,
]
user32.PeekMessageW.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostThreadMessageW.restype = wintypes.BOOL
kernel32.GetCurrentThreadId.restype = wintypes.DWORD

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
WM_APP_WAKE = 0x8000 + 1
PM_NOREMOVE = 0x0000

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

ERROR_HOTKEY_ALREADY_REGISTERED = 1409

HOTKEY_ID = 1

_MODIFIER_FLAGS = {
    Modifier.CTRL: MOD_CONTROL,
    Modifier.SHIFT: MOD_SHIFT,
    Modifier.ALT: MOD_ALT,
    Modifier.META: MOD_WIN,
}


def virtual_key(key: str) -> int:
    if len(key) == 1:
        return ord(key)  # VK codes for 0-9 and A-Z match ASCII
    return 0x70 + int(key[1:]) - 1  # VK_F1 = 0x70


class WindowsHotkeyBackend(HotkeyBackend):
    name = "windows"

    def __init__(self) -> None:
        super().__init__()
        self._ops: queue.Queue = queue.Queue()
        self._callback: HotkeyCallback | None = None
        self._registered = False
        self._thread_id: int | None = None
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, name="hotkey-win32", daemon=True)
        self._thread.start()
        self._ready.wait()

    def _run(self) -> None:
        self._thread_id = kernel32.GetCurrentThreadId()
        msg = wintypes.MSG()
        # Force creation of this thread's message queue before anyone posts to it
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_NOREMOVE)
        self._ready.set()

        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                if self._callback:
                    try:
                        self._callback()
                    except Exception:
                        log.exception("Hotkey callback failed")
            elif msg.message == WM_APP_WAKE:
                self._drain_ops()

        if self._registered:
            user32.UnregisterHotKey(None, HOTKEY_ID)
            self._registered = False
        self._drain_ops()

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
        user32.PostThreadMessageW(self._thread_id, WM_APP_WAKE, 0, 0)
        return future.result(timeout=5)

    def register(self, hotkey: Hotkey, callback: HotkeyCallback) -> None:
        flags = MOD_NOREPEAT
        for modifier in hotkey.modifiers:
            flags |= _MODIFIER_FLAGS[modifier]
        vk = virtual_key(hotkey.key)

        def do_register():
            if self._registered:
                user32.UnregisterHotKey(None, HOTKEY_ID)
                self._registered = False
            if not user32.RegisterHotKey(None, HOTKEY_ID, flags, vk):
                error = ctypes.get_last_error()
                if error == ERROR_HOTKEY_ALREADY_REGISTERED:
                    raise HotkeyError(f"{hotkey} is already used by another application")
                raise HotkeyError(f"RegisterHotKey failed for {hotkey} (error {error})")
            self._registered = True
            self._callback = callback

        self._call(do_register)
        log.info("Registered hotkey %s", hotkey)

    def unregister(self) -> None:
        def do_unregister():
            if self._registered:
                user32.UnregisterHotKey(None, HOTKEY_ID)
                self._registered = False
            self._callback = None

        self._call(do_unregister)

    def stop(self) -> None:
        if self._thread.is_alive():
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            self._thread.join(timeout=2)
