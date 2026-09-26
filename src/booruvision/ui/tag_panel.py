"""Result list with category filters, per-category thresholds, copy and output-format controls."""

from collections.abc import Callable

import flet as ft

from booruvision.formatting import TagFormat, format_tag
from booruvision.i18n import t
from booruvision.tagging.categories import Category, category_color
from booruvision.tagging.prediction import TagResult

THRESHOLD_FIELD_WIDTH = 72


def parse_threshold(text: str) -> float | None:
    """A threshold typed by the user, rounded to 2 decimals, or None unless 0 < value < 1."""
    try:
        value = round(float(text), 2)
    except ValueError:
        return None
    return value if 0 < value < 1 else None


class TagPanel:
    def __init__(
        self,
        tag_format: TagFormat,
        comma_separated: bool,
        on_copy: Callable[[], None],
        on_format_change: Callable[[TagFormat], None],
        on_separator_change: Callable[[bool], None],
        on_category_toggle: Callable[[Category, bool], None],
        on_category_threshold: Callable[[Category, float], None],
        on_reset_thresholds: Callable[[], None],
    ) -> None:
        self._results: list[TagResult] = []
        self._format = tag_format
        self._dark = False
        self._categories: tuple[Category, ...] = ()
        self._enabled: set[Category] = set()
        self._thresholds: dict[Category, float] | None = None
        self._on_format_change = on_format_change
        self._on_separator_change = on_separator_change
        self._on_category_toggle = on_category_toggle
        self._on_category_threshold = on_category_threshold

        self._title = ft.Text(t("tags.title"), theme_style=ft.TextThemeStyle.TITLE_MEDIUM)
        self._categories_row = ft.Row(
            wrap=True, spacing=12, run_spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        self._reset_button = ft.TextButton(
            content=t("tags.reset"),
            icon=ft.Icons.RESTART_ALT,
            tooltip=t("tags.reset_tooltip"),
            on_click=lambda _: on_reset_thresholds(),
        )
        self._list = ft.ListView(expand=True, spacing=2)
        self._empty = ft.Text(t("tags.empty"), color=ft.Colors.ON_SURFACE_VARIANT)

        self.copy_button = ft.FilledButton(
            content=t("tags.copy"), icon=ft.Icons.CONTENT_COPY, on_click=lambda _: on_copy(), disabled=True
        )
        self._format_dropdown = ft.Dropdown(
            label=t("tags.format"),
            value=tag_format.value,
            options=[ft.DropdownOption(key=f.value, text=f.value) for f in TagFormat],
            on_select=self._handle_format,
            dense=True,
            width=200,
        )
        self._comma_checkbox = ft.Checkbox(
            label=t("tags.comma"), value=comma_separated, on_change=self._handle_separator
        )

        self._list_box = ft.Container(
            content=ft.Stack([self._empty, self._list], expand=True),
            expand=True,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=8,
        )
        self._column = ft.Column(
            [
                self._title,
                self._categories_row,
                self._list_box,
                ft.Row(
                    [self._format_dropdown, self._comma_checkbox],
                    wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self.copy_button,
            ],
            expand=True,
        )
        self.view = ft.Container(content=self._column, expand=True)

    def set_list_height(self, height: int | None) -> None:
        """Give the tag list a fixed height (for scrolling layouts), or None to fill the space."""
        fill = height is None
        self.view.expand = self._column.expand = self._list_box.expand = fill
        self._list_box.height = height

    def set_dark(self, dark: bool) -> None:
        """Switch category colors between Danbooru's light and dark palettes."""
        self._dark = dark
        self._render_categories()
        self._render()

    def set_categories(
        self,
        categories: tuple[Category, ...],
        enabled: set[Category],
        thresholds: dict[Category, float] | None,
    ) -> None:
        """Show a checkbox per category, plus a threshold field for each one in `thresholds`.

        `thresholds` is None for models that use the single global threshold instead.
        """
        self._categories = categories
        self._enabled = set(enabled)
        self._thresholds = dict(thresholds) if thresholds is not None else None
        self._render_categories()

    def set_tags(self, results: list[TagResult]) -> None:
        self._results = results
        self._render()

    def _color(self, category: Category) -> str:
        return category_color(category, self._dark) or ft.Colors.ON_SURFACE_VARIANT

    def _render_categories(self) -> None:
        controls: list[ft.Control] = []
        for category in self._categories:
            checkbox = ft.Checkbox(
                label=category.label,
                label_style=ft.TextStyle(color=self._color(category), weight=ft.FontWeight.W_500),
                value=category in self._enabled,
                data=category,
                on_change=self._handle_toggle,
            )
            if self._thresholds is None:
                controls.append(checkbox)
            elif category in self._thresholds:
                field = ft.TextField(
                    value=f"{self._thresholds[category]:.2f}",
                    data=category,
                    width=THRESHOLD_FIELD_WIDTH,
                    dense=True,
                    text_align=ft.TextAlign.RIGHT,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    input_filter=ft.InputFilter(r"[0-9.]"),
                    tooltip=t("tags.threshold_tooltip", category=category.label),
                    on_submit=self._handle_threshold,
                    on_blur=self._handle_threshold,
                )
                controls.append(ft.Row([checkbox, field], tight=True, spacing=6))
            else:
                # e.g. PixAI v0.9 copyright tags, derived from the detected characters
                checkbox.tooltip = t("tags.derived_tooltip")
                controls.append(checkbox)
        if self._thresholds is not None:
            controls.append(self._reset_button)
        self._categories_row.controls = controls
        self._categories_row.visible = bool(controls)

    def _render(self) -> None:
        self._list.controls = [
            ft.Row(
                [
                    ft.Text(
                        format_tag(result.name, self._format),
                        color=self._color(result.category),
                        selectable=True,
                        expand=True,
                    ),
                    ft.Text(f"{result.score:.3f}", color=ft.Colors.ON_SURFACE_VARIANT),
                ]
            )
            for result in self._results
        ]
        self._title.value = (
            t("tags.title_count", count=len(self._results)) if self._results else t("tags.title")
        )
        self._empty.visible = not self._results
        self.copy_button.disabled = not self._results

    def _handle_toggle(self, e: ft.Event[ft.Checkbox]) -> None:
        category: Category = e.control.data
        enabled = bool(e.control.value)
        if enabled:
            self._enabled.add(category)
        else:
            self._enabled.discard(category)
        self._on_category_toggle(category, enabled)

    def _handle_threshold(self, e: ft.Event[ft.TextField]) -> None:
        category: Category = e.control.data
        if self._thresholds is None or category not in self._thresholds:
            return
        value = parse_threshold(e.control.value or "")
        if value is None:
            # Invalid input: show the current value again
            e.control.value = f"{self._thresholds[category]:.2f}"
            return
        e.control.value = f"{value:.2f}"
        if value != self._thresholds[category]:
            self._thresholds[category] = value
            self._on_category_threshold(category, value)

    def _handle_format(self, e: ft.Event[ft.Dropdown]) -> None:
        self._format = TagFormat.parse(e.control.value or "")
        self._render()
        self._on_format_change(self._format)

    def _handle_separator(self, e: ft.Event[ft.Checkbox]) -> None:
        self._on_separator_change(bool(e.control.value))
