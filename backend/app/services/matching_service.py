from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from app.models.match import Match, MatchStatus
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.services.cache_service import cache_service
from app.utils.llm_guard import llm_guard
from anthropic import Anthropic
from app.config import settings
import logging
import httpx
import uuid
import json
import os

logger = logging.getLogger(__name__)

SKILL_SYNONYMS = {
    # Programming Languages & Frameworks
    "node.js": "nodejs",
    "express.js": "express",
    "react.js": "react",
    "reactjs": "react",
    "next.js": "nextjs",
    "vue.js": "vue",
    "angular.js": "angular",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "elastic search": "elasticsearch",
    "google cloud": "gcp",
    "amazon web services": "aws",
    "rest api": "restful",
    "rest": "restful",
    "docker.com": "docker",
    "k8s": "kubernetes",
}

def normalize_skill(skill: str) -> str:
    s = skill.lower().strip()
    return SKILL_SYNONYMS.get(s, s)



def _unwrap_item(val):
    if not val: return ""
    if not isinstance(val, str): return str(val)
    val_s = val.strip()
    if val_s.startswith("{") and val_s.endswith("}"):
        try:
            import json
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


class MatchingService:
    def __init__(self):
        self.claude_client = Anthropic(api_key=settings.CLAUDE_API_KEY) if settings.CLAUDE_API_KEY else None
        self.min_score_threshold = 0.0
        self.candidate_portal_url = getattr(
            settings,
            "CANDIDATE_PORTAL_URL",
            "http://localhost:3000/api",
        ).rstrip("/")
        # Gemini API key (same one used in TalentScout)
        self.gemini_api_key = getattr(settings, "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

    @staticmethod
    def _to_storage_list(db: Session, value) -> Any:
        dialect = (db.bind.dialect.name if db.bind is not None else "").lower()
        normalized = _normalize_list(value)
        if dialect == "postgresql":
            return normalized
        return json.dumps(normalized)

    @staticmethod
    def _clean_tenant_id(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value

    async def _fetch_from_candidate_portal(
        self, job_description: str, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        cleaned_tenant_id = self._clean_tenant_id(tenant_id)
        params = {"tenant_id": cleaned_tenant_id} if cleaned_tenant_id else None
        payload = {
            "description": job_description,
            "threshold": 0,
            "limit": 50,
        }
        if cleaned_tenant_id:
            # Keep this in body for portals that read tenant_id from JSON.
            payload["tenant_id"] = cleaned_tenant_id
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.candidate_portal_url}/match/jd",
                    params=params,
                    json=payload,
                )
                if response.status_code in (200, 201):
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        for key in ("results", "items", "resumes", "candidates", "data"):
                            value = data.get(key)
                            if isinstance(value, list):
                                return value
                    return []
                logger.warning(f"Candidate Portal returned {response.status_code}: {response.text}")
                return []
        except httpx.RequestError as e:
            logger.warning(f"Candidate Portal request failed: {e}")
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch from Candidate Portal: {e}")
            return []

    async def _fetch_portal_resumes_list(self, tenant_id: Optional[str]) -> List[Dict[str, Any]]:
        cleaned_tenant_id = self._clean_tenant_id(tenant_id)
        params = {"tenant_id": cleaned_tenant_id} if cleaned_tenant_id else None
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.candidate_portal_url}/resumes",
                    params=params,
                )
                if response.status_code in (200, 201):
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        for key in ("items", "results", "resumes", "data"):
                            value = data.get(key)
                            if isinstance(value, list):
                                return value
                    return []
                logger.warning(f"Candidate Portal resumes list returned {response.status_code}: {response.text}")
                return []
        except httpx.RequestError as e:
            logger.warning(f"Candidate Portal resume list request failed: {e}")
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch resume list from Candidate Portal: {e}")
            return []

    def _sync_candidate_to_resume(
        self,
        candidate: Dict[str, Any],
        tenant_id: str,
        uploaded_by: str,
        db: Session,
    ) -> Resume:
        skills_value = self._to_storage_list(db, candidate.get("candidateSkills", []))
        email = str(candidate.get("email") or "").strip()
        existing = None
        if email:
            existing = (
                db.query(Resume)
                .filter(
                    Resume.candidate_email == email,
                    Resume.tenant_id == tenant_id,
                )
                .first()
            )

        if existing:
            existing.skills = skills_value
            db.commit()
            db.refresh(existing)
            return existing

        resume = Resume(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            uploaded_by=uploaded_by,
            candidate_name=f"{candidate.get('firstName', '')} {candidate.get('lastName', '')}".strip(),
            candidate_email=email,
            candidate_phone="",
            file_path=f"candidate_portal/{candidate.get('candidateId', '')}",
            file_name="resume.pdf",
            file_type="application/pdf",
            resume_text="",
            skills=skills_value,
            experience_years=0,
            education="",
            current_role="",
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)
        return resume

    async def sync_portal_resumes(self, db: Session, tenant_id: str, uploaded_by: str) -> List[Resume]:
        logger.info(f"Syncing portal resumes for tenant {tenant_id}")
        portal_tenant_id = self._clean_tenant_id(
            settings.CANDIDATE_PORTAL_TENANT_ID or settings.RECRUITING_TENANT_ID or tenant_id
        )
        # Use a rich skill blob to avoid "no known skills" responses from the portal.
        portal_results = await self._fetch_from_candidate_portal(
            job_description="python, javascript, react, node, sql, aws, docker, kubernetes, devops, api",
            tenant_id=portal_tenant_id,
        )
        if not portal_results:
            # Fallback to a direct resumes list endpoint if available.
            portal_results = await self._fetch_portal_resumes_list(tenant_id=portal_tenant_id)
        resumes = []
        for candidate in portal_results:
            resume = self._sync_candidate_to_resume(
                candidate=candidate,
                tenant_id=tenant_id,
                uploaded_by=uploaded_by,
                db=db,
            )
            resumes.append(resume)
        return resumes

    async def _analyze_with_gemini(
        self,
        job: JobDescription,
        resume: Resume,
    ) -> Dict[str, Any]:
        """
        Use Gemini AI (same as TalentScout) to analyze resume vs JD
        and return match percentage + detailed breakdown.
        """
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not set, falling back to basic scoring")
            return {}

        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.gemini_api_key)

            jd_text = f"""
Title: {job.title}
Description: {job.description or ''}
Requirements: {job.requirements or ''}
Required Skills: {', '.join(_normalize_list(job.required_skills))}
Preferred Skills: {', '.join(_normalize_list(job.preferred_skills))}
Experience Required: {job.experience_required or 'Not specified'} years
Location: {job.location or 'Not specified'}
""".strip()

            resume_text = f"""
Candidate Name: {resume.candidate_name or 'Unknown'}
Current Role: {resume.current_role or 'Not specified'}
Experience: {resume.experience_years or 0} years
Education: {resume.education or 'Not specified'}
Skills: {', '.join(_normalize_list(resume.skills))}
Resume Text: {(resume.resume_text or '')[:2000]}
""".strip()

            prompt = f"""You are an expert Senior Technical Recruiter and Hiring Manager.
Analyze the provided Job Description (JD) and Candidate Resume.

JOB DESCRIPTION:
{jd_text}

CANDIDATE RESUME:
{resume_text}

Task 1: Extract skills from the JD into Required and Nice to Have.
Task 2: Evaluate the resume against these skills. Be critical but fair. Look for semantic matches (e.g., React matches React.js).
Task 3: Provide a match score (0-100), detailed gap analysis, strengths, weaknesses, and a final verdict.

Return ONLY a valid JSON object in this exact format:
{{
  "matchPercentage": <number 0-100>,
  "matchedRequired": [<list of matched required skills>],
  "missingRequired": [<list of missing required skills>],
  "matchedNiceToHave": [<list of matched preferred skills>],
  "missingNiceToHave": [<list of missing preferred skills>],
  "strengths": [<list of candidate strengths>],
  "weaknesses": [<list of candidate weaknesses>],
  "experienceGap": "<analysis of experience vs requirements>",
  "summary": "<2-3 sentence executive summary>",
  "finalVerdict": "<one of: Strong Match, Potential Match, Not a Match>"
}}"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )

            text_response = ""
            if getattr(response, "text", None):
                text_response = response.text
            else:
                try:
                    text_response = response.candidates[0].content.parts[0].text
                except Exception:
                    text_response = str(response)
            text_response = text_response.strip()

            # Strip markdown fences if present
            if text_response.startswith("```"):
                text_response = text_response.split("```")[1]
                if text_response.startswith("json"):
                    text_response = text_response[4:]
            text_response = text_response.strip()

            result = json.loads(text_response)
            logger.info(f"Gemini match score for resume {resume.id}: {result.get('matchPercentage')}%")
            return result

        except ImportError:
            logger.warning("google-genai not installed. Run: pip install google-genai")
            return {}
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return {}

    async def generate_matches_for_job(
        self,
        job_id: str,
        db: Session,
        tenant_id: str,
        limit: int = 50,
        resume_ids: Optional[List[str]] = None,
    ) -> List[Match]:
        logger.info(f"Generating matches for job {job_id}")

        job_id = job_id.strip()
        job = db.query(JobDescription).filter(
            JobDescription.id == job_id,
            JobDescription.tenant_id == tenant_id
        ).first()
        if not job:
            raise ValueError(f"Job description {job_id} not found or access denied for tenant {tenant_id}")

        local_resume_count = db.query(Resume).filter(
            Resume.tenant_id == tenant_id
        ).count()
        logger.info(f"Local resumes count: {local_resume_count}")

        if local_resume_count == 0:
            logger.info("No local resumes found, fetching from Candidate Portal...")
            portal_tenant_id = self._clean_tenant_id(
                settings.CANDIDATE_PORTAL_TENANT_ID or settings.RECRUITING_TENANT_ID or tenant_id
            )
            portal_results = await self._fetch_from_candidate_portal(
                job_description=job.description or "",
                tenant_id=portal_tenant_id,
            )
            logger.info(f"Got {len(portal_results)} candidates from Candidate Portal")

            if portal_results:
                from app.models.user import User
                admin_user = db.query(User).filter(User.tenant_id == tenant_id).first()
                uploaded_by = str(admin_user.id) if admin_user else str(uuid.uuid4())

                matches: List[Match] = []

                for candidate in portal_results:
                    resume = self._sync_candidate_to_resume(
                        candidate=candidate,
                        tenant_id=tenant_id,
                        uploaded_by=uploaded_by,
                        db=db,
                    )

                    existing_match = (
                        db.query(Match)
                        .filter(
                            and_(
                                Match.job_description_id == job_id,
                                Match.resume_id == resume.id,
                            )
                        )
                        .first()
                    )

                    if existing_match:
                        continue

                    match_score = float(candidate.get("matchScore", 0))
                    matched_skills = candidate.get("matchedSkills", [])
                    missing_skills = candidate.get("missingSkills", [])

                    match_reasoning = (
                        f"Match score: {match_score}%. "
                        f"Matched skills: {', '.join(matched_skills[:5])}. "
                        f"Missing skills: {', '.join(missing_skills[:3])}."
                    )

                    match = Match(
                        tenant_id=tenant_id,
                        job_description_id=job_id,
                        resume_id=resume.id,
                        overall_score=match_score,
                        skill_match_score=match_score,
                        experience_match_score=50.0,
                        education_match_score=50.0,
                        matched_skills=matched_skills,
                        missing_skills=missing_skills,
                        match_reasoning=match_reasoning,
                        recruiter_status=MatchStatus.NEW.name,
                    )

                    db.add(match)
                    matches.append(match)

                    if len(matches) >= limit:
                        break

                db.commit()
                logger.info(f"Created {len(matches)} matches from Candidate Portal")
                return matches

        # Local matching
        if resume_ids:
            selected_resumes = (
                db.query(Resume)
                .filter(
                    Resume.tenant_id == tenant_id,
                    Resume.id.in_(resume_ids),
                )
                .all()
            )
            resumes_to_match = selected_resumes
        else:
            # Safely get embedding as list
            job_emb = job.embedding
            if isinstance(job_emb, str):
                try:
                    job_emb = json.loads(job_emb)
                except Exception:
                    job_emb = []

            if not job_emb or len(job_emb) == 0:
                logger.warning(
                    f"Job {job_id} has no embedding. Falling back to recent resumes."
                )
                resumes_to_match = (
                    db.query(Resume)
                    .filter(Resume.tenant_id == tenant_id)
                    .order_by(Resume.created_at.desc())
                    .limit(limit * 2)
                    .all()
                )
            else:
                try:
                    similar_resumes = self._find_similar_resumes(
                        job_embedding=job_emb,
                        tenant_id=tenant_id,
                        db=db,
                        limit=limit * 2,
                    )
                    resume_ids_from_vector = [r["id"] for r in similar_resumes]
                    if resume_ids_from_vector:
                        resumes_to_match = (
                            db.query(Resume)
                            .filter(
                                Resume.tenant_id == tenant_id,
                                Resume.id.in_(resume_ids_from_vector),
                            )
                            .all()
                        )
                    else:
                        resumes_to_match = (
                            db.query(Resume)
                            .filter(Resume.tenant_id == tenant_id)
                            .order_by(Resume.created_at.desc())
                            .limit(limit * 2)
                            .all()
                        )
                except Exception as e:
                    logger.warning(f"Vector similarity unavailable, using fallback: {e}")
                    db.rollback()
                    resumes_to_match = (
                        db.query(Resume)
                        .filter(Resume.tenant_id == tenant_id)
                        .order_by(Resume.created_at.desc())
                        .limit(limit * 2)
                        .all()
                    )

        matches: List[Match] = []

        for resume in resumes_to_match:
            existing_match = (
                db.query(Match)
                .filter(
                    and_(
                        Match.job_description_id == job_id,
                        Match.resume_id == resume.id,
                    )
                )
                .first()
            )
            if existing_match:
                continue

            # ✅ Try Gemini first (same as TalentScout)
            gemini_result = await self._analyze_with_gemini(job=job, resume=resume)

            if gemini_result and "matchPercentage" in gemini_result:
                # Use Gemini scores
                overall_score = float(gemini_result["matchPercentage"])
                matched_skills = gemini_result.get("matchedRequired", []) + gemini_result.get("matchedNiceToHave", [])
                missing_skills = gemini_result.get("missingRequired", []) + gemini_result.get("missingNiceToHave", [])
                summary = gemini_result.get("summary", "")
                verdict = gemini_result.get("finalVerdict", "")
                experience_gap = gemini_result.get("experienceGap", "")

                match_reasoning = f"{summary} Verdict: {verdict}. {experience_gap}".strip()

                # Estimate sub-scores from Gemini data
                job_required = _normalize_list(job.required_skills)
                matched_required = gemini_result.get("matchedRequired", [])
                skill_match_score = (len(matched_required) / max(len(job_required), 1)) * 100

                experience_score = self._calculate_experience_score(
                    required_years=job.experience_required,
                    candidate_years=resume.experience_years,
                )

            else:
                # ✅ Fallback to basic scoring if Gemini unavailable
                logger.info(f"Falling back to basic scoring for resume {resume.id}")
                vector_score = 0.5
                scores = self._calculate_match_scores(job, resume, vector_score)
                overall_score = scores["overall_score"]
                matched_skills = scores["matched_skills"]
                missing_skills = scores["missing_skills"]
                skill_match_score = scores["skill_match_score"]
                experience_score = scores["experience_match_score"]
                match_reasoning = await self._generate_match_explanation(
                    job=job,
                    resume=resume,
                    scores=scores,
                    tenant_id=tenant_id,
                )

            if overall_score < self.min_score_threshold:
                continue

            match = Match(
                tenant_id=tenant_id,
                job_description_id=job_id,
                resume_id=resume.id,
                overall_score=round(overall_score, 2),
                skill_match_score=round(skill_match_score, 2),
                experience_match_score=round(experience_score, 2),
                education_match_score=50.0,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                match_reasoning=match_reasoning,
                recruiter_status=MatchStatus.NEW.name,
            )

            db.add(match)
            matches.append(match)

            if len(matches) >= limit:
                break

        db.commit()
        logger.info(f"Created {len(matches)} matches for job {job_id}")
        return matches

    def _find_similar_resumes(
        self,
        job_embedding: List[float],
        tenant_id: str,
        db: Session,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        if job_embedding and isinstance(job_embedding[0],list):
            job_embedding=job_embedding[0]
        embedding_str = "[" + ",".join(map(str, job_embedding)) + "]"
        query = text(
            """
            SELECT
                id,
                1 - (embedding <=> CAST(:embedding AS vector)) as similarity
            FROM resumes
            WHERE embedding IS NOT NULL
              AND tenant_id = :tenant_id
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """
        )
        result = db.execute(
            query,
            {"embedding": embedding_str, "tenant_id": tenant_id, "limit": limit},
        ).fetchall()
        return [{"id": str(row[0]), "similarity": float(row[1])} for row in result]

    def _calculate_match_scores(
        self,
        job: JobDescription,
        resume: Resume,
        vector_score: float,
    ) -> Dict[str, Any]:
        job_required = _normalize_list(job.required_skills)
        job_preferred = _normalize_list(job.preferred_skills)
        job_skills = set(skill.lower() for skill in (job_required + job_preferred))

        resume_skill_list = _normalize_list(resume.skills)
        resume_skills_raw = set(skill.lower() for skill in resume_skill_list)
        
        # Semantic skill matching using synonyms
        normalized_job_skills = {normalize_skill(s) for s in job_skills}
        normalized_resume_skills = {normalize_skill(s) for s in resume_skills_raw}

        # Calculate matches in normalized space
        matched_normalized = normalized_job_skills.intersection(normalized_resume_skills)
        
        # Map back to original job skill names for display
        matched_skills = [s for s in job_skills if normalize_skill(s) in matched_normalized]
        missing_skills = [s for s in job_skills if normalize_skill(s) not in matched_normalized]

        skill_match_score = (len(matched_skills) / len(job_skills) * 100) if job_skills else 0

        experience_score = self._calculate_experience_score(
            required_years=job.experience_required,
            candidate_years=resume.experience_years,
        )

        education_score = 50.0

        overall_score = (
            vector_score * 100 * 0.4
            + skill_match_score * 0.35
            + experience_score * 0.15
            + education_score * 0.10
        )

        return {
            "overall_score": round(overall_score, 2),
            "skill_match_score": round(skill_match_score, 2),
            "experience_match_score": round(experience_score, 2),
            "education_match_score": round(education_score, 2),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
        }

    def _calculate_experience_score(
        self,
        required_years: Optional[int],
        candidate_years: Optional[int],
    ) -> float:
        if not required_years:
            return 50.0
        if not candidate_years:
            return 0.0
        if candidate_years >= required_years:
            return 100.0
        return (candidate_years / required_years) * 100

    async def _generate_match_explanation(
        self,
        job: JobDescription,
        resume: Resume,
        scores: Dict[str, Any],
        tenant_id: str,
    ) -> Optional[str]:
        if not self.claude_client:
            return f"Match score: {scores['overall_score']}%. Matched {len(scores['matched_skills'])} skills."

        cache_key = f"match_explanation:{job.id}:{resume.id}"
        cached = cache_service.get(cache_key, tenant_id=tenant_id)
        if cached is not None:
            return cached

        try:
            def _normalize_skills_list(skills) -> list[str]:
                if not skills:
                    return []
                if isinstance(skills, list):
                    return [str(s) for s in skills if s]
                if isinstance(skills, str):
                    v = skills.strip()
                    if not v:
                        return []
                    if v.startswith("{") and v.endswith("}"):
                        return [item.strip().strip('"') for item in v[1:-1].split(",") if item.strip()]
                    if v.startswith("[") and v.endswith("]"):
                        try:
                            parsed = json.loads(v)
                            if isinstance(parsed, list):
                                return [str(s) for s in parsed if s]
                        except Exception:
                            pass
                    if "," in v:
                        return [s.strip() for s in v.split(",") if s.strip()]
                    return [v]
                return []

            normalized_job_skills = _normalize_skills_list(job.required_skills)
            normalized_resume_skills = _normalize_skills_list(resume.skills)

            is_safe_job, sanitized_job_desc = llm_guard.sanitize_user_input(job.description[:500])
            is_safe_resume, sanitized_resume_text = llm_guard.sanitize_user_input(
                resume.resume_text[:500] if resume.resume_text else ""
            )

            prompt = f"""Analyze this job-candidate match and explain why they're a good fit in 2-3 sentences.

Job: {sanitized_job_desc}
Required Skills: {', '.join(normalized_job_skills[:10])}

Candidate Resume: {sanitized_resume_text}
Candidate Skills: {', '.join(normalized_resume_skills[:10])}

Match Scores:
- Overall: {scores['overall_score']}%
- Skills: {scores['skill_match_score']}%
- Experience: {scores['experience_match_score']}%

Matched Skills: {', '.join(scores['matched_skills'][:5])}
Missing Skills: {', '.join(scores['missing_skills'][:3])}

Provide a concise explanation focusing on strengths and any concerns."""

            response = self.claude_client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )

            explanation = response.content[0].text
            is_safe_output, sanitized_explanation = llm_guard.sanitize_llm_output(explanation)

            cache_service.set(cache_key, sanitized_explanation, ttl=86400, tenant_id=tenant_id)
            return sanitized_explanation

        except Exception as e:
            logger.error(f"Failed to generate match explanation: {str(e)}")
            return f"Match score: {scores['overall_score']}%. Matched {len(scores['matched_skills'])} skills."


# Global instance
matching_service = MatchingService()
