from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.users import get_users_handler
from src.exceptions.users_exceptions.login_failed_exeption import LoginFailedException
from src.exceptions.users_exceptions.username_already_exists_exception import UsernameAlreadyExistsException
from src.handlers.users_handler import UsersHandler
from src.models.users.public_users.user_response import UserResponse
from src.models.users.public_users.user_signup_request import UserSignupRequest
from src.models.users.user_login import UserLogin

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    handler: UsersHandler = Depends(get_users_handler)
):
    users = await handler.get_all()
    return [UserResponse.from_model(u) for u in users]


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: UserSignupRequest,
    handler: UsersHandler = Depends(get_users_handler),
):
    try:
        user_model = signup_data.to_model()
        created_user = await handler.sign_up(user_model)
    except UsernameAlreadyExistsException as e:
        raise HTTPException(status_code=400, detail=str(e))

    return UserResponse.from_model(created_user)


@router.post("/login", response_model=UserResponse)
async def login(
    login_data: UserLogin,
    handler: UsersHandler = Depends(get_users_handler),
):
    try:
        user = await handler.login(login_data)
    except LoginFailedException:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return UserResponse.from_model(user)


@router.patch("/{user_id}/set-admin", response_model=UserResponse)
async def promote_user_to_admin(
    user_id: str,
    handler: UsersHandler = Depends(get_users_handler),
):
    updated = await handler.set_admin(user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Could not update user role")

    user = await handler.get_user_by_id(user_id)
    return UserResponse.from_model(user)

