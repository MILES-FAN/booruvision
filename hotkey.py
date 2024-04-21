keybindEnabled = False

from PyQt5.QtCore import QAbstractNativeEventFilter, QAbstractEventDispatcher
from typing import Optional, Callable
import platform

if platform.system() != "Darwin":
    from pyqtkeybind import keybinder
    keybindEnabled = True
else:
    from pynput import keyboard

class WinEventFilter(QAbstractNativeEventFilter):
    def __init__(self, keybinder):
        self.keybinder = keybinder
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0


class EventDispatcher:
    """Install a native event filter to receive events from the OS"""

    def __init__(self, keybinder) -> None:
        self.win_event_filter = WinEventFilter(keybinder)
        self.event_dispatcher = QAbstractEventDispatcher.instance()
        self.event_dispatcher.installNativeEventFilter(self.win_event_filter)

class KeyBinderBase:
    def register_hotkey(self, hotkey: str, callback: Callable) -> None:
        pass

    def unregister_hotkey(self, hotkey: str) -> None:
        pass

    def __init__(self) -> None:
        pass

class QtKeyBinder(KeyBinderBase):
    def __init__(self, win_id: Optional[int]) -> None:
        keybinder.init()
        self.win_id = win_id

        self.event_dispatcher = EventDispatcher(keybinder=keybinder)
            

    def register_hotkey(self, hotkey: str, callback: Callable) -> None:
        keybinder.register_hotkey(self.win_id, hotkey, callback)
            

    def unregister_hotkey(self, hotkey: str) -> None:
        keybinder.unregister_hotkey(self.win_id, hotkey)

class PynputKeyBinder(KeyBinderBase):
    def __init__(self) -> None:
        self.listener = None
        self.callback = None
        self.blocked = False

    def parse_hotkey(self, hotkey: str):
        return hotkey.replace("Ctrl", "<ctrl>").replace("Shift", "<shift>").replace("Alt", "<alt>").lower()

    def register_hotkey(self, hotkey: str, callback: Callable) -> None:
        print(f"Registered hotkey: {hotkey}")
        self.callback = callback
        self.listener = keyboard.GlobalHotKeys({
            self.parse_hotkey(hotkey): callback
        })
        self.listener.start()

    def unregister_hotkey(self, hotkey: str) -> None:
        hotkey = self.parse_hotkey(hotkey)
        self.listener.stop()
        print(f"Unregistered hotkey: {hotkey}")
        
