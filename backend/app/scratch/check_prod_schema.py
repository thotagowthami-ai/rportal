import urllib.request
import urllib.error
import json

VERCEL_BASE = "https://recruit-app-v1-4urqjtmhp-ven010s-projects.vercel.app/api/backend/api"

try:
    # Login
    req = urllib.request.Request(f'{VERCEL_BASE}/auth/login', 
        data=json.dumps({'email': 'admin2@gmail.com', 'password': 'Admin@123'}).encode(), 
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        token = json.loads(response.read().decode()).get('access_token')

    # We don't have a direct endpoint to run SQL. We need to look at the swagger or find an endpoint.
