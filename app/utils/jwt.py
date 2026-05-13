from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException

from app import config, logger

SECRET_KEY = config.get_value("jwt_tokens", "secret_key")
ALGORITHM = config.get_value("jwt_tokens", "algorithm")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.get_value("jwt_tokens", "access_token_expire_minutes"))
REFRESH_TOKEN_EXPIRE_DAYS = int(config.get_value("jwt_tokens", "refresh_token_expire_days"))

def _now():
    return datetime.now(timezone.utc)

def create_access_token(username: str) -> str:
    expire = _now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": username,
        "exp": expire,
        "iat": _now(),
        "type": "access",
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token missing username")
        return username
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def create_refresh_token_jwt(username: str, raw_jti: str) -> str:
    expire = _now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": username,
        "jti": raw_jti,   # raw jti (we store hash in DB)
        "exp": expire,
        "iat": _now(),
        "type": "refresh",
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_refresh_token_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
