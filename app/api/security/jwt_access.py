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
                "jwt_access_decode_wrong_type",
                extra={"payload": payload, "description": "Expected 'access' token type"}
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        username = payload.get("sub")
        if not username:
            logger.warning(
                "jwt_access_missing_sub",
                extra={"payload": payload, "description": "Missing 'sub' field in access token"}
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing username")

        return username

    except ExpiredSignatureError:
        logger.warning("jwt_access_expired", extra={"description": "Access token expired"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token expired")
    except JWTError as e:
        logger.warning("jwt_access_invalid", extra={"error": str(e), "description": "Invalid access token"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")


async def get_current_username(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency that extracts and validates the Authorization: Bearer token.
    """
    return decode_access_token(credentials.credentials)
