import urllib.request
import json
import sys

RAILWAY_BASE = "https://recruitcore-production.up.railway.app/api"

def test_matches():
    req = urllib.request.Request(f'{RAILWAY_BASE}/auth/login', 
        data=json.dumps({'email': 'sureshnadiminti10@gmail.com', 'password': 'Suresh@123'}).encode(), 
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        token = json.loads(response.read().decode()).get('access_token')

    req2 = urllib.request.Request(f'{RAILWAY_BASE}/jobs', headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req2) as r2:
        jobs = json.loads(r2.read().decode()).get('items', [])
        job = jobs[0]
        print("Job title:", job.get('title'))
        print("Job skills:", job.get('required_skills'))

    req_res = urllib.request.Request(f'{RAILWAY_BASE}/resumes', headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req_res) as r_res:
        resumes = json.loads(r_res.read().decode()).get('items', [])
        print("Resume skills (first 2):")
        for r in resumes[:2]:
            print("ID:", r.get('id'), "Name:", r.get('candidate_name'), "Skills:", r.get('skills'), "Experience:", r.get('experience_years'))

    resume_ids = [r['id'] for r in resumes[:2]]
    payload = json.dumps({
        'job_id': job['id'],
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
            raw_response = r_force.read().decode()
            print(f"Generate response RAW: {raw_response}")
            matches_force = json.loads(raw_response)
            print(f"Generate response items length: {len(matches_force.get('items', []))}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_matches()
