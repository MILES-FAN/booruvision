"""Raw model output for one image, filtered on demand.

A Prediction keeps the score of every tag, so changing thresholds or the selected categories
only re-filters it instead of running the model again.
"""

from dataclasses import dataclass, field

import numpy as np

from booruvision.tagging.categories import Category

_CATEGORY_INDEX = {category: i for i, category in enumerate(Category)}


@dataclass(frozen=True)
class TagResult:
    name: str
    category: Category
    score: float


@dataclass
class Prediction:
    names: list[str]
    categories: list[Category]
    scores: np.ndarray
    # Character tag -> copyright tags, for models that only predict characters (PixAI v0.9)
    derived_copyright: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.scores = np.asarray(self.scores, dtype=np.float32).reshape(-1)
        if not len(self.names) == len(self.categories) == len(self.scores):
            raise ValueError("names, categories and scores must have the same length")
        self._codes = np.array([_CATEGORY_INDEX[c] for c in self.categories], dtype=np.int8)

    def select(self, thresholds: dict[Category, float], enabled: set[Category]) -> list[TagResult]:
        """Tags whose score is at least their category's threshold, highest score first.

        Categories missing from `thresholds` never match.
        """
        limits = np.full(len(Category), np.inf, dtype=np.float32)
        for category, threshold in thresholds.items():
            limits[_CATEGORY_INDEX[category]] = threshold
        (indices,) = np.nonzero(self.scores >= limits[self._codes])

        results: dict[str, TagResult] = {}
        derived: dict[str, float] = {}
        for i in indices:
            name, category, score = self.names[i], self.categories[i], float(self.scores[i])
            if category in enabled:
                results[name] = TagResult(name, category, score)
            for copyright_tag in self.derived_copyright.get(name, ()):
                derived[copyright_tag] = max(score, derived.get(copyright_tag, 0.0))

        if Category.COPYRIGHT in enabled:
            for name, score in derived.items():
                results.setdefault(name, TagResult(name, Category.COPYRIGHT, score))

        return sorted(results.values(), key=lambda r: r.score, reverse=True)
