"""Simplified Chinese UI text."""

MESSAGES = {
    # Main window
    "main.from_clipboard": "从剪贴板读取",
    "main.from_file": "从文件打开",
    "main.analyze": "分析",
    "main.analyzing": "正在使用 {model} 分析…",
    "main.loading_model": "正在加载 {model}（首次使用时需要下载）…",
    "main.open_image": "打开图片",
    "main.load_image_first": "请先载入图片",
    "main.clipboard_no_image": "剪贴板中没有图片",
    "main.open_failed": "无法打开图片：{error}",
    "main.analysis_failed": "分析失败：{error}",
    "main.copied": "已复制 {count} 个标签",
    "main.save_failed": "无法保存设置：{error}",
    "main.shortcut_failed": "无法设置快捷键：{error}",
    "main.shortcut_set": "全局快捷键已设为 {shortcut}",
    # Image panel
    "image.placeholder": "从剪贴板或文件载入图片",
    # Tag panel
    "tags.title": "标签",
    "tags.title_count": "标签（{count}）",
    "tags.empty": "暂无结果",
    "tags.copy": "复制标签",
    "tags.format": "标签格式",
    "tags.comma": "使用 , 作为分隔符",
    "tags.reset": "重置",
    "tags.reset_tooltip": "恢复推荐阈值",
    "tags.threshold_tooltip": "{category}阈值",
    "tags.derived_tooltip": "根据识别出的角色推导",
    # Tag categories
    "category.general": "一般",
    "category.character": "角色",
    "category.copyright": "作品",
    "category.style": "画风（画师）",
    "category.meta": "元数据",
    "category.rating": "分级",
    # Settings bar
    "bar.model": "模型",
    "bar.threshold": "阈值：{value}",
    "bar.settings": "语言与快捷键设置",
    "bar.unload": "每次分析后卸载模型",
    # Settings page
    "settings.title": "设置",
    "settings.language": "语言",
    "settings.language_auto": "自动（{language}）",
    "settings.shortcut_title": "全局快捷键",
    "settings.shortcut_hint": "在任意位置按下快捷键，即可载入剪贴板中的图片并进行分析。",
    "settings.shortcut_hint_mac": "Ctrl 指 Control 键，不是 Cmd 键。",
    "settings.current": "当前：",
    "settings.key": "按键",
    "settings.record": "录制",
    "settings.cancel": "取消",
    "settings.apply": "应用",
    "settings.reset_default": "恢复默认",
    "settings.new_shortcut": "新快捷键：{shortcut}",
    "settings.no_changes": "未更改",
    "settings.press_keys": "请按下新的组合键…",
    # Hotkey errors and status
    "hotkey.needs_modifier": "全局快捷键至少需要一个修饰键",
    "hotkey.unsupported_key": "不支持的按键 {key}：请使用 A-Z、0-9 或 F1-F24",
    "hotkey.invalid": "无效的快捷键 {text}：格式应类似 Ctrl+Shift+I",
    "hotkey.unknown_modifier": "无效的快捷键 {text}：未知的修饰键 {modifier}",
    "hotkey.thread_not_running": "快捷键线程未运行",
    "hotkey.in_use": "{hotkey} 已被其他应用程序占用",
    "hotkey.register_failed": "无法注册 {hotkey}（错误 {error}）",
    "hotkey.no_keycode": "当前键盘布局中没有 {key} 对应的键码",
    "hotkey.key_unsupported_macos": "macOS 不支持 {key}",
    "hotkey.macos_permission": (
        "全局快捷键需要“输入监控”权限。请在“系统设置 → 隐私与安全性 → 输入监控”中启用 BooruVision"
        "（从源码运行时为终端），然后重启应用。"
    ),
    "hotkey.portal_unsupported": (
        "当前桌面的 xdg-desktop-portal 不支持 GlobalShortcuts（需要 KDE Plasma 或 GNOME 48 以上版本）。"
    ),
    "hotkey.portal_denied": "快捷键请求已被取消或拒绝",
    "hotkey.portal_error": "GlobalShortcuts 门户出错：{error}",
    "hotkey.portal_managed": "快捷键由桌面环境管理：{trigger}。请在系统的键盘快捷键设置中修改。",
    "hotkey.portal_unassigned": "尚未分配",
    "hotkey.no_display": "未找到 X11 或 Wayland 显示，全局快捷键已停用。",
    "hotkey.unsupported_platform": "{platform} 不支持全局快捷键。",
    "hotkey.unavailable": "全局快捷键不可用：{error}",
}
