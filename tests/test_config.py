from booruvision.config import ConfigStore, Settings
from booruvision.formatting import TagFormat
from booruvision.tagging.categories import DEFAULT_ENABLED, Category

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


def test_round_trip_categories_and_thresholds(tmp_path):
    store = ConfigStore(tmp_path / "config.ini", legacy_path=tmp_path / "none.ini")
    settings = Settings(
        enabled_categories={Category.GENERAL, Category.META},
        category_thresholds={"pixai-v1.0": {Category.GENERAL: 0.25, Category.RATING: 0.5}},
    )
    store.save(settings)
    assert store.load() == settings
    assert "[Thresholds pixai-v1.0]" in store.path.read_text()


def test_legacy_config_gets_default_categories(tmp_path):
    path = tmp_path / "config.ini"
    path.write_text(LEGACY_CONFIG)
    settings = ConfigStore(path, legacy_path=tmp_path / "none.ini").load()
    assert settings.enabled_categories == set(DEFAULT_ENABLED)
    assert settings.category_thresholds == {}


def test_invalid_category_values_are_ignored(tmp_path):
    path = tmp_path / "config.ini"
    path.write_text(
        "[GUI]\ncategories = nonsense, character\n"
        "[Tagger]\nmodel = wd-vit-v3\nthreshold = 0.5\n"
        "[Thresholds pixai-v1.0]\ngeneral = 0.2\ncharacter = abc\nmeta = 1.5\nbogus = 0.3\n"
    )
    settings = ConfigStore(path, legacy_path=tmp_path / "none.ini").load()
    # The rest of the file still loads
    assert settings.model == "wd-vit-v3" and settings.threshold == 0.5
    assert settings.enabled_categories == {Category.CHARACTER}
    assert settings.category_thresholds == {"pixai-v1.0": {Category.GENERAL: 0.2}}


def test_categories_fall_back_to_defaults_when_none_are_valid(tmp_path):
    path = tmp_path / "config.ini"
    path.write_text("[GUI]\ncategories = nonsense\n")
    settings = ConfigStore(path, legacy_path=tmp_path / "none.ini").load()
    assert settings.enabled_categories == set(DEFAULT_ENABLED)
