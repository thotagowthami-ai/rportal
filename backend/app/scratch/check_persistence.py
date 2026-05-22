
import sys
from pathlib import Path

# Add backend to path (portable)
backend_path = Path(__file__).resolve().parents[2]
sys.path.append(str(backend_path))

try:
    from app.core.redis_client import redis_client
    
    print("--- Recruiting Keys Status ---")
    keys = redis_client.keys("recruit:*")
    
    if not keys:
        print("No 'recruit:' keys found. I will create a permanent one now.")
        redis_client.set("recruit:persistent_test", "This will never expire")
        keys = ["recruit:persistent_test"]
    
    for key in sorted(keys):
        ttl = redis_client.ttl(key)
        # TTL of -1 means it never expires in Redis
        status = "PERMANENT" if ttl == -1 else f"Expires in {ttl}s"
        print(f"Key: {key} | Status: {status}")
            
except Exception as e:
    print(f"Error: {e}")
