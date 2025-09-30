import time
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, inspect
from sqlalchemy.orm import selectinload

from app.adapters.driven.db.models import VideoModel, JobModel
from app.domain.entities import Video, VideoJob, JobStatus


def test_video_from_and_to_entity_roundtrip(session, uid):
    v_ent = Video(
        id=uid(),
        user_id="u1",
        filename="file.mp4",
        storage_ref="s3://bucket/k",
        duration=12.34,
        created_at=datetime.now(timezone.utc),
    )

    v_model = VideoModel.from_entity(v_ent)
    session.add(v_model)
    session.commit()

    db_video = session.scalar(select(VideoModel).where(VideoModel.id == v_ent.id))
    assert db_video is not None
    assert db_video.id == v_ent.id
    assert db_video.user_id == "u1"
    assert db_video.filename == "file.mp4"
    assert db_video.storage_ref == "s3://bucket/k"
    assert db_video.duration == pytest.approx(12.34)
    assert isinstance(db_video.created_at, datetime)

    out_ent = db_video.to_entity()
    assert out_ent.id == v_ent.id
    assert out_ent.user_id == v_ent.user_id
    assert out_ent.filename == v_ent.filename
    assert out_ent.storage_ref == v_ent.storage_ref
    assert out_ent.duration == v_ent.duration
    assert isinstance(out_ent.created_at, datetime)


def test_job_from_and_to_entity_roundtrip_with_defaults(session, uid):
    v = VideoModel(
        id=uid(), user_id="u1", filename="f.mp4", storage_ref="s3://b/k", duration=None
    )
    session.add(v)
    session.commit()

    j_ent = VideoJob(
        id=uid(),
        video_id=v.id,
        user_id="u1",
        status=JobStatus.QUEUED,
        fps=1,
        frame_count=0,
        artifact_ref=None,
        error=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    j_model = JobModel.from_entity(j_ent)
    session.add(j_model)
    session.commit()

    db_job = session.scalar(select(JobModel).where(JobModel.id == j_ent.id))
    assert db_job is not None

    assert db_job.status == JobStatus.QUEUED
    assert db_job.fps == 1
    assert db_job.frame_count == 0
    assert db_job.artifact_ref is None
    assert db_job.error is None
    assert isinstance(db_job.created_at, datetime)
    assert isinstance(db_job.updated_at, datetime)

    out_ent = db_job.to_entity()
    assert out_ent.id == j_ent.id
    assert out_ent.video_id == v.id
    assert out_ent.user_id == "u1"
    assert out_ent.status == JobStatus.QUEUED
    assert out_ent.fps == 1
    assert out_ent.frame_count == 0
    assert out_ent.artifact_ref is None
    assert out_ent.error is None
    assert isinstance(out_ent.created_at, datetime)
    assert isinstance(out_ent.updated_at, datetime)


def test_relationship_video_jobs_and_back_populates(session, uid):
    video = VideoModel(
        id=uid(),
        user_id="u1",
        filename="a.mp4",
        storage_ref="s3://bucket/a",
        duration=3.2,
    )
    job1 = JobModel(
        id=uid(),
        video_id=video.id,
        user_id="u1",
        status=JobStatus.QUEUED,
        fps=2,
        frame_count=10,
    )
    job2 = JobModel(
        id=uid(),
        video_id=video.id,
        user_id="u1",
        status=JobStatus.RUNNING,
        fps=3,
        frame_count=20,
    )

    session.add_all([video, job1, job2])
    session.commit()

    v_db = session.scalar(
        select(VideoModel)
        .options(selectinload(VideoModel.jobs))
        .where(VideoModel.id == video.id)
    )
    assert len(v_db.jobs) == 2
    assert {j.id for j in v_db.jobs} == {job1.id, job2.id}
    assert all(j.video.id == video.id for j in v_db.jobs)


def test_cascade_delete_orphan_jobs(session, uid):
    video = VideoModel(
        id=uid(),
        user_id="u1",
        filename="b.mp4",
        storage_ref="s3://bucket/b",
        duration=1.0,
    )
    job = JobModel(
        id=uid(),
        video_id=video.id,
        user_id="u1",
        status=JobStatus.DONE,
        fps=1,
        frame_count=1,
    )
    session.add_all([video, job])
    session.commit()

    assert (
        session.scalar(select(VideoModel).where(VideoModel.id == video.id)) is not None
    )
    assert session.scalar(select(JobModel).where(JobModel.id == job.id)) is not None

    session.delete(video)
    session.commit()

    assert session.scalar(select(VideoModel).where(VideoModel.id == video.id)) is None
    assert session.scalar(select(JobModel).where(JobModel.id == job.id)) is None


def test_updated_at_changes_on_update(session, uid):
    video = VideoModel(
        id=uid(),
        user_id="u1",
        filename="c.mp4",
        storage_ref="s3://bucket/c",
        duration=2.5,
    )
    job = JobModel(
        id=uid(),
        video_id=video.id,
        user_id="u1",
        status=JobStatus.QUEUED,
        fps=1,
        frame_count=0,
    )
    session.add_all([video, job])
    session.commit()

    before = job.updated_at
    time.sleep(0.01)
    job.status = JobStatus.RUNNING
    session.add(job)
    session.commit()
    session.refresh(job)

    assert job.updated_at >= before
    assert job.status == JobStatus.RUNNING


def test_schema_and_indexes_exist(session, engine, uid):
    insp = inspect(engine)
    assert set(insp.get_table_names()) >= {"videos", "video_jobs"}

    video_indexes = insp.get_indexes("videos")
    video_index_cols = {tuple(i["column_names"]) for i in video_indexes}
    assert ("user_id",) in video_index_cols

    job_indexes = insp.get_indexes("video_jobs")
    job_index_cols = {tuple(i["column_names"]) for i in job_indexes}
    assert ("user_id",) in job_index_cols
    assert ("status",) in job_index_cols
    assert ("created_at",) in job_index_cols
