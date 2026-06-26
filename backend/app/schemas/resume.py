from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class ResumeCreate(BaseModel):
    candidate_name: str = Field(..., min_length=1, max_length=255)
    candidate_email: Optional[EmailStr] = None
    candidate_phone: Optional[str] = Field(None, max_length=50)
    skills: Optional[List[str]] = []
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    education: Optional[str] = None
    current_role: Optional[str] = Field(None, max_length=255)


class ResumeUpdate(BaseModel):
    candidate_name: Optional[str] = Field(None, min_length=1, max_length=255)
    candidate_email: Optional[EmailStr] = None
    candidate_phone: Optional[str] = Field(None, max_length=50)
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    education: Optional[str] = None
    current_role: Optional[str] = Field(None, max_length=255)


class ResumeResponse(BaseModel):
    id: str
    candidate_name: str
    candidate_email: Optional[str]
    candidate_phone: Optional[str]
    file_name: str
    file_type: Optional[str]
    skills: List[str]
    experience_years: Optional[int]
    education: Optional[str]
    current_role: Optional[str]
    work_experience: Optional[List[dict]] = None
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ResumeList(BaseModel):
    items: List[ResumeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
