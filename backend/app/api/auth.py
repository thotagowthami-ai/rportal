from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user
import logging

logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/signup", response_model=Token)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new Organization (Tenant) and its first Admin User.
    """
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists",
        )

    new_tenant = Tenant(name=user_in.tenant_name)
    db.add(new_tenant)
    db.flush()

    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        tenant_id=new_tenant.id,
        is_superuser=True,
    )
    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        logger.exception("Failed to create account")
        raise HTTPException(status_code=500, detail="Unable to create account") from None

    access_token = create_access_token(
        subject=str(new_user.id),
        additional_claims={"tenant_id": str(new_user.tenant_id)},
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return Access Token.
    """
    user = db.query(User).filter(User.email == user_in.email).first()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=str(user.id),
        additional_claims={"tenant_id": str(user.tenant_id)},
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    return current_user
