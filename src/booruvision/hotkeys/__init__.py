"""Global hotkeys, implemented separately per platform.

- Windows: RegisterHotKey on a dedicated message-loop thread (windows.py)
- macOS:   listen-only CGEventTap, requires Input Monitoring permission (macos.py)
- Linux:   XGrabKey on X11 (linux_x11.py), xdg-desktop-portal GlobalShortcuts on Wayland
           (linux_wayland.py)
"""

import logging
import os
import sys

from booruvision.hotkeys.base import (
    MODIFIER_ORDER,
    SUPPORTED_KEYS,
    Hotkey,
    HotkeyBackend,
    HotkeyCallback,
    HotkeyError,
    Modifier,
)
from booruvision.hotkeys.null import NullHotkeyBackend
from booruvision.i18n import Msg

log = logging.getLogger(__name__)

__all__ = [
    "MODIFIER_ORDER",
    "SUPPORTED_KEYS",
    "Hotkey",
    "HotkeyBackend",
    "HotkeyCallback",
    "HotkeyError",
    "Modifier",
    "NullHotkeyBackend",
    "create_backend",
]


def _is_wayland() -> bool:
    return bool(os.environ.get("WAYLAND_DISPLAY")) or os.environ.get("XDG_SESSION_TYPE") == "wayland"


def create_backend() -> HotkeyBackend:
    """Pick the hotkey backend for the current platform/session.

    Never raises: falls back to NullHotkeyBackend with a human-readable reason.
    """
    try:
        if sys.platform == "win32":
            from booruvision.hotkeys.windows import WindowsHotkeyBackend

            return WindowsHotkeyBackend()

        if sys.platform == "darwin":
            from booruvision.hotkeys.macos import MacHotkeyBackend

            return MacHotkeyBackend()

        if sys.platform.startswith("linux"):
            if _is_wayland():
                from booruvision.hotkeys.linux_wayland import WaylandPortalHotkeyBackend

                return WaylandPortalHotkeyBackend()
            if os.environ.get("DISPLAY"):
                from booruvision.hotkeys.linux_x11 import X11HotkeyBackend

                return X11HotkeyBackend()
            return NullHotkeyBackend(Msg("hotkey.no_display"))

        return NullHotkeyBackend(Msg("hotkey.unsupported_platform", platform=sys.platform))
    except Exception as e:  # noqa: BLE001 - any backend failure must not break the app
        log.exception("Failed to initialise hotkey backend")
        return NullHotkeyBackend(Msg("hotkey.unavailable", error=e))
