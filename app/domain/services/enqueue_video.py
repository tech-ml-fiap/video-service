from uuid import uuid4
from typing import BinaryIO
from app.domain.entities import Video, VideoJob, JobStatus
from app.domain.ports.uow import UnitOfWorkPort
from app.domain.ports.storage import StoragePort
from app.domain.ports.message_bus import MessageBusPort

class EnqueueVideoService:
    def __init__(self, uow: UnitOfWorkPort, storage: StoragePort, bus: MessageBusPort):
        self.uow = uow
        self.storage = storage
        self.bus = bus

    def __call__(self, *, user_id: str, file_stream: BinaryIO, filename: str, fps: int = 1) -> str:
        video_id = str(uuid4())
        job_id = str(uuid4())

        with self.uow:
            storage_ref = self.storage.save_upload(file_stream, filename)
            video = Video(id=video_id, user_id=user_id, filename=filename, storage_ref=storage_ref)
            self.uow.videos.add(video)

            job = VideoJob(id=job_id, video_id=video_id, user_id=user_id, status=JobStatus.QUEUED, fps=fps)
            self.uow.jobs.add(job)
            self.uow.commit()

        self.bus.enqueue_process(job_id)
        return job_id
