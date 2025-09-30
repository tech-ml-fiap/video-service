from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


@dataclass
class Video:
    id: str
    user_id: str
    filename: str
    storage_ref: str
    duration: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VideoJob:
    id: str
    video_id: str
    user_id: str
    status: JobStatus = JobStatus.QUEUED
    fps: int = 1
    frame_count: int = 0
    artifact_ref: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
