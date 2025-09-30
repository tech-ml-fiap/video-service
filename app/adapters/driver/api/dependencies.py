from fastapi import Depends, Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.domain.errors import AuthError
from app.domain.ports.customer_auth_port import CustomerAuthPort
from app.config.container import get_auth_gateway

security = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    user_id: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
    auth: CustomerAuthPort = Depends(get_auth_gateway),
) -> CurrentUser:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais ausentes"
        )

    try:
        uid = auth.verify_token(credentials.credentials)
        return CurrentUser(user_id=str(uid))
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
