import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..models import Role, User

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Demo-only default; in the deployed Cloud Run service this MUST be overridden
# via the JWT_SECRET_KEY env var (Secret Manager), not left at the default.
_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "launchpad-ai-demo-secret-change-me")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _pwd_context.verify(plain_password, password_hash)


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user.user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "exp": expire,
    }
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


class TokenPayload:
    def __init__(self, user_id: str, email: str, name: str, role: Role):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.role = role


def decode_access_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
    return TokenPayload(
        user_id=payload["sub"], email=payload["email"], name=payload["name"], role=Role(payload["role"])
    )
