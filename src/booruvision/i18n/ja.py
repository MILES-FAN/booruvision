"""Japanese UI text."""

MESSAGES = {
    # Main window
    "main.from_clipboard": "クリップボードから",
    "main.from_file": "ファイルから",
    "main.analyze": "解析",
    "main.analyzing": "{model} で解析中…",
    "main.loading_model": "{model} を読み込み中（初回はダウンロードします）…",
    "main.open_image": "画像を開く",
    "main.load_image_first": "先に画像を読み込んでください",
    "main.clipboard_no_image": "クリップボードに画像がありません",
    "main.open_failed": "画像を開けませんでした：{error}",
    "main.analysis_failed": "解析に失敗しました：{error}",
    "main.copied": "{count} 個のタグをコピーしました",
    "main.save_failed": "設定を保存できませんでした：{error}",
    "main.shortcut_failed": "ショートカットを設定できませんでした：{error}",
    "main.shortcut_set": "グローバルショートカットを {shortcut} に設定しました",
    # Image panel
    "image.placeholder": "クリップボードまたはファイルから画像を読み込んでください",
    # Tag panel
    "tags.title": "タグ",
    "tags.title_count": "タグ（{count}）",
    "tags.empty": "まだ結果がありません",
    "tags.copy": "タグをコピー",
    "tags.format": "タグ形式",
    "tags.comma": "区切り文字に , を使う",
    "tags.reset": "リセット",
    "tags.reset_tooltip": "推奨しきい値に戻す",
    "tags.threshold_tooltip": "{category}のしきい値",
    "tags.derived_tooltip": "検出されたキャラクターから推定",
    # Tag categories
    "category.general": "一般",
    "category.character": "キャラクター",
    "category.copyright": "作品",
    "category.style": "画風（絵師）",
    "category.meta": "メタ",
    "category.rating": "レーティング",
    # Settings bar
    "bar.model": "モデル",
    "bar.threshold": "しきい値：{value}",
    "bar.settings": "言語とショートカットの設定",
    "bar.unload": "解析のたびにモデルをアンロード",
    # Settings page
    "settings.title": "設定",
    "settings.language": "言語",
    "settings.language_auto": "自動（{language}）",
    "settings.shortcut_title": "グローバルショートカット",
    "settings.shortcut_hint": "どこでもショートカットを押すと、クリップボードの画像を読み込んで解析します。",
    "settings.shortcut_hint_mac": "Ctrl は Control キーのことで、Cmd キーではありません。",
    "settings.current": "現在：",
    "settings.key": "キー",
    "settings.record": "記録",
    "settings.cancel": "キャンセル",
    "settings.apply": "適用",
    "settings.reset_default": "デフォルトに戻す",
    "settings.new_shortcut": "新しいショートカット：{shortcut}",
    "settings.no_changes": "変更なし",
    "settings.press_keys": "新しいキーの組み合わせを押してください…",
    # Hotkey errors and status
    "hotkey.needs_modifier": "グローバルショートカットには修飾キーが 1 つ以上必要です",
    "hotkey.unsupported_key": "{key} は使用できません：A-Z、0-9、F1-F24 を使ってください",
    "hotkey.invalid": "無効なショートカット {text}：Ctrl+Shift+I のように指定してください",
    "hotkey.unknown_modifier": "無効なショートカット {text}：不明な修飾キー {modifier}",
    "hotkey.thread_not_running": "ショートカットのスレッドが動作していません",
    "hotkey.in_use": "{hotkey} は他のアプリケーションで使用されています",
    "hotkey.register_failed": "{hotkey} を登録できませんでした（エラー {error}）",
    "hotkey.no_keycode": "現在のキーボード配列には {key} のキーコードがありません",
    "hotkey.key_unsupported_macos": "{key} は macOS では使用できません",
    "hotkey.macos_permission": (
        "グローバルショートカットには「入力監視」の許可が必要です。"
        "「システム設定 → プライバシーとセキュリティ → 入力監視」で BooruVision"
        "（ソースから実行している場合はターミナル）を有効にし、アプリを再起動してください。"
    ),
    "hotkey.portal_unsupported": (
        "このデスクトップの xdg-desktop-portal は GlobalShortcuts に対応していません"
        "（KDE Plasma または GNOME 48 以降が必要です）。"
    ),
    "hotkey.portal_denied": "ショートカットの要求がキャンセルまたは拒否されました",
    "hotkey.portal_error": "GlobalShortcuts ポータルのエラー：{error}",
    "hotkey.portal_managed": (
        "ショートカットはデスクトップで管理されています：{trigger}。システムのキーボードショートカット設定で"
        "変更してください。"
    ),
    "hotkey.portal_unassigned": "未割り当て",
    "hotkey.no_display": (
        "X11 または Wayland のディスプレイが見つからないため、グローバルショートカットは無効です。"
    ),
    "hotkey.unsupported_platform": "{platform} ではグローバルショートカットに対応していません。",
    "hotkey.unavailable": "グローバルショートカットを利用できません：{error}",
}
