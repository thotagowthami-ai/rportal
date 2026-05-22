
import sys
from pathlib import Path

# Add backend to path (relative to this script's location)
backend_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_path))

try:
    from app.core.redis_client import redis_client
    print("Checking Redis keys...")
    
    # Get all keys
    # Note: keys() can be slow on large DBs, but fine for troubleshooting
    keys = redis_client.keys("*")
    
    if not keys:
        print("No keys found in Redis.")
    else:
        print(f"Found {len(keys)} keys:")
        for key in sorted(keys):
            # Print key and its TTL
            ttl = redis_client.ttl(key)
            print(f" - {key} (TTL: {ttl}s)")
            
except Exception as e:
    print(f"Error connecting to Redis: {e}")
