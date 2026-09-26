import io

from PIL import Image

from booruvision import clipboard


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(buf, "PNG")
    return buf.getvalue()


def test_uri_list_paths():
    text = "# comment\r\nfile:///tmp/a%20b.png\r\nhttps://example.com/x.png\r\n"
    assert clipboard._uri_list_paths(text) == ["/tmp/a b.png"]


def test_wl_paste_reads_image(monkeypatch):
    outputs = {("--list-types",): b"text/plain\nimage/png\n", ("--type", "image/png"): _png()}
    monkeypatch.setattr(clipboard.shutil, "which", lambda _: "/usr/bin/wl-paste")
    monkeypatch.setattr(clipboard, "_wl_paste", lambda *args: outputs.get(args))
    image = clipboard._grab_with_wl_paste()
    assert image is not None and image.size == (4, 4)


def test_wl_paste_reads_copied_file(monkeypatch, tmp_path):
    path = tmp_path / "copied image.png"
    path.write_bytes(_png())
    outputs = {
        ("--list-types",): b"text/uri-list\n",
        ("--type", "text/uri-list"): f"file://{path.as_posix().replace(' ', '%20')}\n".encode(),
    }
    monkeypatch.setattr(clipboard.shutil, "which", lambda _: "/usr/bin/wl-paste")
    monkeypatch.setattr(clipboard, "_wl_paste", lambda *args: outputs.get(args))
    image = clipboard._grab_with_wl_paste()
    assert image is not None and image.size == (4, 4)


def test_wl_paste_missing(monkeypatch):
    monkeypatch.setattr(clipboard.shutil, "which", lambda _: None)
    assert clipboard._grab_with_wl_paste() is None
