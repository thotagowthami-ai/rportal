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
import hashlib

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
        portal_url = getattr(settings, "CANDIDATE_PORTAL_URL", None) or "https://candidateportal-production.up.railway.app/api"
        self.candidate_portal_url = portal_url.rstrip("/")
        # Gemini API key (same one used in TalentScout)
        self.gemini_api_key = getattr(settings, "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

    @staticmethod
    def _portal_headers(request_token: Optional[str] = None) -> Dict[str, str]:
        api_key = str(
            os.environ.get("CANDIDATE_PORTAL_API_KEY", "")
            or getattr(settings, "CANDIDATE_PORTAL_API_KEY", "")
        ).strip().strip("\"'")

        # Read the deployed environment directly first. This also works when
        # the Settings model has not declared CANDIDATE_PORTAL_API_TOKEN.
        token = str(
            os.environ.get("CANDIDATE_PORTAL_API_TOKEN", "")
            or getattr(settings, "CANDIDATE_PORTAL_API_TOKEN", "")
        ).strip()

        # Be tolerant of common Railway variable paste formats.
        if token.startswith("CANDIDATE_PORTAL_API_TOKEN="):
            token = token.split("=", 1)[1].strip()
        token = token.strip("\"'")
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        headers = {"Accept": "application/json"}
        
        active_token = request_token or token
        if active_token:
            if active_token.lower().startswith("bearer "):
                active_token = active_token[7:].strip()
            fingerprint = hashlib.sha256(active_token.encode("utf-8")).hexdigest()[:8]
            logger.info("Candidate Portal authorization configured (token fingerprint=%s)", fingerprint)
            headers["Authorization"] = f"Bearer {active_token}"
            return headers

        if api_key:
            headers["x-api-key"] = api_key
            fingerprint = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:8]
            logger.info(
                "Candidate Portal API-key authorization configured (fingerprint=%s)",
                fingerprint,
            )
            return headers

        logger.warning(
            "Candidate Portal authentication is not configured; set CANDIDATE_PORTAL_API_KEY"
        )
        return headers

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
        self, job_description: str, tenant_id: Optional[str] = None, token: Optional[str] = None
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
                    headers=self._portal_headers(token),
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

    async def _fetch_portal_resumes_list(self, tenant_id: Optional[str], token: Optional[str] = None) -> List[Dict[str, Any]]:
        cleaned_tenant_id = self._clean_tenant_id(tenant_id)
        params = {"tenant_id": cleaned_tenant_id} if cleaned_tenant_id else None
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.candidate_portal_url}/resumes",
                    params=params,
                    headers=self._portal_headers(token),
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
            from datetime import datetime
            existing.updated_at = datetime.utcnow() # Force update to trigger re-match
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
        return resume

    async def sync_portal_resumes(self, db: Session, tenant_id: str, uploaded_by: str, job: Optional[JobDescription] = None, token: Optional[str] = None) -> List[Resume]:
        logger.info(f"Syncing portal resumes for tenant {tenant_id}")
        portal_tenant_id = self._clean_tenant_id(
            settings.CANDIDATE_PORTAL_TENANT_ID or settings.RECRUITING_TENANT_ID or tenant_id
        )
        
        # Always fetch the full list of resumes directly to ensure no candidates are missed
        portal_results = await self._fetch_portal_resumes_list(tenant_id=portal_tenant_id, token=token)
        
        if not portal_results:
            logger.info("Direct resume list failed or empty, falling back to rich skill blob match...")
            
            # Use the actual job skills if available, otherwise a very broad fallback
            fallback_query = "python, javascript, react, node, sql, aws, docker, kubernetes, devops, api"
            if job:
                job_skills = _normalize_list(job.required_skills) + _normalize_list(job.preferred_skills)
                if job_skills:
                    fallback_query = ", ".join(job_skills)
                elif job.title:
                    fallback_query = job.title

            portal_results = await self._fetch_from_candidate_portal(
                job_description=fallback_query,
                tenant_id=portal_tenant_id,
                token=token,
            )

        resumes = []
        for candidate in portal_results:
            resume = self._sync_candidate_to_resume(
                candidate=candidate,
                tenant_id=tenant_id,
                uploaded_by=uploaded_by,
                db=db,
            )
            resumes.append(resume)
        
        try:
            db.commit()
            for resume in resumes:
                db.refresh(resume)
        except Exception:
            db.rollback()
            raise
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
                model=settings.GEMINI_MODEL or "gemini-2.0-flash",
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

        except ImportError as e:
            logger.warning(f"google-genai not installed: {e}. Run: pip install google-genai")
            return {}
        except Exception as e:
            logger.error(f"Gemini analysis failed for resume {resume.id}: {type(e).__name__}: {e}", exc_info=True)
            return {}

    def _get_allowed_tenant_ids(self, tenant_id: str) -> List[str]:
        tenant_ids = [tenant_id]
        portal_tid = str(settings.CANDIDATE_PORTAL_TENANT_ID or settings.RECRUITING_TENANT_ID or "").strip()
        if portal_tid and portal_tid != tenant_id:
            tenant_ids.append(portal_tid)
        return tenant_ids

    async def generate_matches_for_job(
        self,
        job_id: str,
        db: Session,
        tenant_id: str,
        limit: int = 50,
        resume_ids: Optional[List[str]] = None,
        token: Optional[str] = None,
    ) -> List[Match]:
        logger.info(f"Generating matches for job {job_id}")

        job_id = job_id.strip()
        job = db.query(JobDescription).filter(
            JobDescription.id == job_id,
            JobDescription.tenant_id == tenant_id
        ).first()
        if not job:
            raise ValueError(f"Job description {job_id} not found or access denied for tenant {tenant_id}")

        allowed_tenant_ids = self._get_allowed_tenant_ids(tenant_id)

        local_resume_count = db.query(Resume).filter(
            Resume.tenant_id.in_(allowed_tenant_ids)
        ).count()
        logger.info(f"Local resumes count: {local_resume_count}")

        # Always try to sync from candidate portal before matching
        try:
            logger.info("Syncing latest resumes from Candidate Portal before matching...")
            from app.models.user import User
            admin_user = db.query(User).filter(User.tenant_id == tenant_id).first()
            uploaded_by = str(admin_user.id) if admin_user else str(uuid.uuid4())
            import asyncio; asyncio.create_task(self.sync_portal_resumes(db, tenant_id, uploaded_by, job, token))
        except Exception as e:
            logger.warning(f"Failed to auto-sync resumes before matching: {type(e).__name__}: {e}")

        # Local matching
        if resume_ids:
            selected_resumes = (
                db.query(Resume)
                .filter(
                    Resume.tenant_id.in_(allowed_tenant_ids),
                    Resume.id.in_(resume_ids),
                )
                .all()
            )
            if not selected_resumes:
                raise ValueError(f"No resumes found for given IDs in allowed tenants. resume_ids: {resume_ids}, allowed: {allowed_tenant_ids}")
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
                    .filter(Resume.tenant_id.in_(allowed_tenant_ids))
                    .order_by(Resume.created_at.desc())
                    .limit(limit)
                    .all()
                )
            else:
                try:
                    similar_resumes = self._find_similar_resumes(
                        job_embedding=job_emb,
                        tenant_id=tenant_id,
                        db=db,
                        limit=10000,
                    )
                    resume_ids_from_vector = [r["id"] for r in similar_resumes]
                    if resume_ids_from_vector:
                        vector_resumes = (
                            db.query(Resume)
                            .filter(
                                Resume.tenant_id.in_(allowed_tenant_ids),
                                Resume.id.in_(resume_ids_from_vector),
                            )
                            .all()
                        )
                        recent_resumes = (
                            db.query(Resume)
                            .filter(Resume.tenant_id.in_(allowed_tenant_ids))
                            .order_by(Resume.created_at.desc())
                            .limit(limit)
                            .all()
                        )
                        # Combine and deduplicate
                        resumes_dict = {r.id: r for r in vector_resumes}
                        for r in recent_resumes:
                            resumes_dict[r.id] = r
                        resumes_to_match = list(resumes_dict.values())
                    else:
                        resumes_to_match = (
                            db.query(Resume)
                            .filter(Resume.tenant_id.in_(allowed_tenant_ids))
                            .order_by(Resume.created_at.desc())
                            .limit(limit)
                            .all()
                        )
                except Exception as e:
                    logger.warning(f"Vector similarity unavailable, using fallback: {e}")
                    db.rollback()
                    resumes_to_match = (
                        db.query(Resume)
                        .filter(Resume.tenant_id.in_(allowed_tenant_ids))
                        .order_by(Resume.created_at.desc())
                        .limit(limit)
                        .all()
                    )

        # Fetch all existing matches for this job to avoid N+1 queries and to sort priorities
        existing_matches_list = (
            db.query(Match)
            .filter(Match.job_description_id == job_id)
            .all()
        )
        existing_matches = {m.resume_id: m for m in existing_matches_list}

        # Sort resumes to prioritize ones without a match first, then ones needing an update
        def get_priority(r):
            em = existing_matches.get(r.id)
            if not em:
                return 0 # No match yet: highest priority
            if job.updated_at and em.updated_at and em.updated_at < job.updated_at:
                return 1 # Outdated match: medium priority
            if r.updated_at and em.updated_at and em.updated_at < r.updated_at:
                return 1 # Outdated match due to resume update
            return 2 # Up-to-date match: lowest priority

        resumes_to_match.sort(key=get_priority)

        new_generations = 0
        matches: List[Match] = []
        errors: List[str] = []

        for resume in resumes_to_match:
            try:
                existing_match = existing_matches.get(resume.id)
                
                if existing_match:
                    job_newer = job.updated_at and existing_match.updated_at and existing_match.updated_at < job.updated_at
                    resume_newer = resume.updated_at and existing_match.updated_at and existing_match.updated_at < resume.updated_at
                    
                    # Only skip regeneration if up-to-date AND we aren't explicitly forcing it with selected resume_ids
                    if not job_newer and not resume_newer and not resume_ids:
                        matches.append(existing_match)
                        continue

                # If we've reached the generation limit, skip analyzing any MORE new/outdated resumes in this run.
                # But continue looping so we can collect all the up-to-date existing matches.
                if new_generations >= limit and not resume_ids:
                    continue

                if existing_match:
                    match = existing_match
                else:
                    match = Match(
                        tenant_id=tenant_id,
                        job_description_id=job_id,
                        resume_id=resume.id,
                        recruiter_status=MatchStatus.NEW.name,
                    )
                    db.add(match)

                # ✅ Try Gemini first (same as TalentScout)
                gemini_result = await self._analyze_with_gemini(job=job, resume=resume)
                new_generations += 1

                if gemini_result and "matchPercentage" in gemini_result:
                    # Use Gemini scores
                    try:
                        raw_score = gemini_result.get("matchPercentage", 0)
                        if raw_score in (None, "", "N/A", "null"):
                            overall_score = 0.0
                        else:
                            overall_score = float(raw_score)
                    except Exception as e:
                        logger.warning(f"Failed to parse matchPercentage from Gemini: {raw_score}. Error: {e}")
                        overall_score = 0.0

                    matched_req = gemini_result.get("matchedRequired") or []
                    matched_nice = gemini_result.get("matchedNiceToHave") or []
                    missing_req = gemini_result.get("missingRequired") or []
                    missing_nice = gemini_result.get("missingNiceToHave") or []

                    matched_skills = matched_req + matched_nice
                    missing_skills = missing_req + missing_nice
                    summary = gemini_result.get("summary", "")
                    verdict = gemini_result.get("finalVerdict", "")
                    experience_gap = gemini_result.get("experienceGap", "")

                    match_reasoning = f"{summary} Verdict: {verdict}. {experience_gap}".strip()

                    # Estimate sub-scores from Gemini data
                    job_required = _normalize_list(job.required_skills)
                    matched_required = gemini_result.get("matchedRequired") or []
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

                cache_key = f"match_explanation:{job_id}:{resume.id}"
                cache_service.delete(cache_key, tenant_id=tenant_id)

                # Only filter out low scores if we are bulk-generating. If explicitly requested, keep it.
                if overall_score < self.min_score_threshold and not resume_ids:
                    logger.debug(f"Match score {overall_score} below threshold {self.min_score_threshold} for resume {resume.id}")
                    continue

                match.overall_score = round(overall_score, 2)
                match.skill_match_score = round(skill_match_score, 2)
                match.experience_match_score = round(experience_score, 2)
                match.education_match_score = 50.0
                match.matched_skills = matched_skills
                match.missing_skills = missing_skills
                match.match_reasoning = match_reasoning

                if not existing_match:
                    matches.append(match)
                else:
                    matches.append(match) # Also append updated matches so they are returned
                    
            except Exception as e:
                import traceback
                logger.error(f"Error processing resume {resume.id} for job {job_id}:\n{traceback.format_exc()}")
                errors.append(f"Resume {resume.id}: {type(e).__name__}: {str(e)}")
                continue

        if not matches and resumes_to_match:
            raise ValueError(f"Match generation returned empty list! Errors: {errors}. resumes_to_match length: {len(resumes_to_match)}")

        try:
            db.commit()
        except Exception as e:
            logger.error(f"Failed to commit matches to database: {type(e).__name__}: {e}", exc_info=True)
            db.rollback()
            raise
        
        logger.info(f"Successfully generated {len(matches)} matches for job {job_id}")
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
        
        allowed_tenant_ids = self._get_allowed_tenant_ids(tenant_id)
        if not allowed_tenant_ids:
            return []
            
        in_clause = ",".join([f"'{tid}'" for tid in allowed_tenant_ids])

        query = text(
            f"""
            SELECT id, 1 - (embedding <=> :embedding) AS similarity
            FROM resumes
            WHERE tenant_id IN ({in_clause})
            AND embedding IS NOT NULL
            ORDER BY embedding <=> :embedding
            LIMIT :limit
            """
        )
        result = db.execute(
            query,
            {"embedding": embedding_str, "limit": limit},
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
            resume_text=resume.resume_text,
        )

        education_score = self._calculate_education_score(
            required_education=job.education_required,
            candidate_education=resume.education,
        )

        # Rebalanced weights to favor skills
        # Vector: 25%, Skills: 45%, Experience: 20%, Education: 10%
        raw_overall_score = (
            vector_score * 100 * 0.25
            + skill_match_score * 0.45
            + experience_score * 0.20
            + education_score * 0.10
        )

        # Normalization / Boost logic
        # Map a raw score of 60%+ to 85%+
        if raw_overall_score >= 60.0:
            overall_score = 85.0 + ((raw_overall_score - 60.0) / 40.0) * 15.0
            overall_score = min(100.0, overall_score)
        else:
            overall_score = raw_overall_score

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
        resume_text: Optional[str] = None,
    ) -> float:
        if not required_years:
            return 50.0

        # Fallback to regex extraction if candidate_years is missing/0
        if not candidate_years and resume_text:
            import re
            match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)", resume_text, re.IGNORECASE)
            if match:
                try:
                    candidate_years = int(match.group(1))
                except ValueError:
                    pass

        if not candidate_years:
            return 0.0

        if candidate_years >= required_years:
            return 100.0
        return (candidate_years / required_years) * 100

    def _calculate_education_score(
        self,
        required_education: Optional[str],
        candidate_education: Optional[str],
    ) -> float:
        if not required_education:
            return 50.0 # Neutral if no requirement
            
        if not candidate_education:
            return 0.0
            
        def get_education_level(text: str) -> int:
            text = text.lower()
            if "phd" in text or "ph.d" in text or "doctorate" in text:
                return 4
            if "master" in text or "m.tech" in text or "m.sc" in text or "m.e" in text or "mca" in text or "m.com" in text:
                return 3
            if "bachelor" in text or "b.tech" in text or "b.sc" in text or "b.e" in text or "bca" in text or "b.com" in text or "degree" in text:
                return 2
            if "diploma" in text:
                return 1
            return 0
            
        req_level = get_education_level(required_education)
        cand_level = get_education_level(candidate_education)
        
        # If we couldn't parse the requirement, we can't properly score it
        if req_level == 0:
            # Fallback to simple keyword match
            if required_education.lower() in candidate_education.lower():
                return 100.0
            return 50.0
            
        if cand_level >= req_level:
            return 100.0
            
        # Partial credit for being 1 level below
        if cand_level == req_level - 1:
            return 50.0
            
        return 0.0

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
