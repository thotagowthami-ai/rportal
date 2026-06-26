import re
import os
import shutil
import subprocess
import tempfile
from typing import Dict, Any, List, Optional
from PyPDF2 import PdfReader


COMMON_SKILLS = {
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "ruby", "go", "rust", "swift", "kotlin", "php", "scala", "perl",
    # Web Technologies
    "react", "react.js", "next.js", "nextjs", "angular", "vue", "vue.js", "jquery", "html", "css", "sass", "less",
    "bootstrap", "tailwind", "material ui", "redux", "zustand", "graphql", "rest api", "rest", "soap",
    # Backend
    "node.js", "nodejs", "express", "express.js", "django", "flask", "fastapi", "spring", "spring boot",
    "ruby on rails", "rails", "asp.net", ".net", "laravel", "symfony",
    # Databases
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "oracle", "sqlite",
    "dynamodb", "firebase", "supabase", "prisma", "sqlalchemy",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
    "git", "github", "gitlab", "bitbucket", "ci/cd", "cicd", "devops", "cloudformation",
    # Data & ML
    "machine learning", "deep learning", "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "spark",
    "hadoop", "kafka", "airflow", "nlp", "computer vision", "data science", "data engineering",
    # Other
    "agile", "scrum", "jira", "confluence", "linux", "unix", "bash", "shell", "testing", "unit testing",
    "integration testing", "tdd", "bdd", "microservices", "restful", "oop", "solid", "design patterns",
    "leadership", "communication", "problem solving", "teamwork", "project management",
}

ROLE_KEYWORDS = (
    "engineer", "developer", "architect", "manager", "analyst", "scientist", "consultant",
    "designer", "specialist", "administrator", "lead", "intern", "associate", "executive",
    "director", "principal", "senior", "junior", "staff", "head", "vp", "vice president",
)

EDUCATION_KEYWORDS = (
    "bachelor", "master", "phd", "ph.d", "doctorate", "degree", "bsc", "msc", "b.tech",
    "m.tech", "b.e", "m.e", "bca", "mca", "ba", "ma", "b.com", "m.com", "diploma",
    "computer science", "information technology", "it", "software engineering",
)

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


def sanitize_filename(filename: str) -> str:
    if not filename or not isinstance(filename, str):
        return "resume.pdf"
    # Extract only the base name to strip any directory traversal
    base = os.path.basename(filename)
    # Remove ASCII control characters (\x00-\x1F and \x7F)
    base = re.sub(r'[\x00-\x1f\x7f]', '', base)
    # Replace illegal filesystem characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', base).strip()
    # Drop any leading dots (hidden file prevention)
    cleaned = cleaned.lstrip('.')
    return cleaned or "resume.pdf"


def validate_file(
    filename: str,
    file_size: Optional[int] = None,
    file_bytes: Optional[bytes] = None,
) -> tuple[bool, str]:
    if not filename or not isinstance(filename, str):
        return False, "Invalid file name"
    filename_lower = filename.lower()
    file_ext = filename_lower.rsplit(".", 1)[-1] if "." in filename_lower else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type: .{file_ext}"

    if file_ext == "doc" and not is_doc_conversion_available():
        return (
            False,
            "Legacy .doc files require LibreOffice installed on the server. Please upload .docx or PDF, or install LibreOffice and ensure 'soffice' is in PATH.",
        )

    size = file_size
    if size is None and file_bytes is not None:
        size = len(file_bytes)

    if size is not None:
        if size == 0:
            return False, "Uploaded file is empty"
        if size > MAX_UPLOAD_SIZE:
            return False, f"File too large. Max size: {MAX_UPLOAD_SIZE // (1024 * 1024)}MB"

    return True, ""


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        from io import BytesIO

        reader = PdfReader(BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"PDF extraction failed: {e}")
        return ""


def _extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document
        from io import BytesIO

        doc = Document(BytesIO(file_bytes))
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        return "\n".join(text_parts)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"DOCX extraction failed: {e}")
        return ""


def is_doc_conversion_available() -> bool:
    return bool(shutil.which("soffice") or shutil.which("libreoffice"))


def _extract_text_from_doc(file_bytes: bytes) -> str:
    try:
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            raise RuntimeError("LibreOffice not found in PATH")

        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = os.path.join(tmpdir, "input.doc")
            with open(doc_path, "wb") as f:
                f.write(file_bytes)

            subprocess.run(
                [soffice, "--headless", "--convert-to", "docx", "--outdir", tmpdir, doc_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )

            docx_path = os.path.splitext(doc_path)[0] + ".docx"
            if not os.path.exists(docx_path):
                for name in os.listdir(tmpdir):
                    if name.lower().endswith(".docx"):
                        docx_path = os.path.join(tmpdir, name)
                        break

            if not os.path.exists(docx_path):
                return ""

            with open(docx_path, "rb") as f:
                docx_bytes = f.read()
            return _extract_text_from_docx(docx_bytes)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"DOC extraction failed: {e}")
        return ""


def extract_resume_text(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Extract raw text from resume based on content type / extension.
    """
    content_type = (content_type or "").lower()
    filename_lower = filename.lower()

    # Prefer content_type when available
    if "pdf" in content_type or filename_lower.endswith(".pdf"):
        return _extract_text_from_pdf(file_bytes)

    # DOCX
    if (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in content_type
        or filename_lower.endswith(".docx")
    ):
        return _extract_text_from_docx(file_bytes)

    # DOC (fallback to DOCX parser, many libs handle both)
    if "msword" in content_type or filename_lower.endswith(".doc"):
        return _extract_text_from_doc(file_bytes)

    # Fallback: try PDF then DOCX
    text = _extract_text_from_pdf(file_bytes)
    if text:
        return text
    return _extract_text_from_docx(file_bytes)


def _extract_email(text: str) -> str:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    match = re.search(r"(\+?\d[\d\s().-]{7,}\d)", text)
    return match.group(0).strip() if match else ""


def _extract_experience_years(text: str) -> int:
    """
    Improved extraction of experience years from resume text.
    Combines explicit mentions (e.g. "5 years experience") with 
    calculations from date ranges (e.g. "2018 - Present").
    """
    total_years = 0
    
    # Pattern 1: Explicit mentions like "5+ years of experience"
    explicit_patterns = [
        r"(\d{1,2})\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)",
        r"experience[:\s]*(\d{1,2})\+?\s*(?:years?|yrs?)",
        r"(\d{1,2})\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:professional|work|industry)",
    ]
    
    found_explicit = 0
    for pattern in explicit_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            found_explicit = max(found_explicit, int(match.group(1)))
    
    # Pattern 2: Calculating from date ranges like "2018 - 2023" or "Jan 2015 - Present"
    # Collect intervals then merge overlaps to avoid double-counting.
    import datetime
    current_year = datetime.datetime.now().year

    # Match years like 2010 - 2015, or 2018 to Present
    date_range_pattern = r"(?:19|20)\d{2}\s*[-–—to]+\s*(?:(?:19|20)\d{2}|present|current|now)"
    ranges = re.findall(date_range_pattern, text, re.IGNORECASE)

    intervals: list[tuple[int, int]] = []
    for r in ranges:
        parts = re.split(r"[-–—to]+", r, flags=re.IGNORECASE)
        if len(parts) != 2:
            continue
        try:
            start_match = re.search(r"((?:19|20)\d{2})", parts[0])
            if not start_match:
                continue
            start_year = int(start_match.group(1))

            if any(kw in parts[1].lower() for kw in ["present", "current", "now"]):
                end_year = current_year
            else:
                end_match = re.search(r"((?:19|20)\d{2})", parts[1])
                if not end_match:
                    continue
                end_year = int(end_match.group(1))

            if end_year >= start_year:
                intervals.append((start_year, end_year))
        except (ValueError, TypeError):
            continue

    # Merge overlapping / contiguous intervals before summing
    calculated_years = 0
    if intervals:
        intervals.sort()
        merged_start, merged_end = intervals[0]
        for s, e in intervals[1:]:
            if s <= merged_end:          # overlapping or contiguous
                merged_end = max(merged_end, e)
            else:
                calculated_years += merged_end - merged_start
                merged_start, merged_end = s, e
        calculated_years += merged_end - merged_start

    # Use the larger of found explicit or calculated from ranges
    total_years = max(found_explicit, calculated_years)
    
    # Sanity check: cap at 45 years
    return min(45, total_years) if total_years > 0 else 0


def _extract_skills(text: str) -> List[str]:
    found_skills = set()
    text_lower = text.lower()

    # Method 1: look for skills/technologies/tools line
    for line in text.splitlines():
        line_lower = line.lower()
        if "skill" in line_lower or "technologies" in line_lower or "tools" in line_lower:
            parts = re.split(r"[:\-•|]", line, maxsplit=1)
            if len(parts) > 1:
                skills_text = parts[1]
                for skill in re.split(r"[,;/|&\n]", skills_text):
                    skill = skill.strip().strip("•*- ")
                    if skill and 1 < len(skill) < 40:
                        found_skills.add(skill)

    # Method 2: scan entire text for known skills
    for skill in COMMON_SKILLS:
        if re.search(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", text_lower):
            skill_normalized = skill
            if skill == "nextjs":
                skill_normalized = "Next.js"
            elif skill == "nodejs":
                skill_normalized = "Node.js"
            elif skill == "react.js":
                skill_normalized = "React"
            elif skill == "vue.js":
                skill_normalized = "Vue.js"
            elif skill == "express.js":
                skill_normalized = "Express"
            found_skills.add(skill_normalized)

    return sorted(list(found_skills))[:30]


def _extract_education(text: str) -> str:
    lines = text.splitlines()
    
    # More strict - look for education section specifically
    education_keywords = [
        "bachelor", "master", "phd", "ph.d", "doctorate", "degree in",
        "b.sc", "m.sc", "b.tech", "m.tech", "b.e", "m.e", "bca", "mca",
        "ba", "ma", "b.com", "m.com", "diploma in",
        "computer science", "information technology", "software engineering",
        "university of", "college of", "institute of"
    ]
    
    for line in lines:
        line_lower = line.lower()
        # Must contain education-related keywords, not just any keyword
        has_education_keyword = any(kw in line_lower for kw in education_keywords)
        
        # Skip if it looks like contact info
        if "@" in line or "phone" in line_lower or "mobile" in line_lower:
            continue
        if "http://" in line or "https://" in line:
            continue
        # Skip if line has digits that look like phone numbers
        if re.search(r'\d{10,}', line):
            continue
            
        if has_education_keyword and 10 < len(line.strip()) < 150:
            return re.sub(r"\s+", " ", line).strip()
    
    # Try regex pattern for education section
    education_match = re.search(
        r"(?:education|academic|qualification|degree)[:\s]*([^\n]{10,120})",
        text,
        re.IGNORECASE,
    )
    if education_match:
        result = education_match.group(1).strip()
        # Double check the result doesn't have contact info
        if "@" not in result and "phone" not in result.lower():
            return result
    
    return ""


def _is_plausible_role(value: str) -> bool:
    candidate = re.sub(r"\s+", " ", value or "").strip(" -:\t\r\n")
    if len(candidate) < 3 or len(candidate) > 80:
        return False

    lower = candidate.lower()
    blocked_tokens = ("http", "www.", "@", ".com", ".org", ".net", "select ", " from ", "insert ", "update ")
    if any(token in lower for token in blocked_tokens):
        return False
    if "_" in candidate:
        return False
    if not any(ch.isalpha() for ch in candidate):
        return False
    if not any(keyword in lower for keyword in ROLE_KEYWORDS):
        return False
    return True


def _extract_current_role(text: str) -> str:
    lines = text.splitlines()

    # Look in summary/objective section near top
    for i, line in enumerate(lines[:10]):
        line_lower = line.lower()
        if any(kw in line_lower for kw in ["summary", "objective", "profile", "about"]):
            for j in range(i + 1, min(i + 4, len(lines))):
                candidate = lines[j].strip()
                if candidate and _is_plausible_role(candidate):
                    return candidate

    role_patterns = [
        r"(?:as a |as |working as |role[:\s]*)([A-Za-z\s]+(?:engineer|developer|manager|analyst|designer|consultant|specialist|lead|architect))",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\s+(?:Engineer|Developer|Manager|Analyst|Designer|Consultant|Specialist|Lead|Architect|Intern))",
    ]

    for pattern in role_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            role = match.group(1).strip()
            if _is_plausible_role(role):
                return role

    for line in lines[:15]:
        if _is_plausible_role(line):
            return line.strip()

    return ""


def _extract_work_experience(text: str) -> List[Dict[str, str]]:
    """Extract work experience entries from resume text."""
    experiences = []
    lines = text.splitlines()
    
    # Look for "Experience" or "Work Experience" section
    exp_section_start = -1
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        # Accept if "experience" alone or with other qualifiers, or standard career/work history headings
        if "experience" in line_lower or "employment history" in line_lower or "work history" in line_lower:
            exp_section_start = i + 1
            break
    
    if exp_section_start == -1:
        return []
    
    # Extract experience entries (usually formatted as company, role, dates)
    i = exp_section_start
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        
        # Skip empty lines and section headers
        if not line or any(keyword in line.lower() for keyword in ["education", "skills", "project", "certification", "summary", "objective"]):
            if "education" in line.lower() or "skills" in line.lower():
                break
            continue
        
        # Try to extract company name, role, and duration
        company = ""
        role = ""
        duration = ""
        
        # Look for patterns like "Company Name | Role Title | Date Range"
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                company = parts[0]
                role = parts[1]
                if len(parts) >= 3:
                    duration = parts[2]
        elif "-" in line and any(char.isdigit() for char in line):
            # Date range pattern
            if re.search(r"\d{4}|present|current", line, re.IGNORECASE):
                # This might be a date line, look at previous line for role/company
                if experiences and not experiences[-1].get("duration"):
                    experiences[-1]["duration"] = line
                    continue
        
        # Try to find role keywords
        if any(keyword in line.lower() for keyword in ["engineer", "developer", "manager", "analyst", "architect", "designer", "specialist", "lead"]):
            # This line likely contains role information
            if not company and not role:
                role = line
            elif company and not role:
                role = line
        
        if company or role:
            experiences.append({
                "company": company,
                "role": role,
                "duration": duration
            })
    
    return experiences[:10]  # Limit to 10 entries


def parse_resume_text(text: str) -> Dict[str, Any]:
    return {
        "candidate_email": _extract_email(text),
        "candidate_phone": _extract_phone(text),
        "skills": _extract_skills(text),
        "experience_years": _extract_experience_years(text),
        "education": _extract_education(text),
        "current_role": _extract_current_role(text),
        "work_experience": _extract_work_experience(text),
    }
