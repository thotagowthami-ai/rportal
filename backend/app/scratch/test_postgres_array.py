import urllib.request
import urllib.error
import json
import uuid

VERCEL_BASE = "https://recruit-app-v1-4urqjtmhp-ven010s-projects.vercel.app/api/backend/api"
boundary = uuid.uuid4().hex

try:
    req = urllib.request.Request(f'{VERCEL_BASE}/auth/login', 
        data=json.dumps({'email': 'admin2@gmail.com', 'password': 'Admin@123'}).encode(), 
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        token = json.loads(response.read().decode()).get('access_token')

    # Wait, the only way to test this without changing code is to see if we can trigger the error differently.
    # We can't change the server code from the client side request. The server will ALWAYS call json.dumps().
