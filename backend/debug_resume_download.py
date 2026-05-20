#!/usr/bin/env python
"""
Debug script to check why resume download is failing with 404
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models.resume import Resume

# Get the resume ID from command line or hardcode for testing
resume_id = sys.argv[1] if len(sys.argv) > 1 else None

if not resume_id:
    print("❌ Please provide a resume ID")
    print("Usage: python debug_resume_download.py <resume_id>")
    sys.exit(1)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

print(f"\n📋 Debugging Resume Download Issue")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"Resume ID: {resume_id}")
print(f"UPLOADS_DIR: {UPLOADS_DIR}")
print(f"UPLOADS_DIR exists: {os.path.exists(UPLOADS_DIR)}")

db = SessionLocal()
try:
    # Query resume
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    
    if not resume:
        print(f"\n❌ Resume not found in database")
        sys.exit(1)
    
    print(f"\n✅ Resume found in database:")
    print(f"   Name: {resume.candidate_name}")
    print(f"   File: {resume.file_name}")
    print(f"   Type: {resume.file_type}")
    print(f"   Stored file_path: {resume.file_path}")
    
    # Check if file_path exists
    file_path = resume.file_path
    if file_path and os.path.exists(file_path):
        print(f"\n✅ File exists at stored path: {file_path}")
        print(f"   File size: {os.path.getsize(file_path)} bytes")
        print(f"   Readable: {os.access(file_path, os.R_OK)}")
    else:
        print(f"\n❌ File NOT found at stored path: {file_path}")
        
        # Try to find file in UPLOADS_DIR
        print(f"\n🔍 Searching for file in UPLOADS_DIR...")
        if os.path.exists(UPLOADS_DIR):
            files = os.listdir(UPLOADS_DIR)
            matching_files = [f for f in files if f.startswith(resume_id)]
            
            if matching_files:
                print(f"   Found {len(matching_files)} matching file(s):")
                for f in matching_files:
                    full_path = os.path.join(UPLOADS_DIR, f)
                    print(f"   • {f} ({os.path.getsize(full_path)} bytes)")
            else:
                print(f"   No files starting with resume ID found")
                print(f"\n   Files in UPLOADS_DIR:")
                for f in files[:10]:  # Show first 10
                    print(f"   • {f}")
                if len(files) > 10:
                    print(f"   ... and {len(files) - 10} more")
        else:
            print(f"   UPLOADS_DIR does not exist!")
    
finally:
    db.close()

print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
