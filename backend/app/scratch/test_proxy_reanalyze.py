import urllib.request
import urllib.error
import json
import sys

VERCEL_BASE = "https://recruit-app-v1-4urqjtmhp-ven010s-projects.vercel.app/api/backend/api"

try:
    req = urllib.request.Request(f'{VERCEL_BASE}/auth/login', 
        data=json.dumps({'email': 'admin2@gmail.com', 'password': 'Admin@123'}).encode(), 
        headers={'Content-Type': 'application/json'})
        
    with urllib.request.urlopen(req) as response:
        token = json.loads(response.read().decode()).get('access_token')
        
    # Test re-analyze endpoint
    resume_id = "240056d3-3646-4a76-a8d9-a7ec277fa13f"
    req_reanalyze = urllib.request.Request(f'{VERCEL_BASE}/resumes/{resume_id}/re-analyze', data=b"{}", headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req_reanalyze) as r:
        print("Success:", r.status)
        print(json.loads(r.read().decode()))

except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code, e.reason)
    print(e.read().decode())
except Exception as e:
    print('Error:', e)
