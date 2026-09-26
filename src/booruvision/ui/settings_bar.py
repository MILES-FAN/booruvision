"""Model, threshold and memory settings, plus the button that opens the settings page."""

from collections.abc import Awaitable, Callable

import flet as ft

from booruvision.i18n import t


class SettingsBar:
    def __init__(
        self,
        models: list[str],
        model: str,
        threshold: float,
        unload_after: bool,
        on_model_change: Callable[[str], Awaitable[None]],
        on_threshold_change: Callable[[float], None],
        on_unload_change: Callable[[bool], None],
        on_open_config: Callable[[], Awaitable[None]],
    ) -> None:
        self._on_model_change = on_model_change
        self._on_threshold_change = on_threshold_change
        self._on_unload_change = on_unload_change
        self._on_open_config = on_open_config

        self._model = ft.Dropdown(
            label=t("bar.model"),
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
        # Hidden for models with per-category thresholds, which are set in the tag panel
        self._threshold_column = ft.Column([self._threshold_label, self._threshold], spacing=0, tight=True)
        self._settings_button = ft.TextButton(
            content=t("bar.settings"),
            icon=ft.Icons.SETTINGS,
            on_click=self._handle_open_config,
        )
        self._unload = ft.Checkbox(label=t("bar.unload"), value=unload_after, on_change=self._handle_unload)
        self._hotkey_status = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT, visible=False)

        self.view = ft.Column(
            [
                ft.Row(
                    # Two non-wrapping groups: the bar only ever breaks between them
                    [
                        ft.Row(
                            [
                                self._model,
                                self._threshold_column,
                            ],
                            tight=True,
                            spacing=16,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            [self._unload, self._settings_button],
                            tight=True,
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
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
        return t("bar.threshold", value=f"{value:.2f}")

    def set_threshold_visible(self, visible: bool) -> None:
        self._threshold_column.visible = visible

    def set_hotkey_status(self, message: object | None) -> None:
        self._hotkey_status.value = str(message or "")
        self._hotkey_status.visible = bool(message)

    async def _handle_model(self, e: ft.Event[ft.Dropdown]) -> None:
        await self._on_model_change(e.control.value)

    def _handle_threshold_preview(self, e: ft.Event[ft.Slider]) -> None:
        self._threshold_label.value = self._threshold_text(e.control.value)

    def _handle_threshold(self, e: ft.Event[ft.Slider]) -> None:
        self._on_threshold_change(round(float(e.control.value), 2))

    def _handle_unload(self, e: ft.Event[ft.Checkbox]) -> None:
        self._on_unload_change(bool(e.control.value))

    async def _handle_open_config(self, _) -> None:
        await self._on_open_config()
