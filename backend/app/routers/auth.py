from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse, ForgotPasswordRequest, PasswordResetConfirm
from app.services.auth_service import auth_service
from app.services.email_service import email_service
from app.config import settings
from app.api.deps import get_current_user
from datetime import datetime
import logging

import httpx
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Google OAuth configuration (read from settings to ensure .env is loaded)
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
BACKEND_URL = settings.BACKEND_URL or "http://localhost:8000"
FRONTEND_URL = settings.FRONTEND_URL or "http://localhost:3000"

# Note: router is mounted with prefix "/api", so callback is under /api/auth/...
# We prioritize the /api prefix for internal consistency
GOOGLE_REDIRECT_URI = f"{BACKEND_URL}/api/auth/google/callback"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user and create their organization (tenant).

    This creates:
    1. A new tenant (organization)
    2. A new user as admin of that tenant
    3. Returns JWT token for immediate login
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if tenant slug already exists
    existing_tenant = db.query(Tenant).filter(Tenant.slug == user_data.tenant_slug).first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already taken"
        )

    try:
        # Create tenant
        tenant = Tenant(
            name=user_data.tenant_name,
            slug=user_data.tenant_slug,
            is_active=True
        )
        db.add(tenant)
        db.flush()  # Get tenant.id without committing

        # Create user as admin
        user = User(
            email=user_data.email,
            hashed_password=User.hash_password(user_data.password),
            full_name=user_data.full_name,
            tenant_id=tenant.id,
            role="admin",  # First user is always admin
            is_active=True,
            is_verified=True  # Auto-verify first user
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"New user registered: {user.email} (Tenant: {tenant.name})")

        # Generate token
        token = auth_service.create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            role=(user.role.value if hasattr(user.role, "value") else str(user.role))
        )

        full_name = user.full_name or ""
        is_active = True if user.is_active is None else bool(user.is_active)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                full_name=full_name,
                role=(user.role.value if hasattr(user.role, "value") else str(user.role)),
                is_active=is_active,
                is_verified=user.is_verified,
                tenant_id=str(user.tenant_id),
                created_at=user.created_at,
                last_login=user.last_login
            )
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password.

    Returns JWT token on success.
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not user.verify_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    logger.info(f"User logged in: {user.email}")

    # Generate token
    token = auth_service.create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        role=(user.role.value if hasattr(user.role, "value") else str(user.role))
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name or "",
            role=(user.role.value if hasattr(user.role, "value") else str(user.role)),
            is_active=user.is_active,
            is_verified=user.is_verified,
            tenant_id=str(user.tenant_id),
            created_at=user.created_at,
            last_login=user.last_login
        )
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user."""
    full_name = current_user.full_name or ""
    is_active = True if current_user.is_active is None else bool(current_user.is_active)
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=full_name,
        role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        is_active=is_active,
        is_verified=current_user.is_verified,
        tenant_id=str(current_user.tenant_id),
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.get("/google")
async def google_login(source: str = "ats"):
    """
    Start Google OAuth flow:
    Redirects the user to Google's consent screen.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth missing client ID or secret")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured",
        )

    google_url = (
        f"{GOOGLE_AUTH_URL}"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={source}"
    )
    return RedirectResponse(google_url)


@router.get("/google/callback")
async def google_callback(code: str | None = None, state: str | None = None, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback:
    - Exchange code for tokens
    - Fetch user info
    - Find or create user & tenant
    - Issue JWT
    - Redirect to frontend with token
    """
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No authorization code provided")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        logger.error(f"Google token exchange failed: {token_data}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to obtain access token from Google")

    # Fetch user info from Google
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    google_user = user_response.json()
    google_email = google_user.get("email")
    google_name = google_user.get("name") or google_email

    if not google_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google user email not available")

    # Find or create user
    user = db.query(User).filter(User.email == google_email).first()

    if not user:
        # Create default tenant for Google user if needed
        tenant = Tenant(
            name=f"{google_name}'s Workspace",
            slug=f"{google_email.split('@')[0]}-org",
            is_active=True,
        )
        db.add(tenant)
        db.flush()

        user = User(
            email=google_email,
            full_name=google_name,
            hashed_password="",  # No local password; Google only
            tenant_id=tenant.id,
            role="admin",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Google user created: {user.email} (Tenant: {tenant.name})")
    else:
        logger.info(f"Google user logged in: {user.email}")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Issue token
    token = auth_service.create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        role=(user.role.value if hasattr(user.role, "value") else str(user.role)),
    )

    if state == "candidate":
        import json
        import urllib.parse
        full_name = user.full_name or ""
        google_user_json = json.dumps({
            "id": str(user.id),
            "email": user.email,
            "firstName": full_name.split()[0] if full_name else "",
            "lastName": " ".join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else "",
            "resumeUrl": None
        })
        user_param = urllib.parse.quote(google_user_json)
        # Redirect to Candidate Portal URL with both token and user parameters
        redirect_url = f"http://localhost:5173/resume?token={token}&user={user_param}"
    else:
        # Redirect to frontend with token as query param
        redirect_url = f"{FRONTEND_URL}/dashboard?token={token}"
        
    return RedirectResponse(redirect_url)


logger.warning(f"Google OAuth redirect URI: {GOOGLE_REDIRECT_URI}")


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Handle forgot password requests.
    Generates a token and sends a reset email via the configured email service (SMTP).
    """
    user = db.query(User).filter(User.email == request.email).first()
    if user:
        # Generate token
        token = auth_service.create_password_reset_token(str(user.id), user.email)

        # Link to the frontend page
        reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

        # Send email
        email_service.send_reset_password_email(user.email, reset_link)
        logger.info(f"Password reset link sent to {user.email}")

    # Always return success message for security
    return {"message": "If an account exists for that email, you'll receive a reset link shortly."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Reset password using a valid token.
    """
    payload = auth_service.verify_password_reset_token(request.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password
    user.hashed_password = User.hash_password(request.new_password)
    db.commit()

    logger.info(f"Password successfully reset for user: {user.email}")
    return {"message": "Password successfully reset. You can now log in with your new password."}
