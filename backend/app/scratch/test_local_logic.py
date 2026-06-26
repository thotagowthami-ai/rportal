import sys
import json
import asyncio
from typing import Dict, Any

# Mock models
class JobDescription:
    def __init__(self, data):
        self.id = data.get('id')
        self.title = data.get('title')
        self.description = data.get('description')
        self.requirements = data.get('requirements')
        self.required_skills = data.get('required_skills', [])
        self.preferred_skills = data.get('preferred_skills', [])
        self.experience_required = data.get('experience_required')
        self.location = data.get('location')

class Resume:
    def __init__(self, data):
        self.id = data.get('id')
        self.candidate_name = data.get('candidate_name')
        self.current_role = data.get('current_role')
        self.experience_years = data.get('experience_years')
        self.education = data.get('education')
        self.skills = data.get('skills', [])
        self.resume_text = data.get('resume_text', '')

def _unwrap_item(val):
    if not val: return ""
    if not isinstance(val, str): return str(val)
    val_s = val.strip()
    if val_s.startswith("{") and val_s.endswith("}"):
        try:
            parsed = json.loads(val_s)
            if isinstance(parsed, dict):
                for k in ["degree", "skill", "name", "title", "value"]:
                    if k in parsed: return str(parsed[k])
                for v in parsed.values():
                    if isinstance(v, (str, int, float)): return str(v)
            return val_s
        except Exception: return val_s
    return val_s

def _normalize_list(value):
    if isinstance(value, list):
        return [_unwrap_item(i) for i in value if i]
    if value is None:
        return []
    raw_v = str(value).strip()
    if not raw_v:
        return []
    if raw_v.startswith("{") and raw_v.endswith("}"):
        import re
        parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', raw_v[1:-1])
        return [_unwrap_item(p.strip().strip('"')) for p in parts if p.strip()]
    try:
        parsed = json.loads(raw_v)
        if isinstance(parsed, list):
            return [_unwrap_item(i) for i in parsed if i]
        return [_unwrap_item(parsed)]
    except Exception:
        if "," in raw_v:
            return [_unwrap_item(s.strip()) for s in raw_v.split(",") if s.strip()]
        return [_unwrap_item(raw_v)]
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return []
        if v.startswith("{") and v.endswith("}"):
            return [item.strip().strip('"') for item in v[1:-1].split(",") if item.strip()]
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []

# Paste the job and resume data here
job_data = {
    'title': 'Junior AI/ML Engineer (Fresher)',
    'description': 'Position: Junior AI/ML Engineer / Associate Data Scientist\nExperience Level: 0–1 Years (Freshers & Recent Graduates)\nLocation: [City, Country / Remote / Hybrid]\nDepartment: Engineering / Data Science\n\nJob Summary\nWe are seeking a highly motivated and analytical Junior AI/ML Engineer (Fresher) to join our growing Data Science team. In this role, you will work closely with senior engineers and data scientists to design, develop, and deploy machine learning models and artificial intelligence solutions. This is an entry-level position ideal for recent graduates passionate about AI, data analysis, and building intelligent systems.',
    'requirements': 'Bachelor’s or Master’s degree in Computer Science, Data Science, Statistics, Mathematics, or a related field.\nStrong programming skills in Python.\nSolid understanding of fundamental machine learning algorithms (e.g., linear regression, decision trees, clustering, neural networks).\nFamiliarity with ML frameworks and libraries such as Scikit-Learn, TensorFlow, PyTorch, or Keras.\nBasic knowledge of data manipulation and analysis tools (e.g., Pandas, NumPy, SQL).\nUnderstanding of version control systems (e.g., Git).\nExcellent problem-solving, analytical, and critical thinking skills.\nStrong written and verbal communication skills, with the ability to explain complex concepts to non-technical stakeholders.\nA portfolio of personal or academic AI/ML projects (e.g., GitHub repositories, Kaggle competitions) is highly desirable.',
    'required_skills': "[\"aws\", \"azure\", \"git\", \"python\", \"docker\"]",
    'preferred_skills': "[]",
    'experience_required': 0,
    'location': 'Remote'
}

resume_data = {
    'candidate_name': 'YOUR NAME',
    'skills': "['Python', 'SQL', 'AWS', 'Azure', 'Docker', 'Pandas', 'Numpy', 'Machine Learning', 'Git']",
    'experience_years': None,
    'education': '',
    'resume_text': ''
}

job = JobDescription(job_data)
resume = Resume(resume_data)

try:
    print("Normalizing job skills:")
    print(_normalize_list(job.required_skills))
    print("Normalizing resume skills:")
    print(_normalize_list(resume.skills))
    
    # Let's check experience score
    required_years = job.experience_required
    candidate_years = resume.experience_years
    
    if not required_years:
        exp_score = 50.0
    elif not candidate_years:
        exp_score = 0.0
    elif candidate_years >= required_years:
        exp_score = 100.0
    else:
        exp_score = (candidate_years / required_years) * 100
        
    print(f"Exp score: {exp_score}")
    
except Exception as e:
    print(f"Error: {e}")
