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
        
    # Upload a tiny dummy PDF to test the endpoint
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\nxref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n108\n%%EOF"
    
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"test.pdf\"\r\n"
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + pdf_content + f"\r\n--{boundary}--\r\n".encode()

    req_upload = urllib.request.Request(f'{VERCEL_BASE}/resumes/upload', data=body, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    })
    
    with urllib.request.urlopen(req_upload) as r:
        print("Success:", r.status)
        print(json.loads(r.read().decode()))

except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code, e.reason)
    print(e.read().decode())
except Exception as e:
    print('Error:', e)
