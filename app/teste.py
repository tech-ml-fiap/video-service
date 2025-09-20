from app.adapters.driver.worker.celery_app import celery_app
from app.config.container import get_process_service
import logging

service = get_process_service()
service(job_id=job_id)