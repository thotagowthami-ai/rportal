#!/usr/bin/env python
"""Direct migration script to add work_experience column to resumes table"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine
from sqlalchemy import text

def add_work_experience_column():
    """Add work_experience column to resumes table if it doesn't exist"""
    try:
        with engine.connect() as connection:
            # Check if column already exists
            result = connection.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='resumes' AND column_name='work_experience'
                    )
                """)
            )
            column_exists = result.scalar()
            
            if column_exists:
                print("✓ Column 'work_experience' already exists in resumes table")
                return True
            
            # Add the column
            connection.execute(
                text("ALTER TABLE resumes ADD COLUMN work_experience TEXT DEFAULT '[]'")
            )
            connection.commit()
            print("✓ Successfully added 'work_experience' column to resumes table")
            return True
            
    except Exception as e:
        print(f"✗ Error adding column: {e}")
        return False

if __name__ == "__main__":
    print("Adding work_experience column to resumes table...")
    success = add_work_experience_column()
    sys.exit(0 if success else 1)
