import sys
import importlib
import pytest

from app.adapters.driven.broker.celery_bus import CeleryMessageBus


class DummyCelery:
    def __init__(self, name, broker=None, backend=None):
        self.name = name
        self.broker = broker
        self.backend = backend
        self._sent = []

    def send_task(self, task_name, args=None, kwargs=None):
        self._sent.append((task_name, args or [], kwargs or {}))


def _patch_module_celery_symbol(target_cls):
    mod_name = CeleryMessageBus.__module__
    mod = sys.modules.get(mod_name)
    if mod is None:
        mod = importlib.import_module(mod_name)
    setattr(mod, "Celery", target_cls)
    return mod


@pytest.mark.parametrize(
    "broker,backend",
    [
        ("amqp://guest@localhost//", None),
        ("redis://localhost:6379/0", "redis://localhost"),
    ],
)
def test_init_creates_celery_with_expected_params(broker, backend):
    mod = _patch_module_celery_symbol(DummyCelery)

    bus = CeleryMessageBus(broker_url=broker, backend_url=backend)

    assert isinstance(bus._celery, DummyCelery)
    assert bus._celery.name == "video_processor_client"
    assert bus._celery.broker == broker
    expected_backend = backend or None
    assert bus._celery.backend == expected_backend

    # garante que não enviou nada no init
    assert getattr(bus._celery, "_sent", []) == []


def test_enqueue_process_sends_correct_task_name_and_args():
    _patch_module_celery_symbol(DummyCelery)
    bus = CeleryMessageBus(broker_url="amqp://guest@localhost//")

    job_id = "job-123"
    bus.enqueue_process(job_id)

    sent = bus._celery._sent
    assert len(sent) == 1
    task_name, args, kwargs = sent[0]
    assert task_name == "process_video_job"
    assert args == [job_id]
    assert kwargs == {}
