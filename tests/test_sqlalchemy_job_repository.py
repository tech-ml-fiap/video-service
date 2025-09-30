from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func

from app.adapters.driven.db.models import VideoModel, JobModel
from app.adapters.driven.repositories.sqlalchemy_job_repo import SQLAlchemyJobRepository
from app.domain.entities import VideoJob, JobStatus


def _make_parent_video(session, video_id: str, user_id="u1"):
    v = VideoModel(
        id=video_id,
        user_id=user_id,
        filename="file.mp4",
        storage_ref="s3://bucket/key",
        duration=12.3,
    )
    session.add(v)
    session.commit()
    return v


def _make_job_entity(
    job_id,
    video_id,
    user_id="u1",
    status=JobStatus.QUEUED,
    fps=1,
    frame_count=0,
    artifact_ref=None,
    error=None,
):
    now = datetime.now(timezone.utc)
    return VideoJob(
        id=job_id,
        video_id=video_id,
        user_id=user_id,
        status=status,
        fps=fps,
        frame_count=frame_count,
        artifact_ref=artifact_ref,
        error=error,
        created_at=now,
        updated_at=now,
    )


def test_add_and_get_roundtrip(session, uid):
    repo = SQLAlchemyJobRepository(session)
    video_id = uid()
    _make_parent_video(session, video_id)

    job_id = uid()
    ent = _make_job_entity(job_id, video_id, user_id="alice", fps=2, frame_count=5)
    repo.add(ent)
    session.commit()

    got = repo.get(job_id)
    assert isinstance(got, VideoJob)
    assert got.id == job_id
    assert got.video_id == video_id
    assert got.user_id == "alice"
    assert got.status == JobStatus.QUEUED
    assert got.fps == 2
    assert got.frame_count == 5
    assert got.artifact_ref is None
    assert got.error is None
    assert isinstance(got.created_at, datetime)
    assert isinstance(got.updated_at, datetime)


def test_get_returns_none_when_missing(session):
    repo = SQLAlchemyJobRepository(session)
    assert repo.get("non-existent") is None


def test_update_existing_and_noop_when_missing(session, uid):
    repo = SQLAlchemyJobRepository(session)
    video_id = uid()
    _make_parent_video(session, video_id)

    job_id = uid()
    ent = _make_job_entity(
        job_id, video_id, user_id="bob", status=JobStatus.QUEUED, fps=1, frame_count=0
    )
    repo.add(ent)
    session.commit()

    ent_updated = _make_job_entity(
        job_id,
        video_id,
        user_id="bob",
        status=JobStatus.RUNNING,
        fps=4,
        frame_count=42,
        artifact_ref="s3://out/artifact.json",
        error="partial warning",
    )
    repo.update(ent_updated)
    session.commit()

    db_row = session.get(JobModel, job_id)
    assert db_row.status == JobStatus.RUNNING
    assert db_row.fps == 4
    assert db_row.frame_count == 42
    assert db_row.artifact_ref == "s3://out/artifact.json"
    assert db_row.error == "partial warning"

    missing = _make_job_entity("missing-id", video_id)
    before_count = session.scalar(select(func.count()).select_from(JobModel))
    repo.update(missing)
    session.commit()
    after_count = session.scalar(select(func.count()).select_from(JobModel))
    assert after_count == before_count


def test_list_by_user_returns_in_desc_created_at(session, uid):
    repo = SQLAlchemyJobRepository(session)
    video_id = uid()
    _make_parent_video(session, video_id)

    j1 = _make_job_entity(uid(), video_id, user_id="carol", fps=1, frame_count=1)
    repo.add(j1)
    session.commit()

    j2 = _make_job_entity(uid(), video_id, user_id="carol", fps=2, frame_count=2)
    repo.add(j2)
    session.commit()

    t_early = datetime.now(timezone.utc) - timedelta(seconds=10)
    t_late = datetime.now(timezone.utc) + timedelta(seconds=10)
    db_j1 = session.get(JobModel, j1.id)
    db_j2 = session.get(JobModel, j2.id)
    db_j1.created_at = t_early
    db_j2.created_at = t_late
    session.commit()

    listed = list(repo.list_by_user("carol"))
    assert [j.id for j in listed] == [j2.id, j1.id]
    assert listed[0].fps == 2 and listed[1].fps == 1


def test_list_by_user_empty(session):
    repo = SQLAlchemyJobRepository(session)
    assert list(repo.list_by_user("nobody")) == []
