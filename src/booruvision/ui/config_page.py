"""Settings page: interface language and the global shortcut combination."""

import sys
from collections.abc import Awaitable, Callable

import flet as ft

from booruvision.hotkeys import MODIFIER_ORDER, SUPPORTED_KEYS, Hotkey, HotkeyError, Modifier
from booruvision.i18n import AUTO, LANGUAGES, detect_system_language, t

CONFIG_ROUTE = "/config"
DEFAULT_SHORTCUT = "Ctrl+Shift+I"

_META_LABELS = {"darwin": "Cmd", "win32": "Win"}
_MODIFIER_LABELS = {
    Modifier.CTRL: "Ctrl",
    Modifier.ALT: "Option" if sys.platform == "darwin" else "Alt",
    Modifier.SHIFT: "Shift",
    Modifier.META: _META_LABELS.get(sys.platform, "Super"),
}

# Keys reported by Flutter for modifier-only presses; recording waits for a real key
_MODIFIER_KEY_LABELS = {"shift", "control", "alt", "meta", "option", "command", "super", "caps lock", "fn"}


def display_shortcut(hotkey: Hotkey) -> str:
    """Hotkey text with platform-specific modifier names, e.g. 'Ctrl+Cmd+I' on macOS."""
    mods = [_MODIFIER_LABELS[m] for m in MODIFIER_ORDER if m in hotkey.modifiers]
    return " + ".join([*mods, hotkey.key])


def hotkey_from_key_event(e: ft.KeyboardEvent) -> Hotkey | None:
    """Build a hotkey from a key-down event, or None for modifier-only presses.

    Raises HotkeyError for keys that global hotkeys cannot use.
    """
    key = e.key.strip()
    if key.lower().replace(" left", "").replace(" right", "") in _MODIFIER_KEY_LABELS:
        return None
    modifiers = {
        m
        for m, pressed in (
            (Modifier.CTRL, e.ctrl),
            (Modifier.ALT, e.alt),
            (Modifier.SHIFT, e.shift),
            (Modifier.META, e.meta),
        )
        if pressed
    }
    return Hotkey.create(modifiers, key)


class ConfigPage:
    def __init__(
        self,
        page: ft.Page,
        shortcut: str,
        language: str,
        on_apply: Callable[[str], Awaitable[bool]],
        on_language_change: Callable[[str], None],
    ) -> None:
        self.page = page
        self._on_apply = on_apply
        self._on_language_change = on_language_change
        self._current = Hotkey.parse(shortcut)
        self.recording = False

        self._current_text = ft.Text(theme_style=ft.TextThemeStyle.HEADLINE_SMALL, weight=ft.FontWeight.BOLD)
        self._modifier_boxes = {
            m: ft.Checkbox(label=_MODIFIER_LABELS[m], on_change=self._on_field_change) for m in MODIFIER_ORDER
        }
        self._language = ft.Dropdown(
            label=t("settings.language"),
            value=language,
            options=[
                ft.DropdownOption(
                    key=AUTO, text=t("settings.language_auto", language=LANGUAGES[detect_system_language()])
                ),
                *(ft.DropdownOption(key=code, text=name) for code, name in LANGUAGES.items()),
            ],
            on_select=self._handle_language,
            dense=True,
            width=240,
        )
        self._key = ft.Dropdown(
            label=t("settings.key"),
            options=[ft.DropdownOption(key=k, text=k) for k in SUPPORTED_KEYS],
            on_select=self._on_field_change,
            enable_filter=True,
            editable=True,
            menu_height=320,
            width=140,
        )
        self._preview = ft.Text()
        self._record_button = ft.OutlinedButton(
            content=t("settings.record"), icon=ft.Icons.FIBER_MANUAL_RECORD, on_click=self._toggle_recording
        )
        self._apply_button = ft.FilledButton(
            content=t("settings.apply"), icon=ft.Icons.CHECK, on_click=self._apply
        )
        self._reset_button = ft.TextButton(content=t("settings.reset_default"), on_click=self._reset)
        self._status = ft.Text(color=ft.Colors.ON_SURFACE_VARIANT, visible=False)
        self._editor = ft.Column(
            [
                ft.Row(list(self._modifier_boxes.values()), wrap=True),
                ft.Row(
                    [self._key, self._record_button],
                    wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self._preview,
                ft.Row([self._apply_button, self._reset_button], wrap=True),
            ],
            spacing=12,
        )

        hint = t("settings.shortcut_hint")
        if sys.platform == "darwin":
            hint += " " + t("settings.shortcut_hint_mac")
        self._body = ft.Column(
            [
                self._language,
                ft.Divider(),
                ft.Text(t("settings.shortcut_title"), theme_style=ft.TextThemeStyle.TITLE_LARGE),
                ft.Text(hint, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Row(
                    [ft.Text(t("settings.current")), self._current_text],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self._status,
                ft.Divider(),
                self._editor,
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self._load_fields(self._current)

    # ---- public -----------------------------------------------------------------

    def view(self) -> ft.View:
        return ft.View(
            route=CONFIG_ROUTE,
            appbar=ft.AppBar(title=ft.Text(t("settings.title"))),
            controls=[ft.Container(self._body, padding=16, expand=True)],
        )

    def set_hotkey_status(self, message: object | None, *, enabled: bool) -> None:
        self._status.value = str(message or "")
        self._status.visible = bool(message)
        self._editor.disabled = not enabled
        if not enabled:
            self._stop_recording()

    def on_leave(self) -> None:
        self._stop_recording()
        self._load_fields(self._current)

    def handle_key(self, e: ft.KeyboardEvent) -> None:
        if not self.recording:
            return
        try:
            hotkey = hotkey_from_key_event(e)
        except HotkeyError as err:
            self._preview.value = str(err)
            self._preview.color = ft.Colors.ERROR
            self.page.update()
            return
        if hotkey is None:
            return
        self._stop_recording()
        self._load_fields(hotkey)
        self.page.update()

    # ---- fields -----------------------------------------------------------------

    def _load_fields(self, hotkey: Hotkey) -> None:
        for modifier, box in self._modifier_boxes.items():
            box.value = modifier in hotkey.modifiers
        self._key.value = hotkey.key
        self._current_text.value = display_shortcut(self._current)
        self._refresh_preview()

    def _selected(self) -> Hotkey:
        modifiers = [m for m, box in self._modifier_boxes.items() if box.value]
        return Hotkey.create(modifiers, self._key.value or "")

    def _refresh_preview(self) -> None:
        try:
            hotkey = self._selected()
        except HotkeyError as err:
            self._preview.value = str(err)
            self._preview.color = ft.Colors.ERROR
            self._apply_button.disabled = True
            return
        changed = hotkey != self._current
        self._preview.value = (
            t("settings.new_shortcut", shortcut=display_shortcut(hotkey))
            if changed
            else t("settings.no_changes")
        )
        self._preview.color = None
        self._apply_button.disabled = not changed

    def _handle_language(self, e: ft.Event[ft.Dropdown]) -> None:
        self._on_language_change(e.control.value or AUTO)

    def _on_field_change(self, _) -> None:
        self._refresh_preview()

    # ---- recording ----------------------------------------------------------------

    def _toggle_recording(self, _) -> None:
        if self.recording:
            self._stop_recording()
        else:
            self.recording = True
            self._record_button.content = t("settings.cancel")
            self._record_button.icon = ft.Icons.STOP
            self._preview.value = t("settings.press_keys")
            self._preview.color = ft.Colors.PRIMARY

    def _stop_recording(self) -> None:
        if not self.recording:
            return
        self.recording = False
        self._record_button.content = t("settings.record")
        self._record_button.icon = ft.Icons.FIBER_MANUAL_RECORD
        self._refresh_preview()

    # ---- actions --------------------------------------------------------------------

    async def _apply(self, _) -> None:
        try:
            hotkey = self._selected()
        except HotkeyError:
            return
        self._stop_recording()
        self._apply_button.disabled = True
        self.page.update()
        if await self._on_apply(str(hotkey)):
            self._current = hotkey
        # On failure the app has already shown why and kept the old shortcut
        self._load_fields(self._current)
        # page.update() was already called in this handler, so Flet skips its auto-update
        self.page.update()

    def _reset(self, _) -> None:
        self._stop_recording()
        self._load_fields(Hotkey.parse(DEFAULT_SHORTCUT))
