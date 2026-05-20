#!/usr/bin/env python
"""Quick script to run Alembic migrations"""
import subprocess
import sys

try:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd="C:\\Users\\GOWTHAMI\\Downloads\\projects\\recruiting-platform\\backend"
    )
    sys.exit(result.returncode)
except Exception as e:
    print(f"Error running migration: {e}")
    sys.exit(1)
