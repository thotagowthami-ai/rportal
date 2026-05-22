from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MatchCreate(BaseModel):
    """Schema for creating a match (internal use)"""
    job_description_id: str
    resume_id: str
    overall_score: float = Field(..., ge=0, le=100)
    skill_match_score: Optional[float] = Field(None, ge=0, le=100)
    experience_match_score: Optional[float] = Field(None, ge=0, le=100)
    education_match_score: Optional[float] = Field(None, ge=0, le=100)
    matched_skills: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    match_reasoning: Optional[str] = None


class MatchGenerateSelectedRequest(BaseModel):
    """Schema for generating matches for selected resumes"""
    job_id: str
    resume_ids: List[str] = Field(..., min_items=1)
    limit: int = Field(50, ge=1, le=100)


class MatchUpdate(BaseModel):
    """Schema for updating match status"""
    recruiter_status: Optional[str] = Field(None, pattern="(?i)^(new|reviewed|shortlisted|rejected|interviewed|offered)$")
    recruiter_notes: Optional[str] = None

class MatchResponse(BaseModel):
    """Schema for match in responses"""
    id: str
    job_description_id: str
    resume_id: str
    overall_score: float
    skill_match_score: Optional[float]
    experience_match_score: Optional[float]
    education_match_score: Optional[float]
    matched_skills: Optional[List[str]]
    missing_skills: Optional[List[str]]
    match_reasoning: Optional[str]
    recruiter_status: str
    recruiter_notes: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MatchList(BaseModel):
    """Schema for paginated match list"""
    items: List[MatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
