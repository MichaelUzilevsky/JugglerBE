from typing import Optional

from pydantic import BaseModel


class UserSignupRequest(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    team_id: Optional[int] = None


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserLoginRequest(BaseModel):
    username: str
    password: str
