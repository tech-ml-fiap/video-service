from typing import Optional, Iterable
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.domain.entities import VideoJob
from app.domain.ports.repository import JobRepositoryPort
from app.adapters.driven.db.models import JobModel


class SQLAlchemyJobRepository(JobRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def add(self, j: VideoJob) -> None:
        self.session.add(JobModel.from_entity(j))

    def get(self, job_id: str) -> Optional[VideoJob]:
        row = self.session.get(JobModel, job_id)
        return row.to_entity() if row else None

    def update(self, j: VideoJob) -> None:
        db_obj = self.session.get(JobModel, j.id)
        if not db_obj:
            return
        db_obj.status = j.status
        db_obj.fps = j.fps
        db_obj.frame_count = j.frame_count
        db_obj.artifact_ref = j.artifact_ref
        db_obj.error = j.error

    def list_by_user(self, user_id: str) -> Iterable[VideoJob]:
        rows = self.session.scalars(
            select(JobModel)
            .where(JobModel.user_id == user_id)
            .order_by(JobModel.created_at.desc())
        )
        for r in rows:
            yield r.to_entity()
