import sys
import types
import pytest

TASKS_MOD = "app.adapters.driver.worker.tasks"
CELERY_APP_MOD = "app.adapters.driver.worker.celery_app"
CONTAINER_MOD = "app.config.container"


class NoopCelery:
    def task(self, *_, **__):
        def deco(fn):
            return fn

        return deco


def _prepare_modules(fake_service):
    celery_module = types.ModuleType(CELERY_APP_MOD)
    celery_module.celery_app = NoopCelery()
    sys.modules[CELERY_APP_MOD] = celery_module

    container_module = types.ModuleType(CONTAINER_MOD)
    container_module.get_process_service = lambda: fake_service
    sys.modules[CONTAINER_MOD] = container_module

    sys.modules.pop(TASKS_MOD, None)
    return __import__(TASKS_MOD, fromlist=["*"])


def test_process_video_job_success_logs_and_calls_service(caplog):
    called = {}

    def fake_service(*, job_id: str):
        called["job_id"] = job_id

    tasks = _prepare_modules(fake_service)

    with caplog.at_level("INFO"):
        tasks.process_video_job(object(), job_id="job-123")

    assert called == {"job_id": "job-123"}

    joined = " | ".join(rec.getMessage() for rec in caplog.records)
    assert "process_video_job: START job-123" in joined
    assert "process_video_job: DONE job-123" in joined


def test_process_video_job_error_logs_and_reraises(caplog):
    class Boom(Exception):
        pass

    def fake_service(*, job_id: str):
        raise Boom(f"fail {job_id}")

    tasks = _prepare_modules(fake_service)

    with caplog.at_level("INFO"):
        with pytest.raises(Boom):
            tasks.process_video_job(object(), job_id="job-999")

    msgs = [rec.getMessage() for rec in caplog.records]
    assert any("process_video_job: START job-999" in m for m in msgs)
    assert any("process_video_job: ERROR job-999" in m for m in msgs)
