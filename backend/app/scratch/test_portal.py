import sys
import os
import asyncio
import httpx

# Add backend directory to sys.path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.config import settings
from app.services.matching_service import matching_service

async def test_portal_connection():
    print("--- Diagnostic Portal Connection Test ---")
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"CANDIDATE_PORTAL_URL in settings: {settings.CANDIDATE_PORTAL_URL}")
    print(f"CANDIDATE_PORTAL_TENANT_ID in settings: {settings.CANDIDATE_PORTAL_TENANT_ID}")
    print(f"RECRUITING_TENANT_ID in settings: {settings.RECRUITING_TENANT_ID}")
    print(f"CANDIDATE_PORTAL_URL derived in matching_service: {matching_service.candidate_portal_url}")
    
    # 1. Test fetching from resumes list endpoint directly
    url = f"{matching_service.candidate_portal_url}/resumes"
    tenant_id = settings.CANDIDATE_PORTAL_TENANT_ID or settings.RECRUITING_TENANT_ID
    params = {"tenant_id": tenant_id} if tenant_id else {}
    print(f"Testing GET request to: {url} with params {params}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            print(f"Response Status: {resp.status_code}")
            print(f"Response Snippet: {resp.text[:300]}")
    except Exception as e:
        print(f"GET request failed with error: {e}")

    # 2. Test fetching from match/jd endpoint
    url_jd = f"{matching_service.candidate_portal_url}/match/jd"
    payload = {
        "description": "python, javascript, react, node, sql, aws, docker, kubernetes, devops, api",
        "threshold": 0,
        "limit": 50,
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id
    print(f"Testing POST request to: {url_jd} with json {payload}")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url_jd, json=payload, params=params)
            print(f"Response Status: {resp.status_code}")
            print(f"Response Snippet: {resp.text[:300]}")
    except Exception as e:
        print(f"POST request failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_portal_connection())
