"""Turn plain-text resumes / letters / reports into polished PDF and DOCX files."""
import io
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from fpdf import FPDF

ACCENT = (79, 70, 229)
INK = (15, 23, 42)
MUTED = (100, 116, 139)

_REPLACE = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-",
            "…": "...", "•": "-", "●": "-", "▪": "-", " ": " ", "→": "->"}


def _latin(text: str) -> str:
    for a, b in _REPLACE.items():
        text = text.replace(a, b)
    return text.encode("latin-1", "replace").decode("latin-1")


# --------------------------------------------------------------------------- parsing
def parse_resume(text: str):
    """Classify each line: name, contact, heading, role, bullet, text, blank."""
    lines = [l.rstrip() for l in text.replace("\r", "").split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    blocks = []
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            blocks.append(("blank", ""))
        elif i == 0 and len(line) < 60 and not line.startswith("-"):
            blocks.append(("name", line))
        elif i <= 2 and ("@" in line or ("|" in line and blocks and blocks[0][0] == "name"
                                          and not any(b[0] == "heading" for b in blocks))):
            blocks.append(("contact", line))
        elif re.sub(r"[^A-Za-z]", "", line).isupper() and len(line) < 50 and not line.startswith("-"):
            blocks.append(("heading", line.rstrip(":")))
        elif line[:1] in "-•*" :
            blocks.append(("bullet", line.lstrip("-•* ").strip()))
        elif " | " in line and len(line) < 140:
            blocks.append(("role", line))
        else:
            blocks.append(("text", line))
    return blocks


# --------------------------------------------------------------------------- PDF
class _PDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, f"Page {self.page_no()}", 0, 0, "C")


def _new_pdf():
    pdf = _PDF(format="A4")
    pdf.set_margins(16, 14, 16)
    pdf.set_auto_page_break(True, 16)
    pdf.add_page()
    return pdf


def _pdf_bytes(pdf) -> bytes:
    out = pdf.output(dest="S")
    return out.encode("latin-1") if isinstance(out, str) else bytes(out)


def _pdf_bullet(pdf, text, size=10):
    pdf.set_font("Helvetica", "", size)
    pdf.set_text_color(*INK)
    x = pdf.l_margin
    pdf.set_x(x + 2)
    pdf.cell(4, 5, chr(149))
    pdf.multi_cell(pdf.w - pdf.r_margin - pdf.get_x(), 5, _latin(text))
    pdf.ln(0.6)


def resume_pdf(text: str) -> bytes:
    pdf = _new_pdf()
    width = pdf.w - pdf.l_margin - pdf.r_margin
    for kind, line in parse_resume(text):
        if kind == "name":
            pdf.set_font("Helvetica", "B", 21)
            pdf.set_text_color(*INK)
            pdf.cell(0, 10, _latin(line), ln=1, align="C")
        elif kind == "contact":
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(*MUTED)
            pdf.multi_cell(0, 5, _latin(line), align="C")
            pdf.ln(1)
        elif kind == "heading":
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 11.5)
            pdf.set_text_color(*ACCENT)
            pdf.cell(0, 6, _latin(line.upper()), ln=1)
            pdf.set_draw_color(*ACCENT)
            pdf.set_line_width(0.4)
            y = pdf.get_y()
            pdf.line(pdf.l_margin, y, pdf.l_margin + width, y)
            pdf.ln(2)
        elif kind == "role":
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.set_text_color(*INK)
            pdf.multi_cell(0, 5.5, _latin(line))
        elif kind == "bullet":
            _pdf_bullet(pdf, line)
        elif kind == "text":
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*INK)
            if ":" in line[:28]:  # "Languages: Python, ..." -> bold label
                label, rest = line.split(":", 1)
                pdf.set_font("Helvetica", "B", 10)
                pdf.write(5, _latin(label + ":"))
                pdf.set_font("Helvetica", "", 10)
                pdf.write(5, _latin(rest))
                pdf.ln(5.5)
            else:
                pdf.multi_cell(0, 5, _latin(line))
                pdf.ln(0.5)
    return _pdf_bytes(pdf)


def letter_pdf(text: str) -> bytes:
    pdf = _new_pdf()
    pdf.set_margins(24, 22, 24)
    pdf.set_xy(24, 22)
    pdf.set_font("Times", "", 11.5)
    pdf.set_text_color(*INK)
    for para in text.replace("\r", "").split("\n"):
        if para.strip():
            pdf.multi_cell(0, 6, _latin(para.strip()))
        pdf.ln(2.5)
    return _pdf_bytes(pdf)


def report_pdf(report: dict) -> bytes:
    """A shareable one-file summary of the analysis."""
    pdf = _new_pdf()
    ai = report.get("ai") or {}
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*INK)
    pdf.cell(0, 9, "Resume ATS Report", ln=1)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*MUTED)
    sub = " | ".join(x for x in [ai.get("candidate_name"), ai.get("target_role"), report.get("filename")] if x)
    pdf.cell(0, 5, _latin(sub), ln=1)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 34)
    pdf.set_text_color(*ACCENT)
    pdf.cell(32, 16, str(report["overall_score"]))
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*INK)
    pdf.cell(0, 8, _latin(f"/100  -  {report['rating']}"), ln=1)
    if ai.get("verdict"):
        pdf.set_x(pdf.l_margin + 32)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _latin(ai["verdict"]))
    pdf.ln(4)

    def heading(t):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*ACCENT)
        pdf.cell(0, 7, _latin(t), ln=1)
        pdf.set_text_color(*INK)

    heading("Score breakdown")
    for s in report["scores"]:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(70, 6, _latin(s["label"]))
        pdf.set_fill_color(235, 238, 244)
        x, y = pdf.get_x(), pdf.get_y() + 1.8
        pdf.rect(x, y, 80, 2.6, "F")
        pdf.set_fill_color(*ACCENT)
        pdf.rect(x, y, 80 * s["score"] / 100, 2.6, "F")
        pdf.set_x(x + 84)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, str(s["score"]), ln=1)

    kw = report.get("keywords")
    if kw and kw.get("total"):
        heading(f"Keywords ({len(kw['matched'])}/{kw['total']} matched)")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 5.5, "Missing:", ln=1)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _latin(", ".join(k["term"] for k in kw["missing"]) or "None"))
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 5.5, "Matched:", ln=1)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _latin(", ".join(k["term"] for k in kw["matched"]) or "None"))

    if ai.get("strengths"):
        heading("Strengths")
        for s in ai["strengths"]:
            _pdf_bullet(pdf, s)

    heading("Improvement plan")
    items = [(s["priority"], s["title"], s["detail"]) for s in ai.get("suggestions", [])]
    items += [(i["severity"], i["title"], i["fix"]) for i in report.get("issues", [])]
    for sev, title, detail in items:
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 5, _latin(f"[{sev.upper()}] {title}"))
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 4.8, _latin(detail))
        pdf.set_text_color(*INK)
        pdf.ln(1.5)
    return _pdf_bytes(pdf)


# --------------------------------------------------------------------------- DOCX
def _bottom_border(paragraph, color="4F46E5"):
    p_pr = paragraph._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "8"), ("w:space", "1"), ("w:color", color)):
        bottom.set(qn(k), v)
    bdr.append(bottom)
    p_pr.append(bdr)


def _base_doc(font="Calibri", size=10.5):
    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Inches(0.75)
        s.top_margin = s.bottom_margin = Inches(0.6)
    normal = doc.styles["Normal"]
    normal.font.name = font
    normal.font.size = Pt(size)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), font)
    normal.paragraph_format.space_after = Pt(2)
    return doc


def _docx_bytes(doc) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def resume_docx(text: str) -> bytes:
    doc = _base_doc()
    for kind, line in parse_resume(text):
        if kind == "blank":
            continue
        if kind == "name":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(line)
            r.bold, r.font.size, r.font.color.rgb = True, Pt(22), RGBColor(*INK)
        elif kind == "contact":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(line)
            r.font.size, r.font.color.rgb = Pt(9.5), RGBColor(*MUTED)
        elif kind == "heading":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(line.upper())
            r.bold, r.font.size, r.font.color.rgb = True, Pt(11.5), RGBColor(*ACCENT)
            _bottom_border(p)
        elif kind == "role":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(5)
            p.add_run(line).bold = True
        elif kind == "bullet":
            p = doc.add_paragraph(line, style="List Bullet")
            p.paragraph_format.space_after = Pt(1)
        else:
            p = doc.add_paragraph()
            if ":" in line[:28]:
                label, rest = line.split(":", 1)
                p.add_run(label + ":").bold = True
                p.add_run(rest)
            else:
                p.add_run(line)
    return _docx_bytes(doc)


def letter_docx(text: str) -> bytes:
    doc = _base_doc(font="Georgia", size=11)
    for s in doc.sections:
        s.left_margin = s.right_margin = Inches(1)
        s.top_margin = s.bottom_margin = Inches(1)
    for para in text.replace("\r", "").split("\n"):
        p = doc.add_paragraph(para.strip())
        p.paragraph_format.space_after = Pt(6)
    return _docx_bytes(doc)
