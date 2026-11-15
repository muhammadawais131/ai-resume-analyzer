"""All OpenAI calls live here. Every function degrades gracefully when the API is unavailable."""
import hashlib
import json
import logging
import os
import re
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

# Load .env from the project root regardless of the working directory.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()

log = logging.getLogger("ai_service")

CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
MAX_RESUME_CHARS = 12000
MAX_JD_CHARS = 8000

_client = None


def ai_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=90, max_retries=2)
    return _client


def _chat(messages, *, json_mode=False, temperature=0.3, max_tokens=1800) -> str:
    kwargs = {"model": CHAT_MODEL, "messages": messages, "temperature": temperature,
              "max_tokens": max_tokens}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client().chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


def _context(resume_text: str, job_text: str | None) -> str:
    ctx = f"RESUME:\n\"\"\"\n{resume_text[:MAX_RESUME_CHARS]}\n\"\"\""
    if job_text and job_text.strip():
        ctx += f"\n\nJOB DESCRIPTION:\n\"\"\"\n{job_text[:MAX_JD_CHARS]}\n\"\"\""
    return ctx


# --------------------------------------------------------------------------- embeddings
_similarity_cache: dict[str, float] = {}


def semantic_similarity(resume_text: str, job_text: str) -> float | None:
    """Cosine similarity of resume vs job. Cached so the same pair always scores identically
    (the embeddings API returns very slightly different vectors on each call)."""
    if not ai_enabled() or not job_text.strip():
        return None
    key = hashlib.sha256(f"{' '.join(resume_text.split())}\x00{' '.join(job_text.split())}".encode()).hexdigest()
    if key in _similarity_cache:
        return _similarity_cache[key]
    try:
        resp = client().embeddings.create(
            model=EMBED_MODEL, input=[resume_text[:MAX_RESUME_CHARS], job_text[:MAX_JD_CHARS]])
        a, b = (np.array(d.embedding) for d in resp.data)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if not denom:
            return None
        sim = round(float(np.dot(a, b) / denom), 3)
        if len(_similarity_cache) > 2000:
            _similarity_cache.clear()
        _similarity_cache[key] = sim
        return sim
    except Exception as e:  # network / quota / auth
        log.warning("Embedding failed: %s", e)
        return None


# --------------------------------------------------------------------------- review
REVIEW_SYSTEM = """You are a senior technical recruiter and certified resume writer who has \
reviewed 10,000+ resumes for applicant tracking systems (ATS). Give specific, honest, actionable \
feedback that refers to the candidate's actual content. Never invent experience the candidate \
does not have.

Be calibrated, not exhaustive. Only report a problem if fixing it would clearly improve the \
candidate's chances. A strong resume may have only one or two suggestions, and an excellent one \
may have none: returning an empty list is a correct answer. Never pad the list with generic \
advice, nitpicks or matters of taste. Respond ONLY with valid JSON."""

REVIEW_SCHEMA = """Return JSON with exactly these keys:
{
  "candidate_name": string ("" if unknown),
  "detected_role": string (the candidate's current/most recent role),
  "target_role": string (job title from the job description, or best-fit role if none),
  "verdict": string (one punchy sentence: overall verdict a recruiter would say),
  "summary": string (2-3 sentences: overall assessment of fit and quality),
  "strengths": [string] (1-5 genuine, concrete strengths, each under 20 words),
  "suggestions": [
    {"title": string (short imperative, under 10 words),
     "detail": string (why it matters, quoting or referencing THEIR resume, 1-2 sentences),
     "example": string (a concrete before/after or sample line they can paste; "" if n/a),
     "priority": "high" (likely costs them the interview) | "medium" (noticeably weakens it)
                 | "low" (polish),
     "category": "Impact" | "Content" | "Skills" | "Experience" | "Formatting"}
  ] (0-6 items, ONLY real problems in this specific resume, most important first. Do NOT include:
     missing keywords/skills (reported separately), anything listed under ALREADY REPORTED,
     generic tips that would apply to any resume, or problems the resume does not actually have),
  "bullet_rewrites": [
    {"original": string (copied EXACTLY, character for character, from the resume),
     "improved": string (rewritten: action verb + what + measurable result; use [X] placeholders
                         for numbers you do not know),
     "why": string (under 15 words)}
  ] (0-5 items, only lines that are genuinely weak; skip lines that are already strong),
  "recommended_summary": string (a tailored 3-4 line professional summary they can use),
  "jd_keywords": {"hard_skills": [string], "soft_skills": [string]}
     (important skills/tools/certifications from the JOB DESCRIPTION, 1-4 words each, max 25
      hard and 8 soft; empty lists if there is no job description)
}"""


def _str(v, default=""):
    return v.strip() if isinstance(v, str) else default


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _real_rewrite(b: dict, resume_squashed: str) -> bool:
    """Keep a bullet rewrite only if the 'original' really is in the resume and actually changed."""
    orig, new = _squash(b["original"]), _squash(b["improved"])
    return len(orig) >= 15 and orig[:60] in resume_squashed and orig != new


def _normalize_review(data: dict, resume_text: str = "") -> dict:
    sugg = []
    for s in data.get("suggestions") or []:
        if isinstance(s, dict) and _str(s.get("title")):
            pr = _str(s.get("priority")).lower()
            sugg.append({
                "title": _str(s.get("title")), "detail": _str(s.get("detail")),
                "example": _str(s.get("example")),
                "priority": pr if pr in ("high", "medium", "low") else "medium",
                "category": _str(s.get("category"), "Content") or "Content",
            })
    rewrites = [
        {"original": _str(b.get("original")), "improved": _str(b.get("improved")),
         "why": _str(b.get("why"))}
        for b in data.get("bullet_rewrites") or []
        if isinstance(b, dict) and _str(b.get("original")) and _str(b.get("improved"))
    ]
    if resume_text:
        squashed = _squash(resume_text)
        rewrites = [b for b in rewrites if _real_rewrite(b, squashed)]
    kw = data.get("jd_keywords") or {}
    return {
        "candidate_name": _str(data.get("candidate_name")),
        "detected_role": _str(data.get("detected_role")),
        "target_role": _str(data.get("target_role")),
        "verdict": _str(data.get("verdict")),
        "summary": _str(data.get("summary")),
        "strengths": [x.strip() for x in data.get("strengths") or [] if isinstance(x, str)][:6],
        "suggestions": sugg[:6],
        "bullet_rewrites": rewrites[:5],
        "recommended_summary": _str(data.get("recommended_summary")),
        "jd_keywords": {
            "hard_skills": [x for x in kw.get("hard_skills") or [] if isinstance(x, str)][:25],
            "soft_skills": [x for x in kw.get("soft_skills") or [] if isinstance(x, str)][:8],
        },
    }


def ai_review(resume_text: str, job_text: str | None, weak_bullets=None,
              known_issues=None) -> dict | None:
    if not ai_enabled():
        return None
    hint = ""
    if weak_bullets:
        hint += ("\n\nLines our parser flagged as possibly weak (rewrite only those that really are):\n"
                 + "\n".join(f"- {b}" for b in weak_bullets[:8]))
    if known_issues:
        hint += ("\n\nALREADY REPORTED by our ATS checks (do not repeat these as suggestions):\n"
                 + "\n".join(f"- {t}" for t in known_issues))
    task = ("Review this resume against the job description." if job_text and job_text.strip()
            else "Review this resume for general ATS-readiness and quality (no job description given).")
    try:
        raw = _chat([
            {"role": "system", "content": REVIEW_SYSTEM},
            {"role": "user", "content": f"{task}\n\n{_context(resume_text, job_text)}{hint}\n\n{REVIEW_SCHEMA}"},
        ], json_mode=True, temperature=0.2, max_tokens=2500)
        return _normalize_review(json.loads(raw), resume_text)
    except Exception as e:
        log.warning("AI review failed: %s", e)
        return None


# --------------------------------------------------------------------------- generators
REWRITE_SYSTEM = """You are an expert resume writer. Rewrite resumes to be ATS-friendly and \
recruiter-ready while staying 100% truthful to the candidate's real experience.

Formatting rules (strict):
- Plain text only. No markdown, no asterisks, no '#', no tables.
- Line 1: candidate full name. Line 2: contact details separated by ' | '.
- Section headers in UPPERCASE on their own line, in this order when content exists:
  PROFESSIONAL SUMMARY, SKILLS, WORK EXPERIENCE, PROJECTS, EDUCATION, CERTIFICATIONS.
- Under each role: a line 'Job Title | Company | Location | Dates', then bullets.
- Bullets start with '- ' followed by a strong action verb; include metrics where the original
  implies them, otherwise use [X] placeholders the candidate can fill in.
- SKILLS: grouped lines such as 'Languages: ...', 'Frameworks: ...', 'Tools: ...'.
- Separate sections with one blank line. Keep it to 1-2 pages."""


def rewrite_resume(resume_text: str, job_text: str | None = None, missing_keywords=None,
                   tone: str = "professional") -> str:
    if not ai_enabled():
        raise RuntimeError("OpenAI API key is not configured.")
    extra = ""
    if missing_keywords:
        extra = ("\n\nKeywords from the job post missing in the resume: " + ", ".join(missing_keywords)
                 + ". Weave in ONLY those the candidate plausibly has based on their experience.")
    goal = ("Tailor it for the job description." if job_text and job_text.strip()
            else "Optimize it for general ATS readability.")
    text = _chat([
        {"role": "system", "content": REWRITE_SYSTEM},
        {"role": "user", "content": f"{_context(resume_text, job_text)}\n\nRewrite this resume. "
                                    f"{goal} Tone: {tone}.{extra}"},
    ], temperature=0.25, max_tokens=2500)
    for ch in ("**", "*", "###", "##", "•", "●", "▪", "■"):
        text = text.replace(ch, "-" if ch in "•●▪■" else "")
    return text.strip()


def cover_letter(resume_text: str, job_text: str, company: str = "", hiring_manager: str = "",
                 tone: str = "professional", length: str = "medium") -> str:
    if not ai_enabled():
        raise RuntimeError("OpenAI API key is not configured.")
    words = {"short": "180-220", "medium": "250-320", "long": "350-420"}.get(length, "250-320")
    who = hiring_manager or "Hiring Manager"
    return _chat([
        {"role": "system", "content": "You write compelling, specific cover letters that sound "
                                      "human, never generic. Plain text only, no markdown. Never "
                                      "invent experience."},
        {"role": "user", "content": f"{_context(resume_text, job_text)}\n\nWrite a cover letter "
                                    f"({words} words, {tone} tone) addressed to '{who}'"
                                    f"{' at ' + company if company else ''}. Open with a strong hook, "
                                    "connect 2-3 concrete achievements to the job's needs, and close "
                                    "with a confident call to action. End with 'Sincerely,' and the "
                                    "candidate's name."},
    ], temperature=0.6, max_tokens=1200)


def interview_questions(resume_text: str, job_text: str | None) -> list[dict]:
    if not ai_enabled():
        raise RuntimeError("OpenAI API key is not configured.")
    raw = _chat([
        {"role": "system", "content": "You are an experienced interviewer. Respond only with JSON."},
        {"role": "user", "content": f"{_context(resume_text, job_text)}\n\nPredict 8 interview "
                                    "questions this candidate is likely to be asked for this role: mix "
                                    "technical/role-specific, behavioral, and questions probing gaps or "
                                    "weak spots in the resume. Return JSON: {\"questions\": [{\"question\": "
                                    "str, \"type\": \"Technical\"|\"Behavioral\"|\"Gap\"|\"Situational\", "
                                    "\"why\": str (why they'd ask it), \"tip\": str (how to answer using "
                                    "the candidate's own experience, 1-2 sentences)}]}"},
    ], json_mode=True, temperature=0.5, max_tokens=2000)
    items = json.loads(raw).get("questions") or []
    return [
        {"question": _str(q.get("question")), "type": _str(q.get("type"), "Technical"),
         "why": _str(q.get("why")), "tip": _str(q.get("tip"))}
        for q in items if isinstance(q, dict) and _str(q.get("question"))
    ]


def coach_chat(resume_text: str, job_text: str | None, messages: list[dict]) -> str:
    if not ai_enabled():
        raise RuntimeError("OpenAI API key is not configured.")
    history = [m for m in messages if m.get("role") in ("user", "assistant")][-12:]
    return _chat([
        {"role": "system", "content": "You are a friendly, expert career coach. Answer questions "
                                      "about the user's resume and job search concisely (under 200 "
                                      "words unless asked for more). Use short paragraphs or simple "
                                      "bullet lists. Be specific to their resume.\n\n"
                                      + _context(resume_text, job_text)},
        *[{"role": m["role"], "content": str(m.get("content", ""))[:4000]} for m in history],
    ], temperature=0.5, max_tokens=900)
