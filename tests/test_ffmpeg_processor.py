import subprocess
import pytest

from app.adapters.driven.media.ffmpeg_processor import FFmpegVideoProcessor


class RunSpy:
    def __init__(self, to_raise=None):
        self.to_raise = to_raise
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        if self.to_raise:
            raise self.to_raise
        class _R:
            stdout = ""
            stderr = ""
            returncode = 0
        return _R()


def test_extract_frames_success_counts_jpgs_and_builds_cmd(tmp_path, monkeypatch):
    out_dir = tmp_path / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("00000001.jpg", "00000002.jpg", "00000003.jpg", "ignore.png"):
        (out_dir / name).write_bytes(b"x")

    spy = RunSpy()
    monkeypatch.setattr(subprocess, "run", spy)

    proc = FFmpegVideoProcessor(ffmpeg_bin="ffmpeg", timeout_sec=123)
    count = proc.extract_frames(input_path="in.mp4", out_dir=str(out_dir), fps=5)

    assert count == 3

    assert len(spy.calls) == 1
    args, kwargs = spy.calls[0]["args"], spy.calls[0]["kwargs"]
    cmd = args[0]
    assert cmd[:6] == ["ffmpeg", "-y", "-hide_banner", "-v", "error", "-i"]
    assert "in.mp4" in cmd
    assert "-vf" in cmd and f"fps=5" in cmd
    assert "-q:v" in cmd and "2" in cmd
    assert str(out_dir / "%08d.jpg") in cmd
    assert kwargs["check"] is True
    assert kwargs["stdout"] == subprocess.PIPE
    assert kwargs["stderr"] == subprocess.PIPE
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 123


def test_extract_frames_creates_output_dir_if_missing(tmp_path, monkeypatch):
    out_dir = tmp_path / "will_create" / "nested"
    spy = RunSpy()
    monkeypatch.setattr(subprocess, "run", spy)

    def run_then_create_files(cmd, **kwargs):
        (out_dir).mkdir(parents=True, exist_ok=True)
        for name in ("00000001.jpg", "00000002.jpg"):
            (out_dir / name).write_bytes(b"x")
        return type("R", (), {"stdout": "", "stderr": "", "returncode": 0})()

    monkeypatch.setattr(subprocess, "run", run_then_create_files)

    proc = FFmpegVideoProcessor()
    count = proc.extract_frames("in.mp4", str(out_dir))

    assert out_dir.exists()
    assert count == 2


@pytest.mark.parametrize(
    "stderr,stdout,expected",
    [
        ("boom err", "ignored", "boom err"),
        ("", "some out", "some out"),
        ("", "", "ffmpeg failed"),
    ],
)
def test_extract_frames_raises_runtime_on_called_process_error(monkeypatch, tmp_path, stderr, stdout, expected):
    out_dir = tmp_path / "f"
    out_dir.mkdir(parents=True, exist_ok=True)

    cpe = subprocess.CalledProcessError(
        returncode=1,
        cmd=["ffmpeg"],
        output=stdout,
        stderr=stderr,
    )
    spy = RunSpy(to_raise=cpe)
    monkeypatch.setattr(subprocess, "run", spy)

    proc = FFmpegVideoProcessor()
    with pytest.raises(RuntimeError) as exc:
        proc.extract_frames("in.mp4", str(out_dir), fps=2)

    assert expected in str(exc.value)


def test_extract_frames_raises_runtime_on_timeout(monkeypatch, tmp_path):
    out_dir = tmp_path / "t"
    out_dir.mkdir(parents=True, exist_ok=True)

    te = subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=7)
    spy = RunSpy(to_raise=te)
    monkeypatch.setattr(subprocess, "run", spy)

    proc = FFmpegVideoProcessor(timeout_sec=7)
    with pytest.raises(RuntimeError) as exc:
        proc.extract_frames("in.mp4", str(out_dir))

    assert "ffmpeg timeout após 7s" in str(exc.value)
