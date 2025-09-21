from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.driver.api.controllers import router as api_router
import app.adapters.driver.api.controllers as routes_module
from app.adapters.driver.api.dependencies import get_current_user


class DummyUser:
    def __init__(self, user_id: str):
        self.user_id = user_id


def make_app(user_id="u-1"):
    app = FastAPI()
    app.include_router(api_router)

    app.dependency_overrides[get_current_user] = lambda: DummyUser(user_id)
    return app


def test_enqueue_video_202(monkeypatch):
    calls = {}

    def fake_enqueue_service():
        def _svc(user_id, file_stream, filename, fps):
            calls["args"] = {
                "user_id": user_id,
                "filename": filename,
                "fps": fps,
                "peek_bytes": file_stream.read(4),
            }
            return "job-123"
        return _svc

    monkeypatch.setattr(routes_module, "get_enqueue_service", fake_enqueue_service)

    app = make_app(user_id="alice")
    client = TestClient(app)

    files = {"file": ("video.mp4", b"\x00\x01\x02\x03DATA", "video/mp4")}
    resp = client.post("/videos?fps=5", files=files)

    assert resp.status_code == 202
    assert resp.json() == {"job_id": "job-123", "status": "queued"}

    assert calls["args"]["user_id"] == "alice"
    assert calls["args"]["filename"] == "video.mp4"
    assert calls["args"]["fps"] == 5
    assert calls["args"]["peek_bytes"] == b"\x00\x01\x02\x03"


def test_get_status_ok(monkeypatch):
    def fake_status_service():
        def _svc(job_id, user_id):
            assert job_id == "job-1"
            assert user_id == "u-1"
            return {"job_id": job_id, "status": "processing"}
        return _svc

    monkeypatch.setattr(routes_module, "get_status_service", fake_status_service)

    app = make_app(user_id="u-1")
    client = TestClient(app)

    resp = client.get("/videos/job-1")
    assert resp.status_code == 200
    assert resp.json() == {"job_id": "job-1", "status": "processing"}


def test_get_status_not_found_404(monkeypatch):
    def fake_status_service():
        def _svc(job_id, user_id):
            raise KeyError("not found")
        return _svc

    monkeypatch.setattr(routes_module, "get_status_service", fake_status_service)

    app = make_app()
    client = TestClient(app)

    resp = client.get("/videos/missing")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Process not found"


def test_list_jobs_ok(monkeypatch):
    def fake_list_jobs_service():
        def _svc(user_id):
            assert user_id == "u-1"
            return [{"job_id": "a"}, {"job_id": "b"}]
        return _svc

    monkeypatch.setattr(routes_module, "get_list_jobs_service", fake_list_jobs_service)

    app = make_app(user_id="u-1")
    client = TestClient(app)

    resp = client.get("/videos")
    assert resp.status_code == 200
    assert resp.json() == [{"job_id": "a"}, {"job_id": "b"}]


def test_download_404_when_process_missing(monkeypatch):
    def fake_status_service():
        def _svc(job_id, user_id):
            raise KeyError("nope")
        return _svc

    monkeypatch.setattr(routes_module, "get_status_service", fake_status_service)

    app = make_app()
    client = TestClient(app)

    resp = client.get("/download/any")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Process not found"


def test_download_400_when_zip_not_ready(monkeypatch):
    def fake_status_service():
        def _svc(job_id, user_id):
            return {"artifact_ref": None}
        return _svc

    monkeypatch.setattr(routes_module, "get_status_service", fake_status_service)

    app = make_app()
    client = TestClient(app)

    resp = client.get("/download/job-1")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "ZIP not ready"


def test_download_404_when_artifact_missing(tmp_path, monkeypatch):
    def fake_status_service():
        def _svc(job_id, user_id):
            return {"artifact_ref": "/path/missing/file.zip"}
        return _svc

    class FakeStorage:
        def resolve_path(self, ref: str) -> str:
            return ref

    monkeypatch.setattr(routes_module, "get_status_service", fake_status_service)
    monkeypatch.setattr(routes_module, "get_storage", lambda: FakeStorage())

    app = make_app()
    client = TestClient(app)

    resp = client.get("/download/job-1")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Artifact missing"


def test_download_success(tmp_path, monkeypatch):
    zip_path = tmp_path / "out.zip"
    zip_bytes = b"ZIPDATA"
    zip_path.write_bytes(zip_bytes)

    def fake_status_service():
        def _svc(job_id, user_id):
            return {"artifact_ref": str(zip_path)}
        return _svc

    class FakeStorage:
        def resolve_path(self, ref: str) -> str:
            return ref

    monkeypatch.setattr(routes_module, "get_status_service", fake_status_service)
    monkeypatch.setattr(routes_module, "get_storage", lambda: FakeStorage())

    app = make_app(user_id="bob")
    client = TestClient(app)

    resp = client.get("/download/job-9")
    assert resp.status_code == 200
    cd = resp.headers.get("content-disposition", "")
    assert 'filename="out.zip"' in cd or "filename=out.zip" in cd
    assert resp.headers.get("content-type") == "application/zip"
    assert resp.content == zip_bytes
