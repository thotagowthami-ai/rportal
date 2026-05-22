
import sys
from pathlib import Path

# Add backend to path
backend_path = Path("c:/Users/GOWTHAMI/Downloads/projects/recruiting-platform/backend")
sys.path.append(str(backend_path))

try:
    from app.config import settings
    print(f"Current Environment: {settings.ENVIRONMENT}")
    print(f"Current Redis Prefix: {settings.REDIS_KEY_PREFIX}")
    
    # Simulate production
    settings.ENVIRONMENT = "production"
    print(f"Simulated Production Prefix: {settings.REDIS_KEY_PREFIX}")
    
except Exception as e:
    print(f"Error: {e}")
