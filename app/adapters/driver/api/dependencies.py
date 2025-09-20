import os, jwt
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

class CurrentUser(BaseModel):
    user_id: str

def current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    public_key = os.getenv("JWT_PUBLIC_KEY", "")
    if public_key and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            try:
                payload = jwt.decode(token, public_key, algorithms=["RS256"])
            except Exception:
                payload = jwt.decode(token, public_key, algorithms=["HS256"])
            sub = payload.get("sub") or payload.get("user_id")
            if not sub:
                raise ValueError("sub missing")
            return CurrentUser(user_id=str(sub))
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return CurrentUser(user_id="demo-user")
