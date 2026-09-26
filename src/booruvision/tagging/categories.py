"""Tag categories, following Danbooru's, with their display colors."""

from enum import StrEnum


class Category(StrEnum):
    GENERAL = "general"
    CHARACTER = "character"
    COPYRIGHT = "copyright"
    # PixAI calls Danbooru's artist category "style"
    STYLE = "style"
    META = "meta"
    RATING = "rating"

    @property
    def label(self) -> str:
        return "Style (artist)" if self is Category.STYLE else self.value.capitalize()


# (light theme, dark theme) colors, taken from danbooru.donmai.us. Ratings have no Danbooru
# color and use the theme's secondary text color instead.
DANBOORU_COLORS: dict[Category, tuple[str, str]] = {
    Category.GENERAL: ("#0075f8", "#009be6"),
    Category.CHARACTER: ("#00ab2c", "#35c64a"),
    Category.COPYRIGHT: ("#a800aa", "#c797ff"),
    Category.STYLE: ("#c00004", "#ff8a8b"),
    Category.META: ("#fd9200", "#ead084"),
}

DEFAULT_ENABLED = frozenset({Category.GENERAL, Category.CHARACTER, Category.COPYRIGHT})


def category_color(category: Category, dark: bool) -> str | None:
    colors = DANBOORU_COLORS.get(category)
    return colors[dark] if colors else None
