import base64
from datetime import datetime
import hashlib
import logging
import uuid

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text

from app.config import settings
from app.database import Base

logger = logging.getLogger(__name__)

_LEGACY_PREFIX = "plain:"

# Lazy cipher — resolved on first access so the key is read after settings are
# fully initialised and we can emit a warning if falling back to JWT_SECRET_KEY.
_cipher_instance: Fernet | None = None


def _get_cipher() -> Fernet:
    global _cipher_instance
    if _cipher_instance is None:
        raw_key = getattr(settings, "LINKEDIN_ENCRYPTION_KEY", None)
        if raw_key:
            key_bytes = base64.urlsafe_b64encode(hashlib.sha256(raw_key.encode()).digest())
        else:
            logger.warning(
                "LINKEDIN_ENCRYPTION_KEY is not set; falling back to JWT_SECRET_KEY "
                "for LinkedIn token encryption. Set a dedicated LINKEDIN_ENCRYPTION_KEY "
                "in your environment for proper key separation."
            )
            key_bytes = base64.urlsafe_b64encode(
                hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest()
            )
        _cipher_instance = Fernet(key_bytes)
    return _cipher_instance


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

    @property
    def access_token(self) -> str:
        """Transparently decrypt the access token upon retrieval."""
        if not self._access_token:
            return ""
        # Legacy plaintext tokens are stored with an explicit prefix
        if self._access_token.startswith(_LEGACY_PREFIX):
            return self._access_token[len(_LEGACY_PREFIX):]
        try:
            return _get_cipher().decrypt(self._access_token.encode()).decode()
        except InvalidToken:
            logger.error(
                "LinkedIn access_token decryption failed for user_id=%s — "
                "token may have been encrypted with a different key.",
                self.user_id,
            )
            raise ValueError("LinkedIn access token could not be decrypted")

    @access_token.setter
    def access_token(self, value: str) -> None:
        """Transparently encrypt the access token before committing to database."""
        if value:
            self._access_token = _get_cipher().encrypt(value.encode()).decode()
        else:
            self._access_token = ""

    __table_args__ = (
        Index("idx_linkedin_accounts_tenant_user", "tenant_id", "user_id"),
    )
