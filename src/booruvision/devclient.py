"""Branded Flet client for running from source on macOS.

`flet run` shows the UI in a generic, prebuilt Flet.app, so the Dock icon and the
menu-bar app name say "Flet". Built apps (`flet build`) are branded already; for
development we make a copy of the cached client with our name and icon and point
FLET_VIEW_PATH at it. Everything here is best effort: on failure the stock
client is used.
"""

import logging
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

APP_NAME = "BooruVision"
BUNDLE_ID = "io.github.miles_fan.booruvision.dev"
_STAMP = ".booruvision-client-stamp"


def _stock_client() -> tuple[Path, str] | None:
    try:
        from flet_desktop import ensure_client_cached, find_macos_app_bundle
        from flet_desktop.version import version
    except ImportError:
        return None  # built app, or flet-desktop not installed
    app = find_macos_app_bundle(ensure_client_cached())
    return (app, version) if app else None


def _make_icns(png: Path, dest: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "AppIcon.iconset"
        iconset.mkdir()
        for size in (16, 32, 128, 256, 512):
            for scale in (1, 2):
                name = f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
                px = str(size * scale)
                subprocess.run(
                    ["sips", "-z", px, px, str(png), "--out", str(iconset / name)],
                    check=True,
                    capture_output=True,
                )
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(dest)], check=True, capture_output=True
        )


def _build(stock: Path, target: Path, icon: Path) -> None:
    shutil.copytree(stock, target, symlinks=True)
    contents = target / "Contents"

    info_path = contents / "Info.plist"
    with open(info_path, "rb") as f:
        info = plistlib.load(f)
    info["CFBundleName"] = APP_NAME
    info["CFBundleDisplayName"] = APP_NAME
    info["CFBundleIdentifier"] = BUNDLE_ID
    # CFBundleIconName makes macOS read the icon from Assets.car; drop it so the
    # replaced AppIcon.icns (CFBundleIconFile) is used instead
    info.pop("CFBundleIconName", None)
    icon_file = info.get("CFBundleIconFile", "AppIcon")
    with open(info_path, "wb") as f:
        plistlib.dump(info, f)

    _make_icns(icon, contents / "Resources" / f"{Path(icon_file).stem}.icns")

    # Editing the bundle invalidates its (ad-hoc) signature
    subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", str(target)], check=True, capture_output=True
    )


def use_branded_client(project_root: Path, icon: Path) -> None:
    """On macOS, make `flet run` use a client named and iconed as BooruVision."""
    if sys.platform != "darwin" or "FLET_VIEW_PATH" in os.environ or not icon.is_file():
        return
    try:
        stock = _stock_client()
        if stock is None:
            return
        stock_app, version = stock

        client_dir = project_root / ".flet-client"
        target = client_dir / f"{APP_NAME}.app"
        stamp = client_dir / _STAMP
        expected = f"{version}\n{icon.stat().st_mtime_ns}"
        if not (target.is_dir() and stamp.is_file() and stamp.read_text() == expected):
            log.info("Creating branded Flet client in %s", client_dir)
            shutil.rmtree(client_dir, ignore_errors=True)
            client_dir.mkdir(parents=True)
            _build(stock_app, target, icon)
            stamp.write_text(expected)

        os.environ["FLET_VIEW_PATH"] = str(client_dir)
    except (OSError, subprocess.CalledProcessError) as e:
        log.warning("Could not create branded Flet client, using the stock one: %s", e)
