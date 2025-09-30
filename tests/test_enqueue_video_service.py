import io

from app.domain.services.enqueue_video import EnqueueVideoService
from app.domain.entities import Video, VideoJob, JobStatus


class FakeRepo:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


class FakeUoW:
    def __init__(self, events):
        self.videos = FakeRepo()
        self.jobs = FakeRepo()
        self.events = events
        self.entered = False
        self.exited = False
        self.commit_called = False

    def __enter__(self):
        self.entered = True
        self.events.append(("enter", None))
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exited = True
        self.events.append(("exit", exc_type.__name__ if exc_type else None))
        # não suprime exceções
        return False

    def commit(self):
        self.commit_called = True
        self.events.append(("commit", None))

    def rollback(self):
        self.events.append(("rollback", None))


class FakeStorage:
    def __init__(self):
        self.calls = []

    def save_upload(self, file_stream, filename: str) -> str:
        data_peek = file_stream.read(0)
        self.calls.append(("save_upload", filename, data_peek))
        return f"/uploads/{filename}"

    def save_artifact(self, local_path: str) -> str:
        return f"/outputs/{local_path.rsplit('/', 1)[-1]}"

    def make_temp_dir(self, prefix: str) -> str:
        return f"/tmp/{prefix}_x"

    def resolve_path(self, ref: str) -> str:
        return ref


class FakeBus:
    def __init__(self, events):
        self.events = events
        self.enqueued = []

    def enqueue_process(self, job_id: str) -> None:
        self.enqueued.append(job_id)
        self.events.append(("enqueue", job_id))


class _UUIDStub:
    def __init__(self, value):
        self._v = value

    def __str__(self):
        return self._v


def _patch_uuid4(monkeypatch, values):
    it = iter(values)

    def fake_uuid4():
        return _UUIDStub(next(it))

    monkeypatch.setattr("app.domain.services.enqueue_video.uuid4", lambda: fake_uuid4())


def test_enqueue_happy_path_with_custom_fps(monkeypatch):
    _patch_uuid4(monkeypatch, ["vid-uuid", "job-uuid"])

    events = []
    uow = FakeUoW(events)
    storage = FakeStorage()
    bus = FakeBus(events)

    svc = EnqueueVideoService(uow=uow, storage=storage, bus=bus)

    job_id = svc(
        user_id="user-1", file_stream=io.BytesIO(b"data"), filename="video.mp4", fps=5
    )

    assert job_id == "job-uuid"

    assert storage.calls == [("save_upload", "video.mp4", b"")]

    assert len(uow.videos.added) == 1
    v = uow.videos.added[0]
    assert isinstance(v, Video)
    assert v.id == "vid-uuid"
    assert v.user_id == "user-1"
    assert v.filename == "video.mp4"
    assert v.storage_ref == "/uploads/video.mp4"

    assert len(uow.jobs.added) == 1
    j = uow.jobs.added[0]
    assert isinstance(j, VideoJob)
    assert j.id == "job-uuid"
    assert j.video_id == "vid-uuid"
    assert j.user_id == "user-1"
    assert j.status == JobStatus.QUEUED
    assert j.fps == 5

    assert uow.entered is True
    assert uow.exited is True
    assert uow.commit_called is True

    assert bus.enqueued == ["job-uuid"]

    assert [e[0] for e in events] == ["enter", "commit", "exit", "enqueue"]
    assert events[-1] == ("enqueue", "job-uuid")


def test_enqueue_uses_default_fps_when_omitted(monkeypatch):
    _patch_uuid4(monkeypatch, ["v2", "j2"])

    events = []
    uow = FakeUoW(events)
    storage = FakeStorage()
    bus = FakeBus(events)

    svc = EnqueueVideoService(uow=uow, storage=storage, bus=bus)

    job_id = svc(user_id="u2", file_stream=io.BytesIO(b"x"), filename="f.bin")

    assert job_id == "j2"
    job = uow.jobs.added[0]
    assert job.fps == 1
