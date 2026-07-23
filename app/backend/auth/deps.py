from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..models import Role
from .security import TokenPayload, decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    try:
        return decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_roles(*allowed_roles: Role):
    """RBAC per doc §23.5:
    RM              -> view / score / approve
    Product Owner   -> view / edit data / propose weights
    Control Reviewer-> view / review only
    Admin           -> everything, weight changes always audited
    """

    def dependency(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if user.role != Role.ADMIN and user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' is not permitted to perform this action.",
            )
        return user

    return dependency
