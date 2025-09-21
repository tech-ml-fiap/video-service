from app.adapters.driven.gateway.customer_auth_http import CustomerAuthHttp
from app.domain.errors import AuthError

import pytest
import httpx
from fastapi import status


class DummyResp:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class DummyClient:
    def __init__(self):
        self.calls = []
        self.closed = False

    def post(self, url, json=None, **kwargs):
        self.calls.append({"url": url, "json": json, "kwargs": kwargs})
        return DummyResp(200, {"id": "42"})

    def close(self):
        self.closed = True


def _extract_status(exc: BaseException):
    for attr in ("status_code", "status", "http_status", "code"):
        if hasattr(exc, attr):
            return getattr(exc, attr)
    return exc.args[1] if len(getattr(exc, "args", ())) > 1 else None


def _extract_message(exc: BaseException):
    if len(getattr(exc, "args", ())) >= 1:
        return exc.args[0]
    return str(exc)


def test_verify_token_requires_token():
    client = DummyClient()
    auth = CustomerAuthHttp(base_url="http://svc", client=client)
    with pytest.raises(AuthError) as exc:
        auth.verify_token("")
    assert _extract_message(exc.value) == "Credenciais ausentes"
    assert _extract_status(exc.value) == status.HTTP_401_UNAUTHORIZED
    assert client.calls == []


def test_verify_token_success_200_returns_id_string():
    class Client200(DummyClient):
        def post(self, url, json=None, **kwargs):
            self.calls.append({"url": url, "json": json})
            return DummyResp(200, {"id": 123})

    client = Client200()
    auth = CustomerAuthHttp(base_url="https://api.example.com/", client=client)
    user_id = auth.verify_token("tok")
    assert user_id == "123"
    assert len(client.calls) == 1
    assert client.calls[0]["url"] == "https://api.example.com/api/auth"
    assert client.calls[0]["json"] == {"token": "tok"}


@pytest.mark.parametrize(
    "code,expected_msg,expected_status",
    [
        (400, "Token inválido", status.HTTP_401_UNAUTHORIZED),
        (401, "Token inválido", status.HTTP_401_UNAUTHORIZED),
        (403, "Cliente inativo", status.HTTP_403_FORBIDDEN),
        (404, "Cliente não encontrado", status.HTTP_404_NOT_FOUND),
        (500, "Erro no serviço de clientes", status.HTTP_502_BAD_GATEWAY),
        (503, "Erro no serviço de clientes", status.HTTP_502_BAD_GATEWAY),
    ],
)
def test_verify_token_error_paths(code, expected_msg, expected_status):
    class ClientErr(DummyClient):
        def post(self, url, json=None, **kwargs):
            self.calls.append({"url": url, "json": json})
            return DummyResp(code, {})

    client = ClientErr()
    auth = CustomerAuthHttp(base_url="http://svc", client=client)

    with pytest.raises(AuthError) as exc:
        auth.verify_token("t")
    assert _extract_message(exc.value) == expected_msg
    assert _extract_status(exc.value) == expected_status
    assert client.calls[0]["url"] == "http://svc/api/auth"
    assert client.calls[0]["json"] == {"token": "t"}


def test_base_url_from_env_and_rstrip(monkeypatch):
    monkeypatch.setenv("CUSTOMER_SERVICE_URL", "https://svc.example.com///")

    class ClientSpy(DummyClient):
        def post(self, url, json=None, **kwargs):
            self.calls.append({"url": url, "json": json})
            return DummyResp(200, {"id": "u-1"})

    client = ClientSpy()
    auth = CustomerAuthHttp(base_url=None, client=client)
    uid = auth.verify_token("abc")
    assert uid == "u-1"
    assert client.calls[0]["url"] == "https://svc.example.com/api/auth"


def test_uses_provided_client_instance():
    sentinel = DummyClient()
    auth = CustomerAuthHttp(base_url="http://x", client=sentinel)
    assert auth.client is sentinel


def test_default_httpx_client_is_created_with_timeout_60(monkeypatch):
    created = {}

    class ClientFactory:
        def __call__(self, *args, **kwargs):
            created["kwargs"] = kwargs
            return DummyClient()

    factory = ClientFactory()
    monkeypatch.setattr(httpx, "Client", factory)
    auth = CustomerAuthHttp(base_url="http://svc", client=None)
    assert created["kwargs"]["timeout"] == 60
    assert isinstance(auth.client, DummyClient)
