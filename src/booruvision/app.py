"""BooruVision main window."""

import asyncio
import logging
import sys
from pathlib import Path

import flet as ft
from PIL import Image, UnidentifiedImageError

from booruvision import clipboard
from booruvision.config import ConfigStore, Settings
from booruvision.formatting import TagFormat, join_tags
from booruvision.hotkeys import Hotkey, HotkeyBackend, HotkeyError, create_backend
from booruvision.tagging import TaggerService
from booruvision.tagging.categories import Category
from booruvision.tagging.models import DEFAULT_MODEL
from booruvision.tagging.prediction import Prediction, TagResult
from booruvision.ui.config_page import CONFIG_ROUTE, DEFAULT_SHORTCUT, ConfigPage, display_shortcut
from booruvision.ui.image_panel import ImagePanel
from booruvision.ui.settings_bar import SettingsBar
from booruvision.ui.tag_panel import TagPanel

log = logging.getLogger(__name__)

APP_TITLE = "BooruVision"
# Below this logical width the image and tag panels stack vertically
NARROW_LAYOUT_WIDTH = 820
# Panel heights in the narrow, scrolling layout
NARROW_IMAGE_HEIGHT = 280
NARROW_TAG_LIST_HEIGHT = 320
FILE_EXTENSIONS = ["png", "jpg", "jpeg", "bmp", "gif", "webp"]
# Window icon; only used on Windows (other platforms take the icon from the app bundle)
WINDOW_ICON = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"


class BooruVisionApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.store = ConfigStore()
        self.settings: Settings = self.store.load()
        if self.settings.model not in TaggerService.available_models():
            log.warning("Unknown model %r in config, using %s", self.settings.model, DEFAULT_MODEL)
            self.settings.model = DEFAULT_MODEL
        try:
            self.settings.shortcut = str(Hotkey.parse(self.settings.shortcut))
        except HotkeyError as e:
            log.warning("%s, using %s", e, DEFAULT_SHORTCUT)
            self.settings.shortcut = DEFAULT_SHORTCUT

        self.tagger = TaggerService(
            model=self.settings.model,
            unload_after=self.settings.unload_model_when_done,
        )
        self.hotkeys: HotkeyBackend = create_backend()
        self.image: Image.Image | None = None
        # Raw output of the last analysis; threshold and category changes re-filter it
        self.prediction: Prediction | None = None
        self.tags: list[TagResult] = []
        self.busy = False

        self.image_panel = ImagePanel()
        self.tag_panel = TagPanel(
            tag_format=self.settings.tag_format,
            comma_separated=self.settings.comma_separated,
            on_copy=lambda: self.page.run_task(self.copy_tags),
            on_format_change=self.change_tag_format,
            on_separator_change=self.change_separator,
            on_category_toggle=self.toggle_category,
            on_category_threshold=self.change_category_threshold,
            on_reset_thresholds=self.reset_category_thresholds,
        )
        self.settings_bar = SettingsBar(
            models=TaggerService.available_models(),
            model=self.settings.model,
            threshold=self.settings.threshold,
            shortcut=display_shortcut(Hotkey.parse(self.settings.shortcut)),
            unload_after=self.settings.unload_model_when_done,
            on_model_change=self.change_model,
            on_threshold_change=self.change_threshold,
            on_unload_change=self.change_unload,
            on_open_config=self.open_config,
        )
        self._apply_model_controls()
        self.config_page = ConfigPage(page, shortcut=self.settings.shortcut, on_apply=self.change_shortcut)

        self.clipboard_button = ft.Button(
            content="From clipboard", icon=ft.Icons.CONTENT_PASTE, on_click=self._on_clipboard_click
        )
        self.file_button = ft.Button(
            content="From file", icon=ft.Icons.FOLDER_OPEN, on_click=self._on_file_click
        )
        self.analyze_button = ft.FilledButton(
            content="Analyze", icon=ft.Icons.AUTO_AWESOME, on_click=self._on_analyze_click, disabled=True
        )
        self.progress = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)
        self.status = ft.Text("", color=ft.Colors.ON_SURFACE_VARIANT)

        self.image_column = ft.Column(
            [
                self.image_panel.view,
                ft.Row(
                    [
                        self.clipboard_button,
                        self.file_button,
                        self.analyze_button,
                        self.progress,
                        self.status,
                    ],
                    wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            expand=True,
        )
        self.panels = ft.Container(expand=True)

    # ---- setup -------------------------------------------------------------

    def build(self) -> None:
        page = self.page
        page.title = APP_TITLE
        page.theme_mode = ft.ThemeMode.SYSTEM
        page.padding = 16
        page.window.width = 1100
        page.window.height = 720
        page.window.min_width = 480
        page.window.min_height = 560
        if sys.platform == "win32" and WINDOW_ICON.is_file():
            page.window.icon = str(WINDOW_ICON)
        page.on_resize = lambda _: self._apply_layout()
        page.on_close = lambda _: self.hotkeys.stop()
        page.on_route_change = lambda _: self._on_route_change()
        page.on_view_pop = self._on_view_pop
        page.on_keyboard_event = self.config_page.handle_key
        page.on_platform_brightness_change = lambda _: self._apply_brightness()
        self._apply_brightness(update=False)

        self.root = ft.Column([self.panels, ft.Divider(height=1), self.settings_bar.view], expand=True)
        self._apply_layout()
        page.add(self.root)
        self._refresh_hotkey_status()
        page.run_task(self._register_initial_hotkey)

    def _apply_layout(self) -> None:
        narrow = (self.page.width or 0) < NARROW_LAYOUT_WIDTH
        if isinstance(self.panels.content, ft.Column if narrow else ft.Row):
            return

        children = [self.image_column, self.tag_panel.view]
        if narrow:
            # Stacked panels would split the remaining height and can squeeze the tag list
            # to nothing, so give them fixed heights and let the whole page scroll instead.
            self.root.scroll = ft.ScrollMode.AUTO
            self.panels.expand = False
            self.image_column.expand = False
            self.image_panel.set_height(NARROW_IMAGE_HEIGHT)
            self.tag_panel.set_list_height(NARROW_TAG_LIST_HEIGHT)
            self.panels.content = ft.Column(children, spacing=16)
        else:
            self.root.scroll = None
            self.panels.expand = True
            self.image_column.expand = 3
            self.image_panel.set_height(None)
            self.tag_panel.set_list_height(None)
            self.tag_panel.view.expand = 2
            self.panels.content = ft.Row(
                children, expand=True, spacing=16, vertical_alignment=ft.CrossAxisAlignment.STRETCH
            )
        self.page.update()

    def _apply_brightness(self, update: bool = True) -> None:
        self.tag_panel.set_dark(self.page.platform_brightness == ft.Brightness.DARK)
        if update:
            self.page.update()

    async def _register_initial_hotkey(self) -> None:
        try:
            hotkey = Hotkey.parse(self.settings.shortcut)
            await asyncio.to_thread(self.hotkeys.register, hotkey, self._on_hotkey)
        except (HotkeyError, TimeoutError) as e:
            log.warning("Could not register hotkey %s: %s", self.settings.shortcut, e)
            self.hotkeys.status_message = str(e)
        self._refresh_hotkey_status()
        self.page.update()

    def _refresh_hotkey_status(self) -> None:
        enabled = self.hotkeys.available and self.hotkeys.configurable
        self.settings_bar.set_hotkey_status(self.hotkeys.status_message)
        self.config_page.set_hotkey_status(self.hotkeys.status_message, enabled=enabled)

    # ---- navigation -----------------------------------------------------------

    async def open_config(self) -> None:
        await self.page.push_route(CONFIG_ROUTE)

    def _on_route_change(self) -> None:
        # views[0] is the main window; the config page is pushed on top of it
        del self.page.views[1:]
        if self.page.route == CONFIG_ROUTE:
            self.page.views.append(self.config_page.view())
        else:
            self.config_page.on_leave()
        self.page.update()

    async def _on_view_pop(self, _) -> None:
        await self.page.push_route("/")

    # ---- helpers ------------------------------------------------------------

    def _snack(self, message: str) -> None:
        self.page.show_dialog(ft.SnackBar(ft.Text(message)))

    def _set_busy(self, busy: bool, message: str = "") -> None:
        self.busy = busy
        self.progress.visible = busy
        self.status.value = message
        for button in (self.clipboard_button, self.file_button):
            button.disabled = busy
        self.analyze_button.disabled = busy or self.image is None
        self.page.update()

    def _set_image(self, image: Image.Image) -> None:
        self.image = image
        self.image_panel.show(image)
        self.analyze_button.disabled = self.busy
        self.page.update()

    def _category_thresholds(self) -> dict[Category, float] | None:
        """The current model's per-category thresholds, or None if it uses the global one."""
        defaults = TaggerService.info(self.tagger.model).default_thresholds
        if defaults is None:
            return None
        return defaults | self.settings.category_thresholds.get(self.tagger.model, {})

    def _thresholds(self) -> dict[Category, float]:
        thresholds = self._category_thresholds()
        if thresholds is None:
            return {c: self.settings.threshold for c in Category}
        return thresholds

    def _apply_model_controls(self) -> None:
        thresholds = self._category_thresholds()
        self.settings_bar.set_threshold_visible(thresholds is None)
        self.tag_panel.set_categories(
            TaggerService.info(self.tagger.model).categories, self.settings.enabled_categories, thresholds
        )

    def _refresh_tags(self) -> None:
        """Re-filter the last prediction with the current thresholds and categories."""
        self.tags = (
            self.prediction.select(self._thresholds(), self.settings.enabled_categories)
            if self.prediction is not None
            else []
        )
        self.tag_panel.set_tags(self.tags)
        self.page.update()

    def _save_settings(self) -> None:
        try:
            self.store.save(self.settings)
        except OSError as e:
            log.exception("Failed to save settings")
            self._snack(f"Could not save settings: {e}")

    # ---- actions ------------------------------------------------------------

    async def load_from_clipboard(self) -> bool:
        image = await clipboard.read_image()
        if image is None:
            self._snack("The clipboard does not contain an image")
            return False
        self._set_image(image)
        return True

    async def load_from_file(self) -> None:
        files = await ft.FilePicker().pick_files(
            dialog_title="Open image",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=FILE_EXTENSIONS,
        )
        if not files or not files[0].path:
            return
        try:
            image = await asyncio.to_thread(Image.open, files[0].path)
        except (UnidentifiedImageError, OSError) as e:
            self.image_panel.show_error(f"Could not open image: {e}")
            self.page.update()
            return
        self._set_image(image)

    async def analyze(self) -> None:
        if self.image is None:
            self._snack("Load an image first")
            return
        if self.busy:
            return
        message = f"Analyzing with {self.tagger.model}…"
        if not self.tagger.is_loaded():
            message = f"Loading {self.tagger.model} (downloaded on first use)…"
        self._set_busy(True, message)
        try:
            self.prediction = await asyncio.to_thread(self.tagger.predict, self.image)
        except Exception as e:
            log.exception("Analysis failed")
            self._snack(f"Analysis failed: {e}")
        else:
            self._refresh_tags()
        finally:
            self._set_busy(False)

    async def copy_tags(self) -> None:
        text = join_tags([t.name for t in self.tags], self.settings.tag_format, self.settings.comma_separated)
        await ft.Clipboard().set(text)
        self._snack(f"Copied {len(self.tags)} tags")

    async def analyze_clipboard_and_focus(self) -> None:
        if self.busy:
            return
        if await self.load_from_clipboard():
            await self.analyze()
        self.page.window.minimized = False
        self.page.update()
        await self.page.window.to_front()

    # ---- settings -------------------------------------------------------------

    async def change_model(self, model: str) -> None:
        await asyncio.to_thread(self.tagger.set_model, model)
        self.settings.model = model
        self._save_settings()
        # The last result came from the previous model and doesn't match its thresholds
        self.prediction = None
        self._apply_model_controls()
        self._refresh_tags()

    def change_threshold(self, threshold: float) -> None:
        self.settings.threshold = threshold
        self._save_settings()
        self._refresh_tags()

    def toggle_category(self, category: Category, enabled: bool) -> None:
        if enabled:
            self.settings.enabled_categories.add(category)
        else:
            self.settings.enabled_categories.discard(category)
        self._save_settings()
        self._refresh_tags()

    def change_category_threshold(self, category: Category, threshold: float) -> None:
        overrides = self.settings.category_thresholds.setdefault(self.tagger.model, {})
        defaults = TaggerService.info(self.tagger.model).default_thresholds or {}
        if threshold == defaults.get(category):
            overrides.pop(category, None)
        else:
            overrides[category] = threshold
        self._save_settings()
        self._refresh_tags()

    def reset_category_thresholds(self) -> None:
        self.settings.category_thresholds.pop(self.tagger.model, None)
        self._save_settings()
        self._apply_model_controls()
        self._refresh_tags()

    def change_unload(self, unload: bool) -> None:
        self.tagger.unload_after = unload
        self.settings.unload_model_when_done = unload
        self._save_settings()
        if unload and not self.busy:
            self.page.run_thread(self.tagger.unload)

    def change_tag_format(self, tag_format: TagFormat) -> None:
        self.settings.tag_format = tag_format
        self._save_settings()

    def change_separator(self, comma_separated: bool) -> None:
        self.settings.comma_separated = comma_separated
        self._save_settings()

    async def change_shortcut(self, shortcut: str) -> bool:
        """Register `shortcut`, keeping the previous one on failure. Returns success."""
        old = self.settings.shortcut
        success = False
        try:
            hotkey = Hotkey.parse(shortcut)
            await asyncio.to_thread(self.hotkeys.register, hotkey, self._on_hotkey)
        except (HotkeyError, TimeoutError) as e:
            self._snack(f"Could not set shortcut: {e}")
            try:
                await asyncio.to_thread(self.hotkeys.register, Hotkey.parse(old), self._on_hotkey)
            except (HotkeyError, TimeoutError):
                log.exception("Failed to restore previous hotkey %s", old)
        else:
            self.settings.shortcut = str(hotkey)
            self.settings_bar.set_shortcut(display_shortcut(hotkey))
            self._save_settings()
            self._snack(f"Global shortcut set to {hotkey}")
            success = True
        self._refresh_hotkey_status()
        self.page.update()
        return success

    # ---- event adapters --------------------------------------------------------

    def _on_hotkey(self) -> None:
        # Called on the hotkey backend's thread
        if self.config_page.recording:
            return
        self.page.run_task(self.analyze_clipboard_and_focus)

    async def _on_clipboard_click(self, _) -> None:
        await self.load_from_clipboard()

    async def _on_file_click(self, _) -> None:
        await self.load_from_file()

    async def _on_analyze_click(self, _) -> None:
        await self.analyze()


def main(page: ft.Page) -> None:
    BooruVisionApp(page).build()
