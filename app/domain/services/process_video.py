import os, shutil
import zipfile
from datetime import datetime
from app.domain.entities import JobStatus
from app.domain.ports.uow import UnitOfWorkPort
from app.domain.ports.storage import StoragePort
from app.domain.ports.video_processor import VideoProcessorPort

class ProcessVideoService:
    def __init__(self, uow: UnitOfWorkPort, storage: StoragePort, processor: VideoProcessorPort):
        self.uow = uow
        self.storage = storage
        self.processor = processor

    def __call__(self, *, job_id: str) -> None:
        with self.uow:
            job = self.uow.jobs.get(job_id)
            if not job:
                return
            job.status = JobStatus.RUNNING
            self.uow.jobs.update(job)
            self.uow.commit()

        with self.uow:
            job = self.uow.jobs.get(job_id)
            if not job:
                return
            video = self.uow.videos.get(job.video_id)
            if not video:
                job.status = JobStatus.ERROR
                job.error = "Video not found"
                self.uow.jobs.update(job)
                self.uow.commit()
                return

            input_path = self.storage.resolve_path(video.storage_ref)
            temp_dir = self.storage.make_temp_dir(prefix=job.id)

            try:
                frame_count = self.processor.extract_frames(input_path, temp_dir, fps=job.fps)
                if frame_count <= 0:
                    raise RuntimeError("No frames extracted")

                zip_path = os.path.join(temp_dir, f"frames_{job.id}.zip")
                with zipfile.ZipFile(
                        zip_path,
                        mode="w",
                        compression=zipfile.ZIP_DEFLATED,
                        allowZip64=True,
                ) as zf:
                    for root, _, files in os.walk(temp_dir):
                        for f in sorted(files):
                            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                                abs_path = os.path.join(root, f)
                                rel_path = os.path.relpath(abs_path, temp_dir)
                                zf.write(abs_path, arcname=rel_path)

                artifact_ref = self.storage.save_artifact(zip_path)

                job.frame_count = frame_count
                job.artifact_ref = artifact_ref
                job.status = JobStatus.DONE
                job.updated_at = datetime.utcnow()
                self.uow.jobs.update(job)
                self.uow.commit()
            except Exception as e:
                job.status = JobStatus.ERROR
                job.error = str(e)
                job.updated_at = datetime.utcnow()
                self.uow.jobs.update(job)
                self.uow.commit()
            finally:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass
