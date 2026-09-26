"""Read an image from the system clipboard."""

import asyncio
import io
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

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


def is_wayland() -> bool:
    return sys.platform.startswith("linux") and bool(os.environ.get("WAYLAND_DISPLAY"))


def wayland_tool_missing() -> bool:
    """True when reading the clipboard without focus is impossible because wl-paste is missing."""
    return is_wayland() and shutil.which("wl-paste") is None


def _wl_paste(*args: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["wl-paste", "--no-newline", *args], capture_output=True, timeout=5, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        log.debug("wl-paste failed: %s", e)
        return None
    return result.stdout if result.returncode == 0 else None


def _uri_list_paths(text: str) -> list[str]:
    paths = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("file://"):
            paths.append(unquote(urlparse(line).path))
    return paths


def _grab_with_wl_paste() -> Image.Image | None:
    # A Wayland client only sees the clipboard while it has keyboard focus, so the Flet client
    # cannot read it when a global shortcut fires in the background. wl-paste uses the
    # data-control protocol (or a short-lived focused surface) and works regardless.
    if shutil.which("wl-paste") is None:
        return None
    types = _wl_paste("--list-types")
    if not types:
        return None
    mime_types = types.decode(errors="replace").split()
    for mime in mime_types:
        if mime.startswith("image/"):
            data = _wl_paste("--type", mime)
            if data and (image := _open_image(data)) is not None:
                return image
    if "text/uri-list" in mime_types:
        data = _wl_paste("--type", "text/uri-list")
        if data:
            return _first_image_file(_uri_list_paths(data.decode(errors="replace")))
    return None


async def read_image() -> Image.Image | None:
    """Return the clipboard image, or an image file copied in the file manager."""
    if is_wayland():
        image = await asyncio.to_thread(_grab_with_wl_paste)
        if image is not None:
            return image

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
