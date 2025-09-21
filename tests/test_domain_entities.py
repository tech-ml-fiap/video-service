from datetime import datetime, timedelta
from app.domain.entities import JobStatus, Video, VideoJob


def _now_bounds():
    before = datetime.utcnow() - timedelta(seconds=5)
    after = datetime.utcnow() + timedelta(seconds=5)
    return before, after


def test_jobstatus_members_and_values():
    assert list(JobStatus) == [
        JobStatus.QUEUED,
        JobStatus.RUNNING,
        JobStatus.DONE,
        JobStatus.ERROR,
    ]
    assert JobStatus.QUEUED.value == "queued"
    assert JobStatus.RUNNING.value == "running"
    assert JobStatus.DONE.value == "done"
    assert JobStatus.ERROR.value == "error"

    assert JobStatus.QUEUED == "queued"
    assert f"{JobStatus.DONE}" == "JobStatus.DONE"
    assert str(JobStatus.ERROR) == "JobStatus.ERROR"


def test_video_defaults_and_fields():
    before, after = _now_bounds()
    v = Video(
        id="vid-1",
        user_id="u-1",
        filename="video.mp4",
        storage_ref="/uploads/video.mp4",
    )

    assert v.id == "vid-1"
    assert v.user_id == "u-1"
    assert v.filename == "video.mp4"
    assert v.storage_ref == "/uploads/video.mp4"

    assert v.duration is None
    assert isinstance(v.created_at, datetime)
    assert before <= v.created_at <= after


def test_videojob_defaults_created_and_updated_time():
    before, after = _now_bounds()
    j = VideoJob(
        id="job-1",
        video_id="vid-1",
        user_id="u-1",
    )

    assert j.status == JobStatus.QUEUED
    assert j.fps == 1
    assert j.frame_count == 0
    assert j.artifact_ref is None
    assert j.error is None

    assert isinstance(j.created_at, datetime)
    assert isinstance(j.updated_at, datetime)
    assert before <= j.created_at <= after
    assert before <= j.updated_at <= after


def test_videojob_mutation_and_status_transition():
    j = VideoJob(id="job-2", video_id="vid-2", user_id="u-2")

    j.status = JobStatus.RUNNING
    j.frame_count = 7
    j.artifact_ref = "/outputs/frames_job-2.zip"
    j.error = None

    assert j.status == JobStatus.RUNNING
    assert j.frame_count == 7
    assert j.artifact_ref == "/outputs/frames_job-2.zip"
    assert j.error is None

    j.status = JobStatus.DONE
    assert j.status == JobStatus.DONE
