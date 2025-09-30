import os
from celery import Celery

broker_url = os.getenv("BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
result_backend = os.getenv("RESULT_BACKEND", "rpc://")

celery_app = Celery("video_processor", broker=broker_url, backend=result_backend)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


# (opção A) importar o módulo de tasks explicitamente

# (opção B alternativa) ao invés da linha acima:
# celery_app.conf.imports = ("app.adapters.driver.worker.tasks",)
