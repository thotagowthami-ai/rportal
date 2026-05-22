from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse, ForgotPasswordRequest, PasswordResetConfirm
from app.services.auth_service import auth_service
from app.services.email_service import email_service
from app.services.cache_service import cache_service
from app.config import settings
from app.api.deps import get_current_user
from datetime import datetime
import logging
import secrets

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

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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


from pydantic import BaseModel

class CodeExchangeRequest(BaseModel):
    code: str

@router.post("/exchange-code", response_model=TokenResponse)
def exchange_code(payload: CodeExchangeRequest, db: Session = Depends(get_db)):
    """
    Exchange a short-lived one-time authorization code for a full TokenResponse.
    """
    import json
    
    code = payload.code.strip()
    cache_key = f"oauth_code:{code}"
    
    # 1. Fetch token details from Redis
    payload_str = cache_service.get(key=cache_key)
    if not payload_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired one-time code"
        )
        
    # 2. Delete the cache key immediately to enforce strict one-time use
    cache_service.delete(key=cache_key)
    
    try:
        data = json.loads(payload_str)
        return TokenResponse(
            access_token=data["access_token"],
            token_type=data["token_type"],
            expires_in=data["expires_in"],
            user=UserResponse(
                id=data["user"]["id"],
                email=data["user"]["email"],
                full_name=data["user"]["full_name"],
                role=data["user"]["role"],
                is_active=data["user"]["is_active"],
                is_verified=data["user"]["is_verified"],
                tenant_id=data["user"]["tenant_id"],
                created_at=data["user"]["created_at"],
                last_login=data["user"]["last_login"]
            )
        )
    except Exception as e:
        logger.error(f"Error parsing cached token payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication payload corruption"
        )



@router.get("/google")
async def google_login(source: str = "ats"):
    """
    Start Google OAuth flow:
    Redirects the user to Google's consent screen.

    SECURITY: Generates a cryptographically-random nonce per request,
    stores it in Redis (5-min TTL), and embeds it in the OAuth state
    parameter to prevent CSRF attacks.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth missing client ID or secret")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured",
        )

    # Generate a cryptographically-random nonce and store in Redis (5 min TTL)
    nonce = secrets.token_urlsafe(32)
    cache_service.set(key=f"oauth_nonce:{nonce}", value=source, ttl=300)

    # Embed nonce + source in state: "<nonce>:<source>"
    state = f"{nonce}:{source}"

    google_url = (
        f"{GOOGLE_AUTH_URL}"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={state}"
    )
    return RedirectResponse(google_url)


@router.get("/google/callback")
async def google_callback(code: str | None = None, state: str | None = None, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback:
    - Verify CSRF nonce from state parameter against Redis
    - Exchange code for tokens
    - Fetch user info
    - Find or create user & tenant
    - Issue JWT
    - Redirect to frontend with token
    """
    login_url = f"{FRONTEND_URL}/login"

    if not code:
        logger.warning("OAuth callback: missing authorization code")
        return RedirectResponse(f"{login_url}?error=google_no_code")

    # ── CSRF nonce verification ──────────────────────────────────────────────
    if not state or ":" not in state:
        logger.warning("OAuth callback received invalid or missing state parameter")
        return RedirectResponse(f"{login_url}?error=google_invalid_state")

    nonce, source = state.split(":", 1)
    stored_source = cache_service.get(key=f"oauth_nonce:{nonce}")

    if stored_source is None or stored_source != source:
        if stored_source is not None:
            logger.warning(
                f"OAuth CSRF check failed: source mismatch "
                f"(expected='{stored_source}', got='{source}')"
            )
        else:
            logger.warning("OAuth CSRF check failed: nonce not found or expired")
        return RedirectResponse(f"{login_url}?error=google_session_expired")

    # Delete nonce immediately — one-time use only
    cache_service.delete(key=f"oauth_nonce:{nonce}")
    logger.info(f"OAuth CSRF nonce verified and consumed for source='{source}'")
    # ────────────────────────────────────────────────────────────────────────

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
        return RedirectResponse(f"{login_url}?error=google_token_failed")

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
        # Generate a unique slug for the default tenant to prevent collisions
        base_slug = f"{google_email.split('@')[0]}-org"
        import re
        base_slug = re.sub(r"[^a-zA-Z0-9-]", "", base_slug.replace("_", "-")).lower()
        if not base_slug:
            base_slug = "org"

        slug = base_slug
        counter = 1
        while True:
            existing = db.query(Tenant).filter(Tenant.slug == slug).first()
            if not existing:
                break
            import secrets
            suffix = secrets.token_hex(3)
            slug = f"{base_slug}-{suffix}"
            counter += 1
            if counter > 20:
                slug = f"{base_slug}-{secrets.token_hex(6)}"
                break

        tenant = Tenant(
            name=f"{google_name}'s Workspace",
            slug=slug,
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

    # Issue short-lived one-time code to avoid token URL exposure
    import json
    one_time_code = secrets.token_urlsafe(32)
    
    full_name = user.full_name or ""
    is_active = True if user.is_active is None else bool(user.is_active)
    
    payload_data = {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": full_name,
            "role": (user.role.value if hasattr(user.role, "value") else str(user.role)),
            "is_active": is_active,
            "is_verified": user.is_verified,
            "tenant_id": str(user.tenant_id),
            "created_at": user.created_at.isoformat() if hasattr(user.created_at, "isoformat") else str(user.created_at),
            "last_login": user.last_login.isoformat() if (user.last_login and hasattr(user.last_login, "isoformat")) else (str(user.last_login) if user.last_login else None)
        }
    }
    
    cache_service.set(key=f"oauth_code:{one_time_code}", value=json.dumps(payload_data), ttl=60)

    if source == "candidate":
        import urllib.parse
        google_user_json = json.dumps({
            "id": str(user.id),
            "email": user.email,
            "firstName": full_name.split()[0] if full_name else "",
            "lastName": " ".join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else "",
            "resumeUrl": None
        })
        user_param = urllib.parse.quote(google_user_json)
        candidate_base = (settings.CANDIDATE_PORTAL_URL or "http://localhost:5173").rstrip("/")
        # Redirect to Candidate Portal URL with both one-time code and user parameters
        redirect_url = f"{candidate_base}/resume?code={one_time_code}&user={user_param}"
    else:
        # Redirect to frontend with one-time code as query param
        redirect_url = f"{FRONTEND_URL}/dashboard?code={one_time_code}"
        
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
    try:
        user.hashed_password = User.hash_password(request.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    db.commit()

    # Mark the jti as used (remove it) after a successful reset so replay attacks fail
    jti = payload.get("jti")
    if jti:
        from app.services.cache_service import cache_service
        cache_service.delete(f"pwd_reset_jti:{jti}")

    logger.info(f"Password successfully reset for user: {user.email}")
    return {"message": "Password successfully reset. You can now log in with your new password."}
