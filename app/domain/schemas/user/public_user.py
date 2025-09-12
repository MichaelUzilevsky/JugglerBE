from pydantic import BaseModel
from typing import Optional

class UserSignupRequest(BaseModel):
    username: str
    email: str
    full_name: str
    password: str

class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
