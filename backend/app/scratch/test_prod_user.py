import urllib.request
import json
import sys

RAILWAY_BASE = "https://recruitcore-production.up.railway.app/api"

def test_matches():
    print("Logging in...")
    req = urllib.request.Request(f'{RAILWAY_BASE}/auth/login', 
        data=json.dumps({'email': 'sureshnadiminti10@gmail.com', 'password': 'Suresh@123'}).encode(), 
        headers={'Content-Type': 'application/json'})
        
    try:
        with urllib.request.urlopen(req) as response:
            token = json.loads(response.read().decode()).get('access_token')
            print("Login successful.")
    except urllib.error.HTTPError as e:
        print(f"Login failed HTTP Error {e.code}: {e.read().decode()}")
        return
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # get jobs
    print("Getting Jobs...")
    req2 = urllib.request.Request(f'{RAILWAY_BASE}/jobs', headers={'Authorization': f'Bearer {token}'})
    try:
        with urllib.request.urlopen(req2) as r2:
            jobs = json.loads(r2.read().decode()).get('items', [])
            if not jobs:
                print("No jobs found")
                return
            job_id = jobs[0]['id']
            print(f"Using job ID: {job_id}")
    except Exception as e:
        print(f"Failed to get jobs: {e}")
        return

    # get resumes
    print("Getting Resumes...")
    req_res = urllib.request.Request(f'{RAILWAY_BASE}/resumes', headers={'Authorization': f'Bearer {token}'})
    try:
        with urllib.request.urlopen(req_res) as r_res:
            resumes = json.loads(r_res.read().decode()).get('items', [])
            print(f"Total resumes: {len(resumes)}")
            if not resumes:
                print("No resumes found")
                return
    except Exception as e:
        print(f"Failed to get resumes: {e}")
        return

    resume_ids = [r['id'] for r in resumes[:2]] # Take first 2

    print(f"Generating matches for resumes {resume_ids}")
    payload = json.dumps({
        'job_id': job_id,
        'resume_ids': resume_ids,
        'limit': 50
    }).encode()
    
    req_force = urllib.request.Request(
        f'{RAILWAY_BASE}/matches/generate-selected', 
        data=payload, 
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req_force) as r_force:
            matches_force = json.loads(r_force.read().decode())
            print(f"Generate response items length: {len(matches_force.get('items', []))}")
            if matches_force.get('items'):
                print("First match:", matches_force['items'][0])
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"Error generating matches: {e}")

if __name__ == '__main__':
    test_matches()
