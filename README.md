**English** | [简体中文](docs/README.zh-CN.md) | [日本語](docs/README.ja.md)

A GUI tool for labeling images from your clipboard or file system using WD tagger and PixAI tagger models.
Runs on Windows, macOS and Linux (built with [Flet](https://flet.dev)).

---
## How to install and run
[![GitHub Release](https://img.shields.io/github/v/release/MILES-FAN/booruvision?label=Download%20latest%20release&style=for-the-badge&logo=windows)](https://github.com/MILES-FAN/booruvision/releases/)
[![GitHub Release](https://img.shields.io/github/v/release/MILES-FAN/booruvision?label=Download%20latest%20release&style=for-the-badge&logo=apple)](https://github.com/MILES-FAN/booruvision/releases/)

### Use the pre-built app

1. Download the latest release for your platform from [here](https://github.com/MILES-FAN/booruvision/releases/):
   `BooruVision-windows-x64.zip`, `BooruVision-macos-arm64.zip` (Apple Silicon) or `BooruVision-linux-x64.tar.gz`
2. Unzip it and open `BooruVision`
3. Wait for the application to start

The macOS app is not notarized, so the first launch is blocked by Gatekeeper. Right-click the app and
choose `Open`, or run `xattr -dr com.apple.quarantine BooruVision.app`.

### Run from source

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync                          # creates .venv and installs locked dependencies
uv run python src/main.py        # start the app
```

On macOS the first start creates a copy of the Flet client named and iconed as BooruVision
in `.flet-client/`, so the Dock and menu bar show the right app. For hot reload use
`FLET_VIEW_PATH=.flet-client uv run flet run src/main.py` (`flet run` opens the client before
the app code runs, so it needs the path up front).

The first analysis downloads the selected model from Hugging Face, so it takes a while.

## How to use
![BooruVision interface](imgs/new_gui.png)

1. Copy an image (or an image file in your file manager) to the clipboard, or pick a file
2. Click `From clipboard` or `From file`
3. Click `Analyze`, or press the global shortcut to load the clipboard and analyze it in one step
4. Tags appear in the panel next to the image (below it on narrow windows), colored by their
   Danbooru category: general, character, copyright, style (artist) and meta
5. Tick the categories you want above the tag list, then click `Copy tags` to copy them in the
   selected format

Changing a threshold or the ticked categories updates the list right away, without analyzing the
image again.

Extra:
- The interface is available in English, Simplified Chinese and Japanese. It follows the system
  language by default; change it on the settings page (click `Shortcut: …` in the bottom bar)
- `Unload model after every analysis` saves memory, but every analysis has to reload the model
- Tag format can be `Booru` or `Stable Diffusion`, with space or `, ` as the separator

## Global shortcut
The default shortcut is `Ctrl+Shift+I`. To change it, click `Shortcut: …` in the bottom bar to open
the settings page, then either tick the modifiers and pick a key (A–Z, 0–9, F1–F24), or click
`Record` and press the new combination. Click `Apply` to register it; if the combination is
already taken, the previous shortcut is kept.

How it works depends on the platform:

| Platform | Mechanism | Notes |
|---|---|---|
| Windows | `RegisterHotKey` | Fails with a message if another app already uses the combination |
| macOS | `CGEventTap` | Needs **Input Monitoring**: System Settings → Privacy & Security → Input Monitoring, enable BooruVision (or your terminal when running from source), then restart the app. `Ctrl` means the Control key |
| Linux (X11) | `XGrabKey` | Works on any X11 session |
| Linux (Wayland) | xdg-desktop-portal GlobalShortcuts | KDE Plasma and GNOME 48+. The desktop asks you to confirm the shortcut the first time; change it in the system keyboard settings |

If no mechanism is available, the app still works and shows why the shortcut is disabled.

## Configuration
Settings are saved automatically to `config.ini` in your user config directory:

- Windows: `%LOCALAPPDATA%\booruvision\config.ini`
- macOS: `~/Library/Application Support/booruvision/config.ini`
- Linux: `~/.config/booruvision/config.ini`

A `config.ini` from an older version in the working directory is imported on first start.

```ini
[GUI]
shortcut = Ctrl+Shift+I
language = auto
unload_model_when_done = False
tag_format = Booru
comma_separated = False
categories = general,character,copyright

[Tagger]
model = wd-swinv2-v3
threshold = 0.35

# Only written for thresholds you changed from the recommended ones
[Thresholds pixai-v1.0]
general = 0.25
```

`language` is `auto` (follow the system), `en`, `zh` or `ja`.

Default model is `wd-swinv2-v3` and I also recommend these models:
- `wd-swinv2-v3` (default, with overall good performance)
- `wd-convnext-v3` (might deal with rotated images better than other models)
- `wd-vit-v3` (good at character recognition)
- `wd14-moat-v2` (in case you want to use the old model)

Default confidence threshold is `0.35`; lower it if you want more tags (less accurate).

### PixAI tagger
- `pixai-v1.0`: [PixAI Tagger v1.0](https://huggingface.co/pixai-labs/pixai-tagger-v1.0), about
  31,000 tags in general, character, copyright, style (artist), meta and rating categories
- `pixai-v0.9`: [PixAI Tagger v0.9](https://huggingface.co/pixai-labs/pixai-tagger-v0.9), general
  and character tags; copyright tags are derived from the detected characters

PixAI models have a threshold per category instead of the single slider. Each one starts at the
model's recommended value and can be edited next to its category (`Reset` restores the recommended
values). They are much larger than the WD models: the first analysis downloads about 2 GB for v1.0
and 1.3 GB for v0.9, and v1.0 needs around 4 GB of memory and a few seconds per image on a CPU.

## Known issues
- Users in mainland China might have trouble downloading the models from Hugging Face

## Copyright
Original code by https://github.com/picobyte/stable-diffusion-webui-wd14-tagger

Public domain, except borrowed parts (e.g. `tagging/preprocess.py`)
