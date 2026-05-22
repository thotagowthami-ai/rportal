from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Service for JWT token generation and validation"""
    
    @staticmethod
    def create_access_token(user_id: str, tenant_id: str, email: str, role: str) -> str:
        """
        Create JWT access token.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            email: User email
            role: User role
            
        Returns:
            JWT token string
        """
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": user_id,
            "email": email,
            "tenant_id": tenant_id,
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload dict or None if invalid
        """
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
    
    @staticmethod
    def verify_token(token: str) -> bool:
        """
        Verify if token is valid.
        
        Args:
            token: JWT token string
            
        Returns:
            True if valid, False otherwise
        """
        payload = AuthService.decode_token(token)
        return bool(
            payload
            and payload.get("type") == "access"
            and payload.get("sub")
            and payload.get("tenant_id")
            and payload.get("role")
        )

    @staticmethod
    def create_password_reset_token(user_id: str, email: str) -> str:
        """
        Create a short-lived JWT for password reset.
        Valid for PASSWORD_RESET_EXPIRE_MINUTES (default 60).
        """
        import uuid
        from app.services.cache_service import cache_service

        reset_ttl = getattr(settings, "PASSWORD_RESET_EXPIRE_MINUTES", 60)
        expire = datetime.utcnow() + timedelta(minutes=reset_ttl)
        jti = str(uuid.uuid4())
        payload = {
            "sub": user_id,
            "email": email,
            "type": "password_reset",
            "jti": jti,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        # Persist the jti in Redis (TTL is in seconds)
        cache_service.set(f"pwd_reset_jti:{jti}", "unused", ttl=reset_ttl * 60)
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token

    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[dict]:
        """
        Verify a password reset token.
        Returns the payload if valid and of type password_reset.
        """
        from app.services.cache_service import cache_service

        payload = AuthService.decode_token(token)
        if payload and payload.get("type") == "password_reset":
            jti = payload.get("jti")
            if not jti:
                logger.warning("Password reset token missing 'jti'")
                return None
            
            # Check if the jti exists and is unused
            status = cache_service.get(f"pwd_reset_jti:{jti}")
            if status != "unused":
                logger.warning(f"Replay attack detected or token already used: jti={jti}")
                return None
                
            # Mark token as used to prevent replay attacks
            cache_service.set(f"pwd_reset_jti:{jti}", "used", ttl=60)
            
            return payload
        return None

# Global instance
auth_service = AuthService()
