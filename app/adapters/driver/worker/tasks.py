from app.adapters.driver.worker.celery_app import celery_app
from app.config.container import get_process_service
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="process_video_job", bind=True)
def process_video_job(self, job_id: str):
    logger.info("process_video_job: START %s", job_id)
    service = get_process_service()
    try:
        service(job_id=job_id)  # faz todo o trabalho e atualiza o status
        logger.info("process_video_job: DONE %s", job_id)
    except Exception:
        logger.exception("process_video_job: ERROR %s", job_id)
        raise
