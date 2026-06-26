import urllib.request
import json
import sys

VERCEL_BASE = "https://recruit-app-v1-4urqjtmhp-ven010s-projects.vercel.app/api/backend/api"

try:
    req = urllib.request.Request(f'{VERCEL_BASE}/auth/login', 
        data=json.dumps({'email': 'admin@gmail.com', 'password': 'Admin@123'}).encode(), 
        headers={'Content-Type': 'application/json'})
        
    with urllib.request.urlopen(req) as response:
        token = json.loads(response.read().decode()).get('access_token')
        
    req2 = urllib.request.Request(f'{VERCEL_BASE}/jobs', headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req2) as r2:
        jobs = json.loads(r2.read().decode())['items']
        job_id = jobs[0]['id']

    req4 = urllib.request.Request(f'{VERCEL_BASE}/matches/job?job_id={job_id}', headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req4) as r4:
        matches_list = json.loads(r4.read().decode())
        print(json.dumps(matches_list['items'], indent=2))

except Exception as e:
    print('Error:', e)
