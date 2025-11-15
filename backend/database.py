import sqlite3
import os
from datetime import datetime

DB_PATH = "analysis_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        job_description TEXT,
        match_score REAL,
        suggestions TEXT,
        missing_skills TEXT,
        rewritten_resume_path TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_analysis(filename, job_description, match_score, suggestions_str, missing_skills_str, rewritten_resume_path=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO analyses (filename, job_description, match_score, suggestions, missing_skills, rewritten_resume_path, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (filename, job_description, match_score, suggestions_str, missing_skills_str, rewritten_resume_path or "", datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_history(limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, filename, job_description, match_score, suggestions, missing_skills, rewritten_resume_path, created_at FROM analyses ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "filename": r[1],
            "job_description": r[2],
            "match_score": r[3],
            "suggestions": r[4],
            "missing_skills": r[5],
            "rewritten_resume_path": r[6],
            "created_at": r[7]
        })
    return items
