import sys
import types
from fastapi import APIRouter
from fastapi.testclient import TestClient

MODULE_PATH = "app.main"
FAKE_CONTROLLERS = "app.adapters.driver.api.controllers"


def _install_fake_controllers_module():
    for pkg in [
        "app",
        "app.adapters",
        "app.adapters.driver",
        "app.adapters.driver.api",
    ]:
        if pkg not in sys.modules:
            sys.modules[pkg] = types.ModuleType(pkg)

    router = APIRouter()

    @router.get("/ping")
    def ping():
        return {"pong": True}

    from app.domain.errors import AuthError

    @router.get("/boom")
    def boom():
        raise AuthError("Token inválido", 401)

    mod = types.ModuleType(FAKE_CONTROLLERS)
    mod.router = router
    sys.modules[FAKE_CONTROLLERS] = mod


def _import_app_module_fresh():
    sys.modules.pop(MODULE_PATH, None)
    mod = __import__(MODULE_PATH, fromlist=["*"])
    return mod


def test_create_app_health_and_router_and_exception_handler():
    _install_fake_controllers_module()
    mod = _import_app_module_fresh()

    assert hasattr(mod, "create_app")
    assert hasattr(mod, "app")

    app = mod.create_app()
    client = TestClient(app)

    assert app.title == "Video Service"

    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

    r = client.get("/api/ping")
    assert r.status_code == 200
    assert r.json() == {"pong": True}

    r = client.get("/api/boom")
    assert r.status_code == 401
    assert r.json() == {"detail": "Token inválido"}

    gclient = TestClient(mod.app)
    gr = gclient.get("/healthz")
    assert gr.status_code == 200
    assert gr.json() == {"status": "ok"}
