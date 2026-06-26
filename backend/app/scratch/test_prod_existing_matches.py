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
        job_id = job['id']

    req_matches = urllib.request.Request(f'{RAILWAY_BASE}/matches/job?job_id={job_id}&page=1&page_size=20', headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req_matches) as r_matches:
        matches = json.loads(r_matches.read().decode()).get('items', [])
        print(f"Total existing matches for job: {len(matches)}")
        if matches:
            print("First match:", matches[0])

if __name__ == '__main__':
    test_matches()
