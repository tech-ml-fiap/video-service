import os, httpx
from fastapi import status
from app.domain.ports.customer_auth_port import CustomerAuthPort
from app.domain.errors import AuthError

class CustomerAuthHttp(CustomerAuthPort):
    def __init__(self, base_url: str | None = None, client: httpx.Client | None = None):
        base = base_url or os.getenv("CUSTOMER_SERVICE_URL") or ""
        self.base_url = base.rstrip("/")
        self.client = client or httpx.Client(timeout=60)

    def verify_token(self, token: str) -> str:
        if not token:
            raise AuthError("Credenciais ausentes", status.HTTP_401_UNAUTHORIZED)

        resp = self.client.post(f"{self.base_url}/api/auth", json={"token": token})

        if resp.status_code == 200:
            return str(resp.json()["id"])

        if resp.status_code in (400, 401):
            raise AuthError("Token inválido", status.HTTP_401_UNAUTHORIZED)
        if resp.status_code == 403:
            raise AuthError("Cliente inativo", status.HTTP_403_FORBIDDEN)
        if resp.status_code == 404:
            raise AuthError("Cliente não encontrado", status.HTTP_404_NOT_FOUND)

        raise AuthError("Erro no serviço de clientes", status.HTTP_502_BAD_GATEWAY)
