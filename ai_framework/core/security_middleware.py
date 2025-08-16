"""
AI Framework Security Middleware
Comprehensive security implementation for authentication, authorization, and input validation
"""

import re
import hashlib
import hmac
import time
import logging
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import jwt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Comprehensive security middleware for AI Framework"""

    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        self.secret_key = secret_key or "your-super-secure-jwt-secret-key-change-this-in-production"
        self.algorithm = algorithm
        self.security_scheme = HTTPBearer(auto_error=False)

        # Rate limiting configuration
        self.rate_limit_requests = 100  # requests per minute
        self.rate_limit_window = 60     # seconds
        self.request_counts = {}  # IP -> (count, reset_time)

        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
            r"(\b(or|and)\s+\d+\s*=\s*\d+)",
            r"(\b(union|select|insert|update|delete|drop|create|alter)\s+.*\b)",
            r"(--|#|/\*|\*/)",
            r"(\bxp_|sp_|exec\b)",
            r"(\bwaitfor\b)",
            r"(\bdelay\b)",
            r"(\bchar\s*\(\s*\d+\s*\))",
            r"(\bcast\s*\(\s*.*\s+as\s+.*\s*\))",
            r"(\bconvert\s*\(\s*.*\s*,\s*.*\s*\))"
        ]

        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<form[^>]*>",
            r"<input[^>]*>",
            r"<textarea[^>]*>",
            r"<select[^>]*>"
        ]

        # Compile patterns for efficiency
        self.sql_injection_regex = re.compile("|".join(self.sql_injection_patterns), re.IGNORECASE)
        self.xss_regex = re.compile("|".join(self.xss_patterns), re.IGNORECASE)

    async def authenticate_request(self, request: Request) -> Dict[str, Any]:
        """Authenticate incoming request using JWT token"""
        try:
            # Get authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(status_code=401, detail="Authorization header required")

            # Extract token
            if not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Bearer token required")

            token = auth_header[7:]  # Remove "Bearer " prefix

            # Verify token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token expiration
            if "exp" in payload:
                if datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
                    raise HTTPException(status_code=401, detail="Token expired")

            # Add user info to request state
            request.state.user = payload
            return payload

        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")

    def check_authorization(self, user: Dict[str, Any], required_roles: List[str] = None,
                           required_permissions: List[str] = None) -> bool:
        """Check if user has required roles and permissions"""
        try:
            # Check roles
            if required_roles:
                user_roles = user.get("roles", [])
                if not any(role in user_roles for role in required_roles):
                    return False

            # Check permissions
            if required_permissions:
                user_permissions = user.get("permissions", [])
                if not any(perm in user_permissions for perm in required_permissions):
                    return False

            return True

        except Exception as e:
            logger.error(f"Authorization check error: {e}")
            return False

    def validate_input(self, data: Any, input_type: str = "general") -> bool:
        """Validate input data for security threats"""
        try:
            if isinstance(data, str):
                # Check for SQL injection
                if self.sql_injection_regex.search(data):
                    logger.warning(f"SQL injection attempt detected in {input_type}: {data[:100]}")
                    return False

                # Check for XSS
                if self.xss_regex.search(data):
                    logger.warning(f"XSS attempt detected in {input_type}: {data[:100]}")
                    return False

                # Check for command injection
                if any(cmd in data.lower() for cmd in [";", "&&", "||", "`", "$(", "|"]):
                    logger.warning(f"Command injection attempt detected in {input_type}: {data[:100]}")
                    return False

            elif isinstance(data, dict):
                # Recursively validate dictionary values
                for key, value in data.items():
                    if not self.validate_input(value, f"{input_type}.{key}"):
                        return False

            elif isinstance(data, list):
                # Recursively validate list items
                for i, item in enumerate(data):
                    if not self.validate_input(item, f"{input_type}[{i}]"):
                        return False

            return True

        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return False

    async def check_rate_limit_middleware(self, request: Request, call_next):
        """Rate limiting middleware function"""
        try:
            # Get client IP
            client_ip = request.client.host if request.client else "unknown"
            current_time = time.time()

            # Initialize or get existing rate limit data
            if client_ip not in self.request_counts:
                self.request_counts[client_ip] = (0, current_time + self.rate_limit_window)

            count, reset_time = self.request_counts[client_ip]

            # Reset counter if window expired
            if current_time > reset_time:
                count = 0
                reset_time = current_time + self.rate_limit_window

            # Check if limit exceeded
            if count >= self.rate_limit_requests:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."}
                )

            # Increment counter
            self.request_counts[client_ip] = (count + 1, reset_time)

            # Continue with the request
            response = await call_next(request)
            return response

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request if rate limiting fails
            response = await call_next(request)
            return response

    async def add_security_headers_middleware(self, request: Request, call_next):
        """Security headers middleware function"""
        try:
            # Process the request
            response = await call_next(request)

            # Add security headers to the response
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

            return response

        except Exception as e:
            logger.error(f"Error adding security headers: {e}")
            # Continue with the request if headers fail
            response = await call_next(request)
            return response

    def sanitize_input(self, data: str) -> str:
        """Sanitize input data to prevent injection attacks"""
        try:
            if not isinstance(data, str):
                return data

            # Remove or escape dangerous characters
            sanitized = data

            # Escape HTML entities
            html_entities = {
                "<": "&lt;",
                ">": "&gt;",
                "&": "&amp;",
                '"': "&quot;",
                "'": "&#x27;"
            }

            for char, entity in html_entities.items():
                sanitized = sanitized.replace(char, entity)

            # Remove null bytes
            sanitized = sanitized.replace("\x00", "")

            # Remove control characters
            sanitized = "".join(char for char in sanitized if ord(char) >= 32)

            return sanitized

        except Exception as e:
            logger.error(f"Input sanitization error: {e}")
            return data

    def generate_jwt_token(self, user_data: Dict[str, Any], expires_in: int = 3600) -> str:
        """Generate JWT token for authenticated user"""
        try:
            payload = {
                "user_id": user_data.get("user_id"),
                "username": user_data.get("username"),
                "roles": user_data.get("roles", []),
                "permissions": user_data.get("permissions", []),
                "exp": datetime.utcnow() + timedelta(seconds=expires_in),
                "iat": datetime.utcnow()
            }

            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token

        except Exception as e:
            logger.error(f"Token generation error: {e}")
            raise HTTPException(status_code=500, detail="Token generation failed")

    def verify_api_key(self, api_key: str = Header(None)) -> bool:
        """Verify API key for machine-to-machine authentication"""
        try:
            if not api_key:
                return False

            # In production, this should check against a database or secure storage
            # For now, we'll use a simple hash comparison
            expected_key = "your-production-api-key-change-this"
            expected_hash = hashlib.sha256(expected_key.encode()).hexdigest()

            provided_hash = hashlib.sha256(api_key.encode()).hexdigest()

            return hmac.compare_digest(expected_hash, provided_hash)

        except Exception as e:
            logger.error(f"API key verification error: {e}")
            return False

# Global security middleware instance
security_middleware = SecurityMiddleware()

# Dependency functions for FastAPI
async def require_auth(request: Request) -> Dict[str, Any]:
    """Dependency to require authentication"""
    return await security_middleware.authenticate_request(request)

async def require_role(roles: List[str]):
    """Dependency to require specific roles"""
    async def role_checker(request: Request):
        user = await require_auth(request)
        if not security_middleware.check_authorization(user, required_roles=roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

async def require_permission(permissions: List[str]):
    """Dependency to require specific permissions"""
    async def permission_checker(request: Request):
        user = await require_auth(request)
        if not security_middleware.check_authorization(user, required_permissions=permissions):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return permission_checker

def require_api_key():
    """Dependency to require valid API key"""
    async def api_key_checker(api_key: str = Header(None)):
        if not security_middleware.verify_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
        return True
    return api_key_checker
