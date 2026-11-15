"""Passly API - ATS resume analysis, AI rewriting, cover letters and interview prep."""
import hashlib
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import ai_service as ai
from ats_engine import analyze_structure, build_report
from database import (delete_analysis, get_analysis, get_history, get_job_keywords, init_db,
                      save_analysis, save_job_keywords)
from resume_parser import SUPPORTED_EXTENSIONS, extract_resume

logging.basicConfig(level=logging.INFO)
MAX_FILE_BYTES = 10 * 1024 * 1024

app = FastAPI(title="Passly API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
init_db()


# --------------------------------------------------------------------------- models
class TextPayload(BaseModel):
    resume_text: str = Field(..., min_length=20)
    job_description: str = ""


class ScorePayload(TextPayload):
    jd_keywords: dict | None = None


class RewritePayload(TextPayload):
    missing_keywords: list[str] = []
    tone: str = "professional"


class CoverLetterPayload(TextPayload):
    company: str = ""
    hiring_manager: str = ""
    tone: str = "professional"
    length: str = "medium"


class ChatPayload(TextPayload):
    messages: list[dict]


# --------------------------------------------------------------------------- helpers
# Topics the rule engine reports itself. AI suggestions about the same topic are duplicates.
_TOPICS = {
    "impact": re.compile(r"quantif|metric|number|measur|impact|result|achievement", re.I),
    "keywords": re.compile(r"keyword|missing skill|add skill|skills? from the job", re.I),
    "contact": re.compile(r"linkedin|contact|phone|email", re.I),
    "summary": re.compile(r"summary|objective|profile", re.I),
    "verbs": re.compile(r"action verb|weak phrase|responsible for", re.I),
    "length": re.compile(r"too long|too short|length|concise", re.I),
}
_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def calibrate_suggestions(suggestions: list[dict], report: dict) -> list[dict]:
    """Keep only genuine AI findings: no duplicates of rule-engine issues, and fewer, softer
    suggestions for resumes that already score well."""
    reported = {t for t, rx in _TOPICS.items() for i in report["issues"] if rx.search(i["title"])}
    out = []
    for s in suggestions:
        text = f"{s['title']} {s['detail']}"
        if any(rx.search(s["title"]) for t, rx in _TOPICS.items() if t in reported):
            continue  # same topic as an ATS issue already in the list
        if any(rx.search(text) for t, rx in _TOPICS.items() if t == "keywords"):
            continue  # missing keywords have their own section
        out.append(dict(s))

    score = report["overall_score"]
    if score >= 85:    # strong resume: only optional polish
        out = out[:2]
        for s in out:
            s["priority"] = "low"
    elif score >= 70:  # good resume: a few targeted improvements
        out = out[:4]
        for s in out:
            if s["priority"] == "high":
                s["priority"] = "medium"
    return sorted(out, key=lambda s: _PRIORITY_RANK.get(s["priority"], 1))


def run_analysis(resume_text: str, job_description: str, meta: dict, use_ai=True,
                 jd_keywords: dict | None = None) -> dict:
    structure = analyze_structure(resume_text, meta)
    review, similarity = None, None
    if use_ai and ai.ai_enabled():
        # Issues the rule engine already reports, so the AI adds only NEW, genuine findings.
        known = [i["title"] for i in build_report(structure)["issues"]]
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_review = pool.submit(ai.ai_review, resume_text, job_description, structure["weak_bullets"],
                                   known)
            f_sim = pool.submit(ai.semantic_similarity, resume_text, job_description)
            review, similarity = f_review.result(), f_sim.result()
    elif ai.ai_enabled() and job_description.strip():
        similarity = ai.semantic_similarity(resume_text, job_description)

    # Same job description -> same keyword list, every time (AI extraction is not deterministic).
    jd_hash = hashlib.sha256(" ".join(job_description.lower().split()).encode()).hexdigest()
    keywords = jd_keywords or get_job_keywords(jd_hash)
    if keywords is None:
        keywords = (review or {}).get("jd_keywords")
        if keywords and (keywords.get("hard_skills") or keywords.get("soft_skills")):
            save_job_keywords(jd_hash, keywords)
    report = build_report(structure, job_description, keywords, similarity)
    if review:
        review["suggestions"] = calibrate_suggestions(review.get("suggestions", []), report)
    report["ai"] = review
    report["ai_available"] = review is not None
    report["jd_keywords"] = keywords
    report["resume_text"] = resume_text
    report["job_description"] = job_description
    report["meta"] = meta
    return report


def _ai_guard():
    if not ai.ai_enabled():
        raise HTTPException(503, "OPENAI_API_KEY is not configured on the server.")


def _ai_call(fn, *args, **kwargs):
    _ai_guard()
    try:
        return fn(*args, **kwargs)
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("AI call failed")
        raise HTTPException(502, f"AI service error: {e}") from e


# --------------------------------------------------------------------------- routes
@app.get("/health")
def health():
    return {"app": "passly", "status": "ok", "ai_enabled": ai.ai_enabled(), "model": ai.CHAT_MODEL}


@app.post("/analyze")
def analyze(file: UploadFile = File(...), job_description: str = Form(""), client_id: str = Form("")):
    name = file.filename or "resume"
    if not name.lower().endswith(SUPPORTED_EXTENSIONS):
        raise HTTPException(400, "Only PDF and DOCX files are supported.")
    data = file.file.read()
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(413, "File is larger than 10 MB.")
    try:
        text, meta = extract_resume(name, data)
    except Exception as e:
        raise HTTPException(422, f"Could not read this file: {e}") from e

    report = run_analysis(text, job_description or "", meta)
    report["filename"] = name
    report["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report["analysis_id"] = save_analysis(client_id, name, report)
    return report


@app.post("/score")
def score(payload: ScorePayload):
    """Re-score edited text (e.g. the AI rewrite) with the same keyword set - no AI review."""
    report = run_analysis(payload.resume_text, payload.job_description,
                          {"pages": max(1, round(len(payload.resume_text.split()) / 500))},
                          use_ai=False, jd_keywords=payload.jd_keywords)
    return {k: report[k] for k in ("overall_score", "rating", "rating_key", "scores", "keywords",
                                   "issues", "stats")}


@app.post("/rewrite")
def rewrite(payload: RewritePayload):
    text = _ai_call(ai.rewrite_resume, payload.resume_text, payload.job_description,
                    payload.missing_keywords, payload.tone)
    return {"rewritten_resume": text}


@app.post("/cover-letter")
def cover_letter(payload: CoverLetterPayload):
    if not payload.job_description.strip():
        raise HTTPException(400, "A job description is required to write a cover letter.")
    text = _ai_call(ai.cover_letter, payload.resume_text, payload.job_description,
                    payload.company, payload.hiring_manager, payload.tone, payload.length)
    return {"cover_letter": text}


@app.post("/interview")
def interview(payload: TextPayload):
    return {"questions": _ai_call(ai.interview_questions, payload.resume_text,
                                  payload.job_description)}


@app.post("/chat")
def chat(payload: ChatPayload):
    return {"reply": _ai_call(ai.coach_chat, payload.resume_text, payload.job_description,
                              payload.messages)}


# History is always scoped to the caller's client_id - users never see each other's scans.
@app.get("/history")
def history(client_id: str, limit: int = 10):
    return {"history": get_history(client_id, min(limit, 50))}


@app.get("/history/{analysis_id}")
def history_item(analysis_id: int, client_id: str):
    report = get_analysis(client_id, analysis_id)
    if report is None:
        raise HTTPException(404, "Analysis not found.")
    report["analysis_id"] = analysis_id
    return report


@app.delete("/history/{analysis_id}")
def history_delete(analysis_id: int, client_id: str):
    delete_analysis(client_id, analysis_id)
    return {"deleted": analysis_id}
