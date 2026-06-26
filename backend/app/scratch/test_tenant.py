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
        
        req2 = urllib.request.Request('https://recruitcore-production.up.railway.app/api/auth/me', headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req2) as r2:
            me = json.loads(r2.read().decode())
            print(f"My tenant_id: {me['tenant_id']}")
            
        req3 = urllib.request.Request('https://recruitcore-production.up.railway.app/api/resumes', headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req3) as r3:
            resumes = json.loads(r3.read().decode())['items']
            for r in resumes[:2]:
                print(f"Resume {r['id']} candidate_name: {r['candidate_name']} tenant_id: {r.get('tenant_id')}")

except Exception as e:
    print('Other error:', e)
