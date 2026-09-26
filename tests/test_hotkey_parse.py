import pytest

from booruvision.hotkeys import Hotkey, HotkeyError, Modifier


def test_parse_basic():
    hotkey = Hotkey.parse("Ctrl+Shift+I")
    assert hotkey.modifiers == {Modifier.CTRL, Modifier.SHIFT}
    assert hotkey.key == "I"


def test_parse_normalises_aliases_case_and_order():
    hotkey = Hotkey.parse("shift + cmd + alt + ctrl + k")
    assert hotkey.modifiers == set(Modifier)
    assert str(hotkey) == "Ctrl+Alt+Shift+Meta+K"


@pytest.mark.parametrize("key", ["F1", "f12", "F24", "0", "9"])
def test_parse_accepts_function_and_digit_keys(key):
    assert Hotkey.parse(f"Ctrl+{key}").key == key.upper()


@pytest.mark.parametrize("text", ["I", "Ctrl+", "Ctrl++I", "Hyper+I", "Ctrl+Space", "Ctrl+F25", "Ctrl+é"])
def test_parse_rejects_invalid(text):
    with pytest.raises(HotkeyError):
        Hotkey.parse(text)


def test_round_trip_is_stable():
    assert str(Hotkey.parse(str(Hotkey.parse("Ctrl+Shift+J")))) == "Ctrl+Shift+J"


def test_create_requires_a_modifier():
    with pytest.raises(HotkeyError):
        Hotkey.create([], "A")
    assert str(Hotkey.create([Modifier.ALT], "f3")) == "Alt+F3"
