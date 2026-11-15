"""Thin client for the Shortlistly FastAPI backend. Every call returns (data, error_message)."""
import os

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8010").rstrip("/")


def _handle(resp):
    if resp.ok:
        return resp.json(), None
    try:
        detail = resp.json().get("detail", resp.text)
    except ValueError:
        detail = resp.text
    return None, str(detail)


def _post(path, timeout=180, **kwargs):
    try:
        return _handle(requests.post(f"{BACKEND_URL}{path}", timeout=timeout, **kwargs))
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the Shortlistly API. Start it with: .\\run.ps1"
    except requests.exceptions.Timeout:
        return None, "The request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return None, str(e)


def _get(path, timeout=10):
    try:
        return _handle(requests.get(f"{BACKEND_URL}{path}", timeout=timeout))
    except requests.exceptions.RequestException as e:
        return None, str(e)


def health():
    """Returns (data, error). data is None unless the Shortlistly API itself answered."""
    data, err = _get("/health", timeout=3)
    if data is not None and data.get("app") != "shortlistly":
        return None, f"Another program is using {BACKEND_URL}. Run the Shortlistly API on a free port."
    return data, err


def analyze(filename, content, mime, job_description, client_id):
    return _post("/analyze", files={"file": (filename, content, mime)},
                 data={"job_description": job_description or "", "client_id": client_id})


def score(resume_text, job_description, jd_keywords):
    return _post("/score", json={"resume_text": resume_text, "job_description": job_description,
                                 "jd_keywords": jd_keywords})


def rewrite(resume_text, job_description, missing_keywords, tone):
    return _post("/rewrite", json={"resume_text": resume_text, "job_description": job_description,
                                   "missing_keywords": missing_keywords, "tone": tone})


def cover_letter(resume_text, job_description, company, hiring_manager, tone, length):
    return _post("/cover-letter", json={
        "resume_text": resume_text, "job_description": job_description, "company": company,
        "hiring_manager": hiring_manager, "tone": tone, "length": length})


def interview(resume_text, job_description):
    return _post("/interview", json={"resume_text": resume_text, "job_description": job_description})


def chat(resume_text, job_description, messages):
    return _post("/chat", json={"resume_text": resume_text, "job_description": job_description,
                                "messages": messages})


def history(client_id, limit=5):
    data, err = _get(f"/history?client_id={client_id}&limit={limit}")
    return (data or {}).get("history", []), err


def load(analysis_id, client_id):
    return _get(f"/history/{analysis_id}?client_id={client_id}")
