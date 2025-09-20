from app.adapters.driver.worker.celery_app import celery_app
from app.config.container import get_process_service

@celery_app.task(name="process_video_job")
def process_video_job(job_id: str):
    service = get_process_service()
    service(job_id=job_id)
