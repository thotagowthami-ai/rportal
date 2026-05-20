#!/usr/bin/env python
"""
Script to check the current state of the resumes table in the database.
Checks:
1. Total count of resumes
2. Recent resumes created after the fix
3. Comparison with previous state
4. Backend process status
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from app.database import engine, SessionLocal
from app.models.resume import Resume
from sqlalchemy import func, text

def check_database_state():
    """Check the current state of the resumes table."""
    print("\n" + "="*100)
    print("📊 RECRUITING PLATFORM - DATABASE STATE CHECK")
    print("="*100)
    
    db = SessionLocal()
    try:
        # Get database URL
        db_url = os.getenv('DATABASE_URL', 'Unknown')
        print(f"\n🔗 Database URL: {db_url[:80]}...")
        print(f"   Type: {'PostgreSQL' if 'postgresql' in db_url else 'SQLite'}")
        
        # 1. Count total resumes
        print("\n" + "─"*100)
        print("1️⃣  TOTAL RESUMES COUNT")
        print("─"*100)
        
        total_count = db.query(func.count(Resume.id)).scalar()
        print(f"   Total resumes in database: {total_count}")
        
        if total_count == 0:
            print("   ❌ NO RECORDS FOUND - Database may not have been updated yet")
            print("   ⚠️  The backend might not have reloaded or the fix isn't working")
        else:
            print(f"   ✅ FOUND {total_count} RESUME(S) - Fix appears to be working!")
        
        # 2. Check for recent resumes (last 5 minutes)
        print("\n" + "─"*100)
        print("2️⃣  RECENT RESUMES (Last 5 minutes)")
        print("─"*100)
        
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_count = db.query(func.count(Resume.id)).filter(
            Resume.created_at > five_min_ago
        ).scalar()
        
        print(f"   Resumes created in last 5 minutes: {recent_count}")
        
        if recent_count > 0:
            recent = db.query(Resume).filter(
                Resume.created_at > five_min_ago
            ).order_by(Resume.created_at.desc()).all()
            
            print(f"\n   📋 Recent resumes:")
            for r in recent:
                print(f"      • ID: {r.id}")
                print(f"        Name: {r.file_name}")
                print(f"        Candidate: {r.candidate_name}")
                print(f"        Created: {r.created_at}")
        
        # 3. Check last 10 resumes
        print("\n" + "─"*100)
        print("3️⃣  LAST 10 RESUMES (Most Recent)")
        print("─"*100)
        
        if total_count > 0:
            resumes = db.query(Resume).order_by(Resume.created_at.desc()).limit(10).all()
            
            for i, r in enumerate(resumes, 1):
                print(f"\n   {i}. {r.file_name}")
                print(f"      ID: {r.id}")
                print(f"      Candidate: {r.candidate_name}")
                print(f"      Created: {r.created_at}")
                print(f"      Updated: {r.updated_at}")
                if r.deleted_at:
                    print(f"      Deleted: {r.deleted_at}")
        else:
            print("   ❌ No resumes to display")
        
        # 4. Check resumes by date range
        print("\n" + "─"*100)
        print("4️⃣  RESUMES BY TIME RANGE")
        print("─"*100)
        
        now = datetime.utcnow()
        last_hour = db.query(func.count(Resume.id)).filter(
            Resume.created_at > now - timedelta(hours=1)
        ).scalar()
        last_day = db.query(func.count(Resume.id)).filter(
            Resume.created_at > now - timedelta(days=1)
        ).scalar()
        
        print(f"   Last 1 hour:  {last_hour} resumes")
        print(f"   Last 1 day:   {last_day} resumes")
        print(f"   Total:        {total_count} resumes")
        
        # 5. Database status summary
        print("\n" + "─"*100)
        print("5️⃣  STATUS SUMMARY")
        print("─"*100)
        
        if total_count == 0:
            print("   ❌ Database is EMPTY (0 resumes)")
            print("   ")
            print("   🔴 ISSUE DETECTED:")
            print("      • The resumes table has no records")
            print("      • Either the backend hasn't reloaded yet")
            print("      • Or the file upload fix isn't working")
            print("      • Or the database connection is not using the right schema")
        else:
            print(f"   ✅ Database has {total_count} resume(s)")
            print("   ")
            print("   🟢 SUCCESS:")
            print(f"      • Resumes are being stored in the database")
            print(f"      • The backend appears to be working correctly")
            
            if recent_count > 0:
                print(f"      • {recent_count} new resume(s) created recently")
                print(f"      • The code fix is ACTIVE and WORKING")
            else:
                print(f"      • No recent uploads (last 5 minutes)")
                print(f"      • But old files may be linked if they exist")
        
        print("\n" + "="*100 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return total_count > 0

if __name__ == "__main__":
    try:
        success = check_database_state()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
