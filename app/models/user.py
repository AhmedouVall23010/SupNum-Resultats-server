from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId


class User:
    def __init__(
        self,
        email: str,
        password: str,
        role: str = "student",
        email_verified: bool = False,
        verification_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
        token_used: bool = False,
        reset_password_token: Optional[str] = None,
        reset_password_expires_at: Optional[datetime] = None,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None
    ):
        self._id = _id
        self.email = email
        self.password = password
        self.role = role
        self.email_verified = email_verified
        self.verification_token = verification_token
        self.token_expires_at = token_expires_at
        self.token_used = token_used
        self.reset_password_token = reset_password_token
        self.reset_password_expires_at = reset_password_expires_at
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self):
        """Convert user to dictionary for MongoDB"""
        user_dict = {
            "email": self.email,
            "password": self.password,
            "role": self.role,
            "email_verified": self.email_verified,
            "verification_token": self.verification_token,
            "token_expires_at": self.token_expires_at,
            "token_used": self.token_used,
            "reset_password_token": self.reset_password_token,
            "reset_password_expires_at": self.reset_password_expires_at,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        if self._id:
            user_dict["_id"] = self._id
        return user_dict
    
    @classmethod
    def from_dict(cls, user_dict: dict):
        """Create user from dictionary"""
        user_dict.pop("_id", None)
        return cls(**user_dict)

