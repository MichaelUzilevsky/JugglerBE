from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import JSONResponse

from app.api.auth.jwt_auth import create_access_token
from app.api.dependencies.auth import require_admin, get_current_user
from app.api.dependencies.services.users import get_user_service
from app.domain.schemas.user.enums.user_role import UserRole
from app.domain.schemas.user.public_user import UserSignupRequest, UserUpdateRequest
from app.domain.schemas.user.user import UserCreate, UserRead, UserUpdate
from app.domain.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(signup_data: UserSignupRequest, user_service: UserService = Depends(get_user_service)):
    user_create = UserCreate(**signup_data.model_dump())
    return await user_service.signup(user_create)


@router.post("/login")
async def login(username: str, password: str, user_service: UserService = Depends(get_user_service)):
    user = await user_service.login(username, password)
    token = create_access_token(user.username)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"access_token": token, "token_type": "bearer"}
    )


@router.get("/", response_model=List[UserRead])
async def list_users(user_service: UserService = Depends(get_user_service), _: UserRead = Depends(require_admin)):
    return await user_service.list_users()


@router.patch("/{user_id}/update", response_model=UserRead)
async def update_user(
        user_id: int,
        user_update_data: UserUpdateRequest,
        user_service: UserService = Depends(get_user_service),
        current_user: UserRead = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot update other users' data.")
    user_update = UserUpdate(**user_update_data.model_dump())
    if user_update.role is not None and user_id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot update your own role")
    return await user_service.update_user(user_id, user_update)


@router.patch("/{user_id}/promote", response_model=UserRead)
async def promote_user(user_id: int, user_service: UserService = Depends(get_user_service),
                       _: UserRead = Depends(require_admin)):
    return await user_service.promote_to_admin(user_id)


@router.patch("/{user_id}/demote", response_model=UserRead)
async def demote_user(user_id: int, user_service: UserService = Depends(get_user_service),
                      _: UserRead = Depends(require_admin)):
    return await user_service.demote_to_user(user_id)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, user_service: UserService = Depends(get_user_service),
                      _: UserRead = Depends(require_admin)):
    await user_service.delete_user(user_id)
    return JSONResponse(status_code=200, content={"detail": "User deleted"})
