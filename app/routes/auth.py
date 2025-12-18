from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    RefreshTokenResponse, ForgotPasswordRequest, ResetPasswordRequest
)
from app.services.auth_service import AuthService
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user - only email (@supnum.mr) and password required"""
    return AuthService.register_user(user_data)


@router.get("/verify-email")
async def verify_email(token: str = Query(..., description="Verification token from email")):
    """Verify user email using token from verification email"""
    return AuthService.verify_email(token)


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, response: Response):
    """
    Login and get JWT access token (in response body) and refresh token (in HttpOnly Secure cookie).
    Access token should be stored in memory (RAM) only, not in localStorage or cookie.
    Only works if email is verified.
    """
    result = AuthService.authenticate_user(login_data)
    
    # Set refresh token in HttpOnly Secure cookie
    refresh_token = result.pop("refresh_token")  # Remove from response body
    max_age = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # Convert days to seconds
    
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        httponly=settings.REFRESH_TOKEN_COOKIE_HTTP_ONLY,
        secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
        samesite=settings.REFRESH_TOKEN_COOKIE_SAME_SITE,
        path="/"
    )
    
    return result


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: Request):
    """
    Refresh access token using refresh token from HttpOnly Secure cookie.
    Works even if access token is expired.
    Frontend should call this automatically when access token expires (401 error).
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookie"
        )
    
    return AuthService.refresh_access_token(refresh_token)


@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Logout and revoke refresh token.
    Deletes the refresh token cookie and revokes it in database.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    
    if refresh_token:
        # Revoke token in database
        AuthService.revoke_refresh_token(refresh_token)
    
    # Delete cookie
    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        path="/",
        samesite=settings.REFRESH_TOKEN_COOKIE_SAME_SITE
    )
    
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request password reset. Always returns success message for security reasons.
    Only sends email if account exists, is active, and email is verified.
    """
    return AuthService.forgot_password(request.email)


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using token from email.
    Requires token and new password.
    """
    return AuthService.reset_password(request.token, request.new_password)


@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user - reads name and role from access token"""
    token = credentials.credentials
    return AuthService.get_current_user(token)

