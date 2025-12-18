import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    # Convert string to bytes if needed
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Convert password to bytes
    if isinstance(password, str):
        password = password.encode('utf-8')
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    # Return as string
    return hashed.decode('utf-8')


def create_access_token(user_id: str, name: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with user_id, name, and role"""
    to_encode = {
        "sub": user_id,
        "name": name,
        "role": role
    }
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def extract_name_from_email(email: str) -> str:
    """Extract name from email (part before @supnum.mr)"""
    if "@supnum.mr" in email:
        return email.split("@supnum.mr")[0]
    return email.split("@")[0] if "@" in email else email


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_verification_token() -> str:
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)


def get_token_expiration() -> datetime:
    """Get token expiration time (24 hours from now)"""
    return datetime.utcnow() + timedelta(hours=24)


def generate_refresh_token() -> str:
    """Generate a secure random refresh token"""
    return secrets.token_urlsafe(32)


def get_refresh_token_expiration() -> datetime:
    """Get refresh token expiration time (7 days from now)"""
    return datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)


def get_reset_password_token_expiration() -> datetime:
    """Get reset password token expiration time (1 hour from now)"""
    return datetime.utcnow() + timedelta(hours=1)


def is_auth(token: str) -> bool:
    """Check if token is valid and not expired"""
    payload = decode_access_token(token)
    return payload is not None


def get_token_payload(token: str) -> Optional[dict]:
    """Get token payload if valid, None otherwise"""
    return decode_access_token(token)


def is_name_in(token: str, names: list[str]) -> bool:
    """Check if user's name (from token) is in the provided list"""
    payload = get_token_payload(token)
    if not payload:
        return False
    name = payload.get("name", "")
    return name in names


def has_role(token: str, role: str) -> bool:
    """Check if user has the specified role"""
    payload = get_token_payload(token)
    if not payload:
        return False
    user_role = payload.get("role", "")
    return user_role == role


def has_any_role(token: str, roles: list[str]) -> bool:
    """Check if user has any of the specified roles"""
    payload = get_token_payload(token)
    if not payload:
        return False
    user_role = payload.get("role", "")
    return user_role in roles


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from token"""
    payload = get_token_payload(token)
    if not payload:
        return None
    return payload.get("sub")


def get_name_from_token(token: str) -> Optional[str]:
    """Extract name from token"""
    payload = get_token_payload(token)
    if not payload:
        return None
    return payload.get("name")


def get_role_from_token(token: str) -> Optional[str]:
    """Extract role from token"""
    payload = get_token_payload(token)
    if not payload:
        return None
    return payload.get("role")
