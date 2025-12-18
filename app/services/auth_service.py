from fastapi import HTTPException, status
from app.db.mongo import users_collection, refresh_tokens_collection
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.core.security import (
    verify_password, get_password_hash, create_access_token, decode_access_token,
    generate_verification_token, get_token_expiration, extract_name_from_email,
    generate_refresh_token, get_refresh_token_expiration, get_reset_password_token_expiration
)
from app.services.email_service import EmailService
from bson import ObjectId
from datetime import datetime


class AuthService:
    @staticmethod
    def register_user(user_data: UserCreate) -> dict:
        """Register a new user or update existing unverified user and send verification email"""
        # Check if user already exists
        existing_user = users_collection.find_one({"email": user_data.email})
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Generate verification token
        verification_token = generate_verification_token()
        token_expires_at = get_token_expiration()
        
        if existing_user:
            # Check if user is already verified
            if existing_user.get("email_verified", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered and verified. Please login instead."
                )
            
            # Update existing unverified user
            users_collection.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "password": hashed_password,
                        "verification_token": verification_token,
                        "token_expires_at": token_expires_at,
                        "token_used": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            message = "Registration updated. A new verification email has been sent. Please check your email to verify your account."
        else:
            # Create new user
            user = User(
                email=user_data.email,
                password=hashed_password,
                role="student",
                email_verified=False,
                verification_token=verification_token,
                token_expires_at=token_expires_at,
                token_used=False
            )
            
            # Insert into database
            users_collection.insert_one(user.to_dict())
            
            message = "Registration successful. Please check your email to verify your account."
        
        # Send verification email
        EmailService.send_verification_email(user_data.email, verification_token)
        
        return {
            "message": message,
            "email": user_data.email
        }
    
    @staticmethod
    def verify_email(verification_token: str) -> dict:
        """Verify user email using verification token (valid for 24 hours, single use)"""
        # Find user by verification token
        user = users_collection.find_one({"verification_token": verification_token})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        # Check if token already used
        if user.get("token_used", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This verification token has already been used. Please request a new one."
            )
        
        # Check if token expired
        token_expires_at = user.get("token_expires_at")
        if token_expires_at and datetime.utcnow() > token_expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired. Please register again to get a new token."
            )
        
        # Check if already verified
        if user.get("email_verified", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Update user to verified and mark token as used
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "email_verified": True,
                    "verification_token": None,
                    "token_expires_at": None,
                    "token_used": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Email verified successfully. You can now login."}
    
    @staticmethod
    def authenticate_user(login_data: UserLogin) -> dict:
        """Authenticate user and return JWT token"""
        # Find user by email
        user = users_collection.find_one({"email": login_data.email})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if email is verified
        if not user.get("email_verified", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in. Check your inbox for the verification link."
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Extract name from email
        name = extract_name_from_email(user["email"])
        role = user.get("role", "student")
        user_id = str(user["_id"])
        
        # Create access token with name and role
        access_token = create_access_token(user_id=user_id, name=name, role=role)
        
        # Generate and save refresh token
        refresh_token = generate_refresh_token()
        refresh_token_expires_at = get_refresh_token_expiration()
        
        # Save refresh token to database
        refresh_tokens_collection.insert_one({
            "user_id": ObjectId(user_id),
            "token": refresh_token,
            "expires_at": refresh_token_expires_at,
            "revoked": False,
            "created_at": datetime.utcnow(),
            "last_used_at": None
        })
        
        # Return tokens and user info
        user_response = AuthService._user_to_response(user)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_response
        }
    
    @staticmethod
    def get_current_user(token: str) -> UserResponse:
        """Get current authenticated user - reads name and role from token"""
        # Decode token
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user ID, name, and role from token
        user_id: str = payload.get("sub")
        name: str = payload.get("name", "")
        role: str = payload.get("role", "student")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Find user by ID to verify account is still active
        try:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Return user response with data from token (name and role are from token)
        return AuthService._user_to_response(user)
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> dict:
        """Refresh access token using refresh token"""
        # Find refresh token in database
        token_doc = refresh_tokens_collection.find_one({"token": refresh_token})
        
        if not token_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if token is revoked
        if token_doc.get("revoked", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )
        
        # Check if token is expired
        expires_at = token_doc.get("expires_at")
        if expires_at and datetime.utcnow() > expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please login again."
            )
        
        # Get user
        user_id = token_doc.get("user_id")
        user = users_collection.find_one({"_id": user_id})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Extract name from email and get role
        name = extract_name_from_email(user["email"])
        role = user.get("role", "student")
        
        # Create new access token
        access_token = create_access_token(user_id=str(user_id), name=name, role=role)
        
        # Update last_used_at
        refresh_tokens_collection.update_one(
            {"_id": token_doc["_id"]},
            {"$set": {"last_used_at": datetime.utcnow()}}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def revoke_refresh_token(refresh_token: str) -> dict:
        """Revoke a refresh token (logout)"""
        # Find and revoke refresh token
        result = refresh_tokens_collection.update_one(
            {"token": refresh_token},
            {"$set": {"revoked": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refresh token not found"
            )
        
        return {"message": "Token revoked successfully"}
    
    @staticmethod
    def revoke_all_user_tokens(user_id: str) -> dict:
        """Revoke all refresh tokens for a user"""
        result = refresh_tokens_collection.update_many(
            {"user_id": ObjectId(user_id), "revoked": False},
            {"$set": {"revoked": True}}
        )
        
        return {"message": f"Revoked {result.modified_count} tokens"}
    
    @staticmethod
    def forgot_password(email: str) -> dict:
        """
        Request password reset. Always returns success message for security reasons,
        even if account doesn't exist or is disabled.
        """
        # Find user by email
        user = users_collection.find_one({"email": email})
        
        # Security: Always return success message, even if user doesn't exist
        # This prevents email enumeration attacks
        success_message = "Si un compte existe avec cet email et qu'il est activé, un lien de réinitialisation a été envoyé."
        
        # Only send email if user exists, is active, and email is verified
        if user and user.get("is_active", True) and user.get("email_verified", False):
            # Generate reset token
            reset_token = generate_verification_token()
            reset_token_expires_at = get_reset_password_token_expiration()
            
            # Update user with reset token
            users_collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "reset_password_token": reset_token,
                        "reset_password_expires_at": reset_token_expires_at,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Send reset password email
            EmailService.send_reset_password_email(email, reset_token)
        
        return {"message": success_message}
    
    @staticmethod
    def reset_password(reset_token: str, new_password: str) -> dict:
        """Reset password using reset token"""
        # Find user by reset token
        user = users_collection.find_one({"reset_password_token": reset_token})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Check if token expired
        token_expires_at = user.get("reset_password_expires_at")
        if token_expires_at and datetime.utcnow() > token_expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired. Please request a new one."
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Hash new password
        hashed_password = get_password_hash(new_password)
        
        # Update password and clear reset token
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password": hashed_password,
                    "reset_password_token": None,
                    "reset_password_expires_at": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Revoke all refresh tokens for security
        from app.db.mongo import refresh_tokens_collection
        refresh_tokens_collection.update_many(
            {"user_id": user["_id"], "revoked": False},
            {"$set": {"revoked": True}}
        )
        
        return {"message": "Password reset successfully. Please login with your new password."}
    
    @staticmethod
    def _user_to_response(user_dict: dict) -> UserResponse:
        """Convert user dictionary to UserResponse"""
        return UserResponse(
            id=str(user_dict["_id"]),
            email=user_dict["email"],
            role=user_dict.get("role", "student"),
            email_verified=user_dict.get("email_verified", False),
            is_active=user_dict.get("is_active", True),
            created_at=user_dict.get("created_at", datetime.utcnow()),
            updated_at=user_dict.get("updated_at", datetime.utcnow())
        )

