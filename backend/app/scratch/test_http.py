import urllib.request
import json
import sys

try:
    req = urllib.request.Request('https://recruitcore-production.up.railway.app/api/auth/login', 
        data=json.dumps({'email': 'admin@gmail.com', 'password': 'Admin@123'}).encode(), 
        headers={'Content-Type': 'application/json'})
        
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode())
        token = res.get('access_token')
        
        # Get Job ID
        req2 = urllib.request.Request('https://recruitcore-production.up.railway.app/api/jobs', headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req2) as r2:
            jobs = json.loads(r2.read().decode())['items']
            if not jobs:
                print("No jobs found")
                sys.exit(1)
            job_id = jobs[0]['id']

        # Get Resumes
        req3 = urllib.request.Request('https://recruitcore-production.up.railway.app/api/resumes', headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req3) as r3:
            resumes = json.loads(r3.read().decode())['items']
            if not resumes:
                print("No resumes found")
                sys.exit(1)
            resume_ids = [r['id'] for r in resumes[:2]]
        
        # Generate matches
        payload = {
            'job_id': job_id,
            'resume_ids': resume_ids,
            'limit': 50
        }
        print(f"Generating matches for job {job_id} and resumes {resume_ids}")
        req4 = urllib.request.Request('https://recruitcore-production.up.railway.app/api/matches/generate-selected', 
            data=json.dumps(payload).encode(),
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
        
        try:
            with urllib.request.urlopen(req4) as r4:
                print('Generate status:', r4.status)
                print('Generate response:', json.loads(r4.read().decode()))
        except urllib.error.HTTPError as e:
            print('Generate error code:', e.code)
            print('Generate error body:', e.read().decode())

except urllib.error.HTTPError as e:
    print('Error:', e.code, e.read().decode())
except Exception as e:
    print('Other error:', e)
