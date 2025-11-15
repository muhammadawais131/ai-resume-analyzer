import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from matcher import analyze_resume, skill_gap_analysis, rewrite_resume, generate_docx
from resume_parser import extract_text_from_pdf, extract_text_from_docx
from database import save_analysis, init_db, get_history

app = FastAPI()
init_db()

# Analyze Resume Endpoint
# ----------------------
@app.post("/analyze")
async def analyze_resume_api(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())


    try:
        if file.filename.lower().endswith(".pdf"):
            resume_text = extract_text_from_pdf(file_location)
        elif file.filename.lower().endswith(".docx"):
            resume_text = extract_text_from_docx(file_location)
        else:
            return {"error": "Only PDF and DOCX supported"}
    except Exception as e:
        return {"error": f"Failed to extract resume text: {str(e)}"}

    
    try:
        score, suggestions, missing_skills = analyze_resume(resume_text, job_description)
    except Exception as e:
        score, suggestions, missing_skills = 0.0, ["Error analyzing resume."], []

    
    save_analysis(
        filename=file.filename,
        job_description=job_description,
        match_score=float(score),
        suggestions_str="\n".join(suggestions),
        missing_skills_str=", ".join(missing_skills),
        rewritten_resume_path=""
    )

    
    return {
        "match_score": score,
        "missing_skills": missing_skills,
        "suggestions": suggestions,
        "message": "✅ Resume Analysis Completed Successfully"
    }


# Rewriting the  Resume Endpoint 

@app.post("/rewrite")
async def rewrite_api(
    file: UploadFile = File(...),
    job_description: str = Form(None)
):
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    if file.filename.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_location)
    elif file.filename.lower().endswith(".docx"):
        resume_text = extract_text_from_docx(file_location)
    else:
        return {"error": "Only PDF and DOCX supported"}

    rewritten = rewrite_resume(resume_text, job_description)

    #For Save
    save_analysis(
        filename=file.filename,
        job_description=job_description,
        match_score=0.0,
        suggestions_str="Rewritten resume",
        missing_skills_str="",
        rewritten_resume_path=""
    )

    return {"rewritten_resume": rewritten}

# Export DOCX Endpoint

@app.post("/export-docx")
async def export_docx_api(
    file: UploadFile = File(...),
    job_description: str = Form(None)
):
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    if file.filename.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_location)
    elif file.filename.lower().endswith(".docx"):
        resume_text = extract_text_from_docx(file_location)
    else:
        return {"error": "Only PDF and DOCX supported"}

    rewritten = rewrite_resume(resume_text, job_description)
    out_path = generate_docx(rewritten)

    
    save_analysis(
        filename=file.filename,
        job_description=job_description,
        match_score=0.0,
        suggestions_str="Rewritten and DOCX generated",
        missing_skills_str="",
        rewritten_resume_path=out_path
    )

    return FileResponse(
        path=out_path,
        filename=os.path.basename(out_path),
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

@app.get("/history")
def history(limit: int = 50):
    return {"history": get_history(limit)}
