"""Preview of the image that will be analyzed."""

import io

import flet as ft
from PIL import Image

from booruvision.i18n import t

# Longest edge of the preview sent to the client; the model gets the full image
PREVIEW_MAX_EDGE = 1600


def preview_bytes(image: Image.Image) -> bytes:
    preview = image.copy()
    preview.thumbnail((PREVIEW_MAX_EDGE, PREVIEW_MAX_EDGE))
    if preview.mode not in ("RGB", "RGBA"):
        preview = preview.convert("RGBA")
    buffer = io.BytesIO()
    preview.save(buffer, format="PNG")
    return buffer.getvalue()


class ImagePanel:
    def __init__(self) -> None:
        self._placeholder = ft.Column(
            [
                ft.Icon(ft.Icons.IMAGE_OUTLINED, size=48, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(
                    t("image.placeholder"),
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        )
        self.view = ft.Container(
            content=self._placeholder,
            alignment=ft.Alignment.CENTER,
            expand=True,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=8,
        )

    def set_height(self, height: int | None) -> None:
        """Use a fixed height (for scrolling layouts), or None to fill the space."""
        self.view.expand = height is None
        self.view.height = height

    def show(self, image: Image.Image) -> None:
        self.view.content = ft.Image(src=preview_bytes(image), fit=ft.BoxFit.CONTAIN, gapless_playback=True)

    def show_error(self, message: str) -> None:
        self.view.content = ft.Text(message, color=ft.Colors.ERROR, text_align=ft.TextAlign.CENTER)
