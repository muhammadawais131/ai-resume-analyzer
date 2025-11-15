# AI Resume Analyzer & Optimizer

<div align="center">

![AI Resume Analyzer](https://img.shields.io/badge/AI-Resume_Analyzer-blue?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Intelligent Resume Analysis & Optimization Tool**

Transform your resume with AI-powered insights and match it perfectly to job descriptions

[Features](#features) • [Demo](#demo) • [Installation](#installation) • [Usage](#usage) • [Tech Stack](#tech-stack)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**AI Resume Analyzer** is an intelligent application that helps job seekers optimize their resumes for specific job descriptions. Using advanced AI and natural language processing, it analyzes your resume against job requirements, identifies missing skills, provides actionable suggestions, and generates an improved version tailored to the position.

### Why Use This Tool?

- 🎯 **Match Score Analysis** - Get a precise percentage match between your resume and job description
- 🔍 **Skills Gap Detection** - Identify missing technical and soft skills required for the role
- 💡 **Smart Suggestions** - Receive actionable recommendations to improve your resume
- ✨ **AI-Powered Rewriting** - Generate an enhanced, ATS-friendly resume automatically
- 📄 **Multi-Format Export** - Download your improved resume as PDF or DOCX
- 🚀 **Easy to Use** - Clean, professional UI with a simple upload-and-analyze workflow

---

## ✨ Features

### Core Functionality

| Feature | Description |
|---------|-------------|
| **Resume Upload** | Support for PDF and DOCX formats |
| **Job Description Analysis** | Paste any job description for comparison |
| **Match Score Calculation** | AI-powered semantic similarity scoring using embeddings |
| **Missing Skills Detection** | Automatically identifies technical and soft skills gaps |
| **Actionable Suggestions** | Get 5-7 specific recommendations for improvement |
| **AI Resume Rewriting** | Generates professionally formatted, ATS-optimized resume |
| **Export Options** | Download as PDF or DOCX with one click |
| **Analysis History** | Track all your resume analyses (stored in SQLite) |

### Advanced Features

- **Semantic Matching**: Uses OpenAI embeddings for deep content understanding
- **Smart Skill Extraction**: Recognizes 100+ technical skills and frameworks
- **ATS Optimization**: Ensures resumes are applicant tracking system friendly
- **Clean Formatting**: Removes markdown and special characters for compatibility
- **Quantifiable Metrics**: Suggests adding numbers and achievements
- **Action Verb Enhancement**: Recommends stronger language for bullet points

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, high-performance web framework
- **Python 3.8+** - Core programming language
- **OpenAI API** - GPT-4 and text-embedding models
- **SQLite** - Lightweight database for analysis history
- **PyPDF2** - PDF text extraction
- **python-docx** - DOCX file handling

### Frontend
- **Streamlit** - Interactive web interface
- **Custom CSS** - Professional dark blue theme with modern UI/UX

### Libraries & Tools
```
openai>=1.0.0          # AI models
fastapi>=0.104.0       # Backend API
streamlit>=1.28.0      # Frontend interface
python-multipart       # File upload handling
pypdf2                 # PDF processing
python-docx            # DOCX processing
fpdf                   # PDF generation
numpy                  # Numerical operations
python-dotenv          # Environment management
uvicorn                # ASGI server
```

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher**
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

### Step 2: Create Virtual Environment

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
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

Create a `.env` file in the project root:
```bash
touch .env
```

Add your OpenAI API key:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

> **Note:** Never commit your `.env` file to version control. It's already included in `.gitignore`.

---

## ⚙️ Configuration

### OpenAI API Settings

The application uses the following models (configured in `matcher.py`):

- **Embedding Model**: `text-embedding-3-small` (for semantic matching)
- **Chat Model**: `gpt-4o-mini` (for resume rewriting)

You can modify these in the code if needed:
```python
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
```

### Database

Analysis history is stored in `resume_analyzer.db` (SQLite). The database is automatically initialized on first run.

---

## 🎮 Usage

### Starting the Application

#### 1. Start the Backend Server

Open a terminal and run:
```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

#### 2. Start the Frontend Interface

Open a **new terminal** (keep the backend running) and run:
```bash
streamlit run app.py
```

The web interface will open automatically at `http://localhost:8501`

### Using the Application

1. **Upload Resume**: Click "Upload your resume" and select a PDF or DOCX file
2. **Paste Job Description**: Copy and paste the complete job description
3. **Analyze**: Click "🚀 Analyze Resume" button
4. **Review Results**:
   - View your match score percentage
   - Check missing skills
   - Read improvement suggestions
   - Preview the AI-rewritten resume
5. **Export**: Download your improved resume as PDF or DOCX

### Example Workflow
```
1. Upload: software_engineer_resume.pdf
2. Paste: "Senior Backend Developer - Python, Django, AWS..."
3. Results:
   - Match Score: 78%
   - Missing Skills: AWS, Docker, Kubernetes
   - Suggestions: Add quantifiable achievements, Include AWS experience
4. Export: Download improved_resume.pdf
```

---

## 📁 Project Structure
```
ai-resume-analyzer/
├── app.py                  # Streamlit frontend application
├── main.py                 # FastAPI backend server
├── matcher.py              # Core AI analysis logic
├── resume_parser.py        # PDF/DOCX text extraction
├── database.py             # SQLite database operations
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── .gitignore             # Git ignore rules
├── resume_analyzer.db     # SQLite database (auto-generated)
└── README.md              # This file
```

### Key Files

| File | Purpose |
|------|---------|
| `app.py` | Frontend UI with Streamlit, handles user interactions |
| `main.py` | REST API endpoints for analysis, rewriting, and export |
| `matcher.py` | AI logic: embeddings, similarity, skill extraction, GPT rewriting |
| `resume_parser.py` | Extracts text from PDF and DOCX files |
| `database.py` | Manages SQLite database for analysis history |

---

## 🔌 API Endpoints

### POST `/analyze`

Analyze a resume against a job description.

**Request:**
- `file`: Resume file (PDF/DOCX)
- `job_description`: Job description text

**Response:**
```json
{
  "match_score": 78.5,
  "missing_skills": ["AWS", "Docker", "Kubernetes"],
  "suggestions": [
    "Add these technical skills to your Skills section: AWS, Docker",
    "Add quantifiable achievements with numbers"
  ],
  "message": "✅ Resume Analysis Completed Successfully"
}
```

### POST `/rewrite`

Generate an improved resume.

**Request:**
- `file`: Resume file (PDF/DOCX)
- `job_description`: Job description text (optional)

**Response:**
```json
{
  "rewritten_resume": "SUMMARY\nExperienced software engineer..."
}
```

### POST `/export-docx`

Export rewritten resume as DOCX.

**Request:**
- `file`: Resume file (PDF/DOCX)
- `job_description`: Job description text (optional)

**Response:** DOCX file download

### GET `/history?limit=50`

Retrieve analysis history.

**Response:**
```json
{
  "history": [
    {
      "id": 1,
      "filename": "resume.pdf",
      "match_score": 78.5,
      "timestamp": "2025-01-15 10:30:00"
    }
  ]
}
```

---

## 🎨 UI Features

### Modern Dark Blue Theme
- Professional gradient background
- Glass-morphism design elements
- Smooth animations and hover effects
- Responsive layout for all screen sizes

### Color Scheme
- **Primary**: Blue (#3b82f6)
- **Background**: Dark slate (#0f172a, #1e293b)
- **Accent**: Purple gradient
- **Success**: Green (#10b981)
- **Warning**: Amber (#f59e0b)

---

## 🧪 Testing

### Test the Backend
```bash
# Test health check
curl http://127.0.0.1:8000/

# Test analysis endpoint
curl -X POST http://127.0.0.1:8000/analyze \
  -F "file=@sample_resume.pdf" \
  -F "job_description=Python developer with Django experience"
```

### Test the Frontend

1. Navigate to `http://localhost:8501`
2. Upload a sample resume
3. Paste a job description
4. Verify all features work correctly

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Contribution Ideas

- Add support for more file formats (RTF, TXT)
- Implement user authentication
- Add multilingual support
- Create more detailed analytics dashboard
- Improve skill extraction algorithms
- Add cover letter generation

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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

## 📊 Project Status

![GitHub Stars](https://img.shields.io/github/stars/muhammadawais131/ai-resume-analyzer?style=social)
![GitHub Forks](https://img.shields.io/github/forks/muhammadawais131/ai-resume-analyzer?style=social)
![GitHub Issues](https://img.shields.io/github/issues/muhammadawais131/ai-resume-analyzer)

---

## 🔮 Future Roadmap

- [ ] LinkedIn profile integration
- [ ] Cover letter generation
- [ ] Interview question preparation based on resume
- [ ] Multiple resume templates
- [ ] Batch processing for multiple resumes
- [ ] Chrome extension for one-click analysis
- [ ] Mobile application (iOS/Android)

---

<div align="center">

**Made with ❤️ by Muhammad Awais**

If this project helped you, please consider giving it a ⭐!

</div>
