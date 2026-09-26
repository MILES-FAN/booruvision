"""UI translations: English, Simplified Chinese and Japanese.

`t(key, **params)` looks up the current language's text and fills in `{param}` placeholders.
Messages created before the text is shown (hotkey errors, backend status) use `Msg`, which is
translated when it is turned into a string, so it follows later language changes.
"""

import logging
import os
import sys

from booruvision.i18n import en, ja, zh_hans

log = logging.getLogger(__name__)

AUTO = "auto"
DEFAULT_LANGUAGE = "en"
# Language code -> name shown in the language picker (always in its own language)
LANGUAGES = {"en": "English", "zh": "简体中文", "ja": "日本語"}
CATALOGS: dict[str, dict[str, str]] = {"en": en.MESSAGES, "zh": zh_hans.MESSAGES, "ja": ja.MESSAGES}

_current = DEFAULT_LANGUAGE


def t(key: str, /, **params: object) -> str:
    text = CATALOGS[_current].get(key) or CATALOGS[DEFAULT_LANGUAGE][key]
    return text.format(**params) if params else text


class Msg:
    """A translatable message, rendered in the language current when it is shown."""

    def __init__(self, key: str, /, **params: object) -> None:
        self.key = key
        self.params = params

    def __str__(self) -> str:
        return t(self.key, **self.params)

    def __repr__(self) -> str:
        return f"Msg({self.key!r}, {self.params!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Msg) and (self.key, self.params) == (other.key, other.params)

    __hash__ = None  # type: ignore[assignment]


def current_language() -> str:
    return _current


def set_language(code: str) -> None:
    global _current
    _current = code if code in CATALOGS else DEFAULT_LANGUAGE


def match_language(tags: list[str]) -> str:
    """The first supported language in a preference list of locale tags like 'zh-Hans-CN'."""
    for tag in tags:
        code = tag.replace("_", "-").split("-")[0].lower()
        if code in CATALOGS:
            # Traditional Chinese readers get the simplified translation rather than English
            return code
    return DEFAULT_LANGUAGE


def _system_locale_tags() -> list[str]:
    if sys.platform == "darwin":
        try:
            from Foundation import NSLocale

            return [str(tag) for tag in NSLocale.preferredLanguages()]
        except Exception:  # noqa: BLE001 - fall back to the environment
            log.debug("NSLocale unavailable", exc_info=True)
    elif sys.platform == "win32":
        import ctypes
        import locale

        lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        if name := locale.windows_locale.get(lcid):
            return [name]
    tags: list[str] = []
    for var in ("LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        # LANGUAGE is a colon-separated preference list; C/POSIX mean "no preference"
        tags += [v for v in os.environ.get(var, "").split(":") if v and v not in ("C", "POSIX")]
    return tags


def detect_system_language() -> str:
    try:
        return match_language(_system_locale_tags())
    except Exception:  # noqa: BLE001 - never fail startup over language detection
        log.warning("Could not detect the system language", exc_info=True)
        return DEFAULT_LANGUAGE


def resolve_language(setting: str) -> str:
    """Language code for a config value: 'auto' follows the system, unknown values fall back."""
    if setting == AUTO:
        return detect_system_language()
    return setting if setting in CATALOGS else DEFAULT_LANGUAGE
