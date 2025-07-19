from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from src import config

security = HTTPBearer()


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now() + (expires_delta or
                               timedelta(minutes=config.get_value("jwt_tokens", "access_token_expire_minutes")))
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode,
                      config.get_value("jwt_tokens", "secret_key"),
                      algorithm=config.get_value("jwt_tokens", "algorithm"))


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token,
                             config.get_value("jwt_tokens", "secret_key"),
                             algorithms=[config.get_value("jwt_tokens", "algorithm")])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token payload missing user_id")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return decode_access_token(credentials.credentials)
