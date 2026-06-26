import sys
import os

# Add backend app directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

os.environ["TEST_DATABASE_URL"] = "sqlite:///./test.db"

from app.tests.test_epic3 import _validate_test_db_url as validate_epic3_db
from app.tests.test_security import _validate_test_db_url as validate_security_db

def run_tests():
    print("=== Testing Database URL Security Guard ===")
    
    # 1. Test valid database connections
    valid_urls = [
        "sqlite:///./test.db",
        "sqlite:///:memory:",
        "postgresql://user:pass@localhost:5432/my_test_db",
        "postgresql://user:pass@127.0.0.1:5432/neondb", # localhost IP
        "postgresql://user:pass@somehost:5432/test_database", # 'test' in db name
    ]
    
    # 2. Test invalid / unsafe database connections (should raise RuntimeError)
    invalid_urls = [
        "postgresql://user:pass@neon.tech/production_db", # no 'test', no local host
        "postgresql://user:pass@someprodhost:5432/company_records",
    ]
    
    for name, guard in [("Epic3 DB Guard", validate_epic3_db), ("Security DB Guard", validate_security_db)]:
        print(f"\n--- Running: {name} ---")
        for url in valid_urls:
            try:
                guard(url)
                print(f"✅ Allowed (expected): {url}")
            except RuntimeError as e:
                print(f"❌ Rejected (unexpected): {url} - Error: {e}")
                
        for url in invalid_urls:
            try:
                guard(url)
                print(f"❌ Allowed (unexpected!): {url}")
            except RuntimeError as e:
                print(f"✅ Rejected (expected): {url} - Error: {str(e)[:50]}...")

if __name__ == "__main__":
    run_tests()
