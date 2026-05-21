import base64
from datetime import datetime
import hashlib
import uuid

from cryptography.fernet import Fernet
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.ext.hybrid import hybrid_property

from app.config import settings
from app.database import Base

# Generate a secure, deterministic 32-byte Fernet key from the application's secret key
_key = base64.urlsafe_b64encode(hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest())
_cipher = Fernet(_key)


class LinkedInAccount(Base):
    __tablename__ = "linkedin_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    linkedin_sub = Column(String(255), nullable=False, index=True)
    person_urn = Column(String(255), nullable=False)
    
    # Store the encrypted ciphertext directly in the database text column
    _access_token = Column("access_token", Text, nullable=False)
    
    scope = Column(String(500), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @hybrid_property
    def access_token(self) -> str:
        """Transparently decrypt the access token upon retrieval."""
        if not self._access_token:
            return ""
        try:
            return _cipher.decrypt(self._access_token.encode()).decode()
        except Exception:
            # Fallback for plain-text legacy tokens to ensure seamless migration compatibility
            return self._access_token

    @access_token.setter
    def access_token(self, value: str) -> None:
        """Transparently encrypt the access token before committing to database."""
        if value:
            self._access_token = _cipher.encrypt(value.encode()).decode()
        else:
            self._access_token = ""

    __table_args__ = (
        Index("idx_linkedin_accounts_tenant_user", "tenant_id", "user_id"),
    )

