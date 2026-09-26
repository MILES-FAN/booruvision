import logging

import flet as ft

from booruvision.app import main

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

if __name__ == "__main__":
    ft.run(main)
