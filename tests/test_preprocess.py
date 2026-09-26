import numpy as np
from PIL import Image

from booruvision.tagging import preprocess


def test_make_square_pads_with_white_and_resizes():
    img = np.zeros((10, 20, 3), dtype=np.uint8)
    square = preprocess.make_square(img, 16)
    assert square.shape == (20, 20, 3)
    assert (square[0, 0] == 255).all() and (square[10, 10] == 0).all()
    assert preprocess.smart_resize(square, 8).shape == (8, 8, 3)


def test_fill_transparent_uses_white_background():
    image = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    assert preprocess.fill_transparent(image).getpixel((0, 0)) == (255, 255, 255)


def test_rescale_pad_normalize_keeps_aspect_ratio_with_black_padding():
    # Wide red image: scaled to 16x8, centred vertically with black bars
    x = preprocess.rescale_pad_normalize(Image.new("RGB", (40, 20), (255, 0, 0)), 16)
    assert x.shape == (1, 3, 16, 16) and x.dtype == np.float32
    assert np.allclose(x[0, :, 0, 0], -1)  # padding is black, normalized to -1
    assert np.allclose(x[0, :, 8, 8], [1, -1, -1])
    assert np.allclose(x[0, 0, 4:12, :], 1) and np.allclose(x[0, 0, :4, :], -1)


def test_rescale_pad_normalize_tall_image_and_transparency():
    x = preprocess.rescale_pad_normalize(Image.new("RGBA", (10, 20), (0, 0, 0, 0)), 16)
    assert x.shape == (1, 3, 16, 16)
    # Transparent pixels become white; the side bars stay black
    assert np.allclose(x[0, :, 8, 8], 1) and np.allclose(x[0, :, 8, 0], -1)


def test_resize_normalize_stretches():
    x = preprocess.resize_normalize(Image.new("RGB", (40, 20), (0, 0, 255)), 16)
    assert x.shape == (1, 3, 16, 16)
    assert np.allclose(x[0, 2], 1) and np.allclose(x[0, :2], -1)
