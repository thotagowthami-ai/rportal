from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from jose import jwt
from passlib.context import CryptContext
from app.config import settings

# Setup password hashing context (using bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain text password matches the stored hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Generate a secure hash from a plain text password.
    """
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Any],
    expires_delta: timedelta = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a JWT token that expires after a set time.
    
    Args:
        subject: The primary data to encode (usually User ID or Email)
        expires_delta: Optional custom expiration time
        additional_claims: Optional extra claims to include in the token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Initialize with additional claims and ensure reserved claims take precedence
    to_encode = dict(additional_claims or {})
    to_encode.update({"exp": expire, "sub": str(subject)})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt
