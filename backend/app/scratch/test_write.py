
import sys
from pathlib import Path

# Add backend to path
backend_path = Path("c:/Users/GOWTHAMI/Downloads/projects/recruiting-platform/backend")
sys.path.append(str(backend_path))

try:
    from app.core.redis_client import redis_client
    
    # Create a test key for the recruiting platform
    test_key = "recruit:connection_test"
    test_value = "Success - Unified Client Working"
    
    print(f"Attempting to write key: {test_key}")
    redis_client.setex(test_key, 600, test_value)  # 10 minute TTL
    
    # Verify the write
    val = redis_client.get(test_key)
    if val == test_value:
        print(f"VERIFICATION SUCCESS: Found '{val}' in Redis.")
    else:
        print(f"VERIFICATION FAILED: Expected '{test_value}', got '{val}'")
        
except Exception as e:
    print(f"Error: {e}")
