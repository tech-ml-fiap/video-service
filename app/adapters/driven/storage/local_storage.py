import os, shutil, tempfile
from typing import BinaryIO
from app.domain.ports.storage import StoragePort

class LocalStorage(StoragePort):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.outputs_dir, exist_ok=True)
        os.makedirs(self.temp_dir_root, exist_ok=True)

    @property
    def uploads_dir(self) -> str:
        return os.path.join(self.base_dir, "uploads")

    @property
    def outputs_dir(self) -> str:
        return os.path.join(self.base_dir, "outputs")

    @property
    def temp_dir_root(self) -> str:
        return os.path.join(self.base_dir, "temp")

    def save_upload(self, file_stream: BinaryIO, filename: str) -> str:
        path = os.path.join(self.uploads_dir, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(file_stream, f)
        return path

    def save_artifact(self, local_path: str) -> str:
        dest = os.path.join(self.outputs_dir, os.path.basename(local_path))
        shutil.move(local_path, dest)
        return dest

    def make_temp_dir(self, prefix: str) -> str:
        return tempfile.mkdtemp(prefix=f"{prefix}_", dir=self.temp_dir_root)

    def resolve_path(self, ref: str) -> str:
        return ref
