from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole

# Request Schemas
class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

    full_name: str = Field(..., min_length=2, max_length=255)
    tenant_name: str = Field(..., min_length=2, max_length=255)
    tenant_slug: str = Field(..., min_length=2, max_length=100, pattern="^[a-z0-9-]+$")
    
    @validator('password')
    def validate_password(cls, v):
        """Ensure password has minimum complexity"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"

class UserResponse(BaseModel):
    """Schema for user in responses"""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    tenant_id: str
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None

class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=72)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Ensure password has minimum complexity"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

# Update forward reference
TokenResponse.model_rebuild()

class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=72)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Ensure password has minimum complexity"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

