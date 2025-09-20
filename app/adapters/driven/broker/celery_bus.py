from celery import Celery
from app.domain.ports.message_bus import MessageBusPort

class CeleryMessageBus(MessageBusPort):
    def __init__(self, broker_url: str, backend_url: str | None = None):
        self._celery = Celery("video_processor_client", broker=broker_url, backend=backend_url or None)

    def enqueue_process(self, job_id: str) -> None:
        self._celery.send_task("process_video_job", args=[job_id])
