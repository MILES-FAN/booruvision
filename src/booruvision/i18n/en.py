"""English UI text. Every other catalog must have the same keys and placeholders."""

MESSAGES = {
    # Main window
    "main.from_clipboard": "From clipboard",
    "main.from_file": "From file",
    "main.analyze": "Analyze",
    "main.analyzing": "Analyzing with {model}…",
    "main.loading_model": "Loading {model} (downloaded on first use)…",
    "main.open_image": "Open image",
    "main.load_image_first": "Load an image first",
    "main.clipboard_no_image": "The clipboard does not contain an image",
    "main.clipboard_needs_wl_paste": (
        "No clipboard image found. On Wayland, install"
        " wl-clipboard (wl-paste) so the shortcut can read the clipboard"
    ),
    "main.open_failed": "Could not open image: {error}",
    "main.analysis_failed": "Analysis failed: {error}",
    "main.copied": "Copied {count} tags",
    "main.save_failed": "Could not save settings: {error}",
    "main.shortcut_failed": "Could not set shortcut: {error}",
    "main.shortcut_set": "Global shortcut set to {shortcut}",
    # Image panel
    "image.placeholder": "Load an image from the clipboard or a file",
    # Tag panel
    "tags.title": "Tags",
    "tags.title_count": "Tags ({count})",
    "tags.empty": "No results yet",
    "tags.copy": "Copy tags",
    "tags.format": "Tag format",
    "tags.comma": "Use , as separator",
    "tags.reset": "Reset",
    "tags.reset_tooltip": "Restore the recommended thresholds",
    "tags.threshold_tooltip": "{category} threshold",
    "tags.derived_tooltip": "Derived from the detected characters",
    # Tag categories
    "category.general": "General",
    "category.character": "Character",
    "category.copyright": "Copyright",
    "category.style": "Style (artist)",
    "category.meta": "Meta",
    "category.rating": "Rating",
    # Settings bar
    "bar.model": "Model",
    "bar.threshold": "Threshold: {value}",
    "bar.settings": "Language & shortcut settings",
    "bar.unload": "Unload model after every analysis",
    # Settings page
    "settings.title": "Settings",
    "settings.language": "Language",
    "settings.language_auto": "Automatic ({language})",
    "settings.shortcut_title": "Global shortcut",
    "settings.shortcut_hint": "Press the shortcut anywhere to load the clipboard image and analyze it.",
    "settings.shortcut_hint_mac": "Ctrl is the Control key, not Cmd.",
    "settings.current": "Current:",
    "settings.key": "Key",
    "settings.record": "Record",
    "settings.cancel": "Cancel",
    "settings.apply": "Apply",
    "settings.reset_default": "Reset to default",
    "settings.new_shortcut": "New shortcut: {shortcut}",
    "settings.no_changes": "No changes",
    "settings.press_keys": "Press the new key combination…",
    # Hotkey errors and status
    "hotkey.needs_modifier": "A global hotkey needs at least one modifier",
    "hotkey.unsupported_key": "Unsupported key {key}: use A-Z, 0-9 or F1-F24",
    "hotkey.invalid": "Invalid hotkey {text}: expected e.g. Ctrl+Shift+I",
    "hotkey.unknown_modifier": "Invalid hotkey {text}: unknown modifier {modifier}",
    "hotkey.thread_not_running": "Hotkey thread is not running",
    "hotkey.in_use": "{hotkey} is already used by another application",
    "hotkey.register_failed": "Could not register {hotkey} (error {error})",
    "hotkey.no_keycode": "No keycode for {key} in the current keyboard layout",
    "hotkey.key_unsupported_macos": "{key} is not supported on macOS",
    "hotkey.macos_permission": (
        "Global hotkey needs the Input Monitoring permission. Enable BooruVision (or your terminal) in "
        "System Settings → Privacy & Security → Input Monitoring, then restart the app."
    ),
    "hotkey.portal_unsupported": (
        "This desktop's xdg-desktop-portal has no GlobalShortcuts support (needs KDE Plasma or GNOME 48+)."
    ),
    "hotkey.portal_denied": "The shortcut request was cancelled or denied",
    "hotkey.portal_error": "GlobalShortcuts portal error: {error}",
    "hotkey.portal_managed": (
        "Shortcut managed by your desktop: {trigger}. Change it in the system keyboard shortcut settings."
    ),
    "hotkey.portal_unassigned": "not assigned yet",
    "hotkey.no_display": "No X11 or Wayland display found; global hotkeys are disabled.",
    "hotkey.unsupported_platform": "Global hotkeys are not supported on {platform}.",
    "hotkey.unavailable": "Global hotkeys unavailable: {error}",
}
