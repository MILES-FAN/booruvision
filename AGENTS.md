# AGENTS.md

BooruVision is a Flet 1.0 desktop app that tags images (clipboard or file) with WD tagger ONNX
models, with a per-platform global hotkey. User-facing docs live in `README.md`; this file is for
contributors and coding agents.

## Commands

Dependencies are managed with uv only (`pyproject.toml` + `uv.lock`); there is no requirements.txt.

```bash
uv sync                          # install locked deps into .venv
uv run python src/main.py        # run the app
uv run pytest                    # tests
uv run ruff check .              # lint
uv run ruff format .             # format (CI runs `ruff format --check`)
uv add <package>                 # add a dependency; commit uv.lock with it
uv run flet build macos          # package (windows / linux); output in build/<platform>
```

Run `ruff check`, `ruff format --check` and `pytest` before committing; CI enforces all three.

- Run the app with `python src/main.py`, not `flet run`: on macOS, `devclient.py` points
  `FLET_VIEW_PATH` at a branded copy of the Flet client (`.flet-client/`), but `flet run` opens
  the client before app code runs. For hot reload:
  `FLET_VIEW_PATH=.flet-client uv run flet run src/main.py`.
- `flet build` cannot cross-compile; each platform builds on its own OS. A local macOS build needs
  full Xcode and CocoaPods, not just the Command Line Tools.

## Layout

```
src/main.py                entry point for running and for `flet build` ([tool.flet.app] path = "src")
src/assets/                icon.png (bundle icon), icon.ico (Windows window icon)
src/booruvision/
  app.py                   BooruVisionApp: page setup, routing, actions, settings changes
  config.py                Settings dataclass + ConfigStore (config.ini in the platformdirs user dir)
  formatting.py            TagFormat (Booru / Stable Diffusion), joining with separators
  clipboard.py             clipboard image: ft.Clipboard first, Pillow ImageGrab fallback
  devclient.py             macOS-only branded dev client (see above)
  ui/                      image_panel, tag_panel, settings_bar, config_page (/config route)
  tagging/                 interrogators, preprocessing, model registry, TaggerService
  hotkeys/                 base.py (Hotkey, HotkeyBackend) + one backend per platform
tests/                     pytest; pythonpath = src
```

## Conventions and gotchas

- **Threading.** Hotkey callbacks run on each backend's own thread. They must hop to the UI with
  `page.run_task(...)`, which is thread-safe. Inference runs through
  `asyncio.to_thread(TaggerService.tag, ...)`, and `TaggerService` serializes calls with a lock.
  Call `HotkeyBackend.register` / `unregister` via `asyncio.to_thread`: they can block on OS
  permission prompts or Wayland portal dialogs.
- **Hotkey backends.** `hotkeys.create_backend()` picks one of:
  - `windows.py`: RegisterHotKey on a message-loop thread
  - `macos.py`: listen-only CGEventTap; needs Input Monitoring
  - `linux_x11.py`: XGrabKey
  - `linux_wayland.py`: xdg-desktop-portal GlobalShortcuts via dbus-next

  If none is available, it falls back to `NullHotkeyBackend` instead of raising. A backend holds
  one hotkey; `register` replaces it. Platform modules import platform-only packages, so import
  them only from `create_backend` (CI imports each one on its own OS to catch breakage).
- **Hotkey strings.** Parse and validate with `Hotkey.parse` / `Hotkey.create`. At least one
  modifier is required. Keys are A–Z, 0–9 and F1–F24 (macOS supports up to F20). Store
  `str(hotkey)` in config; show `display_shortcut()` in the UI (platform modifier names).
- **Model output must not change.** Preprocessing (`tagging/preprocess.py`, OpenCV) and
  postprocessing match the original implementation exactly. Check any change there against the
  previous version on a real image, not just unit tests.
- **Config compatibility.** Keep the existing `config.ini` keys (`[GUI]` shortcut /
  unload_model_when_done / tag_format / comma_separated, `[Tagger]` model / threshold). Invalid
  values fall back to defaults. A legacy `./config.ini` is imported on first start.
- **Layout.** Don't size anything in physical pixels or from screen resolution; Flet handles DPI.
  Below `NARROW_LAYOUT_WIDTH` the panels stack in a scrolling column with fixed heights. Flet has
  no min-height, and `expand` children are not allowed inside a scrolling column.
- **Flet 1.0 API.** Many names changed from 0.2x: `ft.run`, `ft.Button(content=...)`,
  `Dropdown.on_select`, `ft.DropdownOption`, services such as `ft.Clipboard()` /
  `ft.FilePicker()` used directly with `await`, and `page.show_dialog` for snack bars. Check the
  installed package in `.venv` rather than older docs or examples.
- **Python version.** `.python-version` is 3.14 because `flet build` bundles the newest Python
  allowed by `requires-python`. Keep dev, CI and the bundle on the same version.
- **macOS builds are arm64-only** (`[tool.flet.macos] target_arch`): onnxruntime ships no x86_64
  macOS wheels. The app is not sandboxed, because CGEventTap requires that.

## CI and releases

`.github/workflows/ci.yml` runs these jobs:

| Trigger | Lint + tests (3 OS) | Build (3 OS) | GitHub Release |
|---|---|---|---|
| Push to a feature branch | ✓ | | |
| Pull request, push to `master`, manual run | ✓ | ✓ | |
| Push a `v*` tag | ✓ | ✓ | ✓ |

- Builds are archived before upload, because `upload-artifact` drops symlinks and execute bits,
  which breaks the `.app`. The archives are attached to the run as artifacts.
- To release, bump `version` in `pyproject.toml`, commit, then push a matching tag, e.g.
  `git tag v0.2.0 && git push origin v0.2.0`. Tags containing `-` (e.g. `v0.3.0-rc1`) become
  pre-releases.
