import pytest
from app.domain.errors import AuthError


def test_auth_error_defaults_and_attributes():
    err = AuthError("Credenciais ausentes")
    assert err.message == "Credenciais ausentes"
    assert err.status_code == 401
    assert err.args == ("Credenciais ausentes",)
    assert str(err) == "Credenciais ausentes"


def test_auth_error_custom_status_code():
    err = AuthError("Cliente inativo", status_code=403)
    assert err.message == "Cliente inativo"
    assert err.status_code == 403
    assert err.args == ("Cliente inativo",)
    assert str(err) == "Cliente inativo"


def test_auth_error_raise_and_catch():
    with pytest.raises(AuthError) as exc:
        raise AuthError("Token inválido", 401)
    e = exc.value
    assert isinstance(e, AuthError)
    assert e.message == "Token inválido"
    assert e.status_code == 401
    assert e.args == ("Token inválido",)
