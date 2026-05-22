from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
import enum


class MatchStatus(str, enum.Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    INTERVIEWED = "interviewed"
    OFFERED = "offered"


class Match(Base):
    __tablename__ = "matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description_id = Column(String(36), ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)

    overall_score = Column(Float, nullable=False, index=True)
    skill_match_score = Column(Float, nullable=True)
    experience_match_score = Column(Float, nullable=True)
    education_match_score = Column(Float, nullable=True)

    matched_skills = Column(
        JSON().with_variant(postgresql.ARRAY(String()), "postgresql"),
        nullable=True,
    )
    missing_skills = Column(
        JSON().with_variant(postgresql.ARRAY(String()), "postgresql"),
        nullable=True,
    )
    match_reasoning = Column(Text, nullable=True)

    recruiter_status = Column(String(20), nullable=False, default=MatchStatus.NEW.value, index=True)
    recruiter_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="matches")
    job_description = relationship("JobDescription", back_populates="matches")
    resume = relationship("Resume", back_populates="matches")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        Index("idx_match_unique", "job_description_id", "resume_id", unique=True),
        Index("idx_match_job_score_desc", "job_description_id", "overall_score"),
        Index("idx_match_job_status", "job_description_id", "recruiter_status"),
        Index("idx_match_tenant_status", "tenant_id", "recruiter_status"),
    )
