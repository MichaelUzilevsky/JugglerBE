from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, ExpiredSignatureError
from starlette import status

from app import config, logger

security = HTTPBearer()

SECRET_KEY = config.get_value("jwt_tokens", "secret_key")
ALGORITHM = config.get_value("jwt_tokens", "algorithm")


def decode_access_token(token: str) -> str:
    """
    Decode and validate an access token. Returns the username.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            logger.warning(
                "Expected 'access' token type, got different type",
                extra={"event": "jwt_access_wrong_type"}
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        username = payload.get("sub")
        if not username:
            logger.warning(
                "Access token missing 'sub' (username) field",
                extra={"event": "jwt_access_missing_sub"}
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing username")

        return username

    except ExpiredSignatureError:
        logger.warning("Access token expired", extra={"event": "jwt_access_expired"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token expired")
    except JWTError as e:
        logger.warning("Invalid access token", extra={"event": "jwt_access_invalid", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")


async def get_current_username(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency that extracts and validates the Authorization: Bearer token.
    """
    return decode_access_token(credentials.credentials)
