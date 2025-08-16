"""
AI Framework Authentication System
Secure user authentication and session management
"""

import hashlib
import secrets
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta

from .security_middleware import security_middleware, require_auth

logger = logging.getLogger(__name__)

# Router for authentication endpoints
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

# Basic HTTP authentication
security = HTTPBasic()

# User model
class User(BaseModel):
    username: str
    email: str
    roles: list[str] = []
    permissions: list[str] = []
    is_active: bool = True
    created_at: datetime = None
    last_login: datetime = None

# Login request model
class LoginRequest(BaseModel):
    username: str
    password: str

# Login response model
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

# Mock user database (in production, use real database)
USERS_DB = {
    "admin": {
        "username": "admin",
        "email": "admin@aiframework.com",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "roles": ["admin", "user"],
        "permissions": ["read", "write", "delete", "admin"],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    },
    "user": {
        "username": "user",
        "email": "user@aiframework.com",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "roles": ["user"],
        "permissions": ["read", "write"],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    },
    "demo": {
        "username": "demo",
        "email": "demo@aiframework.com",
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
        "roles": ["demo"],
        "permissions": ["read"],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
}

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username from database"""
    return USERS_DB.get(username)

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with username and password"""
    user = get_user_by_username(username)
    if not user:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    if not user["is_active"]:
        return None

    return user

@auth_router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return JWT token"""
    try:
        # Validate input
        if not security_middleware.validate_input(login_data.username, "username"):
            raise HTTPException(status_code=400, detail="Invalid username format")

        if not security_middleware.validate_input(login_data.password, "password"):
            raise HTTPException(status_code=400, detail="Invalid password format")

        # Authenticate user
        user = authenticate_user(login_data.username, login_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Update last login
        user["last_login"] = datetime.utcnow()

        # Generate JWT token
        token_data = {
            "user_id": user["username"],
            "username": user["username"],
            "roles": user["roles"],
            "permissions": user["permissions"]
        }

        access_token = security_middleware.generate_jwt_token(token_data, expires_in=3600)

        # Create response
        response_data = LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,
            user=User(
                username=user["username"],
                email=user["email"],
                roles=user["roles"],
                permissions=user["permissions"],
                is_active=user["is_active"],
                created_at=user["created_at"],
                last_login=user["last_login"]
            )
        )

        logger.info(f"User {login_data.username} logged in successfully")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@auth_router.post("/logout")
async def logout(request: Request, user: Dict[str, Any] = Depends(require_auth)):
    """Logout user (in production, this would invalidate the token)"""
    try:
        username = user.get("username", "unknown")
        logger.info(f"User {username} logged out")

        # In production, you would add the token to a blacklist
        # For now, we'll just return success
        return {"message": "Logout successful"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@auth_router.get("/me", response_model=User)
async def get_current_user(user: Dict[str, Any] = Depends(require_auth)):
    """Get current user information"""
    try:
        username = user.get("username")
        user_data = get_user_by_username(username)

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        return User(
            username=user_data["username"],
            email=user_data["email"],
            roles=user_data["roles"],
            permissions=user_data["permissions"],
            is_active=user_data["is_active"],
            created_at=user_data["created_at"],
            last_login=user_data["last_login"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user information")

@auth_router.post("/refresh")
async def refresh_token(request: Request, user: Dict[str, Any] = Depends(require_auth)):
    """Refresh JWT token"""
    try:
        # Generate new token
        token_data = {
            "user_id": user.get("user_id"),
            "username": user.get("username"),
            "roles": user.get("roles", []),
            "permissions": user.get("permissions", [])
        }

        new_token = security_middleware.generate_jwt_token(token_data, expires_in=3600)

        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": 3600
        }

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@auth_router.get("/users", response_model=list[User])
async def list_users(user: Dict[str, Any] = Depends(require_auth)):
    """List all users (admin only)"""
    try:
        # Check if user has admin role
        if "admin" not in user.get("roles", []):
            raise HTTPException(status_code=403, detail="Admin access required")

        users = []
        for username, user_data in USERS_DB.items():
            users.append(User(
                username=user_data["username"],
                email=user_data["email"],
                roles=user_data["roles"],
                permissions=user_data["permissions"],
                is_active=user_data["is_active"],
                created_at=user_data["created_at"],
                last_login=user_data["last_login"]
            ))

        return users

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")

# Health check endpoint (no authentication required)
@auth_router.get("/health")
async def auth_health():
    """Authentication service health check"""
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat(),
        "users_count": len(USERS_DB)
    }
