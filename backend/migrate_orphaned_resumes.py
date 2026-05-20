#!/usr/bin/env python
"""
Migration script to restore database records for orphaned resume files.
This script scans the uploads directory and creates corresponding database records.
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, set_tenant_context
from app.models.resume import Resume
from app.models.user import User


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    ext = os.path.splitext(filename)[1].lstrip(".").lower()[:50] or "unknown"
    return ext


def get_file_id_and_name(filename: str) -> tuple[str, str]:
    """Extract UUID and original filename from stored filename."""
    parts = filename.split("_", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, filename


def migrate_orphaned_files():
    """Migrate orphaned resume files from disk to database."""
    db = SessionLocal()
    
    try:
        # Get the uploads directory
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        uploads_dir = os.path.join(base_dir, "uploads")
        
        if not os.path.exists(uploads_dir):
            print(f"❌ ERROR: Uploads directory not found: {uploads_dir}")
            return False
        
        # Get the default/system user (typically admin)
        system_user = db.query(User).first()
        if not system_user:
            print("❌ ERROR: No users found in database. Please create a user first.")
            return False
        
        tenant_id = str(system_user.tenant_id)
        set_tenant_context(db, tenant_id)
        
        # List all files in uploads directory
        files = [f for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]
        
        if not files:
            print(f"ℹ️  No files found in {uploads_dir}")
            return True
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"\n📂 Found {len(files)} files in {uploads_dir}")
        print(f"🔑 Using tenant: {tenant_id}")
        print(f"👤 Using user: {system_user.id}")
        print("\n" + "="*80)
        
        for filename in sorted(files):
            file_path = os.path.join(uploads_dir, filename)
            file_size = os.path.getsize(file_path)
            
            # Skip very small files (likely corrupted)
            if file_size < 100:
                print(f"⏭️  SKIP (corrupted): {filename} ({file_size} bytes)")
                skipped_count += 1
                continue
            
            file_id, original_name = get_file_id_and_name(filename)
            file_ext = get_file_extension(original_name)
            
            try:
                # Check if this resume already exists
                existing = db.query(Resume).filter(Resume.id == file_id).first()
                if existing:
                    print(f"⏭️  SKIP (exists): {original_name}")
                    skipped_count += 1
                    continue
                
                # Create new resume record
                resume = Resume(
                    id=file_id,
                    tenant_id=tenant_id,
                    uploaded_by=str(system_user.id),
                    candidate_name=original_name.rsplit(".", 1)[0],  # Use filename without extension as name
                    file_path=file_path,
                    file_name=original_name,
                    file_type=file_ext,
                )
                
                db.add(resume)
                db.flush()  # Flush to check for errors
                created_count += 1
                print(f"✅ CREATE: {original_name}")
                
            except Exception as e:
                error_count += 1
                print(f"❌ ERROR: {original_name} - {str(e)}")
                db.rollback()
                continue
        
        # Commit all changes
        try:
            db.commit()
            print("\n" + "="*80)
            print(f"\n✅ MIGRATION COMPLETE")
            print(f"   Created:  {created_count}")
            print(f"   Skipped:  {skipped_count}")
            print(f"   Errors:   {error_count}")
            print(f"   Total:    {len(files)}")
            return True
        except Exception as e:
            print(f"\n❌ COMMIT FAILED: {str(e)}")
            db.rollback()
            return False
            
    finally:
        db.close()


if __name__ == "__main__":
    success = migrate_orphaned_files()
    sys.exit(0 if success else 1)
