A GUI for tagging image from your clipboard or file system using wd tagger
---
## How to install and run

1. Create a virtual environment and activate it

```bash
python3 -m venv venv
```

for windows
```bash
./venv/scripts/activate
```

for macos and linux
```bash
source venv/bin/activate
```

2. Install the requirements

```bash
pip install -r requirements.txt
```

3. Run the application

```bash
python gui.py
```

## How to use
![interface](imgs/interface.png)
1. Copy an image to your clipboard or select a file
2. Click on the `load image from clipboard` or `load image from file` button
3. Click on the `analyze image` button or press a keybinding.
4. The tags will be displayed in a new window
5. You can copy the tags to your clipboard by clicking on the `copy tags to clipboard` button
![tags](imgs/tagswindow.png)
Extra: 
- Check `Unload model after every analysis` can save you some memory, but it will take longer to analyze the image
- You can choose tag format, currently support `Booru` and `Stable Diffusion` format

## Copyright
Original code by https://github.com/picobyte/stable-diffusion-webui-wd14-tagger

Public domain, except borrowed parts (e.g. `dbimutils.py`)
