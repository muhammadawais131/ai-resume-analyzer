# ResumeIQ: AI Resume Analyzer & ATS Checker

ResumeIQ scores your resume the way an Applicant Tracking System (ATS) does. It finds missing keywords
from the job post and uses AI to rewrite weak content, so you get more interviews.

## How it works: one upload, three steps

1. **Your score:** an ATS score from 0 to 100 with a breakdown (keywords, job relevance, impact, structure,
   language, readability, contact), missing vs. found keywords, and what's already working.
2. **Fix it:** one prioritized fix list (critical → low) you can tick off, before/after rewrites of your
   weakest lines, and a tailored professional summary to copy.
3. **Download:** AI rewrites the whole resume, shows the new score (e.g. 68 → 75), and you edit and download
   it as PDF / Word / TXT. Optional extras: cover letter and interview questions.

A job description is optional. Without one, you get a general resume check.
Scan history is private: each browser session only sees its own scans.

## Tech stack

- **Backend:** FastAPI, PyMuPDF, python-docx, OpenAI (`gpt-4o-mini` + `text-embedding-3-small`),
  SQLAlchemy (SQLite by default at `backend/data/resumeiq.db`; set `DATABASE_URL` for PostgreSQL)
- **Frontend:** Streamlit, FPDF, python-docx

```
backend/
  main.py           API routes
  ats_engine.py     rule-based ATS scoring, checks and issues
  ai_service.py     OpenAI calls: review, rewrite, cover letter, interview, chat
  skills_data.py    skills, action verbs, weak phrases, section aliases
  resume_parser.py  in-memory PDF/DOCX text extraction
  database.py       analysis history (SQLite)
frontend/
  app.py            Streamlit UI
  ui.py             styling and HTML components
  exporters.py      PDF / DOCX generation
  api.py            backend client
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r backend/requirements-backend.txt -r frontend/requirements_frontend.txt
```

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
# optional
OPENAI_MODEL=gpt-4o-mini
# optional - use PostgreSQL instead of the built-in SQLite file (pip install "psycopg[binary]")
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/resumeiq
```

## Run

Windows (one command, everything in the same terminal, Ctrl+C stops it): `.\run.ps1`
Then open http://localhost:8502

Or in two terminals:

```bash
# terminal 1 - API on http://127.0.0.1:8010  (docs at /docs)
cd backend
uvicorn main:app --port 8010 --reload

# terminal 2 - UI on http://localhost:8502  (run from the project root)
streamlit run frontend/app.py --server.port 8502
```

Set `BACKEND_URL` if the API runs somewhere other than `http://127.0.0.1:8010`.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Status and whether AI is enabled |
| POST | `/analyze` | Multipart `file` + optional `job_description` → full report |
| POST | `/score` | Re-score edited text (no AI review) |
| POST | `/rewrite` | AI-optimized resume |
| POST | `/cover-letter` | Cover letter |
| POST | `/interview` | Interview questions |
| POST | `/chat` | AI coach |
| GET/DELETE | `/history`, `/history/{id}` | Past analyses |
