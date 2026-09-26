"""Tag output formats."""

from collections.abc import Iterable
from enum import StrEnum


class TagFormat(StrEnum):
    BOORU = "Booru"
    STABLE_DIFFUSION = "Stable Diffusion"

    @classmethod
    def parse(cls, value: str) -> "TagFormat":
        for fmt in cls:
            if fmt.value.lower() == value.strip().lower():
                return fmt
        return cls.BOORU


def format_tag(tag: str, fmt: TagFormat) -> str:
    if fmt is TagFormat.STABLE_DIFFUSION:
        return tag.replace("_", " ").replace("(", r"\(").replace(")", r"\)")
    return tag


def join_tags(tags: Iterable[str], fmt: TagFormat, comma_separated: bool) -> str:
    separator = ", " if comma_separated else " "
    return separator.join(format_tag(tag, fmt) for tag in tags)
