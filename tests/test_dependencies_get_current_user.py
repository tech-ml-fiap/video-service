from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

import app.adapters.driver.api.dependencies as deps_mod
from app.adapters.driver.api.dependencies import get_current_user
from app.domain.errors import AuthError


class FakeAuthOK:
    def __init__(self, uid="u-123"):
        self.uid = uid
    def verify_token(self, token: str) -> str:
        assert token == "good-token"
        return self.uid


class FakeAuthError:
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
    def verify_token(self, token: str) -> str:
        raise AuthError(self.message, self.status_code)


def make_app():
    app = FastAPI()

    @app.get("/me")
    def me(user = Depends(get_current_user)):
        return {"user_id": user.user_id}

    return app


def test_missing_credentials_returns_401():
    app = make_app()
    client = TestClient(app)

    resp = client.get("/me")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Credenciais ausentes"


def test_wrong_scheme_returns_401():
    app = make_app()
    client = TestClient(app)

    resp = client.get("/me", headers={"Authorization": "Basic abc"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Credenciais ausentes"


def test_valid_bearer_token_returns_current_user():
    app = make_app()
    app.dependency_overrides[deps_mod.get_auth_gateway] = lambda: FakeAuthOK(uid="user-42")

    client = TestClient(app)
    resp = client.get("/me", headers={"Authorization": "Bearer good-token"})
    assert resp.status_code == 200
    assert resp.json() == {"user_id": "user-42"}


def test_invalid_token_maps_to_401():
    app = make_app()
    app.dependency_overrides[deps_mod.get_auth_gateway] = lambda: FakeAuthError("Token inválido", 401)

    client = TestClient(app)
    resp = client.get("/me", headers={"Authorization": "Bearer any"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token inválido"


def test_inactive_user_maps_to_403():
    app = make_app()
    app.dependency_overrides[deps_mod.get_auth_gateway] = lambda: FakeAuthError("Cliente inativo", 403)

    client = TestClient(app)
    resp = client.get("/me", headers={"Authorization": "Bearer any"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Cliente inativo"
