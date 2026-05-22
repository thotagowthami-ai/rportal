
import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path("c:/Users/GOWTHAMI/Downloads/projects/recruiting-platform/backend")
sys.path.append(str(backend_path))

try:
    from app.core.redis_client import redis_client
    
    # 1. Create a sample analytics key to show the format
    sample_key = "recruit:analytics:overview:test_tenant:30"
    sample_data = {"total_jobs": 15, "total_resumes": 42, "last_updated": "2024-05-13"}
    redis_client.setex(sample_key, 600, json.dumps(sample_data))
    
    print("--- Redis Keys (Filtered by 'recruit:') ---")
    keys = redis_client.keys("recruit:*")
    
    if not keys:
        print("No recruiting data found yet.")
    else:
        for key in sorted(keys):
            ttl = redis_client.ttl(key)
            print(f"Key: {key}")
            print(f"  - TTL: {ttl}s")
            # If it's the test data, show the content
            if "test" in key:
                val = redis_client.get(key)
                print(f"  - Content: {val}")
    
except Exception as e:
    print(f"Error: {e}")
