import sqlite3
import os
import re
from pathlib import Path

# Connect to database
db_path = "test.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all resume file_paths from database
cursor.execute("SELECT file_path, file_name, id FROM resumes WHERE deleted_at IS NULL")
db_resumes = cursor.fetchall()
conn.close()

print(f"✓ Total resume records in database: {len(db_resumes)}")
print("\nFiles in database:")

# Extract file IDs from db file_paths (assuming format: uploads/{uuid}_{filename})
db_file_ids = set()
for file_path, file_name, resume_id in db_resumes:
    # file_path is like "uploads/033f621c-88e7-44ed-a70a-0d0d9e005d09_Varshasoni_Go.pdf"
    if file_path:
        parts = file_path.split('/')
        if len(parts) > 0:
            filename = parts[-1]
            # Extract UUID (first 36 chars)
            if len(filename) >= 36:
                uuid_part = filename[:36]
                db_file_ids.add(uuid_part)
                print(f"  {uuid_part} -> {file_path}")

# List all files on disk
uploads_dir = "uploads"
disk_file_ids = set()
disk_files = {}

for file in os.listdir(uploads_dir):
    file_path = os.path.join(uploads_dir, file)
    if os.path.isfile(file_path):
        # Extract UUID (first 36 chars of filename)
        if len(file) >= 36:
            uuid_part = file[:36]
            disk_file_ids.add(uuid_part)
            disk_files[uuid_part] = file

print(f"\n✓ Total files on disk: {len(disk_file_ids)}")

# Find orphaned files (on disk but not in database)
orphaned_ids = disk_file_ids - db_file_ids
print(f"\n⚠ Orphaned files (on disk but NOT in database): {len(orphaned_ids)}")

if orphaned_ids:
    print("\nOrphaned files:")
    for uuid_id in sorted(orphaned_ids):
        filename = disk_files[uuid_id]
        print(f"  {uuid_id} -> {filename}")

# Find missing files (in database but not on disk)
missing_ids = db_file_ids - disk_file_ids
print(f"\n⚠ Missing files (in database but NOT on disk): {len(missing_ids)}")

if missing_ids:
    print("\nMissing files:")
    for uuid_id in sorted(missing_ids):
        print(f"  {uuid_id}")

print(f"\n" + "="*70)
print(f"SUMMARY:")
print(f"  Files on disk:           {len(disk_file_ids)}")
print(f"  Resume records in DB:    {len(db_file_ids)}")
print(f"  Orphaned (disk only):    {len(orphaned_ids)}")
print(f"  Missing (DB only):       {len(missing_ids)}")
print(f"="*70)
