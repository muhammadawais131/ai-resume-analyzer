"""Analysis history storage (SQLAlchemy).

Uses SQLite by default (zero setup). For production set DATABASE_URL, e.g.
    DATABASE_URL=postgresql+psycopg://user:password@host:5432/passly
Every record belongs to a ``client_id`` (one per browser session), so users only ever see
their own scans.
"""
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import JSON, DateTime, Float, Integer, String, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

DATA_DIR = Path(__file__).resolve().parent / "data"
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{(DATA_DIR / 'passly.db').as_posix()}"

if DATABASE_URL.startswith("sqlite"):
    DATA_DIR.mkdir(exist_ok=True)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True)
    filename: Mapped[str] = mapped_column(String(255), default="")
    target_role: Mapped[str] = mapped_column(String(255), default="")
    score: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    report: Mapped[dict] = mapped_column(JSON)


class JobKeywords(Base):
    """AI-extracted keywords per job description, so the same job is always scored the same way."""
    __tablename__ = "job_keywords"

    jd_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    keywords: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def get_job_keywords(jd_hash: str):
    with Session(engine) as s:
        row = s.get(JobKeywords, jd_hash)
        return row.keywords if row else None


def save_job_keywords(jd_hash: str, keywords: dict):
    with Session(engine) as s:
        if s.get(JobKeywords, jd_hash) is None:
            s.add(JobKeywords(jd_hash=jd_hash, keywords=keywords))
            s.commit()


def init_db():
    Base.metadata.create_all(engine)


def save_analysis(client_id: str, filename: str, report: dict) -> int:
    with Session(engine) as s:
        row = Analysis(client_id=client_id or "anonymous", filename=(filename or "")[:255],
                       target_role=((report.get("ai") or {}).get("target_role") or "")[:255],
                       score=float(report.get("overall_score", 0)), report=report)
        s.add(row)
        s.commit()
        return row.id


def get_history(client_id: str, limit: int = 10):
    with Session(engine) as s:
        rows = s.scalars(select(Analysis).where(Analysis.client_id == client_id)
                         .order_by(Analysis.id.desc()).limit(limit)).all()
        return [{"id": r.id, "filename": r.filename, "target_role": r.target_role,
                 "score": round(r.score), "created_at": r.created_at.isoformat()} for r in rows]


def get_analysis(client_id: str, analysis_id: int):
    with Session(engine) as s:
        row = s.get(Analysis, analysis_id)
        if row is None or row.client_id != client_id:
            return None
        return row.report


def delete_analysis(client_id: str, analysis_id: int):
    with Session(engine) as s:
        s.execute(delete(Analysis).where(Analysis.id == analysis_id,
                                         Analysis.client_id == client_id))
        s.commit()
