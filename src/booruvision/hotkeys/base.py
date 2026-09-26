"""Platform-independent hotkey model and backend interface."""

import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

HotkeyCallback = Callable[[], None]


class HotkeyError(Exception):
    """Raised when a hotkey cannot be parsed or registered."""


class Modifier(StrEnum):
    CTRL = "Ctrl"
    SHIFT = "Shift"
    ALT = "Alt"
    META = "Meta"  # Cmd on macOS, Win on Windows, Super on Linux


_MODIFIER_ALIASES = {
    "ctrl": Modifier.CTRL,
    "control": Modifier.CTRL,
    "shift": Modifier.SHIFT,
    "alt": Modifier.ALT,
    "option": Modifier.ALT,
    "meta": Modifier.META,
    "cmd": Modifier.META,
    "command": Modifier.META,
    "win": Modifier.META,
    "super": Modifier.META,
}

_MODIFIER_ORDER = [Modifier.CTRL, Modifier.ALT, Modifier.SHIFT, Modifier.META]

_FUNCTION_KEY = re.compile(r"^F([1-9]|1[0-9]|2[0-4])$")


@dataclass(frozen=True)
class Hotkey:
    modifiers: frozenset[Modifier]
    key: str  # "A".."Z", "0".."9" or "F1".."F24"

    @classmethod
    def parse(cls, text: str) -> "Hotkey":
        parts = [p.strip() for p in text.split("+")]
        if len(parts) < 2 or any(not p for p in parts):
            raise HotkeyError(f"Invalid hotkey {text!r}: expected e.g. 'Ctrl+Shift+I'")

        *mod_parts, key = parts
        modifiers = set()
        for part in mod_parts:
            modifier = _MODIFIER_ALIASES.get(part.lower())
            if modifier is None:
                raise HotkeyError(f"Invalid hotkey {text!r}: unknown modifier {part!r}")
            modifiers.add(modifier)

        key = key.upper()
        if not ((len(key) == 1 and (key.isascii() and key.isalnum())) or _FUNCTION_KEY.match(key)):
            raise HotkeyError(f"Invalid hotkey {text!r}: unsupported key {key!r}")

        return cls(frozenset(modifiers), key)

    def __str__(self) -> str:
        mods = [m.value for m in _MODIFIER_ORDER if m in self.modifiers]
        return "+".join([*mods, self.key])


class HotkeyBackend(ABC):
    """A global hotkey listener. Holds at most one hotkey at a time.

    Callbacks are invoked on the backend's own thread; callers must hop back to
    their UI loop themselves. `register`/`unregister` may block (e.g. waiting for
    a system permission dialog), so call them off the UI thread.
    """

    name: str = "unknown"

    def __init__(self) -> None:
        self.status_message: str | None = None

    @property
    def available(self) -> bool:
        return True

    @property
    def configurable(self) -> bool:
        """Whether the app itself chooses the key combination."""
        return True

    @abstractmethod
    def register(self, hotkey: Hotkey, callback: HotkeyCallback) -> None:
        """Replace the current hotkey. Raises HotkeyError on failure."""

    @abstractmethod
    def unregister(self) -> None: ...

    @abstractmethod
    def stop(self) -> None:
        """Unregister and release all OS resources."""
