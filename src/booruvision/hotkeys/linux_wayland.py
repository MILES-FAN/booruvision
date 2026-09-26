"""Wayland global hotkey via the xdg-desktop-portal GlobalShortcuts interface.

Wayland does not let clients grab keys, so the app asks the portal to bind a
shortcut; the compositor may show a confirmation dialog and the user can change
the actual trigger in system settings. Supported by KDE Plasma and GNOME 48+.

All D-Bus traffic runs on a private asyncio loop in a worker thread.
https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html
"""

import asyncio
import logging
import secrets
import threading

from dbus_next import BusType, Message, MessageType, Variant
from dbus_next.aio import MessageBus

from booruvision.hotkeys.base import Hotkey, HotkeyBackend, HotkeyCallback, HotkeyError, Modifier

log = logging.getLogger(__name__)

PORTAL_BUS = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
SHORTCUTS_IFACE = "org.freedesktop.portal.GlobalShortcuts"
APP_ID = "io.github.miles_fan.booruvision"
SHORTCUT_ID = "analyze-clipboard"
SHORTCUT_DESCRIPTION = "Analyze clipboard image"

# Portal requests can wait on a user confirmation dialog
_REQUEST_TIMEOUT = 120

# https://specifications.freedesktop.org/shortcuts-spec/latest/
_TRIGGER_MODIFIERS = {
    Modifier.CTRL: "CTRL",
    Modifier.ALT: "ALT",
    Modifier.SHIFT: "SHIFT",
    Modifier.META: "LOGO",
}
_TRIGGER_ORDER = [Modifier.CTRL, Modifier.ALT, Modifier.SHIFT, Modifier.META]


def preferred_trigger(hotkey: Hotkey) -> str:
    mods = [_TRIGGER_MODIFIERS[m] for m in _TRIGGER_ORDER if m in hotkey.modifiers]
    key = hotkey.key.lower() if len(hotkey.key) == 1 else hotkey.key
    return "+".join([*mods, key])


class WaylandPortalHotkeyBackend(HotkeyBackend):
    name = "wayland-portal"

    def __init__(self) -> None:
        super().__init__()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, name="hotkey-portal", daemon=True)
        self._thread.start()

        self._bus: MessageBus | None = None
        self._shortcuts = None
        self._session: str | None = None
        self._pending: dict[str, asyncio.Future] = {}
        self._callback: HotkeyCallback | None = None

        try:
            self._call(self._connect(), timeout=10)
        except Exception:
            self.stop()
            raise

    @property
    def configurable(self) -> bool:
        return False

    def _call(self, coro, timeout: float = _REQUEST_TIMEOUT):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout=timeout)

    async def _connect(self) -> None:
        self._bus = await MessageBus(bus_type=BusType.SESSION).connect()

        # Non-sandboxed apps must tell the portal who they are (xdg-desktop-portal >= 1.19);
        # older portals derive the app id from the desktop file / cgroup instead.
        await self._bus.call(
            Message(
                destination=PORTAL_BUS,
                path=PORTAL_PATH,
                interface="org.freedesktop.host.portal.Registry",
                member="Register",
                signature="sa{sv}",
                body=[APP_ID, {}],
            )
        )

        introspection = await self._bus.introspect(PORTAL_BUS, PORTAL_PATH)
        if not any(i.name == SHORTCUTS_IFACE for i in introspection.interfaces):
            raise HotkeyError(
                "This desktop's xdg-desktop-portal has no GlobalShortcuts support "
                "(needs KDE Plasma or GNOME 48+)."
            )
        proxy = self._bus.get_proxy_object(PORTAL_BUS, PORTAL_PATH, introspection)
        self._shortcuts = proxy.get_interface(SHORTCUTS_IFACE)
        self._shortcuts.on_activated(self._on_activated)

        await self._add_match("type='signal',interface='org.freedesktop.portal.Request',member='Response'")
        self._bus.add_message_handler(self._on_message)

    async def _add_match(self, rule: str) -> None:
        await self._bus.call(
            Message(
                destination="org.freedesktop.DBus",
                path="/org/freedesktop/DBus",
                interface="org.freedesktop.DBus",
                member="AddMatch",
                signature="s",
                body=[rule],
            )
        )

    def _on_message(self, message: Message):
        if (
            message.message_type == MessageType.SIGNAL
            and message.interface == "org.freedesktop.portal.Request"
            and message.member == "Response"
        ):
            future = self._pending.pop(message.path, None)
            if future is not None and not future.done():
                future.set_result(message.body)
        return None

    def _on_activated(self, session_handle, shortcut_id, timestamp, options) -> None:
        if session_handle != self._session or shortcut_id != SHORTCUT_ID or self._callback is None:
            return
        try:
            self._callback()
        except Exception:
            log.exception("Hotkey callback failed")

    def _request_path(self, token: str) -> str:
        sender = self._bus.unique_name.lstrip(":").replace(".", "_")
        return f"{PORTAL_PATH}/request/{sender}/{token}"

    async def _request(self, method: str, *args, options: dict) -> dict:
        """Call a portal method that answers through a Request.Response signal."""
        token = f"booruvision_{secrets.token_hex(8)}"
        options = {**options, "handle_token": Variant("s", token)}
        # Subscribe before calling so a fast response is not missed
        path = self._request_path(token)
        future = self._loop.create_future()
        self._pending[path] = future
        try:
            await getattr(self._shortcuts, f"call_{method}")(*args, options)
            response, results = await asyncio.wait_for(future, _REQUEST_TIMEOUT)
        finally:
            self._pending.pop(path, None)
        if response != 0:
            raise HotkeyError("The shortcut request was cancelled or denied")
        return results

    async def _close_session(self) -> None:
        if self._session is None:
            return
        session, self._session = self._session, None
        await self._bus.call(
            Message(
                destination=PORTAL_BUS,
                path=session,
                interface="org.freedesktop.portal.Session",
                member="Close",
            )
        )

    async def _bind(self, hotkey: Hotkey) -> str | None:
        # Rebinding in an existing session is not allowed, so start a fresh one
        await self._close_session()
        results = await self._request(
            "create_session",
            options={"session_handle_token": Variant("s", f"booruvision_{secrets.token_hex(8)}")},
        )
        self._session = results["session_handle"].value

        shortcuts = [
            [
                SHORTCUT_ID,
                {
                    "description": Variant("s", SHORTCUT_DESCRIPTION),
                    "preferred_trigger": Variant("s", preferred_trigger(hotkey)),
                },
            ]
        ]
        results = await self._request("bind_shortcuts", self._session, shortcuts, "", options={})
        for shortcut_id, props in results.get("shortcuts", Variant("a(sa{sv})", [])).value:
            if shortcut_id == SHORTCUT_ID and "trigger_description" in props:
                return props["trigger_description"].value
        return None

    def register(self, hotkey: Hotkey, callback: HotkeyCallback) -> None:
        try:
            trigger = self._call(self._bind(hotkey))
        except HotkeyError:
            raise
        except Exception as e:
            raise HotkeyError(f"GlobalShortcuts portal error: {e}") from e

        self._callback = callback
        self.status_message = (
            f"Shortcut managed by your desktop: {trigger or 'not assigned yet'}. "
            "Change it in the system keyboard shortcut settings."
        )
        log.info("Bound portal shortcut, trigger: %s", trigger)

    def unregister(self) -> None:
        self._callback = None
        try:
            self._call(self._close_session(), timeout=5)
        except Exception:
            log.exception("Failed to close portal session")

    def stop(self) -> None:
        if not self._thread.is_alive():
            return
        self._callback = None
        try:
            if self._bus is not None:
                self._call(self._close_session(), timeout=5)
                self._bus.disconnect()
        except Exception:
            log.exception("Failed to close portal session")
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=2)
