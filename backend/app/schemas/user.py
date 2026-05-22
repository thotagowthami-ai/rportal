from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    tenant_name: str = Field(min_length=3, description="Organization name is required for signup")

# Properties to return to client (NEVER return the password!)
class UserResponse(UserBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True # Enables ORM compatibility

# Properties for Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Properties for Token Response
class Token(BaseModel):
    access_token: str
    token_type: str