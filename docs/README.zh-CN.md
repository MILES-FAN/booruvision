[English](../README.md) | **简体中文** | [日本語](README.ja.md)

一款使用 WD tagger 和 PixAI tagger 模型为剪贴板或文件中的图片打标签的图形界面工具。
支持 Windows、macOS 和 Linux（基于 [Flet](https://flet.dev) 构建）。

---
## 安装与运行
[![GitHub Release](https://img.shields.io/github/v/release/MILES-FAN/booruvision?label=Download%20latest%20release&style=for-the-badge&logo=windows)](https://github.com/MILES-FAN/booruvision/releases/)
[![GitHub Release](https://img.shields.io/github/v/release/MILES-FAN/booruvision?label=Download%20latest%20release&style=for-the-badge&logo=apple)](https://github.com/MILES-FAN/booruvision/releases/)

### 使用预构建版本

1. 从[这里](https://github.com/MILES-FAN/booruvision/releases/)下载适合你平台的最新版本：
   `BooruVision-windows-x64.zip`、`BooruVision-macos-arm64.zip`（Apple 芯片）或 `BooruVision-linux-x64.tar.gz`
2. 解压后打开 `BooruVision`
3. 等待应用启动

macOS 版本没有经过公证，首次启动会被 Gatekeeper 拦截。请右键点击应用并选择“打开”，
或者运行 `xattr -dr com.apple.quarantine BooruVision.app`。

### 从源码运行

需要先安装 [uv](https://docs.astral.sh/uv/)。

```bash
uv sync                          # 创建 .venv 并安装锁定的依赖
uv run python src/main.py        # 启动应用
```

在 macOS 上，首次启动时会在 `.flet-client/` 中复制一份名称和图标都改为 BooruVision 的 Flet 客户端，
这样程序坞和菜单栏会显示正确的应用。如需热重载，请使用
`FLET_VIEW_PATH=.flet-client uv run flet run src/main.py`（`flet run` 会在应用代码运行之前打开客户端，
所以需要提前指定路径）。

首次分析时会从 Hugging Face 下载所选模型，需要等待一段时间。

## 使用方法
![BooruVision 界面](../imgs/new_gui.png)

1. 将图片（或文件管理器中的图片文件）复制到剪贴板，或者选择一个文件
2. 点击“从剪贴板读取”或“从文件打开”
3. 点击“分析”，或者按下全局快捷键，一步完成读取剪贴板和分析
4. 标签会显示在图片旁边的面板中（窗口较窄时显示在图片下方），并按 Danbooru 类别着色：
   一般、角色、作品、画风（画师）和元数据
5. 在标签列表上方勾选需要的类别，然后点击“复制标签”，按所选格式复制

修改阈值或勾选的类别后，列表会立即更新，不需要重新分析图片。

其他：
- 界面支持英语、简体中文和日语。默认跟随系统语言，可以在设置页中更改（点击底栏的“快捷键：…”）
- “每次分析后卸载模型”可以节省内存，但每次分析都需要重新加载模型
- 标签格式可选 `Booru` 或 `Stable Diffusion`，分隔符可选空格或 `, `

## 全局快捷键
默认快捷键是 `Ctrl+Shift+I`。要修改它，请点击底栏的“快捷键：…”打开设置页，然后勾选修饰键并选择一个按键
（A–Z、0–9、F1–F24），或者点击“录制”后按下新的组合键。点击“应用”完成注册；如果该组合键已被占用，
会保留原来的快捷键。

具体实现因平台而异：

| 平台 | 实现方式 | 说明 |
|---|---|---|
| Windows | `RegisterHotKey` | 如果组合键已被其他应用占用，会提示失败 |
| macOS | `CGEventTap` | 需要**输入监控**权限：在“系统设置 → 隐私与安全性 → 输入监控”中启用 BooruVision（从源码运行时为终端），然后重启应用。`Ctrl` 指 Control 键 |
| Linux (X11) | `XGrabKey` | 适用于任何 X11 会话 |
| Linux (Wayland) | xdg-desktop-portal GlobalShortcuts | 支持 KDE Plasma 和 GNOME 48 以上版本。首次使用时桌面会要求确认快捷键；之后请在系统的键盘设置中修改 |

如果没有可用的实现方式，应用仍可正常使用，并会显示快捷键被停用的原因。

## 配置
设置会自动保存到用户配置目录中的 `config.ini`：

- Windows：`%LOCALAPPDATA%\booruvision\config.ini`
- macOS：`~/Library/Application Support/booruvision/config.ini`
- Linux：`~/.config/booruvision/config.ini`

首次启动时会导入工作目录中旧版本留下的 `config.ini`。

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

# 只有修改过推荐值的阈值才会写入
[Thresholds pixai-v1.0]
general = 0.25
```

`language` 可设为 `auto`（跟随系统）、`en`、`zh` 或 `ja`。

默认模型是 `wd-swinv2-v3`，另外推荐以下模型：
- `wd-swinv2-v3`（默认，整体表现良好）
- `wd-convnext-v3`（处理旋转图片可能比其他模型更好）
- `wd-vit-v3`（擅长识别角色）
- `wd14-moat-v2`（如果你想使用旧模型）

默认置信度阈值是 `0.35`；调低可以得到更多标签（但准确度会下降）。

### PixAI tagger
- `pixai-v1.0`：[PixAI Tagger v1.0](https://huggingface.co/pixai-labs/pixai-tagger-v1.0)，约 31,000 个标签，
  分为一般、角色、作品、画风（画师）、元数据和分级类别
- `pixai-v0.9`：[PixAI Tagger v0.9](https://huggingface.co/pixai-labs/pixai-tagger-v0.9)，包含一般和角色标签；
  作品标签根据识别出的角色推导

PixAI 模型为每个类别单独设置阈值，而不是使用统一的滑块。每个阈值的初始值是模型的推荐值，
可以在对应类别旁边修改（“重置”可恢复推荐值）。这些模型比 WD 模型大得多：首次分析时 v1.0 需要下载约 2 GB，
v0.9 约 1.3 GB；v1.0 需要约 4 GB 内存，在 CPU 上每张图片需要几秒钟。

## 已知问题
- 中国大陆用户可能无法顺利从 Hugging Face 下载模型

## 版权
原始代码来自 https://github.com/picobyte/stable-diffusion-webui-wd14-tagger

除借用的部分（例如 `tagging/preprocess.py`）外，均属于公有领域。
