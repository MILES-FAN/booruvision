"""Model, threshold, hotkey and memory settings."""

from collections.abc import Awaitable, Callable

import flet as ft

PRESET_SHORTCUTS = ["Ctrl+Shift+I", "Ctrl+Shift+J", "Ctrl+Shift+K"]


def shortcut_options(current: str) -> list[ft.DropdownOption]:
    shortcuts = PRESET_SHORTCUTS if current in PRESET_SHORTCUTS else [*PRESET_SHORTCUTS, current]
    return [ft.DropdownOption(key=s, text=s) for s in shortcuts]


class SettingsBar:
    def __init__(
        self,
        models: list[str],
        model: str,
        threshold: float,
        shortcut: str,
        unload_after: bool,
        on_model_change: Callable[[str], Awaitable[None]],
        on_threshold_change: Callable[[float], None],
        on_shortcut_change: Callable[[str], Awaitable[None]],
        on_unload_change: Callable[[bool], None],
    ) -> None:
        self._on_model_change = on_model_change
        self._on_threshold_change = on_threshold_change
        self._on_shortcut_change = on_shortcut_change
        self._on_unload_change = on_unload_change

        self._model = ft.Dropdown(
            label="Model",
            value=model,
            options=[ft.DropdownOption(key=m, text=m) for m in models],
            on_select=self._handle_model,
            dense=True,
            width=220,
        )
        self._threshold_label = ft.Text(self._threshold_text(threshold))
        self._threshold = ft.Slider(
            value=threshold,
            min=0.05,
            max=0.95,
            divisions=90,
            round=2,
            label="{value}",
            width=220,
            on_change=self._handle_threshold_preview,
            on_change_end=self._handle_threshold,
        )
        self.shortcut = ft.Dropdown(
            label="Global shortcut",
            value=shortcut,
            options=shortcut_options(shortcut),
            on_select=self._handle_shortcut,
            dense=True,
            width=200,
        )
        self._unload = ft.Checkbox(
            label="Unload model after every analysis", value=unload_after, on_change=self._handle_unload
        )
        self._hotkey_status = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT, visible=False)

        self.view = ft.Column(
            [
                ft.Row(
                    [
                        self._model,
                        ft.Column([self._threshold_label, self._threshold], spacing=0, tight=True),
                        self.shortcut,
                        self._unload,
                    ],
                    wrap=True,
                    spacing=16,
                    run_spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self._hotkey_status,
            ],
            spacing=4,
            tight=True,
        )

    @staticmethod
    def _threshold_text(value: float) -> str:
        return f"Threshold: {value:.2f}"

    def set_shortcut(self, shortcut: str) -> None:
        self.shortcut.options = shortcut_options(shortcut)
        self.shortcut.value = shortcut

    def set_hotkey_status(self, message: str | None, *, enabled: bool) -> None:
        self._hotkey_status.value = message or ""
        self._hotkey_status.visible = bool(message)
        self.shortcut.disabled = not enabled

    async def _handle_model(self, e: ft.Event[ft.Dropdown]) -> None:
        await self._on_model_change(e.control.value)

    def _handle_threshold_preview(self, e: ft.Event[ft.Slider]) -> None:
        self._threshold_label.value = self._threshold_text(e.control.value)

    def _handle_threshold(self, e: ft.Event[ft.Slider]) -> None:
        self._on_threshold_change(round(float(e.control.value), 2))

    async def _handle_shortcut(self, e: ft.Event[ft.Dropdown]) -> None:
        await self._on_shortcut_change(e.control.value)

    def _handle_unload(self, e: ft.Event[ft.Checkbox]) -> None:
        self._on_unload_change(bool(e.control.value))
