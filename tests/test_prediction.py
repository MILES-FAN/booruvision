import numpy as np
import pytest

from booruvision.tagging.categories import Category
from booruvision.tagging.prediction import Prediction, TagResult

G, C, R = Category.GENERAL, Category.CHARACTER, Category.RATING


def make_prediction(**kwargs) -> Prediction:
    return Prediction(
        names=["a", "b", "c", "d", "miku", "rating:g"],
        categories=[G, G, G, G, C, R],
        scores=np.array([0.2, 0.9, 0.5, 0.35, 0.6, 0.8]),
        **kwargs,
    )


def test_select_filters_by_threshold_inclusively_and_sorts_by_score():
    results = make_prediction().select({G: 0.35}, {G})
    assert [(r.name, round(r.score, 2)) for r in results] == [("b", 0.9), ("c", 0.5), ("d", 0.35)]
    assert all(isinstance(r, TagResult) and r.category is G for r in results)


def test_select_uses_per_category_thresholds_and_enabled_categories():
    p = make_prediction()
    assert [r.name for r in p.select({G: 0.4, C: 0.7, R: 0.5}, {G, C, R})] == ["b", "rating:g", "c"]
    assert [r.name for r in p.select({G: 0.4, C: 0.5}, {C})] == ["miku"]
    # A category without a threshold never matches
    assert p.select({G: 0.4}, {C}) == []


def test_select_derives_copyright_from_characters():
    p = Prediction(
        names=["miku", "rin", "hat"],
        categories=[C, C, G],
        scores=np.array([0.9, 0.95, 0.99]),
        derived_copyright={"miku": ["vocaloid"], "rin": ["vocaloid", "project_diva"]},
    )
    results = p.select({C: 0.85, G: 0.3}, {Category.COPYRIGHT})
    assert [(r.name, r.category, round(r.score, 2)) for r in results] == [
        ("vocaloid", Category.COPYRIGHT, 0.95),
        ("project_diva", Category.COPYRIGHT, 0.95),
    ]
    # Characters below their threshold contribute nothing, even with copyright enabled
    assert p.select({C: 0.99, G: 0.3}, {Category.COPYRIGHT}) == []


def test_prediction_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        Prediction(names=["a"], categories=[G, G], scores=np.zeros(2))
