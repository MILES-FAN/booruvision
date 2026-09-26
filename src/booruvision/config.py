"""User settings, stored as config.ini in the per-user config directory."""

import configparser
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_config_path

from booruvision.formatting import TagFormat
from booruvision.tagging.categories import DEFAULT_ENABLED, Category
from booruvision.tagging.models import DEFAULT_MODEL

log = logging.getLogger(__name__)

APP_NAME = "booruvision"
CONFIG_FILENAME = "config.ini"
# One section per model with per-category threshold overrides, e.g. [Thresholds pixai-v1.0]
THRESHOLDS_SECTION_PREFIX = "Thresholds "


def default_config_path() -> Path:
    return user_config_path(APP_NAME, appauthor=False, ensure_exists=True) / CONFIG_FILENAME


@dataclass
class Settings:
    shortcut: str = "Ctrl+Shift+I"
    unload_model_when_done: bool = False
    tag_format: TagFormat = TagFormat.BOORU
    comma_separated: bool = False
    model: str = DEFAULT_MODEL
    threshold: float = 0.35
    enabled_categories: set[Category] = field(default_factory=lambda: set(DEFAULT_ENABLED))
    # model -> thresholds the user changed from the model's recommended ones
    category_thresholds: dict[str, dict[Category, float]] = field(default_factory=dict)


def _parse_categories(value: str) -> set[Category]:
    categories = {Category(name) for name in value.replace(" ", "").split(",") if name in Category}
    return categories or set(DEFAULT_ENABLED)


def _parse_thresholds(section: configparser.SectionProxy) -> dict[Category, float]:
    thresholds = {}
    for key, value in section.items():
        try:
            threshold = float(value)
        except ValueError:
            continue
        if key in Category and 0 < threshold < 1:
            thresholds[Category(key)] = threshold
    return thresholds


class ConfigStore:
    def __init__(self, path: Path | None = None, legacy_path: Path | None = None):
        self.path = path or default_config_path()
        # Older releases wrote config.ini into the working directory
        self.legacy_path = legacy_path if legacy_path is not None else Path.cwd() / CONFIG_FILENAME

    def load(self) -> Settings:
        if not self.path.exists() and self.legacy_path.is_file():
            log.info("Importing legacy config from %s", self.legacy_path)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.legacy_path, self.path)

        settings = Settings()
        if not self.path.exists():
            self.save(settings)
            return settings

        parser = configparser.ConfigParser()
        try:
            parser.read(self.path, encoding="utf-8")
            gui = parser["GUI"] if parser.has_section("GUI") else {}
            tagger = parser["Tagger"] if parser.has_section("Tagger") else {}
            settings.shortcut = gui.get("shortcut", settings.shortcut)
            if "unload_model_when_done" in gui:
                settings.unload_model_when_done = parser.getboolean("GUI", "unload_model_when_done")
            if "comma_separated" in gui:
                settings.comma_separated = parser.getboolean("GUI", "comma_separated")
            settings.tag_format = TagFormat.parse(gui.get("tag_format", settings.tag_format.value))
            settings.model = tagger.get("model", settings.model)
            settings.threshold = float(tagger.get("threshold", settings.threshold))
            if "categories" in gui:
                settings.enabled_categories = _parse_categories(gui["categories"])
            for section in parser.sections():
                if section.startswith(THRESHOLDS_SECTION_PREFIX):
                    if thresholds := _parse_thresholds(parser[section]):
                        settings.category_thresholds[section.removeprefix(THRESHOLDS_SECTION_PREFIX)] = (
                            thresholds
                        )
        except (configparser.Error, ValueError) as e:
            log.warning("Invalid config file %s (%s), using defaults", self.path, e)
            settings = Settings()
            self.save(settings)
        return settings

    def save(self, settings: Settings) -> None:
        parser = configparser.ConfigParser()
        parser["GUI"] = {
            "shortcut": settings.shortcut,
            "unload_model_when_done": str(settings.unload_model_when_done),
            "tag_format": settings.tag_format.value,
            "comma_separated": str(settings.comma_separated),
            # Saved in Category order so the file doesn't change between runs
            "categories": ",".join(c.value for c in Category if c in settings.enabled_categories),
        }
        parser["Tagger"] = {
            "model": settings.model,
            "threshold": str(settings.threshold),
        }
        for model, thresholds in settings.category_thresholds.items():
            if thresholds:
                parser[THRESHOLDS_SECTION_PREFIX + model] = {c.value: str(t) for c, t in thresholds.items()}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            parser.write(f)
