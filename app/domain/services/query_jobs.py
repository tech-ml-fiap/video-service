from typing import List, Dict
from app.domain.ports.uow import UnitOfWorkPort

class GetJobStatusService:
    def __init__(self, uow: UnitOfWorkPort):
        self.uow = uow

    def __call__(self, *, job_id: str, user_id: str) -> dict:
        with self.uow:
            job = self.uow.jobs.get(job_id)
            if not job or job.user_id != user_id:
                raise KeyError("Job not found")
            return {
                "job_id": job.id,
                "status": job.status,
                "fps": job.fps,
                "frames": job.frame_count,
                "artifact_ref": job.artifact_ref,
                "error": job.error,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat()
            }

class ListJobsByUserService:
    def __init__(self, uow: UnitOfWorkPort):
        self.uow = uow

    def __call__(self, *, user_id: str) -> List[Dict]:
        with self.uow:
            jobs = self.uow.jobs.list_by_user(user_id)
            return [
                {"job_id": j.id, "status": j.status, "fps": j.fps, "frames": j.frame_count, "artifact_ref": j.artifact_ref}
                for j in jobs
            ]
