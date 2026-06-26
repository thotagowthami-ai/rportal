from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.config import settings
from app.database import init_db
import json

from app.routers import jobs, resumes, auth, analytics, matches, linkedin_posts, linkedin


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    redirect_slashes=True,
)

allowed_origins = settings.ALLOWED_ORIGINS
if isinstance(allowed_origins, str):
    raw = allowed_origins.strip()
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                expanded = []
                for item in parsed:
                    if isinstance(item, str):
                        expanded.extend([o.strip() for o in item.split(",") if o.strip()])
                allowed_origins = expanded
            else:
                allowed_origins = [o.strip() for o in raw.split(",") if o.strip()]
        except Exception:
            cleaned = raw.strip("[]").replace('"', "").replace("'", "")
            allowed_origins = [o.strip() for o in cleaned.split(",") if o.strip()]
    else:
        allowed_origins = [o.strip() for o in raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=(settings.ALLOWED_ORIGIN_REGEX or None),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    if settings.AUTO_CREATE_TABLES:
        init_db()


# Routers
app.include_router(jobs.router, prefix="/api")
app.include_router(resumes.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(matches.router, prefix="/api")
app.include_router(linkedin_posts.router, prefix="/api")
app.include_router(linkedin.router, prefix="/api")


@app.get("/linkedin/callback")
def linkedin_callback_fallback(
    code: str = None,
    state: str = None,
    error: str = None,
    error_description: str = None,
):
    import urllib.parse
    params = {}
    if code: params["code"] = code
    if state: params["state"] = state
    if error: params["error"] = error
    if error_description: params["error_description"] = error_description
    
    qs = f"?{urllib.parse.urlencode(params)}" if params else ""
    return RedirectResponse(url=f"/api/linkedin/callback{qs}")


@app.get("/")
def read_root():
    return {"message": "Welcome to Recruiting Platform API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
