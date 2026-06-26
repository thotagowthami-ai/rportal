import urllib.request
import json
import sys

VERCEL_BASE = "https://recruit-app-v1-4urqjtmhp-ven010s-projects.vercel.app/api/backend/api"

try:
    print("Logging in...")
    req = urllib.request.Request(f'{VERCEL_BASE}/auth/login', 
        data=json.dumps({'email': 'admin@gmail.com', 'password': 'Admin@123'}).encode(), 
        headers={'Content-Type': 'application/json'})
        
    with urllib.request.urlopen(req) as response:
        token = json.loads(response.read().decode()).get('access_token')
        
    print("Getting Jobs...")
    req2 = urllib.request.Request(f'{VERCEL_BASE}/jobs', headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req2) as r2:
        jobs = json.loads(r2.read().decode())['items']
        job_id = jobs[0]['id']
        
    print("Getting Resumes...")
    req_res = urllib.request.Request(f'{VERCEL_BASE}/resumes', headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req_res) as r_res:
        resumes = json.loads(r_res.read().decode())['items']
        print(f"Total resumes: {len(resumes)}")
        
    if not resumes:
        print("No resumes to test")
        sys.exit(0)

    resume_ids = [r['id'] for r in resumes[:2]] # Take first 2

    print(f"Forcing matches generation for resumes {resume_ids}")
    payload = json.dumps({
        'job_id': job_id,
        'resume_ids': resume_ids,
        'limit': 50
    }).encode()
    
    req_force = urllib.request.Request(
        f'{VERCEL_BASE}/matches/generate-selected', 
        data=payload, 
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req_force) as r_force:
        matches_force = json.loads(r_force.read().decode())
        print(f"Force Generate response items length: {len(matches_force['items'])}")
        if len(matches_force['items']) > 0:
            print("First match score:", matches_force['items'][0].get('overall_score'))

except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code, e.read().decode())
except Exception as e:
    print('Other error:', e)
