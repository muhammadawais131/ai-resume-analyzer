# Shortlistly: AI Resume Analyzer & ATS Checker

<div align="center">

![AI Resume Analyzer](https://img.shields.io/badge/AI-Resume_Analyzer-blueviolet?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Scan your resume like an Applicant Tracking System does, then fix it with AI**

Get an ATS score in about 30 seconds, see exactly which keywords you're missing, and download an improved resume

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Tech Stack](#️-tech-stack) • [API](#-api-endpoints)

</div>

---

## 📋 Table of Contents

- [Screenshots](#-screenshots)
- [Overview](#-overview)
- [Features](#-features)
- [How Scoring Works](#-how-scoring-works)
- [Tech Stack](#️-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [License](#-license)

---

## 📸 Screenshots

*Example scan of a fictional sample resume against an "AI Engineer" job post.*

| Upload | ① Your score |
|:---:|:---:|
| ![Upload page](Media/01_home.png) | ![Score page](Media/02_score.png) |
| **② Fix it** | **③ Download** |
| ![Fix list](Media/03_fix.png) | ![Improved resume](Media/04_download.png) |

---

## 🎯 Overview

Most companies filter resumes with an **Applicant Tracking System (ATS)** before a human ever sees them.
**Shortlistly** shows you how your resume performs against those filters, for a specific job or in general,
and helps you fix it. You get a clear score, a prioritized fix list, and an AI-improved resume you can download.

### Why Use This Tool?

- 🎯 **ATS Score (0-100)** - A transparent score built from 7 factors, not a black box
- 🔍 **Keyword Gap Analysis** - See which skills from the job post are missing from your resume
- 💡 **Prioritized Fix List** - Critical → low suggestions you can tick off as you go
- ✨ **AI Rewrite + Re-score** - See your score improve (e.g. 72 → 84) before you download
- 📄 **PDF & Word Export** - Clean, ATS-friendly formatting
- 🔒 **Private** - Each user only sees their own scans

---

## ✨ Features

The app is one simple journey: **Upload → ① Your score → ② Fix it → ③ Download**

| Step | What you get |
|------|-------------|
| **Upload** | PDF or DOCX resume, plus an optional job description (leave it empty for a general check) |
| **① Your score** | ATS score with breakdown, missing/found keywords, and what's already working |
| **② Fix it** | Prioritized fix list with progress tracking, before/after rewrites of weak bullet points, a tailored professional summary |
| **③ Download** | AI-optimized resume you can edit and re-score, exported to PDF / Word / TXT |
| **Extras** | Cover letter generator, likely interview questions with answer tips, full PDF score report |

### Smart Details

- **Either/or skills**: if a job asks for "AWS, GCP, or Azure" and you have AWS, the others aren't counted as missing
- **Phrase matching**: "model deployment" in a job post matches "deployed ML models" in your resume
- **Consistent results**: the same resume + the same job always gets the same score
- **Honest AI**: the rewrite only adds skills your resume shows you have, and tells you what it left out
- **Works without AI**: if the OpenAI key is missing, the built-in ATS checks still score your resume

---

## 📊 How Scoring Works

| Factor | Weight | What it measures |
|--------|--------|------------------|
| Keyword Match | 30% | Job-post skills found in your resume |
| Impact & Achievements | 18% | Quantified results and action-verb bullets |
| Job Relevance | 15% | AI semantic similarity between resume and job |
| Structure & Sections | 15% | Standard sections ATS look for (Experience, Skills, Education...) |
| Language & Tone | 8% | No weak phrases ("responsible for"), clichés or pronouns |
| Length & Readability | 7% | Word count and bullet length |
| Contact Info | 7% | Email, phone, LinkedIn, portfolio |

Without a job description, Keyword Match and Job Relevance are skipped and the rest are re-weighted.

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - REST API
- **OpenAI API** - `gpt-4o-mini` (review, rewrite, cover letter, interview prep) and `text-embedding-3-small` (job relevance)
- **SQLAlchemy** - Database layer (SQLite by default, PostgreSQL supported)
- **PyMuPDF** - PDF text extraction
- **python-docx** - DOCX reading

### Frontend
- **Streamlit** - Web interface
- **Custom CSS** - Dark "tech" theme with a 3-step guided flow
- **FPDF + python-docx** - PDF and Word export

---

## 📦 Prerequisites

- **Python 3.10 or higher**
- **pip** (Python package manager)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **Git** (for cloning the repository)

---

## 🚀 Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/muhammadawais131/ai-resume-analyzer.git
cd ai-resume-analyzer
```

### Step 2: Create a Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r backend/requirements-backend.txt -r frontend/requirements_frontend.txt
```

### Step 4: Set Up Environment Variables

Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

> **Note:** Never commit your `.env` file to version control. It's already included in `.gitignore`.

---

## ⚙️ Configuration

All settings are optional and go in `.env`:

```env
OPENAI_MODEL=gpt-4o-mini                       # chat model
OPENAI_EMBED_MODEL=text-embedding-3-small      # embedding model
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/shortlistly   # use PostgreSQL
BACKEND_URL=http://127.0.0.1:8010              # where the frontend finds the API
```

### Database

By default, scan history is stored in SQLite at `backend/data/shortlistly.db`, created automatically on first run.
To use PostgreSQL, run `pip install "psycopg[binary]"` and set `DATABASE_URL`.

---

## 🎮 Usage

### Starting the Application

**Windows (one command):** runs the API and the website in the same terminal. Press **Ctrl+C** to stop.
```bash
.\run.ps1
```

**Or in two terminals (any OS):**
```bash
# Terminal 1 - API on http://127.0.0.1:8010 (interactive docs at /docs)
cd backend
uvicorn main:app --port 8010 --reload

# Terminal 2 - website (run from the project root)
streamlit run frontend/app.py --server.port 8502
```

Then open **http://localhost:8502**

### Using the Application

1. **Upload** your resume (PDF or DOCX)
2. **Paste** the job description (optional, but gives a more precise match)
3. Click **Scan my resume**
4. **① Your score** - check your score and missing keywords
5. **② Fix it** - work through the fix list, copy the improved bullet points
6. **③ Download** - let AI rewrite the resume, check the new score, edit, and download

### Example
```
Upload:  resume.pdf
Job:     "AI Engineer - Python, TensorFlow, PyTorch or scikit-learn, AWS/GCP/Azure..."
Result:  Score 72 → missing: Model Deployment, Cloud Platforms
Rewrite: Score 84 → downloaded as resume.docx
```

---

## 📁 Project Structure
```
ai-resume-analyzer/
├── backend/
│   ├── main.py              # FastAPI routes
│   ├── ats_engine.py        # ATS scoring, checks, keyword matching, fix list
│   ├── ai_service.py        # OpenAI calls: review, rewrite, cover letter, interview prep
│   ├── skills_data.py       # Skills, action verbs, weak phrases, section names
│   ├── resume_parser.py     # PDF/DOCX text extraction (in memory)
│   ├── database.py          # SQLAlchemy models: scan history, job keyword cache
│   └── requirements-backend.txt
├── frontend/
│   ├── app.py               # Streamlit app (3-step flow)
│   ├── ui.py                # Theme and HTML components
│   ├── exporters.py         # PDF / DOCX generation
│   ├── api.py               # Backend client
│   └── requirements_frontend.txt
├── .streamlit/config.toml   # Dark theme
├── run.ps1                  # Windows launcher
├── .env                     # Your API key (create this)
└── README.md
```

---

## 🔌 API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Status and whether AI is enabled |
| POST | `/analyze` | Multipart `file` + optional `job_description` + `client_id` → full report |
| POST | `/score` | Re-score edited resume text |
| POST | `/rewrite` | AI-optimized resume |
| POST | `/cover-letter` | Cover letter |
| POST | `/interview` | Likely interview questions |
| POST | `/chat` | Ask the AI about the resume |
| GET / DELETE | `/history?client_id=...`, `/history/{id}?client_id=...` | The user's own past scans |

Interactive API docs: http://127.0.0.1:8010/docs

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **OpenAI** - For providing powerful AI models
- **Streamlit** - For the excellent web framework
- **FastAPI** - For the high-performance backend framework
- **Open Source Community** - For all the amazing libraries

---

## 📞 Contact & Support

**Muhammad Awais**

- GitHub: [@muhammadawais131](https://github.com/muhammadawais131)
- Project Link: [https://github.com/muhammadawais131/ai-resume-analyzer](https://github.com/muhammadawais131/ai-resume-analyzer)

### Issues & Bug Reports

Found a bug? Please [open an issue](https://github.com/muhammadawais131/ai-resume-analyzer/issues) with:
- Detailed description
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)

---

<div align="center">

**Made with ❤️ by Muhammad Awais**

If this project helped you, please consider giving it a ⭐!

</div>
