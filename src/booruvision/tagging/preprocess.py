"""Image preprocessing helpers shared by the interrogators."""

import cv2
import numpy as np
from PIL import Image


def fill_transparent(image: Image.Image, color="WHITE") -> Image.Image:
    image = image.convert("RGBA")
    new_image = Image.new("RGBA", image.size, color)
    new_image.paste(image, mask=image)
    return new_image.convert("RGB")


def resize(pic: Image.Image, size: int, keep_ratio=True) -> Image.Image:
    if not keep_ratio:
        target_size = (size, size)
    else:
        min_edge = min(pic.size)
        target_size = (
            int(pic.size[0] / min_edge * size),
            int(pic.size[1] / min_edge * size),
        )

    target_size = (target_size[0] & ~3, target_size[1] & ~3)

    return pic.resize(target_size, resample=Image.Resampling.LANCZOS)


def make_square(img: np.ndarray, target_size: int) -> np.ndarray:
    """Pad an image with white so that it becomes square."""
    old_size = img.shape[:2]
    desired_size = max(max(old_size), target_size)

    delta_w = desired_size - old_size[1]
    delta_h = desired_size - old_size[0]
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    return cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[255, 255, 255])


def smart_resize(img: np.ndarray, size: int) -> np.ndarray:
    """Resize a square image, picking the interpolation by direction."""
    if img.shape[0] > size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    elif img.shape[0] < size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_CUBIC)
    return img


def _to_normalized_nchw(image: Image.Image) -> np.ndarray:
    """RGB image -> 1CHW float32 scaled to [-1, 1] (mean = std = 0.5)."""
    x = np.asarray(image, dtype=np.float32) / 255
    x = (x - 0.5) / 0.5
    return np.expand_dims(x.transpose((2, 0, 1)), 0)


def rescale_pad_normalize(image: Image.Image, size: int) -> np.ndarray:
    """Fit into a black size x size square, keeping the aspect ratio (PixAI v1.0)."""
    image = fill_transparent(image)
    width, height = image.size
    if (width, height) != (size, size):
        ratio = min(size / height, size / width)
        new_width, new_height = int(width * ratio), int(height * ratio)
        resized = image.resize((new_width, new_height), resample=Image.Resampling.BILINEAR)
        image = Image.new("RGB", (size, size), (0, 0, 0))
        image.paste(resized, ((size - new_width) // 2, (size - new_height) // 2))
    return _to_normalized_nchw(image)


def resize_normalize(image: Image.Image, size: int) -> np.ndarray:
    """Stretch to size x size (PixAI v0.9)."""
    image = fill_transparent(image).resize((size, size), resample=Image.Resampling.BILINEAR)
    return _to_normalized_nchw(image)
