import string

import pytest

from booruvision import i18n
from booruvision.hotkeys import Hotkey, HotkeyError
from booruvision.i18n import (
    CATALOGS,
    DEFAULT_LANGUAGE,
    Msg,
    match_language,
    resolve_language,
    set_language,
    t,
)
from booruvision.tagging.categories import Category


@pytest.fixture(autouse=True)
def restore_language():
    yield
    set_language(DEFAULT_LANGUAGE)


def placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


@pytest.mark.parametrize("code", sorted(set(CATALOGS) - {DEFAULT_LANGUAGE}))
def test_catalogs_have_the_same_keys_and_placeholders(code):
    english = CATALOGS[DEFAULT_LANGUAGE]
    catalog = CATALOGS[code]
    assert catalog.keys() == english.keys()
    for key, text in english.items():
        assert placeholders(catalog[key]) == placeholders(text), key


def test_every_category_has_a_label():
    for code in CATALOGS:
        set_language(code)
        assert all(category.label for category in Category)


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        (["zh-Hans-CN", "en-US"], "zh"),
        (["zh_TW"], "zh"),
        (["ja-JP"], "ja"),
        (["fr-FR", "ja_JP.UTF-8"], "ja"),
        (["en_US.UTF-8"], "en"),
        (["fr-FR"], "en"),
        ([], "en"),
    ],
)
def test_match_language(tags, expected):
    assert match_language(tags) == expected


def test_resolve_language():
    assert resolve_language("ja") == "ja"
    assert resolve_language("klingon") == DEFAULT_LANGUAGE
    assert resolve_language("auto") in CATALOGS


def test_t_formats_and_falls_back_to_unknown_language():
    set_language("zh")
    assert t("main.copied", count=3) == "已复制 3 个标签"
    set_language("xx")
    assert i18n.current_language() == DEFAULT_LANGUAGE


def test_msg_is_translated_when_shown():
    message = Msg("hotkey.needs_modifier")
    set_language("ja")
    assert str(message) == CATALOGS["ja"]["hotkey.needs_modifier"]
    set_language("en")
    assert str(message) == CATALOGS["en"]["hotkey.needs_modifier"]


def test_hotkey_errors_follow_the_language():
    with pytest.raises(HotkeyError) as info:
        Hotkey.parse("Ctrl+F25")
    set_language("zh")
    assert str(info.value) == "不支持的按键 F25：请使用 A-Z、0-9 或 F1-F24"
