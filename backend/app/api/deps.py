from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.database import get_db, set_tenant_context
from app.config import settings
from app.models.user import User, UserRole
from uuid import UUID
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# This tells FastAPI that the token comes from the "Authorization: Bearer" header
# auto_error=False allows optional auth flows to return None instead of immediate 401.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate Token -> Get User -> Set Tenant Context
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        logger.warning("get_current_user: token is None")
        raise credentials_exception

    try:
        payload = _decode_token(token)
        logger.info(f"get_current_user: Decoded token payload: {payload}")

        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")

        if not user_id or not tenant_id:
            logger.warning(f"get_current_user: missing user_id ({user_id}) or tenant_id ({tenant_id}) in payload")
            raise credentials_exception

        try:
            user_id_uuid = UUID(user_id)
            tenant_id_uuid = UUID(tenant_id)
        except ValueError as e:
            logger.warning(f"get_current_user: invalid UUID structure for user_id ({user_id}) or tenant_id ({tenant_id}): {e}")
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"get_current_user: JWT decode failed: {e}")
        raise credentials_exception
    set_tenant_context(db, tenant_id_uuid)

    user = db.query(User).filter(
        User.id == str(user_id_uuid),
        User.tenant_id == str(tenant_id_uuid)
    ).first()

    if user is None:
        logger.warning(f"get_current_user: User not found in DB with id={user_id_uuid} and tenant_id={tenant_id_uuid}")
        raise credentials_exception

    if not user.is_active:
        logger.warning(f"get_current_user: User {user.email} is inactive")
        raise credentials_exception
    return user

         

def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User | None:
    """
    Optional authentication.
    - If token is missing: return None (fail-closed RLS will return zero rows)
    - If token is invalid: raise 401
    """
    if token is None:
        db.info.pop("tenant_id", None)
        return None

    try:
        payload = _decode_token(token)
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        if user_id is None or tenant_id is None:
            raise JWTError()
        try:
            user_id = str(UUID(user_id))
            tenant_id = str(UUID(tenant_id))
        except ValueError:
            raise JWTError()
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    set_tenant_context(db, tenant_id)
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id
    ).first()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require an active admin user.
    """
    if not current_user.is_active or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
