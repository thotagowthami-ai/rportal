import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.database import SessionLocal
from app.models.user import User
from app.routers.analytics import get_dashboard_metrics

db = SessionLocal()
# Find any user in the database
user = db.query(User).first()
if not user:
    print("No user found in database.")
    sys.exit(0)

print(f"Testing dashboard API function for user: {user.email}")

try:
    response = get_dashboard_metrics(db=db, current_user=user)
    print("Success! Dashboard response data:")
    import json
    print(json.dumps(response, indent=2))
except Exception as e:
    import traceback
    print(f"Exception raised: {e}")
    traceback.print_exc()
finally:
    db.close()
