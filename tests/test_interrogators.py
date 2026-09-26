import csv
import io

import numpy as np
import pytest
from PIL import Image

from booruvision.tagging.categories import Category
from booruvision.tagging.interrogator import PixAIV09Interrogator, PixAIV1Interrogator, _sigmoid
from booruvision.tagging.models import interrogators

TAG_MAP = {
    "num_classes": 4,
    "categories": [
        {"name": "general", "offset": 0, "count": 2, "tags": ["1girl", "hat"]},
        {"name": "style", "offset": 2, "count": 1, "tags": ["some_artist"]},
        {"name": "rating", "offset": 3, "count": 1, "tags": ["rating:g"]},
    ],
}

V09_CSV = """\
id,tag_id,name,category,count,ips
0,1,1girl,0,100,[]
1,2,hatsune_miku,4,50,"[""vocaloid""]"
"""


class FakeInput:
    name = "input"


class FakeSession:
    def __init__(self, output: np.ndarray):
        self.output = output
        self.inputs = []

    def get_inputs(self):
        return [FakeInput()]

    def run(self, names, feed):
        self.inputs.append(feed["input"])
        return [self.output]


def test_sigmoid_is_stable_for_large_logits():
    y = _sigmoid(np.array([-1000.0, 0.0, 1000.0], dtype=np.float32))
    assert np.allclose(y, [0, 0.5, 1]) and np.isfinite(y).all()


def test_pixai_v1_parses_tag_map_in_model_order():
    names, categories = PixAIV1Interrogator.parse_tags(TAG_MAP)
    assert names == ["1girl", "hat", "some_artist", "rating:g"]
    assert categories == [Category.GENERAL, Category.GENERAL, Category.STYLE, Category.RATING]


def test_pixai_v1_rejects_inconsistent_tag_map():
    bad = {**TAG_MAP, "num_classes": 5}
    with pytest.raises(ValueError):
        PixAIV1Interrogator.parse_tags(bad)


def test_pixai_v1_interrogate_applies_sigmoid_to_logits():
    it = PixAIV1Interrogator("test", repo_id="x", revision="y")
    it.image_size = 8
    it.tags, it.tag_categories = PixAIV1Interrogator.parse_tags(TAG_MAP)
    it.model = FakeSession(np.array([[5.0, -5.0, 0.0, 2.0]], dtype=np.float32))

    p = it.interrogate(Image.new("RGB", (12, 6)))

    assert it.model.inputs[0].shape == (1, 3, 8, 8)
    assert np.allclose(p.scores, _sigmoid(np.array([5.0, -5.0, 0.0, 2.0])))
    assert [r.name for r in p.select(it.default_thresholds, set(Category))] == [
        "1girl",
        "rating:g",
        "some_artist",
    ]


def test_pixai_v09_parses_categories_and_ips():
    names, categories, ips = PixAIV09Interrogator.parse_tags(csv.DictReader(io.StringIO(V09_CSV)))
    assert names == ["1girl", "hatsune_miku"]
    assert categories == [Category.GENERAL, Category.CHARACTER]
    assert ips == {"hatsune_miku": ["vocaloid"]}


def test_pixai_v09_interrogate_derives_copyright():
    it = PixAIV09Interrogator("test", repo_id="x", revision="y")
    it.image_size = 8
    it.tags, it.tag_categories, it.derived_copyright = PixAIV09Interrogator.parse_tags(
        csv.DictReader(io.StringIO(V09_CSV))
    )
    it.model = FakeSession(np.array([[0.9, 0.95]], dtype=np.float32))

    results = it.interrogate(Image.new("RGB", (6, 12))).select(it.default_thresholds, set(Category))

    assert [(r.name, r.category) for r in results] == [
        ("hatsune_miku", Category.CHARACTER),
        ("vocaloid", Category.COPYRIGHT),
        ("1girl", Category.GENERAL),
    ]


def test_registry_models_declare_thresholds_for_known_categories():
    for interrogator in interrogators.values():
        if interrogator.default_thresholds is not None:
            assert set(interrogator.default_thresholds) <= set(interrogator.categories)
