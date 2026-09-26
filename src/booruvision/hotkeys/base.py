"""Platform-independent hotkey model and backend interface."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
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

MODIFIER_ORDER = [Modifier.CTRL, Modifier.ALT, Modifier.SHIFT, Modifier.META]

SUPPORTED_KEYS = (
    [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    + [str(d) for d in range(10)]
    + [f"F{n}" for n in range(1, 25)]
)
_SUPPORTED_KEYS = frozenset(SUPPORTED_KEYS)


@dataclass(frozen=True)
class Hotkey:
    modifiers: frozenset[Modifier]
    key: str  # one of SUPPORTED_KEYS

    @classmethod
    def create(cls, modifiers: Iterable[Modifier], key: str) -> "Hotkey":
        modifiers = frozenset(modifiers)
        key = key.strip().upper()
        if not modifiers:
            raise HotkeyError("A global hotkey needs at least one modifier")
        if key not in _SUPPORTED_KEYS:
            raise HotkeyError(f"Unsupported key {key!r}: use A-Z, 0-9 or F1-F24")
        return cls(modifiers, key)

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

        return cls.create(modifiers, key)

    def __str__(self) -> str:
        mods = [m.value for m in MODIFIER_ORDER if m in self.modifiers]
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
