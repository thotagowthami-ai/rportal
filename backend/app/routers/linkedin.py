from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.linkedin_account import LinkedInAccount
from app.models.user import User


router = APIRouter(prefix="/linkedin", tags=["linkedin"])


class ConnectResponse(BaseModel):
    auth_url: str


class StatusResponse(BaseModel):
    connected: bool
    person_urn: str | None = None
    expires_at: str | None = None


class PostRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=3000)


class PostResponse(BaseModel):
    ok: bool
    post_id: str
    url: str


class ConnectRequest(BaseModel):
    return_to: str = "/linkedin-generator"


def _require_linkedin_config() -> None:
    if (
        not settings.LINKEDIN_CLIENT_ID
        or not settings.LINKEDIN_CLIENT_SECRET
        or not settings.LINKEDIN_REDIRECT_URI
        or not settings.FRONTEND_URL
    ):
        raise HTTPException(status_code=500, detail="LinkedIn OAuth is not configured on server")


def _build_frontend_url(path: str) -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    safe_path = path if path.startswith("/") else "/linkedin-generator"
    return f"{base}{safe_path}"


def _build_state_token(user: User, return_to: str) -> str:
    import secrets
    from app.services.cache_service import cache_service

    nonce = secrets.token_urlsafe(32)
    cache_service.set(key=f"oauth_nonce:{nonce}", value="linkedin", ttl=600)

    payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "return_to": return_to if return_to.startswith("/") else "/linkedin-generator",
        "exp": datetime.utcnow() + timedelta(minutes=10),
        "kind": "linkedin_oauth_state",
        "nonce": nonce,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_state_token(state: str) -> dict[str, Any]:
    return jwt.decode(state, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


async def _get_linkedin_profile(access_token: str, scope_value: str) -> tuple[str, str]:
    headers = {"Authorization": f"Bearer {access_token}"}
    uses_openid = any(part in scope_value.split() for part in ["openid", "profile", "email"])
    async with httpx.AsyncClient(timeout=20.0) as client:
        endpoints = (
            ["https://api.linkedin.com/v2/userinfo", "https://api.linkedin.com/v2/me"]
            if uses_openid
            else ["https://api.linkedin.com/v2/me", "https://api.linkedin.com/v2/userinfo"]
        )
        for endpoint in endpoints:
            resp = await client.get(endpoint, headers=headers)
            if resp.status_code >= 400:
                continue
            data = resp.json()
            member_id = str(data.get("sub", "") or data.get("id", "")).strip()
            if member_id:
                return member_id, f"urn:li:person:{member_id}"

    raise HTTPException(status_code=400, detail="LinkedIn profile id not found")


@router.post("/connect", response_model=ConnectResponse)
async def connect_linkedin(
    payload: ConnectRequest,
    current_user: User = Depends(get_current_user),
):
    _require_linkedin_config()
    state = _build_state_token(current_user, payload.return_to)

    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": settings.LINKEDIN_SCOPES,
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return ConnectResponse(auth_url=auth_url)


@router.get("/callback")
async def linkedin_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    _require_linkedin_config()

    if error:
        import urllib.parse
        base_url = _build_frontend_url("/linkedin-generator")
        params = {"linkedin": "error"}
        if error_description:
            params["reason"] = error_description
        return RedirectResponse(f"{base_url}?{urllib.parse.urlencode(params)}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing LinkedIn callback params")

    try:
        parsed = _decode_state_token(state)
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    from app.services.cache_service import cache_service
    nonce = parsed.get("nonce")
    if not nonce:
        raise HTTPException(status_code=400, detail="OAuth state missing validation nonce")
    
    stored = cache_service.get(key=f"oauth_nonce:{nonce}")
    if stored != "linkedin":
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    
    # Consume immediately
    cache_service.delete(key=f"oauth_nonce:{nonce}")

    user_id = str(parsed.get("sub", ""))
    tenant_id = str(parsed.get("tenant_id", ""))
    return_to = str(parsed.get("return_to", "/linkedin-generator"))
    if parsed.get("kind") != "linkedin_oauth_state" or not user_id or not tenant_id:
        raise HTTPException(status_code=400, detail="Invalid OAuth state payload")

    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found for OAuth callback")

    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_resp = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data=token_payload,
            headers=headers,
        )
    if token_resp.status_code >= 400:
        import urllib.parse
        base_url = _build_frontend_url("/linkedin-generator")
        params = {"linkedin": "error", "reason": "token_exchange_failed"}
        return RedirectResponse(f"{base_url}?{urllib.parse.urlencode(params)}")

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in")
    scope = token_data.get("scope")
    if not access_token:
        import urllib.parse
        base_url = _build_frontend_url("/linkedin-generator")
        params = {"linkedin": "error", "reason": "missing_access_token"}
        return RedirectResponse(f"{base_url}?{urllib.parse.urlencode(params)}")

    resolved_scope = scope if isinstance(scope, str) and scope.strip() else settings.LINKEDIN_SCOPES
    try:
        linkedin_sub, person_urn = await _get_linkedin_profile(access_token, resolved_scope)
    except HTTPException:
        import urllib.parse
        base_url = _build_frontend_url("/linkedin-generator")
        params = {"linkedin": "error", "reason": "missing_member_id"}
        return RedirectResponse(f"{base_url}?{urllib.parse.urlencode(params)}")
    expires_at = None
    if isinstance(expires_in, int):
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    account = db.query(LinkedInAccount).filter(LinkedInAccount.user_id == user_id).first()
    if not account:
        account = LinkedInAccount(
            user_id=user_id,
            tenant_id=tenant_id,
            linkedin_sub=linkedin_sub,
            person_urn=person_urn,
            access_token=access_token,
            scope=scope if isinstance(scope, str) else None,
            expires_at=expires_at,
        )
        db.add(account)
    else:
        account.linkedin_sub = linkedin_sub
        account.person_urn = person_urn
        account.access_token = access_token
        account.scope = scope if isinstance(scope, str) else account.scope
        account.expires_at = expires_at

    db.commit()
    import urllib.parse
    parsed_return = urllib.parse.urlparse(return_to)
    query_params = urllib.parse.parse_qsl(parsed_return.query)
    query_dict = dict(query_params)
    query_dict["linkedin"] = "connected"

    clean_path = parsed_return.path
    if not clean_path.startswith("/"):
        clean_path = "/" + clean_path

    base_url = _build_frontend_url(clean_path)
    redirect_url = f"{base_url}?{urllib.parse.urlencode(query_dict)}"
    return RedirectResponse(redirect_url)


@router.get("/status", response_model=StatusResponse)
async def linkedin_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(LinkedInAccount).filter(LinkedInAccount.user_id == str(current_user.id)).first()
    if not account:
        return StatusResponse(connected=False)
    return StatusResponse(
        connected=True,
        person_urn=account.person_urn,
        expires_at=account.expires_at.isoformat() if account.expires_at else None,
    )


@router.delete("/disconnect")
async def linkedin_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(LinkedInAccount).filter(LinkedInAccount.user_id == str(current_user.id)).first()
    if account:
        db.delete(account)
        db.commit()
    return {"ok": True}


@router.post("/post", response_model=PostResponse)
async def create_linkedin_post(
    payload: PostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(LinkedInAccount).filter(LinkedInAccount.user_id == str(current_user.id)).first()
    if not account:
        raise HTTPException(status_code=400, detail="LinkedIn account not connected")

    if account.expires_at and datetime.utcnow() >= account.expires_at:
        raise HTTPException(status_code=401, detail="LinkedIn token expired. Please reconnect LinkedIn.")

    headers = {
        "Authorization": f"Bearer {account.access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    body = {
        "author": account.person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": payload.text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post("https://api.linkedin.com/v2/ugcPosts", json=body, headers=headers)
    if resp.status_code >= 400:
        message = "LinkedIn post failed"
        try:
            data = resp.json()
            message = data.get("message") or data.get("error_description") or message
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=message)

    post_id = resp.headers.get("x-restli-id", "")
    post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else "https://www.linkedin.com/feed/"
    return PostResponse(ok=True, post_id=post_id, url=post_url)
