import logging
from pathlib import Path

import flet as ft

from booruvision.app import main

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ft.run(main, assets_dir=str(Path(__file__).resolve().parent.parent / "assets"))
