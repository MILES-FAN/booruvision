"""User settings, stored as config.ini in the per-user config directory."""

import configparser
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_path

from booruvision.formatting import TagFormat
from booruvision.tagging.models import DEFAULT_MODEL

log = logging.getLogger(__name__)

APP_NAME = "booruvision"
CONFIG_FILENAME = "config.ini"


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
        }
        parser["Tagger"] = {
            "model": settings.model,
            "threshold": str(settings.threshold),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            parser.write(f)
