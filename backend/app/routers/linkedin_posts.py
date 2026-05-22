import json
import re
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.config import settings
from app.models.user import User


from app.utils.llm_guard import llm_guard

router = APIRouter(prefix="/linkedin-posts", tags=["linkedin-posts"])


GEMINI_SYSTEM_PROMPT = """
You are an AI that turns ANY kind of hiring input into a SHORT, high-converting LinkedIn post.

Input can be:
- A clean job description
- Messy bullets
- Notes from a call
- Just a role + a few details

Your job:
- Infer missing structure
- Never ask for a specific format
- Always output a finished LinkedIn post

STYLE:
- Hook-first, human, founder-ish
- Short lines with frequent breaks
- Professional with slight edge
- 90-180 words

STRUCTURE:
- 1-2 line hook with role + why it matters
- 3-6 short lines about impact, stack, and who this is for
- 3-5 concise bullet points
- Clear CTA at the end

RULES:
- Do NOT ask follow-up questions
- Do NOT mention the input format
- Use **double asterisks** around section headers like Tech stack and What you'll do
- Return valid JSON only in this shape:
{
  "post": "string",
  "rating": 0,
  "feedback": ["string", "string"]
}
- rating must be an integer between 0 and 100.
- If rating is below 90, improve the post and only return the improved version with rating >= 90.
""".strip()

OPENAI_SYSTEM_PROMPT = """
You are an AI that turns any hiring input into a high-converting LinkedIn job post.

Requirements:
- Hook-first style
- 90-180 words
- 3-5 bullet points
- Clear CTA at the end
- Professional, concise, and readable
- Use **double asterisks** around section headers like Tech stack and What you'll do

Return valid JSON only in this shape:
{
  "post": "string",
  "rating": 0,
  "feedback": ["string", "string"]
}

Rules:
- rating must be an integer between 0 and 100
- if rating is below 90, rewrite and return only an improved post with rating >= 90
""".strip()


class GeneratePostRequest(BaseModel):
    input: str = Field(..., min_length=1)
    tone: str = Field(default="professional", min_length=1, max_length=60)
    model: str = Field(default="gemini", pattern="^(gemini|openai|deepseek)$")


class GeneratePostResponse(BaseModel):
    post: str
    rating: int
    feedback: list[str]
    source: str


def _clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, value))


def _get_word_count(text: str) -> int:
    return len([word for word in text.strip().split() if word])


def _has_cta(text: str) -> bool:
    return bool(re.search(r"(apply|dm|message|reach out|comment|share your profile|send your resume)", text, re.IGNORECASE))


def _has_bullets(text: str) -> bool:
    return bool(re.search(r"(^|\n)\s*(?:[-*•]\s+|\d+[.)]\s+)", text, re.MULTILINE))


def _has_hook(text: str) -> bool:
    first_two_lines = " ".join(text.split("\n")[:2]).strip()
    return bool(
        re.search(
            r"(hiring|hiring for|join us|we're hiring|role|opportunity|looking for)",
            first_two_lines,
            re.IGNORECASE,
        )
    )


def _score_post(post: str) -> tuple[int, list[str]]:
    feedback: list[str] = []
    score = 55

    words = _get_word_count(post)
    if 90 <= words <= 180:
        score += 12
    elif 70 <= words <= 220:
        score += 6
        feedback.append("Tighten the length to 90-180 words for better readability.")
    else:
        feedback.append("Post length is off-target; aim for 90-180 words.")

    if _has_hook(post):
        score += 10
    else:
        feedback.append("Add a stronger hook in the first 1-2 lines.")

    if _has_bullets(post):
        score += 12
    else:
        feedback.append("Add 3-5 bullet points for clarity.")

    if _has_cta(post):
        score += 9
    else:
        feedback.append("Add a clear call-to-action at the end.")

    if re.search(r"(impact|build|scale|ownership|team|product|customers)", post, re.IGNORECASE):
        score += 8
    else:
        feedback.append("Highlight impact and outcomes more explicitly.")

    if not feedback:
        feedback.append("Strong structure, tone, and CTA.")

    return _clamp(round(score), 0, 100), feedback


def _extract_role(input_text: str) -> str:
    def _infer_role_from_text(text: str) -> str:
        lower = text.lower()
        role_patterns = [
            (r"\btechnical product manager\b|\bproduct manager\b|\bgrowth product manager\b", "Technical Product Manager"),
            (r"\bbackend engineer\b|\bbackend developer\b|\bfastapi\b|\bapi\b", "Backend Engineer"),
            (r"\bfrontend engineer\b|\bfrontend developer\b|\breact\b|\bnext\.?js\b", "Frontend Engineer"),
            (r"\bfull ?stack\b", "Full Stack Engineer"),
            (r"\bdata engineer\b|\betl\b|\bdata pipeline\b", "Data Engineer"),
            (r"\bml engineer\b|\bmachine learning engineer\b|\bllm\b|\bai engineer\b", "ML Engineer"),
            (r"\bdevops\b|\bsite reliability\b|\bsre\b", "DevOps Engineer"),
            (r"\bperformance marketing\b|\bppc\b|\broas\b|\bmeta ads\b|\bgoogle ads\b", "Performance Marketing Executive"),
            (r"\bcivil engineer\b|\bconstruction\b|\bautocad\b|\bboq\b", "Junior Civil Engineer"),
        ]
        for pattern, label in role_patterns:
            if re.search(pattern, lower):
                return label
        return "Hiring Role"

    def _normalize_explicit_role(value: str) -> str:
        cleaned_value = re.sub(r"\s+", " ", value).strip(" -:|")
        if not cleaned_value:
            return ""
        if len(cleaned_value) > 90:
            return ""
        if re.search(r"[.!?].+[A-Za-z]", cleaned_value):
            return ""
        return cleaned_value

    # Prefer explicit role/title mention anywhere in JD text.
    explicit_match = re.search(
        r"(?im)^\s*(?:job\s*title|role|title|position)\s*:\s*(.+)$",
        input_text,
    )
    if explicit_match:
        explicit = _normalize_explicit_role(explicit_match.group(1))
        if explicit and explicit.lower() not in {"job title", "title", "role", "position", "n/a", "na", "tbd", "not specified"}:
            return explicit

    # Handle narrative phrasing like "We are seeking a Technical Product Manager..."
    narrative_match = re.search(
        r"(?i)\b(?:hiring|seeking|looking for)\s+(?:an?\s+)?([A-Za-z][A-Za-z0-9&/() +.-]{3,60})",
        input_text,
    )
    if narrative_match:
        narrative = _normalize_explicit_role(narrative_match.group(1))
        if narrative:
            return narrative

    role_line = ""
    for line in input_text.split("\n"):
        if re.search(r"(job description|job title|role|title|position)", line, re.IGNORECASE):
            role_line = line
            break
    if not role_line:
        role_line = input_text.split("\n")[0] if input_text.split("\n") else ""
    cleaned = re.sub(r"^(job description|job title|role|title|position)\s*:\s*", "", role_line, flags=re.IGNORECASE).strip()
    if cleaned.lower() in {"", "job title", "title", "role", "position", "n/a", "na", "tbd", "not specified"}:
        return _infer_role_from_text(input_text)
    return cleaned


def _extract_location(input_text: str) -> str:
    location_line = ""
    for line in input_text.split("\n"):
        if re.search(r"(location|remote|hybrid|onsite)", line, re.IGNORECASE):
            location_line = line
            break
    if not location_line:
        return "Remote"
    # Remove emojis and common prefixes
    cleaned = re.sub(r"^[\U0001F4CD📍]+\s*", "", location_line)  # Remove location pin emoji
    cleaned = re.sub(r"^location\s*:\s*", "", cleaned, flags=re.IGNORECASE).strip()
    # Remove duplicate "Location:" prefix if already present
    cleaned = re.sub(r"^location:\s*", "", cleaned, flags=re.IGNORECASE).strip()
    if cleaned.lower() in {"", "location", "n/a", "na", "tbd", "not specified"}:
        return "Remote/Hybrid"
    return cleaned


def _extract_skills(input_text: str) -> list[str]:
    lower = input_text.lower()
    dictionary = [
        (r"\bnext\.?js\b", "Next.js"),
        (r"\breact\b", "React"),
        (r"\btypescript\b", "TypeScript"),
        (r"\bjavascript\b", "JavaScript"),
        (r"\bpython\b", "Python"),
        (r"\bfastapi\b", "FastAPI"),
        (r"\bnode\.?js\b", "Node.js"),
        (r"\bpostgres(ql)?\b", "PostgreSQL"),
        (r"\bsql\b", "SQL"),
        (r"\baws\b", "AWS"),
        (r"\bgcp\b", "GCP"),
        (r"\bazure\b", "Azure"),
        (r"\b(?:llm|ai|machine learning|ml)\b", "AI/LLMs"),
        (r"\bcivil\b", "Civil Engineering"),
        (r"\bautocad\b", "AutoCAD"),
        (r"\bsite supervision\b", "Site Supervision"),
        (r"\bboq\b", "BOQ/Estimation"),
        (r"\bquantity estimation|quantity surveying\b", "Quantity Estimation"),
        (r"\bstructural drawings?|rcc\b", "Structural Drawings"),
        (r"\bgoogle ads?\b|google adwords|performance max|pmax\b", "Google Ads"),
        (r"\bmeta ads?( manager)?\b|facebook ads?\b|instagram ads?\b", "Meta Ads Manager"),
        (r"\blinkedin ads?\b|\blinkedin campaign manager\b|\blinkedin lead gen\b", "LinkedIn Campaign Manager"),
        (r"\bgoogle analytics 4\b|\bga4\b|\bgoogle analytics\b", "Google Analytics 4"),
        (r"\bppc\b|pay[- ]per[- ]click", "PPC"),
        (r"\broas\b|\breturn on ad spend\b", "ROAS"),
        (r"\bcpl\b|cost per lead", "CPL"),
        (r"\bcac\b|customer acquisition cost", "CAC"),
    ]

    found: list[str] = []
    for pattern, label in dictionary:
        if re.search(pattern, lower):
            found.append(label)
    return list(dict.fromkeys(found))[:6]


def _extract_experience_line(input_text: str) -> str | None:
    for raw in input_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.search(r"\b(experience|years?|yrs?)\b", line, re.IGNORECASE):
            cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
            cleaned = re.sub(r"\bexperienc\b", "experience", cleaned, flags=re.IGNORECASE)
            return cleaned if cleaned else None
    return None


def _extract_context_line(input_text: str) -> str | None:
    for raw in input_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.search(r"\b(projects?|domain|industry|team|product|clients?|business)\b", line, re.IGNORECASE):
            cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
            return cleaned if cleaned else None
    return None


def _extract_responsibilities(input_text: str) -> list[str]:
    responsibilities: list[str] = []
    verb_pattern = r"^(assist|build|design|develop|manage|lead|coordinate|analyze|create|implement|optimize|maintain|support|deliver|test|monitor|plan|execute|prepare|review)\b"

    for raw in input_text.splitlines():
        line = raw.strip()
        if not line:
            continue

        bullet_match = re.match(r"^\s*(?:[-*•]|\d+[.)])\s+(.+)$", line)
        if bullet_match:
            candidate = bullet_match.group(1).strip()
        else:
            candidate = line

        lower = candidate.lower()
        if re.search(r"\b(role|title|location|skills?|requirements?|experience|salary|company)\b", lower):
            continue
        if bullet_match or re.search(verb_pattern, lower):
            cleaned = candidate.rstrip(" .")
            if 20 <= len(cleaned) <= 140:
                responsibilities.append(cleaned)
        if len(responsibilities) == 4:
            break

    if not responsibilities:
        responsibilities = [
            "Execute core role responsibilities end-to-end",
            "Collaborate with cross-functional teams and stakeholders",
            "Improve quality, reliability, and delivery outcomes",
            "Communicate progress, risks, and solutions clearly",
        ]
    return responsibilities[:4]


def _default_responsibilities_for_role(role: str) -> list[str]:
    role_lower = role.lower()
    if "product manager" in role_lower:
        return [
            "Define growth hypotheses and run A/B experiments across activation and engagement funnels",
            "Translate business goals into prioritized product requirements with clear success metrics",
            "Partner with engineering, design, and data to ship features and measure impact",
            "Build weekly KPI reviews for activation, retention, conversion, and revenue outcomes",
        ]
    if "backend" in role_lower:
        return [
            "Design and ship scalable APIs with strong reliability and observability",
            "Optimize database performance, query efficiency, and service latency under load",
            "Implement secure integrations, async jobs, and fault-tolerant workflows",
            "Collaborate with product and frontend teams to deliver production-ready features",
        ]
    return [
        "Execute core role responsibilities end-to-end",
        "Collaborate with cross-functional teams and stakeholders",
        "Improve quality, reliability, and delivery outcomes",
        "Communicate progress, risks, and solutions clearly",
    ]


def _build_hashtags(role: str, skills: list[str]) -> str:
    tags = ["#Hiring"]
    if skills:
        tags.extend([f"#{re.sub(r'[^A-Za-z0-9]', '', skill)}" for skill in skills[:4]])
    else:
        role_words = re.findall(r"[A-Za-z][A-Za-z0-9+/.-]{2,}", role)
        tags.extend([f"#{re.sub(r'[^A-Za-z0-9]', '', word)}" for word in role_words[:3]])
    deduped: list[str] = []
    for tag in tags:
        if tag and tag not in deduped:
            deduped.append(tag)
    return " ".join(deduped[:5])


def _build_template_post(input_text: str, tone: str) -> str:
    role = _extract_role(input_text)
    location = _extract_location(input_text)
    skills = _extract_skills(input_text)
    stack = _build_hashtags(role, skills)
    highlighted_skills = (
        " | ".join([f"{skill}" for skill in skills])
        if skills
        else "Role-specific skills | Execution | Collaboration"
    )
    responsibilities = _extract_responsibilities(input_text)
    if len(responsibilities) < 4:
        defaults = _default_responsibilities_for_role(role)
        for item in defaults:
            if item not in responsibilities:
                responsibilities.append(item)
            if len(responsibilities) == 4:
                break
    experience_line = _extract_experience_line(input_text)
    context_line = _extract_context_line(input_text)

    tone_line = "This role offers hands-on ownership with direct delivery impact. You'll work closely with product and design teams to build and ship features that matter."

    role_focus = re.sub(r"\s+", " ", role).strip()
    hook = f"🚀 Hiring {role_focus}"
    if role_focus.lower() in {"hiring role", "founding engineer"}:
        hook = "🚀 We're hiring for a high-impact role with clear ownership."

    cta = "Interested candidates, please DM your resume or drop your email in the comments"
    marketing_signals = {"Google Ads", "Meta Ads Manager", "LinkedIn Campaign Manager", "PPC", "ROAS", "CPL", "CAC"}
    role_lower = role.lower()
    if any(skill in marketing_signals for skill in skills) or "performance marketing" in role_lower:
        cta = "DM your resume plus your best ROAS/CPL win, or apply now."

    lines = [
        hook,
        "",
        f"📍 Location: {location}",
        "",
        tone_line,
    ]
    if context_line:
        lines.append(context_line)
    if experience_line:
        lines.append(experience_line)
    lines.extend(
        [
        "",
        f"**🛠 Tech stack: {highlighted_skills}**",   # ← add **
        "",
        "**✅ What you'll do**",                        # ← add **
        *[f"• {item}" for item in responsibilities],
        "",
        cta,
        "",
        stack,
    ]
)
    return "\n".join(lines)


def _enforce_high_score(post: str, input_text: str, tone: str) -> tuple[str, int, list[str]]:
    rating, feedback = _score_post(post)
    if rating >= 90:
        return post, rating, feedback
    improved = _build_template_post(input_text, tone)
    rescored_rating, rescored_feedback = _score_post(improved)
    return improved, rescored_rating, rescored_feedback


def _build_local_post(user_input: str, tone: str) -> GeneratePostResponse:
    base_post = _build_template_post(user_input, tone)
    post, rating, feedback = _enforce_high_score(base_post, user_input, tone)
    sanitized_post = _sanitize_generated_post(post)
    rescored_rating, rescored_feedback = _score_post(sanitized_post)
    return GeneratePostResponse(
        post=_apply_symbols(sanitized_post),
        rating=rescored_rating,
        feedback=rescored_feedback if rescored_feedback else feedback,
        source="local",
    )


def _parse_json_block(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def _apply_symbols(post: str) -> str:
    lines = post.splitlines()
    if not lines:
        return post

    updated: list[str] = []
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped:
            updated.append(raw)
            continue

        # Add 🚀 to first line if not present
        if index == 0 and not stripped.startswith("🚀"):
            updated.append(f"🚀 {raw}")
            continue
        # Add 📍 before Location if not present
        if stripped.lower().startswith("location:") and not stripped.startswith("📍"):
            updated.append(raw.replace("Location:", "📍 Location:", 1))
            continue
        # Add 🛠 before Tech stack if not present - skip if already has **
        if re.search(r"tech stack:", stripped, re.IGNORECASE) and "🛠" not in stripped:
            clean = re.sub(r"\*\*", "", stripped)  # remove existing **
            updated.append(f"**🛠 {clean}**")
            continue
        # Handle What you'll do line
        if "what you'll do" in stripped.lower():
            clean = re.sub(r"\*\*", "", stripped).strip()
            clean = re.sub(r"^[•\-\*✅]\s*", "", clean).strip()  # remove bullet prefix
            updated.append(f"**✅ What you'll do**")
            continue
        # If line already has ** bold markers, keep as is
        updated.append(raw)

    return "\n".join(updated)


def _sanitize_generated_post(post: str) -> str:
    lines = [line.rstrip() for line in post.splitlines()]
    deduped: list[str] = []
    seen: set[str] = set()

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            if deduped and deduped[-1] != "":
                deduped.append("")
            continue

        normalized = re.sub(r"\s+", " ", stripped.lower())
        key = re.sub(r"^[^a-z0-9]+", "", normalized)
        if key in seen and len(key) >= 18:
            continue
        seen.add(key)
        deduped.append(stripped)

    cleaned = "\n".join(deduped).strip()
    cleaned = re.sub(
        r"(?im)^([^\n]*\brole:\s*)(job title|title|role|position|n/?a|tbd|not specified)\s*$",
        r"\1Hiring Role",
        cleaned,
    )
    cleaned = re.sub(
        r"(?im)^([^\n]*\blocation:\s*)(location|n/?a|tbd|not specified)\s*$",
        r"\1Remote/Hybrid",
        cleaned,
    )

    words = cleaned.split()
    if len(words) > 185:
        cleaned = " ".join(words[:180]).strip() + "..."

    return cleaned


def _to_result_from_json(parsed: dict[str, Any], source: str) -> GeneratePostResponse | None:
    post = parsed.get("post")
    if not isinstance(post, str) or not post.strip():
        return None
    sanitized_post = _sanitize_generated_post(post.strip())
    rescored_rating, rescored_feedback = _score_post(sanitized_post)
    raw_rating = parsed.get("rating")
    rating = int(raw_rating) if isinstance(raw_rating, int) else rescored_rating
    feedback = parsed.get("feedback")
    if not isinstance(feedback, list):
        feedback = rescored_feedback
    feedback = [item for item in feedback if isinstance(item, str)]
    if not feedback:
        feedback = rescored_feedback
    return GeneratePostResponse(
        post=_apply_symbols(sanitized_post),
        rating=rescored_rating,
        feedback=feedback,
        source=source,
    )


async def _generate_with_gemini(user_input: str, tone: str) -> GeneratePostResponse | None:
    if not settings.GEMINI_API_KEY:
        return None
    model = settings.GEMINI_MODEL or "gemini-2.0-flash"
    _, sanitized_input = llm_guard.sanitize_user_input(user_input)
    _, sanitized_tone = llm_guard.sanitize_user_input(tone)
    normalized = sanitized_input.strip() if sanitized_input.strip() else "Role: Not specified. Location, stack, and context: not specified."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    params = {"key": settings.GEMINI_API_KEY}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
    {"text": GEMINI_SYSTEM_PROMPT},
    {"text": f"Tone: {sanitized_tone}"},
    {"text": "IMPORTANT: Use **double asterisks** for bold text on section headers like '**🛠 Tech stack:**' and '**✅ What you'll do**'. This is required for LinkedIn formatting."},
    {"text": f"Here is the input:\n\n{normalized}"},
],
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, params=params, json=payload)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    candidates = data.get("candidates", [])
    if not candidates:
        return None
    parts = candidates[0].get("content", {}).get("parts", [])
    text = " ".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if not text:
        return None

    parsed = _parse_json_block(text)
    if not parsed:
        return None
    return _to_result_from_json(parsed, "gemini")


async def _generate_with_openai(user_input: str, tone: str) -> GeneratePostResponse | None:
    if not settings.OPENAI_API_KEY:
        return None
    model = settings.OPENAI_MODEL or "gpt-4o-mini"
    _, sanitized_input = llm_guard.sanitize_user_input(user_input)
    _, sanitized_tone = llm_guard.sanitize_user_input(tone)
    normalized = sanitized_input.strip() if sanitized_input.strip() else "Role: Not specified. Location, stack, and context: not specified."

    payload = {
        "model": model,
        "messages": [
    {"role": "system", "content": OPENAI_SYSTEM_PROMPT},
    {"role": "user", "content": f"Tone: {sanitized_tone}\n\nIMPORTANT: Use **double asterisks** for bold text on section headers like '**🛠 Tech stack:**' and '**✅ What you'll do**'. This is required for LinkedIn formatting.\n\nInput:\n{normalized}"},
],
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not text:
        return None
    parsed = _parse_json_block(text)
    if not parsed:
        return None
    return _to_result_from_json(parsed, "openai")


async def _generate_with_deepseek(user_input: str, tone: str) -> GeneratePostResponse | None:
    if not settings.OPENROUTER_API_KEY:
        return None
    model = settings.OPENROUTER_MODEL or "deepseek/deepseek-chat"
    _, sanitized_input = llm_guard.sanitize_user_input(user_input)
    _, sanitized_tone = llm_guard.sanitize_user_input(tone)
    normalized = sanitized_input.strip() if sanitized_input.strip() else "Role: Not specified. Location, stack, and context: not specified."

    prompt = (
    "You are a LinkedIn content writer. Turn the following job description into a short, high-converting LinkedIn job post.\n\n"
    f"Tone: {sanitized_tone}\n"
    "Constraints:\n"
    "- Hook-first, human, founder-style\n"
    "- Short lines, frequent breaks\n"
    "- 90-180 words\n"
    "- 3-5 bullet points\n"
    "- End with a clear CTA\n"
    "- No explanations, only the final post\n"
    "- Use **double asterisks** for bold on section headers like '**🛠 Tech stack:**' and '**✅ What you'll do**'\n\n"  # ← ADD THIS
    "Job description:\n"
    f"{normalized}"
)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert LinkedIn content writer."},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not text:
        return None

    sanitized_post = _sanitize_generated_post(text)
    rating, feedback = _score_post(sanitized_post)
    if rating < 90:
        return None

    return GeneratePostResponse(
        post=_apply_symbols(sanitized_post),
        rating=rating,
        feedback=feedback,
        source="deepseek",
    )


@router.post("/generate", response_model=GeneratePostResponse)
async def generate_linkedin_post(
    payload: GeneratePostRequest,
    current_user: User = Depends(get_current_user),
):
    user_input = payload.input.strip()
    if not user_input:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text is required")

    _ = current_user
    tone = payload.tone.strip()
    model = payload.model.strip().lower()

    if model == "openai":
        result = await _generate_with_openai(user_input, tone)
    elif model == "deepseek":
        result = await _generate_with_deepseek(user_input, tone)
    else:
        result = await _generate_with_gemini(user_input, tone)

    if result:
        improved_post, improved_rating, improved_feedback = _enforce_high_score(result.post, user_input, tone)
        sanitized_improved = _sanitize_generated_post(improved_post)
        rescored_rating, rescored_feedback = _score_post(sanitized_improved)
        result.post = _apply_symbols(sanitized_improved)
        result.rating = rescored_rating
        result.feedback = rescored_feedback if rescored_feedback else improved_feedback
        return result
    fallback = _build_local_post(user_input, tone)
    return fallback
