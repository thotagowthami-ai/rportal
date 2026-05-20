#!/usr/bin/env python
"""
Cleanup script to find and fix missing resume files.
Options:
  1. List missing files
  2. Soft delete (mark as deleted)
  3. Update file paths (if file exists elsewhere)
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models.resume import Resume
from sqlalchemy import func

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

def find_missing_resumes():
    """Find all resumes whose files are missing from disk."""
    db = SessionLocal()
    try:
        # Get all non-deleted resumes
        resumes = db.query(Resume).filter(Resume.deleted_at.is_(None)).all()
        
        missing = []
        found = []
        
        for resume in resumes:
            file_path = resume.file_path
            if not file_path or not os.path.exists(file_path):
                missing.append({
                    'id': resume.id,
                    'name': resume.file_name,
                    'candidate': resume.candidate_name,
                    'path': file_path,
                    'created_at': resume.created_at
                })
            else:
                found.append(resume.id)
        
        return missing, found
    finally:
        db.close()

def soft_delete_missing_resumes():
    """Mark missing resumes as deleted."""
    missing, _ = find_missing_resumes()
    
    if not missing:
        print("✅ No missing resumes found!")
        return True
    
    db = SessionLocal()
    try:
        deleted_count = 0
        for resume_data in missing:
            resume = db.query(Resume).filter(Resume.id == resume_data['id']).first()
            if resume and not resume.deleted_at:
                resume.deleted_at = datetime.utcnow()
                deleted_count += 1
        
        db.commit()
        print(f"✅ Marked {deleted_count} missing resume(s) as deleted")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def main():
    print("\n" + "="*80)
    print("📋 RESUME CLEANUP UTILITY")
    print("="*80)
    
    print(f"\nChecking uploads directory: {UPLOADS_DIR}")
    print(f"Directory exists: {os.path.exists(UPLOADS_DIR)}\n")
    
    missing, found = find_missing_resumes()
    total = len(missing) + len(found)
    
    print(f"📊 SUMMARY")
    print(f"{"─"*80}")
    print(f"Total resumes in database: {total}")
    print(f"✅ Files found on disk:    {len(found)}")
    print(f"❌ Files missing on disk:  {len(missing)}")
    
    if missing:
        print(f"\n🔴 MISSING RESUMES ({len(missing)}):")
        print(f"{"─"*80}")
        for i, res in enumerate(missing, 1):
            print(f"{i}. {res['name']}")
            print(f"   ID: {res['id']}")
            print(f"   Candidate: {res['candidate']}")
            print(f"   Expected path: {res['path']}")
            print(f"   Created: {res['created_at']}")
            print()
        
        print("💡 RECOMMENDED ACTION:")
        print("   Run with --cleanup flag to mark these as deleted:")
        print("   python cleanup_resumes.py --cleanup")
        print()
    else:
        print("\n✅ All resume files are intact!")
    
    # Handle command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--cleanup":
            print(f"\n🔧 CLEANING UP {len(missing)} MISSING RESUME(S)...")
            if soft_delete_missing_resumes():
                print("✅ Cleanup completed successfully!")
            else:
                print("❌ Cleanup failed!")
                return False
    
    print(f"\n{"="*80}\n")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
