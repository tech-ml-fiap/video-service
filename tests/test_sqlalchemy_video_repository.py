from datetime import datetime, timezone

from app.adapters.driven.repositories.sqlalchemy_video_repo import SQLAlchemyVideoRepository
from app.domain.entities import Video
from app.adapters.driven.db.models import VideoModel


def _make_video_entity(video_id: str, user_id="u1"):
    return Video(
        id=video_id,
        user_id=user_id,
        filename="movie.mp4",
        storage_ref="s3://bucket/key",
        duration=123.45,
        created_at=datetime.now(timezone.utc),
    )


def test_add_and_get_roundtrip(session, uid):
    repo = SQLAlchemyVideoRepository(session)

    vid = uid()
    ent = _make_video_entity(vid, user_id="alice")

    repo.add(ent)
    session.commit()

    got = repo.get(vid)
    assert got is not None
    assert got.id == vid
    assert got.user_id == "alice"
    assert got.filename == "movie.mp4"
    assert got.storage_ref == "s3://bucket/key"
    assert got.duration == 123.45
    assert isinstance(got.created_at, datetime)

    db_row = session.get(VideoModel, vid)
    assert db_row is not None
    assert db_row.filename == "movie.mp4"


def test_get_returns_none_when_missing(session):
    repo = SQLAlchemyVideoRepository(session)
    assert repo.get("does-not-exist") is None
