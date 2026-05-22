from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    users = relationship("User", back_populates="tenant")
    resumes = relationship("Resume", back_populates="tenant")
    job_descriptions = relationship("JobDescription", back_populates="tenant")
    matches = relationship("Match", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant {self.name}>"