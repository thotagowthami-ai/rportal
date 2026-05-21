from pydantic import BaseModel, Field, validator, field_validator, model_validator
from typing import Optional, List
from datetime import datetime


class JobDescriptionCreate(BaseModel):
    """Schema for creating a job description"""
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=50)
    requirements: str = Field(default="")
    responsibilities: Optional[str] = None
    required_skills: List[str] = Field(..., min_items=1, max_items=50)
    preferred_skills: Optional[List[str]] = Field(default_factory=list, max_items=50)
    location: Optional[str] = Field(None, max_length=255)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    experience_required: Optional[int] = Field(None, ge=0, le=50)
    education_required: Optional[str] = None
    employment_type: Optional[str] = Field(None, pattern="^(full-time|part-time|contract|internship)$")
    status: Optional[str] = Field("draft", pattern="^(draft|active|paused|closed)$")
    
    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        """Ensure max salary is greater than min salary"""
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('salary_max must be greater than salary_min')
        return v
    
    @validator('required_skills')
    def validate_required_skills(cls, v):
        """Clean and validate skills list"""
        # Remove duplicates and empty strings
        cleaned = list(set(s.strip() for s in v if s.strip()))
        if not cleaned:
            raise ValueError('At least one skill is required')
        return cleaned

    @validator('requirements')
    def validate_requirements(cls, v):
        if v is None:
            return ""
        if v.strip() and len(v.strip()) < 50:
            raise ValueError('requirements must be at least 50 characters when provided')
        return v


class JobDescriptionFromTextCreate(BaseModel):
    """Schema for creating a job from plain text"""
    raw_text: str = Field(..., min_length=50)
    status: Optional[str] = Field("active", pattern="^(draft|active|paused|closed)$")


class JobDescriptionUpdate(BaseModel):
    """Schema for updating a job description"""
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=50)
    requirements: Optional[str] = Field(None)
    responsibilities: Optional[str] = None
    required_skills: Optional[List[str]] = Field(None, min_items=1, max_items=50)
    preferred_skills: Optional[List[str]] = Field(None, max_items=50)
    location: Optional[str] = Field(None, max_length=255)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    experience_required: Optional[int] = Field(None, ge=0, le=50)
    education_required: Optional[str] = None
    employment_type: Optional[str] = Field(None, pattern="^(full-time|part-time|contract|internship)$")
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|closed)$")

    @field_validator("requirements", mode="before")
    @classmethod
    def validate_requirements(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            stripped = v.strip()
            if stripped and len(stripped) < 50:
                raise ValueError("requirements must be at least 50 characters when provided")
            return stripped
        return v

    @field_validator("required_skills", mode="before")
    @classmethod
    def validate_required_skills(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            cleaned = list(set(s.strip() for s in v if isinstance(s, str) and s.strip()))
            if not cleaned:
                raise ValueError("required_skills must have at least 1 item after normalization")
            if len(cleaned) > 50:
                raise ValueError("required_skills cannot have more than 50 items")
            return cleaned
        return v

    @field_validator("preferred_skills", mode="before")
    @classmethod
    def validate_preferred_skills(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            cleaned = list(set(s.strip() for s in v if isinstance(s, str) and s.strip()))
            if len(cleaned) > 50:
                raise ValueError("preferred_skills cannot have more than 50 items")
            return cleaned
        return v

    @model_validator(mode="after")
    def validate_salary_range(self) -> 'JobDescriptionUpdate':
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_max < self.salary_min:
                raise ValueError("salary_max must be greater than or equal to salary_min")
        return self


class JobDescriptionResponse(BaseModel):
    """Schema for job description in responses"""
    id: str
    title: str
    description: str
    requirements: str
    responsibilities: Optional[str]
    required_skills: List[str]
    preferred_skills: Optional[List[str]]
    location: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    experience_required: Optional[int]
    education_required: Optional[str]
    employment_type: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    candidate_count: int = 0
    
    class Config:
        from_attributes = True


class JobDescriptionList(BaseModel):
    """Schema for paginated job description list"""
    items: List[JobDescriptionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
