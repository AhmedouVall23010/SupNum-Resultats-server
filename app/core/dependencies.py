from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import (
    is_auth, has_role, has_any_role, is_name_in,
    get_user_id_from_token, get_name_from_token, get_role_from_token
)
from typing import Optional, List

security = HTTPBearer()


def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract token from Authorization header"""
    return credentials.credentials


def require_auth(token: str = Depends(get_token)) -> dict:
    """
    Dependency to require valid authentication.
    Returns token payload if valid, raises 401 if not.
    """
    from app.core.security import get_token_payload
    
    payload = get_token_payload(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.
    Usage: @router.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    def role_checker(token: str = Depends(get_token)) -> dict:
        payload = require_auth(token)
        user_role = payload.get("role", "")
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}, but user has role: {user_role}"
            )
        return payload
    return role_checker


def require_any_role(required_roles: List[str]):
    """
    Dependency factory to require any of the specified roles.
    Usage: @router.get("/endpoint", dependencies=[Depends(require_any_role(["admin", "teacher"]))])
    """
    def role_checker(token: str = Depends(get_token)) -> dict:
        payload = require_auth(token)
        user_role = payload.get("role", "")
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required one of roles: {required_roles}, but user has role: {user_role}"
            )
        return payload
    return role_checker


def require_name_in(allowed_names: List[str]):
    """
    Dependency factory to require user's name to be in the allowed list.
    Usage: @router.get("/endpoint", dependencies=[Depends(require_name_in(["ahmedou", "admin"]))])
    """
    def name_checker(token: str = Depends(get_token)) -> dict:
        payload = require_auth(token)
        user_name = payload.get("name", "")
        if user_name not in allowed_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for user: {user_name}"
            )
        return payload
    return name_checker


def get_current_user_id(token: str = Depends(get_token)) -> str:
    """Get current user ID from token"""
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


def get_current_user_name(token: str = Depends(get_token)) -> str:
    """Get current user name from token"""
    name = get_name_from_token(token)
    if not name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return name


def get_current_user_role(token: str = Depends(get_token)) -> str:
    """Get current user role from token"""
    role = get_role_from_token(token)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return role

