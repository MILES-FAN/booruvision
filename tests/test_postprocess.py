import numpy as np
from PIL import Image

from booruvision.tagging import preprocess
from booruvision.tagging.interrogator import Interrogator


def test_postprocess_filters_by_threshold_and_sorts_by_confidence():
    tags = {"a": 0.2, "b": 0.9, "c": 0.5, "d": 0.35}
    assert list(Interrogator.postprocess_tags(tags, threshold=0.35).items()) == [
        ("b", 0.9),
        ("c", 0.5),
        ("d", 0.35),
    ]


def test_postprocess_options():
    tags = {"long_hair": 0.9, "smile_(face)": 0.8, "skip": 0.95}
    result = Interrogator.postprocess_tags(
        tags,
        threshold=0.5,
        exclude_tags=["skip"],
        sort_by_alphabetical_order=True,
        replace_underscore=True,
        escape_tag=True,
    )
    assert result == {"long hair": 0.9, r"smile \(face\)": 0.8}


def test_make_square_pads_with_white_and_resizes():
    img = np.zeros((10, 20, 3), dtype=np.uint8)
    square = preprocess.make_square(img, 16)
    assert square.shape == (20, 20, 3)
    assert (square[0, 0] == 255).all() and (square[10, 10] == 0).all()
    assert preprocess.smart_resize(square, 8).shape == (8, 8, 3)


def test_fill_transparent_uses_white_background():
    image = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    assert preprocess.fill_transparent(image).getpixel((0, 0)) == (255, 255, 255)
