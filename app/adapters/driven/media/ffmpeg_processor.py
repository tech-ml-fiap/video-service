from pathlib import Path
import subprocess
from app.domain.ports.video_processor import VideoProcessorPort


class FFmpegVideoProcessor(VideoProcessorPort):
    def __init__(self, ffmpeg_bin: str = "ffmpeg", timeout_sec: int = 600):
        self.ffmpeg_bin = ffmpeg_bin
        self.timeout_sec = timeout_sec

    def extract_frames(self, input_path: str, out_dir: str, fps: int = 1) -> int:
        out_dir_p = Path(out_dir)
        out_dir_p.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-hide_banner",
            "-v",
            "error",
            "-i",
            input_path,
            "-vf",
            f"fps={fps}",
            "-q:v",
            "2",
            str(out_dir_p / "%08d.jpg"),
        ]

        try:
            res = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout_sec,
            )
        except subprocess.CalledProcessError as e:
            msg = e.stderr.strip() or e.stdout.strip() or "ffmpeg failed"
            raise RuntimeError(msg) from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"ffmpeg timeout após {self.timeout_sec}s") from e

        return sum(1 for _ in out_dir_p.glob("*.jpg"))
