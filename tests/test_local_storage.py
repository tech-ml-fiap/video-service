import io
import os
from pathlib import Path

from app.adapters.driven.storage.local_storage import LocalStorage


def test_init_creates_directories(tmp_path):
    base = tmp_path / "data"
    ls = LocalStorage(str(base))

    assert Path(ls.base_dir).is_dir()
    assert Path(ls.uploads_dir).is_dir()
    assert Path(ls.outputs_dir).is_dir()
    assert Path(ls.temp_dir_root).is_dir()

    ls2 = LocalStorage(str(base))
    assert Path(ls2.uploads_dir).is_dir()


def test_save_upload_writes_file(tmp_path):
    ls = LocalStorage(str(tmp_path))
    content = b"hello world"
    filename = "up.bin"

    path = ls.save_upload(io.BytesIO(content), filename)

    assert path == os.path.join(ls.uploads_dir, filename)
    with open(path, "rb") as f:
        assert f.read() == content


def test_save_artifact_moves_with_basename_and_preserves_content(tmp_path):
    ls = LocalStorage(str(tmp_path))

    nested = tmp_path / "some" / "deep"
    nested.mkdir(parents=True, exist_ok=True)
    src = nested / "artifact.txt"
    payload = b"payload-123"
    src.write_bytes(payload)

    dest = ls.save_artifact(str(src))

    assert dest == os.path.join(ls.outputs_dir, "artifact.txt")
    assert not src.exists()
    with open(dest, "rb") as f:
        assert f.read() == payload


def test_make_temp_dir_creates_under_root_with_prefix(tmp_path):
    ls = LocalStorage(str(tmp_path))
    d = ls.make_temp_dir("job42")

    p = Path(d)
    assert p.is_dir()
    assert p.parent == Path(ls.temp_dir_root)
    assert p.name.startswith("job42_")


def test_resolve_path_passthrough(tmp_path):
    ls = LocalStorage(str(tmp_path))
    ref = os.path.join(ls.uploads_dir, "foo.bin")
    assert ls.resolve_path(ref) == ref
