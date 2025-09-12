from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import JSONResponse

from app.api.auth.jwt_auth import create_access_token
from app.api.dependencies.auth import require_admin, get_current_user
from app.domain.schemas.user.public_user import UserSignupRequest, UserUpdateRequest
from app.domain.services.user_service import UserService
from app.api.dependencies.services.users import get_user_service
from app.domain.schemas.user.user import UserCreate, UserRead, UserUpdate
from app.exceptions.users_exceptions.email_already_exists_exception import EmailAlreadyExistsException
from app.exceptions.users_exceptions.login_failed_exception import LoginFailedException
from app.exceptions.users_exceptions.user_not_found_exception import UserNotFoundException
from app.exceptions.users_exceptions.username_already_exists_exception import UsernameAlreadyExistsException

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: UserSignupRequest,
    user_service: UserService = Depends(get_user_service),
):
    user_create = UserCreate(**signup_data.model_dump())
    try:
        return await user_service.signup(user_create)
    except UsernameAlreadyExistsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EmailAlreadyExistsException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(
    username: str,
    password: str,
    user_service: UserService = Depends(get_user_service),
):
    try:
        user = await user_service.login(username, password)
    except LoginFailedException as e:
        raise HTTPException(status_code=401, detail=str(e))

    token = create_access_token(user.username)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token": token,
            "token_type": "bearer"
        },
    )


@router.get("/", response_model=List[UserRead])
async def list_users(
    user_service: UserService = Depends(get_user_service),
    _: UserRead = Depends(require_admin),
):
    return await user_service.list_users()


@router.patch("/{user_id}/update", response_model=UserRead)
async def update_user(
    user_id: int,
    user_update_data: UserUpdateRequest,
    user_service: UserService = Depends(get_user_service),
    current_user: UserRead = Depends(get_current_user),
):
    # Prevent users from updating their own role
    user_update = UserUpdate(**user_update_data.model_dump())
    if user_update.role is not None and user_id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot update your own role")
    try:
        return await user_service.update_user(user_id, user_update)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UsernameAlreadyExistsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EmailAlreadyExistsException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{user_id}/promote", response_model=UserRead)
async def promote_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    _: UserRead = Depends(require_admin),
):
    try:
        return await user_service.promote_to_admin(user_id)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{user_id}/demote", response_model=UserRead)
async def demote_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    _: UserRead = Depends(require_admin),
):
    try:
        return await user_service.demote_to_user(user_id)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    _: UserRead = Depends(require_admin),
):
    try:
        await user_service.delete_user(user_id)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    return JSONResponse(status_code=200, content={"detail": "User deleted"})
