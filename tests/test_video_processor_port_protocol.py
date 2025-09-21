from app.domain.ports.video_processor import VideoProcessorPort
import pytest


def run_extract(proc: VideoProcessorPort, fps_arg=None) -> int:
    input_path = "input.mp4"
    out_dir = "/tmp/frames"
    if fps_arg is None:
        return proc.extract_frames(input_path, out_dir)
    else:
        return proc.extract_frames(input_path, out_dir, fps=fps_arg)


class ImplOK:
    def __init__(self):
        self.calls = []

    def extract_frames(self, input_path: str, out_dir: str, fps: int = 1) -> int:
        self.calls.append((input_path, out_dir, fps))
        return fps * 10


class MissingMethod:
    pass


def test_duck_typing_calls_with_default_and_custom_fps():
    proc = ImplOK()

    res_default = run_extract(proc)
    res_custom = run_extract(proc, fps_arg=5)

    assert res_default == 10
    assert res_custom == 50

    assert proc.calls == [
        ("input.mp4", "/tmp/frames", 1),
        ("input.mp4", "/tmp/frames", 5),
    ]


def test_missing_method_raises_attribute_error():
    with pytest.raises(AttributeError):
        run_extract(MissingMethod())


def test_isinstance_and_issubclass_raise_typeerror_without_runtime_checkable():
    with pytest.raises(TypeError):
        isinstance(ImplOK(), VideoProcessorPort)  # noqa: B015
    with pytest.raises(TypeError):
        issubclass(ImplOK, VideoProcessorPort)    # noqa: B015
