from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
import enum
import json


class JobStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    responsibilities = Column(Text)

    required_skills = Column(Text, default="[]")
    preferred_skills = Column(Text, default="[]")

    location = Column(String(255))
    salary_range = Column(String(100))
    experience_required = Column(Integer)
    education_required = Column(String(255))
    employment_type = Column(String(50))

    status = Column(String(50), default=JobStatus.DRAFT.value, nullable=False)

    embedding = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    deleted_at = Column(DateTime)

    tenant = relationship("Tenant", back_populates="job_descriptions")
    creator = relationship("User")
    matches = relationship("Match", back_populates="job_description")

    __table_args__ = (
        Index("idx_job_desc_tenant", "tenant_id"),
        Index("idx_job_desc_status", "status"),
    )

    def to_text_for_embedding(self) -> str:
        if isinstance(self.required_skills, list):
            skills = self.required_skills
        else:
            try:
                skills = json.loads(self.required_skills or "[]")
            except Exception:
                skills = []
        return f"{self.title}\n{self.description}\nSkills: {', '.join(skills)}"
