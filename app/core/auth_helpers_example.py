"""
Examples of using authentication helper functions

This file shows how to use the authentication helper functions
in your routes and services.
"""

from fastapi import APIRouter, Depends
from app.core.dependencies import (
    require_auth, require_role, require_any_role, require_name_in,
    get_current_user_id, get_current_user_name, get_current_user_role,
    get_token
)
from app.core.security import (
    is_auth, has_role, has_any_role, is_name_in,
    get_user_id_from_token, get_name_from_token, get_role_from_token
)

router = APIRouter()

# ============================================
# Example 1: Using dependencies in routes
# ============================================

@router.get("/protected")
async def protected_route(payload: dict = Depends(require_auth)):
    """Route that requires authentication"""
    user_id = payload.get("sub")
    name = payload.get("name")
    role = payload.get("role")
    return {
        "message": "You are authenticated",
        "user_id": user_id,
        "name": name,
        "role": role
    }


@router.get("/admin-only")
async def admin_route(payload: dict = Depends(require_role("admin"))):
    """Route that requires admin role"""
    return {"message": "Admin access granted", "user": payload.get("name")}


@router.get("/teacher-or-admin")
async def teacher_or_admin_route(
    payload: dict = Depends(require_any_role(["teacher", "admin"]))
):
    """Route that requires teacher or admin role"""
    return {"message": "Access granted", "user": payload.get("name")}


@router.get("/specific-users")
async def specific_users_route(
    payload: dict = Depends(require_name_in(["ahmedou", "admin"]))
):
    """Route that only allows specific users by name"""
    return {"message": "Access granted", "user": payload.get("name")}


# ============================================
# Example 2: Using helper functions directly
# ============================================

@router.get("/check-auth")
async def check_auth(token: str = Depends(get_token)):
    """Check if token is valid using helper function"""
    if is_auth(token):
        return {"authenticated": True}
    return {"authenticated": False}


@router.get("/check-role")
async def check_role(token: str = Depends(get_token)):
    """Check user role using helper function"""
    if has_role(token, "admin"):
        return {"is_admin": True}
    return {"is_admin": False}


@router.get("/check-name")
async def check_name(token: str = Depends(get_token)):
    """Check if user name is in list"""
    allowed_names = ["ahmedou", "admin", "teacher"]
    if is_name_in(token, allowed_names):
        name = get_name_from_token(token)
        return {"allowed": True, "name": name}
    return {"allowed": False}


# ============================================
# Example 3: Using in service functions
# ============================================

def some_service_function(token: str):
    """Example service function using helper functions"""
    # Check if authenticated
    if not is_auth(token):
        raise ValueError("Not authenticated")
    
    # Get user info
    user_id = get_user_id_from_token(token)
    name = get_name_from_token(token)
    role = get_role_from_token(token)
    
    # Check permissions
    if not has_role(token, "admin"):
        raise ValueError("Admin access required")
    
    # Check if name is allowed
    if not is_name_in(token, ["ahmedou", "admin"]):
        raise ValueError("Access denied")
    
    return {
        "user_id": user_id,
        "name": name,
        "role": role
    }


# ============================================
# Example 4: Conditional logic
# ============================================

@router.get("/conditional-access")
async def conditional_access(token: str = Depends(get_token)):
    """Example of conditional access based on role"""
    if not is_auth(token):
        return {"error": "Not authenticated"}
    
    if has_role(token, "admin"):
        return {"access_level": "full", "message": "Admin access"}
    elif has_any_role(token, ["teacher", "student"]):
        return {"access_level": "limited", "message": "Standard access"}
    else:
        return {"access_level": "none", "message": "No access"}

