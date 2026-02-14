import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.user import Role


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: Role = Role.teacher


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
