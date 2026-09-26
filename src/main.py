import logging
from pathlib import Path

import flet as ft

from booruvision.app import main
from booruvision.devclient import use_branded_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ASSETS_DIR = Path(__file__).resolve().parent / "assets"

if __name__ == "__main__":
    use_branded_client(ASSETS_DIR.parent.parent, ASSETS_DIR / "icon.png")
    ft.run(main)
