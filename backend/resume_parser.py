"""Extract plain text (and a little metadata) from PDF / DOCX resumes, in memory."""
import io
import re

import docx

try:
    import pymupdf as fitz
except ImportError:  # older PyMuPDF versions
    import fitz

SUPPORTED_EXTENSIONS = (".pdf", ".docx")


def _normalize(text: str) -> str:
    text = text.replace("\r", "\n").replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf_bytes(data: bytes):
    pages = 0
    parts = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        pages = doc.page_count
        for page in doc:
            parts.append(page.get_text("text"))
    return _normalize("\n".join(parts)), {"pages": pages}


def _is_list_item(paragraph) -> bool:
    """Word stores bullets as list formatting, not as characters - detect it."""
    style = (paragraph.style.name or "").lower() if paragraph.style is not None else ""
    if "list" in style:
        return True
    p_pr = paragraph._p.pPr
    return p_pr is not None and p_pr.numPr is not None


def extract_text_from_docx_bytes(data: bytes):
    document = docx.Document(io.BytesIO(data))
    parts = [("- " + p.text) if _is_list_item(p) and p.text.strip() else p.text
             for p in document.paragraphs]
    # Many resume templates put content in tables - read those too.
    for table in document.tables:
        for row in table.rows:
            seen = set()
            for cell in row.cells:
                if id(cell._tc) in seen:  # merged cells repeat
                    continue
                seen.add(id(cell._tc))
                parts.append(cell.text)
    text = _normalize("\n".join(parts))
    # Rough page estimate (~500 words per page).
    pages = max(1, round(len(text.split()) / 500))
    return text, {"pages": pages, "has_tables": bool(document.tables)}


def extract_resume(filename: str, data: bytes):
    """Return (text, meta). Raises ValueError for unsupported/unreadable files."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        text, meta = extract_text_from_pdf_bytes(data)
    elif name.endswith(".docx"):
        text, meta = extract_text_from_docx_bytes(data)
    else:
        raise ValueError("Only PDF and DOCX files are supported.")
    meta["file_type"] = name.rsplit(".", 1)[-1]
    return text, meta
