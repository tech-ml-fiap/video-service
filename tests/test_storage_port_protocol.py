from app.domain.ports.storage import StoragePort
import io
import os
import pytest

def use_storage(storage: StoragePort, upload_bytes: bytes, upload_name: str,
                local_artifact_path: str, temp_prefix: str, ref: str):
    p1 = storage.save_upload(io.BytesIO(upload_bytes), upload_name)
    p2 = storage.save_artifact(local_artifact_path)
    d1 = storage.make_temp_dir(temp_prefix)
    p3 = storage.resolve_path(ref)
    return p1, p2, d1, p3

class ImplOK:
    def __init__(self): self.calls = []
    def save_upload(self, file_stream, filename: str) -> str:
        data = file_stream.read()
        self.calls.append(("save_upload", filename, data))
        return os.path.join("/uploads", filename)
    def save_artifact(self, local_path: str) -> str:
        self.calls.append(("save_artifact", local_path))
        return os.path.join("/outputs", os.path.basename(local_path))
    def make_temp_dir(self, prefix: str) -> str:
        self.calls.append(("make_temp_dir", prefix))
        return f"/tmp/{prefix}_12345"
    def resolve_path(self, ref: str) -> str:
        self.calls.append(("resolve_path", ref))
        return ref

class MissingMethod:
    def save_upload(self, file_stream, filename: str) -> str:
        return os.path.join("/uploads", filename)
    def save_artifact(self, local_path: str) -> str:
        return os.path.join("/outputs", os.path.basename(local_path))
    # falta make_temp_dir
    def resolve_path(self, ref: str) -> str:
        return ref

def test_duck_typing_happy_path_calls_all_methods():
    st = ImplOK()
    out = use_storage(
        st,
        upload_bytes=b"hello",
        upload_name="file.bin",
        local_artifact_path="/any/folder/art.zip",
        temp_prefix="job42",
        ref="/outputs/art.zip",
    )
    assert out == (
        os.path.join("/uploads", "file.bin"),
        os.path.join("/outputs", "art.zip"),
        "/tmp/job42_12345",
        "/outputs/art.zip",
    )
    kinds = [c[0] for c in st.calls]
    assert kinds == ["save_upload", "save_artifact", "make_temp_dir", "resolve_path"]

def test_duck_typing_missing_method_raises_attribute_error():
    st = MissingMethod()
    with pytest.raises(AttributeError):
        use_storage(
            st,
            upload_bytes=b"x",
            upload_name="a.txt",
            local_artifact_path="/x/y/z.bin",
            temp_prefix="pfx",
            ref="/whatever",
        )

def test_isinstance_and_issubclass_raise_typeerror_without_runtime_checkable():
    with pytest.raises(TypeError):
        isinstance(ImplOK(), StoragePort)
    with pytest.raises(TypeError):
        issubclass(ImplOK, StoragePort)
