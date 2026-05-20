from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Index, String, Text

from app.database import Base


class LinkedInAccount(Base):
    __tablename__ = "linkedin_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, unique=True, index=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    linkedin_sub = Column(String(255), nullable=False, index=True)
    person_urn = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=False)
    scope = Column(String(500), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_linkedin_accounts_tenant_user", "tenant_id", "user_id"),
    )
