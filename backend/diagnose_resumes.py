#!/usr/bin/env python
"""
Quick diagnostic to check the health of resume storage system
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models.resume import Resume
from sqlalchemy import func

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

def diagnose():
    db = SessionLocal()
    try:
        total = db.query(func.count(Resume.id)).scalar()
        deleted = db.query(func.count(Resume.id)).filter(Resume.deleted_at.isnot(None)).scalar()
        active = total - deleted
        
        files_on_disk = len([f for f in os.listdir(UPLOADS_DIR) if os.path.isfile(os.path.join(UPLOADS_DIR, f))])
        
        print("\n" + "="*60)
        print("🔍 RESUME SYSTEM DIAGNOSTIC")
        print("="*60)
        print(f"📊 Total resumes in DB:        {total}")
        print(f"✅ Active resumes:            {active}")
        print(f"🗑️  Deleted resumes:          {deleted}")
        print(f"📁 Files on disk:             {files_on_disk}")
        print(f"✅ Disk space health:        ", end="")
        
        if files_on_disk >= active * 0.8:
            print("✅ GOOD (80%+ files present)")
        elif files_on_disk >= active * 0.5:
            print("⚠️  WARNING (50-80% files present)")
        else:
            print("❌ CRITICAL (<50% files present)")
        
        print("\n💡 RECOMMENDATIONS:")
        if active > files_on_disk:
            missing = active - files_on_disk
            print(f"   • {missing} resume file(s) are missing")
            print(f"   • Run: python cleanup_resumes.py --cleanup")
        else:
            print("   ✅ All active resumes have files on disk")
        
        print("="*60 + "\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    try:
        diagnose()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
