from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
import uuid
from datetime import datetime
import enum

# Password hashing context.
# Tuned Argon2 parameters reduce CPU/memory pressure on small deployed instances
# while keeping a strong adaptive hash.
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__type="ID",
    argon2__time_cost=2,
    argon2__memory_cost=19456,
    argon2__parallelism=1,
)


class UserRole(str, enum.Enum):
    """User role for role-based access control"""
    ADMIN = "admin"
    RECRUITER = "recruiter"
    VIEWER = "viewer"


class User(Base):
    """
    User model with authentication and role-based access control.
    Each user belongs to one tenant (organization).
    """
    __tablename__ = "users"

    # ─── IDs (SQLite-safe UUIDs) ─────────────────────────────
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )

    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ─── Authentication ─────────────────────────────────────
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # ─── Profile ────────────────────────────────────────────
    full_name = Column(String(255), nullable=False)

    # ─── Role-based access control ──────────────────────────
    role = Column(
        String(20),
        nullable=False,
        default=UserRole.VIEWER.value
    )

    # ─── Status ─────────────────────────────────────────────
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # ─── Timestamps ─────────────────────────────────────────
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    last_login = Column(DateTime, nullable=True)

    # ─── Relationships ──────────────────────────────────────
    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self):
        return f"<User {self.email}>"

    # ─── Password helpers ───────────────────────────────────
    def verify_password(self, plain_password: str) -> bool:
        if not self.hashed_password:
            return False
        if len(plain_password.encode("utf-8")) > 72:
            return False
        try:
            return pwd_context.verify(plain_password, self.hashed_password)
        except UnknownHashError:
            return False

    @staticmethod
    def hash_password(password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 bytes")
        return pwd_context.hash(password)

    # ─── Authorization helpers ──────────────────────────────
    def has_permission(self, required_role: UserRole) -> bool:
        role_hierarchy = {
            UserRole.VIEWER.value: 1,
            UserRole.RECRUITER.value: 2,
            UserRole.ADMIN.value: 3,
        }
        current_role_val = self.role.value if hasattr(self.role, "value") else str(self.role)
        if current_role_val not in role_hierarchy:
            import logging
            logging.getLogger(__name__).warning("Unrecognized user role: %s", current_role_val)
            return False

        current = role_hierarchy[current_role_val]
        required = role_hierarchy.get(required_role.value, 0)
        return current >= required

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value
