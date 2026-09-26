from types import SimpleNamespace

import pytest

from booruvision.hotkeys import Hotkey, HotkeyError, Modifier
from booruvision.ui.config_page import hotkey_from_key_event


def key_event(key, ctrl=False, alt=False, shift=False, meta=False):
    return SimpleNamespace(key=key, ctrl=ctrl, alt=alt, shift=shift, meta=meta)


def test_records_modifiers_and_key():
    hotkey = hotkey_from_key_event(key_event("K", ctrl=True, shift=True))
    assert hotkey == Hotkey.parse("Ctrl+Shift+K")


def test_function_key_with_meta():
    assert hotkey_from_key_event(key_event("F5", meta=True)) == Hotkey(frozenset({Modifier.META}), "F5")


@pytest.mark.parametrize("key", ["Shift Left", "Control Right", "Meta Left", "Alt Left", "Caps Lock"])
def test_modifier_only_press_is_ignored(key):
    assert hotkey_from_key_event(key_event(key, ctrl=True, shift=True)) is None


def test_key_without_modifier_is_rejected():
    with pytest.raises(HotkeyError):
        hotkey_from_key_event(key_event("A"))


def test_unsupported_key_is_rejected():
    with pytest.raises(HotkeyError):
        hotkey_from_key_event(key_event("Space", ctrl=True))
