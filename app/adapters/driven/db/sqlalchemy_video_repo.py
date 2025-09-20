from typing import Optional
from sqlalchemy.orm import Session
from app.domain.entities import Video
from app.domain.ports.repository import VideoRepositoryPort
from .models import VideoModel

class SQLAlchemyVideoRepository(VideoRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def add(self, v: Video) -> None:
        self.session.add(VideoModel.from_entity(v))

    def get(self, video_id: str) -> Optional[Video]:
        row = self.session.get(VideoModel, video_id)
        return row.to_entity() if row else None
