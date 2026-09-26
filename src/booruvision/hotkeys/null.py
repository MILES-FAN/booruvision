from booruvision.hotkeys.base import Hotkey, HotkeyBackend, HotkeyCallback
from booruvision.i18n import Msg


class NullHotkeyBackend(HotkeyBackend):
    """Used when no global hotkey mechanism is available on this system."""

    name = "none"

    def __init__(self, reason: str | Msg) -> None:
        super().__init__()
        self.status_message = reason

    @property
    def available(self) -> bool:
        return False

    def register(self, hotkey: Hotkey, callback: HotkeyCallback) -> None:
        pass

    def unregister(self) -> None:
        pass

    def stop(self) -> None:
        pass
