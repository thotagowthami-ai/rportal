import sys
import logging
from app.database import SessionLocal
from app.models.match import Match
from app.models.resume import Resume
from app.models.job_description import JobDescription

db = SessionLocal()
jobs = db.query(JobDescription).all()
print(f"Jobs in DB: {len(jobs)}")
if jobs:
    print(f"First Job ID: {jobs[0].id}")

resumes = db.query(Resume).all()
print(f"Resumes in DB: {len(resumes)}")

matches = db.query(Match).all()
print(f"Matches in DB: {len(matches)}")
