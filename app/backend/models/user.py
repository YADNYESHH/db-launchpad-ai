from pydantic import BaseModel

from .enums import Role


class User(BaseModel):
    user_id: str
    email: str
    name: str
    role: Role
    password_hash: str


class UserPublic(BaseModel):
    user_id: str
    email: str
    name: str
    role: Role
