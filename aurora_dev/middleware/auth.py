"""
Authentication and Authorization middleware for AURORA-DEV.

Provides JWT-based authentication with role-based access control.

Example usage:
    from aurora_dev.middleware.auth import AuthMiddleware, get_current_user
    
    app.add_middleware(AuthMiddleware, secret_key="your-secret")
    
    @app.get("/protected")
    async def protected_route(user: User = Depends(get_current_user)):
        return {"user": user.username}
"""
import hashlib
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class UserRole(Enum):
    """User roles for authorization."""
    
    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    VIEWER = "viewer"


# Role permissions
ROLE_PERMISSIONS = {
    UserRole.ADMIN: ["*"],  # All permissions
    UserRole.DEVELOPER: [
        "projects:read", "projects:write",
        "tasks:read", "tasks:write",
        "agents:read", "agents:control",
        "workflows:read", "workflows:execute",
    ],
    UserRole.OPERATOR: [
        "projects:read",
        "tasks:read",
        "agents:read", "agents:control",
        "workflows:read", "workflows:execute",
    ],
    UserRole.VIEWER: [
        "projects:read",
        "tasks:read",
        "agents:read",
        "workflows:read",
    ],
}


@dataclass
class User:
    """Authenticated user."""
    
    id: str
    username: str
    email: str
    role: UserRole
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        # Admin has all permissions
        if self.role == UserRole.ADMIN:
            return True
        
        # Check explicit permissions
        if permission in self.permissions:
            return True
        
        # Check role permissions
        role_perms = ROLE_PERMISSIONS.get(self.role, [])
        if "*" in role_perms or permission in role_perms:
            return True
        
        return False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "permissions": self.permissions,
        }


@dataclass
class TokenPayload:
    """JWT token payload."""
    
    sub: str  # Subject (user ID)
    username: str
    email: str
    role: str
    permissions: list[str]
    exp: float  # Expiration timestamp
    iat: float  # Issued at timestamp
    jti: str  # JWT ID (for revocation)


class JWTHandler:
    """
    Handles JWT token creation and verification.
    
    Uses HMAC-SHA256 for token signing.
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        """
        Initialize JWT handler.
        
        Args:
            secret_key: Secret key for signing tokens.
            algorithm: Signing algorithm.
            access_token_expire_minutes: Access token lifetime.
            refresh_token_expire_days: Refresh token lifetime.
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self._revoked_tokens: set[str] = set()
        self._logger = get_logger(__name__)
    
    def create_access_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create an access token for a user.
        
        Args:
            user: User to create token for.
            expires_delta: Custom expiration time.
            
        Returns:
            Encoded JWT token.
        """
        now = time.time()
        
        if expires_delta:
            expire = now + expires_delta.total_seconds()
        else:
            expire = now + (self.access_token_expire_minutes * 60)
        
        jti = secrets.token_hex(16)
        
        payload = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "permissions": user.permissions,
            "exp": expire,
            "iat": now,
            "jti": jti,
        }
        
        return self._encode_token(payload)
    
    def create_refresh_token(self, user: User) -> str:
        """Create a refresh token for a user."""
        expires = timedelta(days=self.refresh_token_expire_days)
        now = time.time()
        
        payload = {
            "sub": user.id,
            "type": "refresh",
            "exp": now + expires.total_seconds(),
            "iat": now,
            "jti": secrets.token_hex(16),
        }
        
        return self._encode_token(payload)
    
    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """
        Verify and decode a token.
        
        Args:
            token: JWT token to verify.
            
        Returns:
            Decoded payload or None if invalid.
        """
        try:
            payload = self._decode_token(token)
            
            if not payload:
                return None
            
            # Check expiration
            if payload.get("exp", 0) < time.time():
                self._logger.warning("Token expired")
                return None
            
            # Check revocation
            jti = payload.get("jti", "")
            if jti in self._revoked_tokens:
                self._logger.warning("Token has been revoked")
                return None
            
            return TokenPayload(
                sub=payload["sub"],
                username=payload.get("username", ""),
                email=payload.get("email", ""),
                role=payload.get("role", "viewer"),
                permissions=payload.get("permissions", []),
                exp=payload["exp"],
                iat=payload.get("iat", 0),
                jti=jti,
            )
            
        except Exception as e:
            self._logger.error(f"Token verification failed: {e}")
            return None
    
    def revoke_token(self, jti: str) -> None:
        """Revoke a token by its ID."""
        self._revoked_tokens.add(jti)
        self._logger.info(f"Token revoked: {jti[:8]}...")
    
    def _encode_token(self, payload: dict) -> str:
        """
        Encode payload as JWT.
        
        Simple implementation without external dependencies.
        For production, use python-jose or PyJWT.
        """
        import base64
        import hmac
        import json
        
        # Header
        header = {"alg": self.algorithm, "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).rstrip(b"=").decode()
        
        # Payload
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).rstrip(b"=").decode()
        
        # Signature
        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"
    
    def _decode_token(self, token: str) -> Optional[dict]:
        """Decode and verify JWT token."""
        import base64
        import hmac
        import json
        
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Verify signature
            message = f"{header_b64}.{payload_b64}"
            expected_sig = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256,
            ).digest()
            expected_sig_b64 = base64.urlsafe_b64encode(
                expected_sig
            ).rstrip(b"=").decode()
            
            if not hmac.compare_digest(signature_b64, expected_sig_b64):
                return None
            
            # Decode payload
            # Add padding if needed
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            return json.loads(payload_bytes)
            
        except Exception:
            return None


# Global JWT handler
_jwt_handler: Optional[JWTHandler] = None


def init_jwt_handler(secret_key: str, **kwargs) -> JWTHandler:
    """Initialize the global JWT handler."""
    global _jwt_handler
    _jwt_handler = JWTHandler(secret_key, **kwargs)
    return _jwt_handler


def get_jwt_handler() -> JWTHandler:
    """Get the global JWT handler."""
    if _jwt_handler is None:
        raise RuntimeError("JWT handler not initialized. Call init_jwt_handler first.")
    return _jwt_handler


# FastAPI security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    Usage:
        @app.get("/me")
        async def get_me(user: User = Depends(get_current_user)):
            return user.to_dict()
    """
    # Try to get from request state (if set by middleware)
    if hasattr(request.state, "user"):
        return request.state.user
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    handler = get_jwt_handler()
    payload = handler.verify_token(credentials.credentials)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return User(
        id=payload.sub,
        username=payload.username,
        email=payload.email,
        role=UserRole(payload.role),
        permissions=payload.permissions,
    )


def require_permission(permission: str):
    """
    Dependency to require a specific permission.
    
    Usage:
        @app.delete("/projects/{id}")
        async def delete_project(
            id: str,
            user: User = Depends(require_permission("projects:delete"))
        ):
            ...
    """
    async def check_permission(
        user: User = Depends(get_current_user),
    ) -> User:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}",
            )
        return user
    
    return check_permission


def require_role(role: UserRole):
    """
    Dependency to require a specific role.
    
    Usage:
        @app.post("/admin/settings")
        async def update_settings(
            user: User = Depends(require_role(UserRole.ADMIN))
        ):
            ...
    """
    async def check_role(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role != role and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.value}",
            )
        return user
    
    return check_role


class AuthMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for authentication.
    
    Validates JWT tokens and populates request.state.user.
    """
    
    # Paths that don't require authentication
    PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}
    
    def __init__(
        self,
        app,
        secret_key: str,
        public_paths: Optional[set[str]] = None,
    ):
        """
        Initialize auth middleware.
        
        Args:
            app: FastAPI application.
            secret_key: JWT secret key.
            public_paths: Additional public paths.
        """
        super().__init__(app)
        self.handler = init_jwt_handler(secret_key)
        self.public_paths = self.PUBLIC_PATHS | (public_paths or set())
        self._logger = get_logger(__name__)
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ):
        """Process request through authentication."""
        path = request.url.path
        
        # Skip public paths
        if path in self.public_paths or path.startswith("/api/v1/auth"):
            return await call_next(request)
        
        # Extract token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Missing authentication token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = auth_header[7:]  # Remove "Bearer "
        
        # Verify token
        payload = self.handler.verify_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create user and attach to request
        user = User(
            id=payload.sub,
            username=payload.username,
            email=payload.email,
            role=UserRole(payload.role),
            permissions=payload.permissions,
        )
        request.state.user = user
        
        # Continue with request
        response = await call_next(request)
        return response


# Password hashing utilities
class PasswordHasher:
    """Utility for secure password hashing."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256 with salt."""
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            100000,
        )
        return f"{salt}${hashed.hex()}"
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt, hash_hex = hashed.split("$")
            expected = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                salt.encode(),
                100000,
            )
            return hmac.compare_digest(expected.hex(), hash_hex)
        except Exception:
            return False


# API key authentication (alternative to JWT)
class APIKeyAuth:
    """Simple API key authentication."""
    
    def __init__(self):
        """Initialize API key auth."""
        self._keys: dict[str, User] = {}
        self._logger = get_logger(__name__)
    
    def create_key(self, user: User) -> str:
        """Create an API key for a user."""
        key = f"aurora_{secrets.token_hex(32)}"
        self._keys[key] = user
        return key
    
    def validate_key(self, key: str) -> Optional[User]:
        """Validate an API key and return associated user."""
        return self._keys.get(key)
    
    def revoke_key(self, key: str) -> bool:
        """Revoke an API key."""
        if key in self._keys:
            del self._keys[key]
            return True
        return False


# Import hmac for the password verification fix
import hmac
