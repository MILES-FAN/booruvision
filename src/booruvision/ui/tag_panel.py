"""Result list with copy and output-format controls."""

from collections.abc import Callable

import flet as ft

from booruvision.formatting import TagFormat, format_tags


class TagPanel:
    def __init__(
        self,
        tag_format: TagFormat,
        comma_separated: bool,
        on_copy: Callable[[], None],
        on_format_change: Callable[[TagFormat], None],
        on_separator_change: Callable[[bool], None],
    ) -> None:
        self._tags: dict[str, float] = {}
        self._format = tag_format
        self._on_format_change = on_format_change
        self._on_separator_change = on_separator_change

        self._title = ft.Text("Tags", theme_style=ft.TextThemeStyle.TITLE_MEDIUM)
        self._list = ft.ListView(expand=True, spacing=2)
        self._empty = ft.Text("No results yet", color=ft.Colors.ON_SURFACE_VARIANT)

        self.copy_button = ft.FilledButton(
            content="Copy tags", icon=ft.Icons.CONTENT_COPY, on_click=lambda _: on_copy(), disabled=True
        )
        self._format_dropdown = ft.Dropdown(
            label="Tag format",
            value=tag_format.value,
            options=[ft.DropdownOption(key=f.value, text=f.value) for f in TagFormat],
            on_select=self._handle_format,
            dense=True,
            width=200,
        )
        self._comma_checkbox = ft.Checkbox(
            label="Use , as separator", value=comma_separated, on_change=self._handle_separator
        )

        self.view = ft.Container(
            content=ft.Column(
                [
                    self._title,
                    ft.Container(
                        content=ft.Stack([self._empty, self._list], expand=True),
                        expand=True,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                        border_radius=8,
                        padding=8,
                    ),
                    ft.Row(
                        [self._format_dropdown, self._comma_checkbox],
                        wrap=True,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.copy_button,
                ],
                expand=True,
            ),
            expand=True,
        )

    def set_tags(self, tags: dict[str, float]) -> None:
        self._tags = tags
        self._render()

    def _render(self) -> None:
        self._list.controls = [
            ft.Row(
                [
                    ft.Text(tag, selectable=True, expand=True),
                    ft.Text(f"{confidence:.3f}", color=ft.Colors.ON_SURFACE_VARIANT),
                ]
            )
            for tag, confidence in format_tags(self._tags, self._format).items()
        ]
        self._title.value = f"Tags ({len(self._tags)})" if self._tags else "Tags"
        self._empty.visible = not self._tags
        self.copy_button.disabled = not self._tags

    def _handle_format(self, e: ft.Event[ft.Dropdown]) -> None:
        self._format = TagFormat.parse(e.control.value or "")
        self._render()
        self._on_format_change(self._format)

    def _handle_separator(self, e: ft.Event[ft.Checkbox]) -> None:
        self._on_separator_change(bool(e.control.value))
