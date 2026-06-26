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
            job_id = jobs[0]['id']

        # Get Matches
        print(f"Getting matches for job {job_id}")
        req3 = urllib.request.Request(f'https://recruitcore-production.up.railway.app/api/matches/job?job_id={job_id}', headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req3) as r3:
            matches = json.loads(r3.read().decode())
            print(f"Matches count: {matches['total']}")
            print(matches['items'])

except urllib.error.HTTPError as e:
    print('Error:', e.code, e.read().decode())
except Exception as e:
    print('Other error:', e)
