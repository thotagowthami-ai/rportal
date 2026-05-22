from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
import json


class Resume(Base):
    __tablename__ = "resumes"

    # ─── IDs (UUID as string) ───────────────────────────────
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id"),
        nullable=False
    )

    uploaded_by = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )

    # ─── Candidate Information ─────────────────────────────
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255))
    candidate_phone = Column(String(50))

    # ─── Resume Content ────────────────────────────────────
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50))
    resume_text = Column(Text)

    # ─── Parsed Data (SQLite-safe) ─────────────────────────
    skills = Column(Text, default="[]")  # JSON string
    experience_years = Column(Integer)
    education = Column(Text)
    current_role = Column(String(255))
    work_experience = Column(Text, default="[]")  # JSON string

    # ─── Embedding (DISABLED IN SQLITE) ────────────────────
    embedding = Column(Text, nullable=True)  # placeholder

    # ─── Timestamps ───────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    deleted_at = Column(DateTime)

    # ─── Relationships ────────────────────────────────────
    tenant = relationship("Tenant", back_populates="resumes")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    matches = relationship("Match", back_populates="resume")

    __table_args__ = (
        Index("idx_resumes_tenant", "tenant_id"),
        Index("idx_resumes_uploaded_by", "uploaded_by"),
        Index("idx_resumes_candidate_email", "candidate_email"),
    )