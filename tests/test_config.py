from booruvision.config import ConfigStore, Settings
from booruvision.formatting import TagFormat

LEGACY_CONFIG = """\
[GUI]
shortcut = Ctrl+Shift+K
unload_model_when_done = True
tag_format = Stable Diffusion

[Tagger]
model = wd-vit-v3
threshold = 0.5
"""


def test_missing_config_creates_defaults(tmp_path):
    store = ConfigStore(tmp_path / "cfg" / "config.ini", legacy_path=tmp_path / "none.ini")
    assert store.load() == Settings()
    assert store.path.exists()


def test_round_trip(tmp_path):
    store = ConfigStore(tmp_path / "config.ini", legacy_path=tmp_path / "none.ini")
    settings = Settings(
        shortcut="Ctrl+Shift+J",
        unload_model_when_done=True,
        tag_format=TagFormat.STABLE_DIFFUSION,
        comma_separated=True,
        model="wd-convnext-v3",
        threshold=0.42,
    )
    store.save(settings)
    assert store.load() == settings


def test_imports_legacy_config_from_working_directory(tmp_path):
    legacy = tmp_path / "config.ini"
    legacy.write_text(LEGACY_CONFIG)
    store = ConfigStore(tmp_path / "user" / "config.ini", legacy_path=legacy)

    settings = store.load()

    assert settings.shortcut == "Ctrl+Shift+K"
    assert settings.unload_model_when_done is True
    assert settings.tag_format is TagFormat.STABLE_DIFFUSION
    assert settings.comma_separated is False
    assert settings.model == "wd-vit-v3"
    assert settings.threshold == 0.5
    assert store.path.exists()


def test_invalid_config_falls_back_to_defaults(tmp_path):
    path = tmp_path / "config.ini"
    path.write_text("[Tagger]\nthreshold = not-a-number\n")
    store = ConfigStore(path, legacy_path=tmp_path / "none.ini")
    assert store.load() == Settings()
