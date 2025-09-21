import os
import sys
import types
import importlib.util
from pathlib import Path

MODULE_NAME = "app.adapters.driver.worker.celery_app"

FILE_PATH = (Path(__file__).resolve().parents[1] / "app" / "adapters" / "driver" / "worker" / "celery_app.py")


def _ensure_pkg(name: str):
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        mod.__path__ = []
        sys.modules[name] = mod
    elif not hasattr(mod, "__path__"):
        mod.__path__ = []
    return mod


def _inject_dummy_tasks_module():
    _ensure_pkg("app")
    _ensure_pkg("app.adapters")
    _ensure_pkg("app.adapters.driver")
    _ensure_pkg("app.adapters.driver.worker")
    tasks_name = "app.adapters.driver.worker.tasks"
    if tasks_name not in sys.modules:
        m = types.ModuleType(tasks_name)
        m.DUMMY_TASKS_IMPORTED = True
        sys.modules[tasks_name] = m
    return sys.modules[tasks_name]


def _load_celery_module_with_env(broker_url: str | None, backend_url: str | None):
    sys.modules.pop(MODULE_NAME, None)

    _inject_dummy_tasks_module()

    if broker_url is None:
        os.environ.pop("BROKER_URL", None)
    else:
        os.environ["BROKER_URL"] = broker_url

    if backend_url is None:
        os.environ.pop("RESULT_BACKEND", None)
    else:
        os.environ["RESULT_BACKEND"] = backend_url

    assert FILE_PATH.exists(), f"Arquivo não encontrado: {FILE_PATH}"
    spec = importlib.util.spec_from_file_location(MODULE_NAME, FILE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = mod
    assert spec and spec.loader, "Spec/loader inválidos para celery_app.py"
    spec.loader.exec_module(mod)
    return mod


def test_celery_app_uses_env_and_imports_tasks():
    custom_broker = "redis://localhost:6379/0"
    custom_backend = "rpc://"
    mod = _load_celery_module_with_env(custom_broker, custom_backend)

    assert hasattr(mod, "celery_app")
    app = mod.celery_app

    assert getattr(app, "main", None) == "video_processor"
    assert app.conf.broker_url == custom_broker
    assert app.conf.result_backend == custom_backend

    assert app.conf.task_track_started is True
    assert app.conf.task_time_limit == 600
    assert app.conf.task_soft_time_limit == 540
    assert app.conf.worker_prefetch_multiplier == 1
    assert app.conf.task_acks_late is True

    tasks_mod = sys.modules.get("app.adapters.driver.worker.tasks")
    assert tasks_mod and getattr(tasks_mod, "DUMMY_TASKS_IMPORTED", False) is True


def test_celery_app_defaults_when_env_missing():
    mod = _load_celery_module_with_env(None, None)
    app = mod.celery_app

    assert app.conf.broker_url == "amqp://guest:guest@rabbitmq:5672//"
    assert app.conf.result_backend == "rpc://"

    assert app.conf.task_track_started is True
    assert app.conf.task_time_limit == 600
    assert app.conf.task_soft_time_limit == 540
    assert app.conf.worker_prefetch_multiplier == 1
    assert app.conf.task_acks_late is True
