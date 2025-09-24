from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, ExpiredSignatureError

from app import config, logger

security = HTTPBearer()

SECRET_KEY = config.get_value("jwt_tokens", "secret_key")
ALGORITHM = config.get_value("jwt_tokens", "algorithm")
ACCESS_TOKEN_EXPIRE_MINUTES = config.get_value("jwt_tokens", "access_token_expire_minutes")


def create_access_token(username: str) -> str:
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": username,
        "exp": expire,
        "iat": datetime.now(),
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token payload missing username")
            raise HTTPException(status_code=401, detail="Token missing username")
        return username
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_username(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return decode_access_token(credentials.credentials)
