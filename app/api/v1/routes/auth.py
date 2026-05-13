import os
from typing import Optional

from fastapi import APIRouter, Depends, Response, HTTPException, Cookie
from starlette import status
from starlette.responses import JSONResponse

from app import config, logger
from app.api.dependencies.auth import logged_in_only
from app.api.dependencies.services.jwt import get_jwt_service
from app.api.dependencies.services.users import get_user_service
from app.domain.schemas.user.public_user import UserLoginRequest
from app.domain.schemas.user.user import UserRead
from app.domain.services.user_service import UserService

router = APIRouter(prefix="/security", tags=["Auth"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_EXP_DAYS = int(config.get_value("jwt_tokens", "refresh_token_expire_days"))
COOKIE_SECURE = os.getenv("APP_ENV", "dev") == "prod"


@router.post("/login")
async def login(
        login_user: UserLoginRequest,
        user_service: UserService = Depends(get_user_service),
        jwt_service=Depends(get_jwt_service)
):
    user = await user_service.login(login_user.username, login_user.password)
    access_jwt, refresh_jwt, _ = await jwt_service.create_and_store_refresh_token(user_id=user.id,
                                                                                  username=user.username)

    # set cookie
    max_age = REFRESH_EXP_DAYS * 24 * 60 * 60

    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"access_token": access_jwt, "token_type": "bearer"},
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_jwt,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=max_age,
    )
    return response


@router.post("/refresh")
async def refresh(
        response: Response,
        refresh_token: Optional[str] = Cookie(None),
        jwt_service=Depends(get_jwt_service)
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        new_access, new_refresh = await jwt_service.rotate_refresh_token(refresh_token)
    except Exception as e:
        logger.warning("refresh_failed", extra={"error": str(e)})
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # set new cookie (rotation)
    max_age = REFRESH_EXP_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=new_refresh,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=max_age,
    )

    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/logout")
async def logout(
        response: Response,
        refresh_token: Optional[str] = Cookie(None),
        jwt_service=Depends(get_jwt_service),
        _: UserRead = Depends(logged_in_only)
):
    # Always delete cookie on client
    response.delete_cookie(REFRESH_COOKIE_NAME)
    if not refresh_token:
        return {"message": "logged out"}
    await jwt_service.revoke_refresh_token(refresh_token)
    return {"message": "logged out"}


@router.get("/me", response_model=UserRead)
async def me(user: UserRead = Depends(logged_in_only)):
    return user
