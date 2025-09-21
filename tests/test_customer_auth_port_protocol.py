from app.domain.ports.customer_auth_port import CustomerAuthPort


class ImplReturnsStr:
    def verify_token(self, token: str) -> str:
        return f"user:{token}"


class ImplReturnsInt:
    def verify_token(self, token: str) -> int:
        return 42


class MissingMethod:
    pass


class VerifyTokenNotCallable:
    verify_token = "não sou função"


def test_structural_isinstance_and_issubclass_accepts_valid_implementations():
    ok_str = ImplReturnsStr()
    ok_int = ImplReturnsInt()

    assert isinstance(ok_str, CustomerAuthPort)
    assert isinstance(ok_int, CustomerAuthPort)

    assert issubclass(ImplReturnsStr, CustomerAuthPort)
    assert issubclass(ImplReturnsInt, CustomerAuthPort)

    assert ok_str.verify_token("abc") == "user:abc"
    assert ok_int.verify_token("abc") == 42


def test_isinstance_fails_when_method_missing_or_not_callable():
    assert not isinstance(MissingMethod(), CustomerAuthPort)
    assert not issubclass(MissingMethod, CustomerAuthPort)

    assert isinstance(VerifyTokenNotCallable(), CustomerAuthPort)
    assert issubclass(VerifyTokenNotCallable, CustomerAuthPort)
