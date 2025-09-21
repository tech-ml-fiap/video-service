from typing import Protocol, runtime_checkable

@runtime_checkable
class CustomerAuthPort(Protocol):
    def verify_token(self, token: str) -> str | int:
        """Deve retornar o user_id (string ou int). Lança exceção em caso de token inválido."""
        ...
