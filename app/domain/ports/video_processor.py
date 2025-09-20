from typing import Protocol

class VideoProcessorPort(Protocol):
    def extract_frames(self, input_path: str, out_dir: str, fps: int = 1) -> int: ...
