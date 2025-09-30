import os
import zipfile
from datetime import datetime, timedelta

from app.domain.services.process_video import ProcessVideoService
from app.domain.entities import JobStatus


class _Video:
    def __init__(self, id, user_id, filename, storage_ref):
        self.id = id
        self.user_id = user_id
        self.filename = filename
        self.storage_ref = storage_ref


class _Job:
    def __init__(self, id, video_id, user_id, status=JobStatus.QUEUED, fps=1):
        self.id = id
        self.video_id = video_id
        self.user_id = user_id
        self.status = status
        self.fps = fps
        self.frame_count = 0
        self.artifact_ref = None
        self.error = None
        self.updated_at = None


class _VideoRepo:
    def __init__(self):
        self._by_id = {}

    def add(self, v):
        self._by_id[v.id] = v

    def get(self, video_id):
        return self._by_id.get(video_id)


class _JobRepo:
    def __init__(self):
        self._by_id = {}

    def add(self, j):
        self._by_id[j.id] = j

    def get(self, job_id):
        return self._by_id.get(job_id)

    def update(self, j):
        self._by_id[j.id] = j


class _UoW:
    def __init__(self, videos: _VideoRepo, jobs: _JobRepo):
        self.videos = videos
        self.jobs = jobs
        self.commits = 0
        self.enters = 0
        self.exits = 0

    def __enter__(self):
        self.enters += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exits += 1
        return False

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


class _Storage:
    def __init__(self, tmp_path):
        self.tmp_path = tmp_path
        self.saved_zip_path = None
        self.saved_zip_entries = None
        self._seed_files = []

    def resolve_path(self, ref: str) -> str:
        return ref

    def make_temp_dir(self, prefix: str) -> str:
        d = self.tmp_path / f"{prefix}_tmp"
        d.mkdir(parents=True, exist_ok=True)
        for name in self._seed_files:
            p = d / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"x")
        return str(d)

    def save_artifact(self, local_path: str) -> str:
        self.saved_zip_path = local_path
        with zipfile.ZipFile(local_path, "r") as zf:
            self.saved_zip_entries = sorted(zf.namelist())
        return os.path.join("/outputs", os.path.basename(local_path))


class _ProcessorOK:
    def __init__(self, frame_count: int):
        self.frame_count = frame_count
        self.calls = []

    def extract_frames(self, input_path, out_dir, fps=1) -> int:
        self.calls.append((input_path, out_dir, fps))
        return self.frame_count


class _ProcessorBoom:
    def __init__(self, exc: Exception):
        self.exc = exc
        self.calls = []

    def extract_frames(self, input_path, out_dir, fps=1) -> int:
        self.calls.append((input_path, out_dir, fps))
        raise self.exc


def test_returns_early_when_job_missing(tmp_path):
    videos = _VideoRepo()
    jobs = _JobRepo()  # vazio
    uow = _UoW(videos, jobs)
    storage = _Storage(tmp_path)
    processor = _ProcessorOK(frame_count=2)

    svc = ProcessVideoService(uow=uow, storage=storage, processor=processor)
    svc(job_id="nope")

    assert uow.commits == 0
    assert processor.calls == []


def test_sets_running_then_completes_successfully_creates_zip_only_images(tmp_path):
    videos = _VideoRepo()
    jobs = _JobRepo()
    job = _Job(id="job1", video_id="vid1", user_id="u1", status=JobStatus.QUEUED, fps=3)
    video = _Video(
        id="vid1", user_id="u1", filename="v.mp4", storage_ref=str(tmp_path / "v.mp4")
    )
    (tmp_path / "v.mp4").write_bytes(b"video")  # input local

    jobs.add(job)
    videos.add(video)

    uow = _UoW(videos, jobs)
    storage = _Storage(tmp_path)
    storage._seed_files = [
        "00000001.jpg",
        "nested/00000002.PNG",
        "ignore.txt",
        "also/ignore.jpegx",
    ]
    processor = _ProcessorOK(frame_count=2)

    svc = ProcessVideoService(uow=uow, storage=storage, processor=processor)
    before = datetime.utcnow() - timedelta(seconds=1)
    svc(job_id="job1")
    after = datetime.utcnow() + timedelta(seconds=1)

    assert uow.commits == 2
    j = jobs.get("job1")
    assert j.status == JobStatus.DONE
    assert j.frame_count == 2
    assert j.artifact_ref == os.path.join("/outputs", "frames_job1.zip")
    assert j.updated_at is not None and before <= j.updated_at <= after

    assert storage.saved_zip_entries == ["00000001.jpg", "nested/00000002.PNG"]

    [(in_path, out_dir, fps)] = processor.calls
    assert in_path == str(tmp_path / "v.mp4")
    assert not os.path.exists(out_dir)
    assert out_dir.endswith("job1_tmp")
    assert fps == 3


def test_video_not_found_sets_error_and_does_not_call_processor(tmp_path):
    videos = _VideoRepo()
    jobs = _JobRepo()
    job = _Job(
        id="job2", video_id="vid_missing", user_id="u1", status=JobStatus.QUEUED, fps=1
    )
    jobs.add(job)

    uow = _UoW(videos, jobs)
    storage = _Storage(tmp_path)
    processor = _ProcessorOK(frame_count=5)

    svc = ProcessVideoService(uow=uow, storage=storage, processor=processor)
    svc(job_id="job2")

    j = jobs.get("job2")
    assert j.status == JobStatus.ERROR
    assert j.error == "Video not found"
    assert uow.commits == 2
    assert processor.calls == []


def test_no_frames_extracted_sets_error(tmp_path):
    videos = _VideoRepo()
    jobs = _JobRepo()
    job = _Job(id="job3", video_id="vid3", user_id="u1", status=JobStatus.QUEUED, fps=1)
    video = _Video(
        id="vid3", user_id="u1", filename="v.mp4", storage_ref=str(tmp_path / "v3.mp4")
    )
    (tmp_path / "v3.mp4").write_bytes(b"v")

    jobs.add(job)
    videos.add(video)

    uow = _UoW(videos, jobs)
    storage = _Storage(tmp_path)
    storage._seed_files = []
    processor = _ProcessorOK(frame_count=0)

    svc = ProcessVideoService(uow=uow, storage=storage, processor=processor)
    svc(job_id="job3")

    j = jobs.get("job3")
    assert j.status == JobStatus.ERROR
    assert j.error == "No frames extracted"
    assert j.updated_at is not None
    assert uow.commits == 2


def test_processor_raises_exception_sets_error_with_message(tmp_path):
    videos = _VideoRepo()
    jobs = _JobRepo()
    job = _Job(id="job4", video_id="vid4", user_id="u1", status=JobStatus.QUEUED, fps=2)
    video = _Video(
        id="vid4", user_id="u1", filename="v.mp4", storage_ref=str(tmp_path / "v4.mp4")
    )
    (tmp_path / "v4.mp4").write_bytes(b"v")

    jobs.add(job)
    videos.add(video)

    uow = _UoW(videos, jobs)
    storage = _Storage(tmp_path)
    storage._seed_files = ["a.jpg"]
    processor = _ProcessorBoom(RuntimeError("boom"))

    svc = ProcessVideoService(uow=uow, storage=storage, processor=processor)
    svc(job_id="job4")

    j = jobs.get("job4")
    assert j.status == JobStatus.ERROR
    assert j.error == "boom"
    assert j.updated_at is not None
    assert uow.commits == 2
