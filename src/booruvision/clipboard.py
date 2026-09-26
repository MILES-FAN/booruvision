"""Read an image from the system clipboard."""

import asyncio
import io
import logging
from pathlib import Path

import flet as ft
from PIL import Image, ImageGrab, UnidentifiedImageError

log = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


def _open_image(data: bytes) -> Image.Image | None:
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
        return image
    except (UnidentifiedImageError, OSError):
        return None


def _grab_with_pillow() -> Image.Image | None:
    try:
        content = ImageGrab.grabclipboard()
    except (NotImplementedError, OSError) as e:
        # Linux needs wl-paste or xclip for this
        log.debug("Pillow clipboard grab failed: %s", e)
        return None
    if isinstance(content, Image.Image):
        return content
    if isinstance(content, list):
        return _first_image_file(content)
    return None


def _first_image_file(paths: list[str]) -> Image.Image | None:
    for path in paths:
        if Path(path).suffix.lower() in IMAGE_EXTENSIONS:
            try:
                return Image.open(path)
            except (UnidentifiedImageError, OSError):
                continue
    return None


async def read_image() -> Image.Image | None:
    """Return the clipboard image, or an image file copied in the file manager."""
    clipboard = ft.Clipboard()
    try:
        data = await clipboard.get_image()
        if data:
            image = _open_image(data)
            if image is not None:
                return image
        files = await clipboard.get_files()
        if files:
            image = _first_image_file(files)
            if image is not None:
                return image
    except Exception as e:  # noqa: BLE001 - fall back to Pillow on any client-side failure
        log.debug("Flet clipboard read failed: %s", e)

    return await asyncio.to_thread(_grab_with_pillow)
