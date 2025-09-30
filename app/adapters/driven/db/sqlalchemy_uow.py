from sqlalchemy.orm import sessionmaker, Session
from app.domain.ports.uow import UnitOfWorkPort
from app.domain.ports.repository import VideoRepositoryPort, JobRepositoryPort
from app.adapters.driven.repositories.sqlalchemy_video_repo import (
    SQLAlchemyVideoRepository,
)
from app.adapters.driven.repositories.sqlalchemy_job_repo import SQLAlchemyJobRepository


class SQLAlchemyUnitOfWork(UnitOfWorkPort):
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
        self._session: Session | None = None
        self.videos: VideoRepositoryPort | None = None
        self.jobs: JobRepositoryPort | None = None

    def __enter__(self):
        self._session = self._session_factory()
        self.videos = SQLAlchemyVideoRepository(self._session)
        self.jobs = SQLAlchemyJobRepository(self._session)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                self._session.rollback()
            else:
                self._session.commit()
        finally:
            self._session.close()

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()
