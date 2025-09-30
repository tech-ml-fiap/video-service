# app/adapters/driven/db/models.py
from __future__ import annotations

from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Enum, DateTime, Text, Float, ForeignKey, func
from app.domain.entities import JobStatus


class Base(DeclarativeBase):
    pass


class VideoModel(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_ref: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    jobs: Mapped[List["JobModel"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )

    def to_entity(self):
        from app.domain.entities import Video

        return Video(
            id=self.id,
            user_id=self.user_id,
            filename=self.filename,
            storage_ref=self.storage_ref,
            duration=self.duration,
            created_at=self.created_at,
        )

    @staticmethod
    def from_entity(v):
        return VideoModel(
            id=v.id,
            user_id=v.user_id,
            filename=v.filename,
            storage_ref=v.storage_ref,
            duration=v.duration,
        )


class JobModel(Base):
    __tablename__ = "video_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(64), index=True)

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True,
    )

    fps: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    frame_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    artifact_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    video: Mapped["VideoModel"] = relationship(back_populates="jobs")

    def to_entity(self):
        from app.domain.entities import VideoJob

        return VideoJob(
            id=self.id,
            video_id=self.video_id,
            user_id=self.user_id,
            status=self.status,
            fps=self.fps,
            frame_count=self.frame_count,
            artifact_ref=self.artifact_ref,
            error=self.error,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def from_entity(j):
        return JobModel(
            id=j.id,
            video_id=j.video_id,
            user_id=j.user_id,
            status=j.status,
            fps=j.fps,
            frame_count=j.frame_count,
            artifact_ref=j.artifact_ref,
            error=j.error,
        )
