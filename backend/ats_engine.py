"""Deterministic, explainable ATS scoring.

The engine works in two phases:
1. ``analyze_structure(text)`` - parses sections, bullets, contact info, language quality.
   It needs nothing but the resume text, so it runs before the AI call.
2. ``build_report(...)`` - combines the structure with job-description keywords and
   (optionally) semantic similarity into scores, a checklist and prioritized issues.
"""
import re

from skills_data import (
    ACTION_VERBS, BUZZWORDS, HARD_SKILLS, SECTION_ALIASES, SKILL_ALIASES, SOFT_SKILLS,
    WEAK_PHRASES,
)

BULLET_CHARS = "-•●▪◦*➢►✓■○◆·–—»>❖✔→"
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
_URL_RE = re.compile(r"(https?://|www\.)\S+|\b[\w-]+\.(com|io|dev|me|net|org|app)(/\S*)?\b", re.I)
_YEAR_RE = re.compile(r"\b(19[89]\d|20[0-4]\d)\b")
_QUANT_RE = re.compile(
    r"(\d+(\.\d+)?\s?%"
    r"|[$€£₹]\s?\d"
    r"|\b\d+(\.\d+)?\s?(k|m|b|x|\+)(?=\W|$)"
    r"|\b\d{1,3}(,\d{3})+\b"
    r"|\b(?!(19|20)\d{2}\b)\d{2,}\b"
    r"|\b\d+\s+(users|clients|customers|people|members|projects|engineers|developers|"
    r"employees|students|hours|days|weeks|months|countries|stores|reports|applications|apps|"
    r"features|tickets|teams|products|services|websites|sites|accounts|languages|branches))",
    re.I,
)

_PRETTY = {
    "c++": "C++", "c#": "C#", "node.js": "Node.js", "next.js": "Next.js", "express.js": "Express.js",
    "javascript": "JavaScript", "typescript": "TypeScript", "github": "GitHub", "gitlab": "GitLab",
    "github actions": "GitHub Actions", "gitlab ci": "GitLab CI", "mysql": "MySQL",
    "postgresql": "PostgreSQL", "mongodb": "MongoDB", "sqlite": "SQLite", "graphql": "GraphQL",
    "fastapi": "FastAPI", "nestjs": "NestJS", "pytorch": "PyTorch", "tensorflow": "TensorFlow",
    "scikit-learn": "scikit-learn", "numpy": "NumPy", "opencv": "OpenCV", "phpunit": "PHPUnit",
    "wordpress": "WordPress", "hubspot": "HubSpot", "quickbooks": "QuickBooks", "dynamodb": "DynamoDB",
    "ci/cd": "CI/CD", "tcp/ip": "TCP/IP", "a/b testing": "A/B Testing", "rest api": "REST API",
    "restful": "RESTful", ".net": ".NET", "asp.net": "ASP.NET", "jquery": "jQuery", "git": "Git",
    "vue": "Vue", "jest": "Jest", "vite": "Vite", "dbt": "dbt", "ios": "iOS", "llm": "LLM",
    "powershell": "PowerShell", "javascript es6": "JavaScript", "power bi": "Power BI",
}


def pretty(term: str) -> str:
    if term in _PRETTY:
        return _PRETTY[term]
    words = []
    for w in term.split():
        words.append(w.upper() if len(w) <= 3 and w.isalpha() else w[:1].upper() + w[1:])
    return " ".join(words)


def canonical(term: str) -> str:
    t = re.sub(r"\s+", " ", term.strip().lower())
    return SKILL_ALIASES.get(t, t)


def _term_regex(term: str):
    return re.compile(r"(?<![\w+#.])" + re.escape(term) + r"(?![\w+#])", re.I)


def count_term(text: str, term: str) -> int:
    """Count a skill in text, including its known aliases."""
    variants = {term} | {a for a, c in SKILL_ALIASES.items() if c == term}
    # Also allow simple separator variations: "problem-solving" vs "problem solving".
    variants |= {v.replace("-", " ") for v in variants} | {v.replace(" ", "-") for v in variants}
    return sum(len(_term_regex(v).findall(text)) for v in variants)


# --------------------------------------------------------------------------- phase 1
def _clean_header(line: str) -> str:
    line = line.strip().strip(BULLET_CHARS + ":|#").strip().lower()
    return re.sub(r"\s+", " ", line)


def detect_sections(lines):
    """Return {section: [line indexes]} and the header line index for each section."""
    alias_lookup = {a: name for name, aliases in SECTION_ALIASES.items() for a in aliases}
    headers = []
    for i, line in enumerate(lines):
        cleaned = _clean_header(line)
        if not cleaned or len(cleaned) > 40:
            continue
        name = alias_lookup.get(cleaned)
        if name is None and line.strip().isupper() and len(cleaned.split()) <= 4:
            name = next((n for a, n in alias_lookup.items() if a in cleaned), None)
        if name:
            headers.append((i, name))

    sections = {}
    for idx, (start, name) in enumerate(headers):
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        sections.setdefault(name, []).extend(range(start + 1, end))
    return sections


def _is_continuation(current: str, line: str) -> bool:
    if line[0].islower() or line[0] in ",;&(%":
        return True
    # Otherwise only if the bullet clearly isn't finished and the line isn't a heading / job line.
    return (not current.rstrip().endswith((".", "!", "?", ":"))
            and " | " not in line and not line.isupper() and not _YEAR_RE.search(line)
            and len(line.split()) <= 14)


def extract_bullets(lines, sections):
    """Find achievement statements: marker bullets, else long lines in experience/projects."""
    bullets = []
    current = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line and line[0] in BULLET_CHARS and (len(line) == 1 or not line[1].isdigit()):
            body = line.lstrip(BULLET_CHARS).strip()
            if not body and i + 1 < len(lines):  # bullet glyph on its own line (common in PDFs)
                i += 1
                body = lines[i].strip()
            if current:
                bullets.append(current)
            current = body
        elif current is not None and line and _is_continuation(current, line):
            current += " " + line  # bullet text wrapped onto the next line (common in PDFs)
        else:
            if current:
                bullets.append(current)
            current = None
        i += 1
    if current:
        bullets.append(current)
    bullets = [b for b in bullets if len(b.split()) >= 4]

    if len(bullets) >= 3:
        return bullets, True

    # Fallback: sentence-like lines inside experience/projects (or whole doc).
    scope = sections.get("experience", []) + sections.get("projects", [])
    scope_lines = [lines[i] for i in scope] if scope else lines
    statements = [l.strip() for l in scope_lines if len(l.split()) >= 7]
    return statements, False


def analyze_structure(text: str, meta: dict | None = None) -> dict:
    meta = meta or {}
    lines = [l for l in text.split("\n")]
    lower = text.lower()
    sections = detect_sections(lines)
    bullets, has_marker_bullets = extract_bullets(lines, sections)

    quantified = [b for b in bullets if _QUANT_RE.search(b)]
    verb_led = [b for b in bullets if re.sub(r"[^a-z]", "", b.split()[0].lower()) in ACTION_VERBS]
    weak_bullets = [
        b for b in bullets
        if not _QUANT_RE.search(b)
        or re.sub(r"[^a-z]", "", b.split()[0].lower()) not in ACTION_VERBS
        or any(p in b.lower() for p in WEAK_PHRASES)
    ]

    phones = [p for p in _PHONE_RE.findall(text) if 9 <= len(re.sub(r"\D", "", p)) <= 15]
    urls = [m.group(0) for m in _URL_RE.finditer(text) if "@" not in m.group(0)]
    contact = {
        "email": bool(_EMAIL_RE.search(text)),
        "phone": bool(phones),
        "linkedin": "linkedin" in lower,
        "portfolio": any(k in lower for k in ("github.com", "behance", "dribbble", "portfolio"))
        or any("linkedin" not in u.lower() for u in urls),
    }

    words = re.findall(r"[A-Za-z][A-Za-z'+#.-]*", text)
    word_count = len(words)
    pronouns = len(re.findall(r"\b(i|me|my|mine|myself)\b", lower))
    weak_found = sorted({p for p in WEAK_PHRASES if p in lower})
    buzz_found = sorted({b for b in BUZZWORDS if re.search(r"\b" + re.escape(b) + r"\b", lower)})
    dense_lines = [l for l in lines if len(l.split()) > 45]
    exp_text = "\n".join(lines[i] for i in sections.get("experience", []))
    exp_has_dates = bool(_YEAR_RE.search(exp_text)) if exp_text else bool(_YEAR_RE.search(text))
    icon_glyphs = len(re.findall(r"[-�]", text))

    return {
        "text": text,
        "lines": lines,
        "sections_found": {name: name in sections for name in SECTION_ALIASES},
        "bullets": bullets,
        "has_marker_bullets": has_marker_bullets,
        "quantified": quantified,
        "verb_led": verb_led,
        "weak_bullets": weak_bullets[:8],
        "contact": contact,
        "word_count": word_count,
        "pages": meta.get("pages", 1),
        "pronouns": pronouns,
        "weak_phrases": weak_found,
        "buzzwords": buzz_found,
        "dense_lines": len(dense_lines),
        "exp_has_dates": exp_has_dates,
        "icon_glyphs": icon_glyphs,
        "has_tables": meta.get("has_tables", False),
    }


# --------------------------------------------------------------------------- keywords
def extract_jd_keywords(job_text: str, ai_keywords: dict | None = None):
    """Return list of {term, type, importance} found in the job description."""
    jd_lower = job_text.lower()
    found = {}

    def add(term, kind, count):
        term = canonical(term)
        if not term or len(term) > 40:
            return
        prev = found.get(term)
        if prev is None or count > prev["count"]:
            found[term] = {"term": term, "type": kind, "count": max(count, 1)}

    for skill in HARD_SKILLS | set(SKILL_ALIASES):
        c = count_term(jd_lower, canonical(skill))
        if c:
            add(skill, "hard", c)
    for skill in SOFT_SKILLS:
        c = count_term(jd_lower, skill)
        if c:
            add(skill, "soft", c)

    if ai_keywords:
        jd_stems = [_stem(t) for t in re.findall(r"[a-z0-9+#]+", jd_lower)]
        for kind, key in (("hard", "hard_skills"), ("soft", "soft_skills")):
            for term in ai_keywords.get(key, []) or []:
                if not (isinstance(term, str) and term.strip()):
                    continue
                c = canonical(term)
                hits = count_term(jd_lower, c)
                # Only keep AI keywords that really appear in the job post (exactly or as a phrase
                # in another word form, e.g. "model deployment" <- "deploying models").
                # The AI sometimes adds plausible skills the employer never asked for.
                if hits or (" " in c and _fuzzy_phrase_hit(jd_stems, c, window=6)):
                    add(term, kind, hits or 1)

    items = sorted(found.values(), key=lambda k: (k["type"] != "hard", -k["count"], k["term"]))
    for k in items:
        k["importance"] = "high" if k["count"] >= 2 or k["type"] == "hard" else "medium"
    items = items[:40]
    _mark_alternatives(jd_lower, items)
    return items


def _first_span(text: str, term: str):
    variants = {term} | {a for a, c in SKILL_ALIASES.items() if c == term}
    spans = [m.span() for v in variants for m in [_term_regex(v).search(text)] if m]
    return min(spans) if spans else None


_ALT_SEP = re.compile(r"\s*(,|/|\bor\b|,\s*or\b|\band/or\b|,\s*and/or\b)\s*")


def _mark_alternatives(jd_lower: str, items):
    """Tag 'either/or' groups, e.g. 'AWS, GCP, or Azure' - knowing ONE of them is enough."""
    located = sorted(((s, k) for k in items for s in [_first_span(jd_lower, k["term"])] if s),
                     key=lambda x: x[0])
    group, has_or, gid = [], False, 0

    def close():
        nonlocal gid
        if len(group) >= 2 and has_or:
            gid += 1
            for k in group:
                k["group"] = gid

    for i, (span, k) in enumerate(located):
        if group:
            between = jd_lower[located[i - 1][0][1]:span[0]]
            if _ALT_SEP.fullmatch(between):
                group.append(k)
                has_or = has_or or "or" in between or "/" in between
                continue
            close()
        group, has_or = [k], False
    close()


_FILLER = {"of", "and", "the", "with", "for", "to", "in", "on", "a", "an", "&"}


def _stem(word: str) -> str:
    return re.sub(r"(ments?|ing|ed|es|s)$", "", word)[:5]


def _fuzzy_phrase_hit(tokens_stems, term: str, window=8) -> bool:
    """'model deployment' matches 'deployed ML models': all word stems within a short window."""
    need = {_stem(w) for w in re.findall(r"[a-z0-9+#]+", term) if w not in _FILLER}
    if len(need) < 2:
        return False
    for i in range(len(tokens_stems)):
        if need <= set(tokens_stems[i:i + window]):
            return True
    return False


def match_keywords(resume_text: str, jd_keywords):
    """Return (matched, missing, covered). 'covered' = alternatives satisfied by another option."""
    lower = resume_text.lower()
    stems = [_stem(t) for t in re.findall(r"[a-z0-9+#]+", lower)]
    results = []
    for k in jd_keywords:
        hits = count_term(lower, k["term"])
        if not hits and " " in k["term"] and _fuzzy_phrase_hit(stems, k["term"]):
            hits = 1
        # Soft skills in another word form: "communication" <- "communicate", "collaborated".
        if not hits and k["type"] == "soft" and " " not in k["term"] and len(k["term"]) >= 7:
            root = k["term"].replace("-", "")[:-3]
            hits = int(bool(re.search(r"\b" + re.escape(root), lower)))
        results.append((k, hits))

    satisfied_groups = {k.get("group") for k, hits in results if hits and k.get("group")}
    matched, missing, covered = [], [], []
    for k, hits in results:
        item = {"term": pretty(k["term"]), "type": k["type"], "importance": k["importance"],
                "jd_count": k["count"], "resume_count": hits}
        if hits:
            matched.append(item)
        elif k.get("group") in satisfied_groups:
            covered.append(item)
        else:
            missing.append(item)
    return matched, missing, covered


# --------------------------------------------------------------------------- phase 2
def _clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def rating_for(score):
    if score >= 85:
        return "Excellent", "excellent"
    if score >= 70:
        return "Good", "good"
    if score >= 55:
        return "Fair", "fair"
    return "Needs Work", "poor"


def build_report(structure: dict, job_text: str = "", ai_keywords: dict | None = None,
                 semantic_similarity: float | None = None) -> dict:
    s = structure
    has_jd = bool(job_text and job_text.strip())
    checks, issues = [], []

    def check(label, passed, detail, category):
        checks.append({"label": label, "passed": bool(passed), "detail": detail, "category": category})

    def issue(severity, category, title, detail, fix):
        issues.append({"severity": severity, "category": category, "title": title,
                       "detail": detail, "fix": fix, "source": "ats"})

    # ---- Parseability
    # "Unreadable" means almost no text could be extracted (scanned/image PDF). A short but
    # readable resume is handled separately by the length checks below.
    readable = s["word_count"] >= 50
    check("ATS can read your text", readable,
          f"{s['word_count']} words extracted from the file.", "Parsing")
    if not readable:
        issue("critical", "Parsing", "ATS could barely read your resume",
              "Very little text could be extracted. Image-based PDFs, scanned documents or "
              "text inside graphics are invisible to most applicant tracking systems.",
              "Export your resume from Word/Google Docs as a text-based PDF or DOCX.")
    check("No icon fonts or unreadable symbols", s["icon_glyphs"] < 3,
          "Icons often turn into garbage characters in ATS parsers.", "Parsing")
    if s["icon_glyphs"] >= 3:
        issue("medium", "Parsing", "Icons or special glyphs detected",
              f"{s['icon_glyphs']} unreadable symbols were found (often icon fonts next to "
              "phone/email).", "Replace icons with plain-text labels like 'Email:' and 'Phone:'.")
    if s["has_tables"]:
        check("Simple single-column layout", False,
              "Tables were detected. Some ATS read tables out of order.", "Parsing")
        issue("low", "Parsing", "Tables detected in layout",
              "Tables and multi-column layouts can scramble the reading order in older ATS.",
              "Prefer a single-column layout with standard headings.")

    # ---- Contact
    c = s["contact"]
    contact_score = (40 if c["email"] else 0) + (30 if c["phone"] else 0) + \
                    (20 if c["linkedin"] else 0) + (10 if c["portfolio"] else 0)
    check("Email address", c["email"], "Recruiters need a professional email.", "Contact")
    check("Phone number", c["phone"], "Include a reachable phone number with country code.", "Contact")
    check("LinkedIn profile", c["linkedin"], "Most recruiters check LinkedIn before calling.", "Contact")
    check("Portfolio / GitHub / website", c["portfolio"], "Proof of work builds trust.", "Contact")
    if not c["email"] or not c["phone"]:
        missing = " and ".join(x for x, ok in (("email", c["email"]), ("phone", c["phone"])) if not ok)
        issue("critical", "Contact", f"Missing {missing}",
              "Without basic contact details a recruiter cannot reach you, even if you match.",
              "Add your email and phone number at the very top of the resume.")
    if not c["linkedin"]:
        issue("medium", "Contact", "Add your LinkedIn URL",
              "Profiles with a LinkedIn link get more recruiter follow-ups.",
              "Add linkedin.com/in/your-name next to your email and phone.")

    # ---- Structure
    sec = s["sections_found"]
    structure_score = 0
    structure_score += 20 if sec["experience"] or sec["projects"] else 0
    structure_score += 20 if sec["education"] else 0
    structure_score += 20 if sec["skills"] else 0
    structure_score += 15 if sec["summary"] else 0
    structure_score += 10 if (sec["projects"] or sec["certifications"] or sec["achievements"]) else 0
    structure_score += 15 if len(s["bullets"]) >= 5 else 7 if s["bullets"] else 0
    for name, label in (("summary", "Professional summary"), ("experience", "Work experience"),
                        ("education", "Education"), ("skills", "Skills section")):
        check(f"{label} section", sec[name], "Standard headings help ATS map your content.", "Sections")
    if not sec["experience"] and not sec["projects"]:
        issue("high", "Sections", "No 'Experience' section detected",
              "ATS look for a standard heading such as 'Work Experience' to find your jobs.",
              "Use a clear heading: WORK EXPERIENCE (or PROJECTS if you are a fresher).")
    if not sec["skills"]:
        issue("high", "Sections", "No 'Skills' section detected",
              "A dedicated skills section is where ATS look first for keyword matches.",
              "Add a SKILLS section listing tools, technologies and core competencies.")
    if not sec["summary"]:
        issue("medium", "Sections", "Add a professional summary",
              "A 2-3 line summary tells recruiters who you are within 6 seconds.",
              "Write a summary with your title, years of experience, top skills and a key win.")
    if not sec["education"]:
        issue("medium", "Sections", "No 'Education' section detected",
              "Many ATS filters require education information.",
              "Add an EDUCATION section with degree, institution and year.")
    check("Experience includes dates", s["exp_has_dates"],
          "Dates let recruiters understand your timeline.", "Sections")
    if (sec["experience"]) and not s["exp_has_dates"]:
        issue("medium", "Sections", "Experience is missing dates",
              "Roles without dates look suspicious to recruiters and confuse ATS.",
              "Add month/year ranges, e.g. 'Jan 2022 - Present'.")

    # ---- Impact
    n_b = len(s["bullets"])
    q_ratio = len(s["quantified"]) / n_b if n_b else 0
    v_ratio = len(s["verb_led"]) / n_b if n_b else 0
    impact_score = round(min(1, q_ratio / 0.5) * 65 + min(1, v_ratio / 0.7) * 35) if n_b else 25
    check("Achievements are quantified", q_ratio >= 0.3,
          f"{len(s['quantified'])} of {n_b} bullet points contain numbers.", "Impact")
    check("Bullets start with action verbs", v_ratio >= 0.5,
          f"{len(s['verb_led'])} of {n_b} bullet points start with a strong verb.", "Impact")
    check("Uses bullet points", s["has_marker_bullets"],
          "Bullets are easier to scan than paragraphs.", "Impact")
    if n_b and q_ratio < 0.3:
        # Almost no numbers is serious; some numbers but not enough is a medium improvement.
        issue("high" if q_ratio < 0.15 else "medium", "Impact", "Quantify your achievements",
              f"Only {round(q_ratio * 100)}% of your bullets include numbers. Metrics prove impact "
              "and are what recruiters remember.",
              "Add numbers: % improvement, $ saved, users served, team size, time reduced.")
    if n_b and v_ratio < 0.5:
        issue("medium", "Impact", "Start bullets with strong action verbs",
              f"Only {round(v_ratio * 100)}% of bullets begin with an action verb.",
              "Begin each bullet with verbs like Led, Built, Increased, Reduced, Launched.")
    if not s["has_marker_bullets"]:
        issue("medium", "Formatting", "Use bullet points for experience",
              "Paragraph-style experience is hard to scan in the 6-8 seconds a recruiter spends.",
              "Break each role into 3-6 concise bullets of one to two lines each.")

    # ---- Language
    language_score = _clamp(100 - 10 * len(s["weak_phrases"]) - 6 * len(s["buzzwords"])
                            - (15 if s["pronouns"] > 3 else 0))
    check("No weak phrases (e.g. 'responsible for')", not s["weak_phrases"],
          ", ".join(f"'{p}'" for p in s["weak_phrases"]) or "Looks good.", "Language")
    check("No clichés or buzzwords", not s["buzzwords"],
          ", ".join(f"'{b}'" for b in s["buzzwords"]) or "Looks good.", "Language")
    check("Written without personal pronouns", s["pronouns"] <= 3,
          f"'I/me/my' used {s['pronouns']} times.", "Language")
    if s["weak_phrases"]:
        issue("medium", "Language", "Replace passive, weak phrases",
              "Found: " + ", ".join(f"'{p}'" for p in s["weak_phrases"]) + ". These describe "
              "duties rather than results.",
              "Rewrite as outcomes, e.g. 'Responsible for reports' -> 'Automated weekly reports, "
              "saving 6 hours per week'.")
    if s["buzzwords"]:
        issue("low", "Language", "Remove clichés and buzzwords",
              "Found: " + ", ".join(f"'{b}'" for b in s["buzzwords"]) + ". Recruiters skip these.",
              "Show the trait through an achievement instead of claiming it.")
    if s["pronouns"] > 3:
        issue("low", "Language", "Drop personal pronouns",
              "Resumes are conventionally written without 'I', 'me' and 'my'.",
              "Write 'Led a team of 5' instead of 'I led a team of 5'.")

    # ---- Readability / length
    wc = s["word_count"]
    if 400 <= wc <= 900:
        length_pts = 70
    elif 300 <= wc < 400 or 900 < wc <= 1200:
        length_pts = 50
    else:
        length_pts = 25
    avg_len = (sum(len(b.split()) for b in s["bullets"]) / n_b) if n_b else 0
    bullet_pts = 30 if 8 <= avg_len <= 30 else 15 if n_b else 10
    readability_score = _clamp(length_pts + bullet_pts - 5 * s["dense_lines"])
    good_len = 400 <= wc <= 1000
    check("Ideal length (400-1000 words)", good_len, f"Your resume has {wc} words.", "Readability")
    check("Concise bullets (under 30 words)", not n_b or avg_len <= 30,
          f"Average bullet length: {round(avg_len)} words.", "Readability")
    if wc < 300 and readable:
        issue("high", "Readability", "Your resume is too short",
              f"Only {wc} words. Short resumes rarely contain enough keywords to pass ATS filters.",
              "Expand experience with achievements, add projects, skills and certifications.")
    elif wc > 1200:
        issue("medium", "Readability", "Your resume is too long",
              f"{wc} words ({s['pages']} pages). Recruiters prefer 1-2 focused pages.",
              "Trim older or irrelevant roles and keep only the most impactful bullets.")
    if n_b and avg_len > 30:
        issue("low", "Readability", "Bullets are too long",
              f"Your bullets average {round(avg_len)} words.",
              "Keep bullets to 1-2 lines: action + task + measurable result.")

    # ---- Keywords (only with a job description)
    keywords = None
    keyword_score = None
    semantic_score = None
    if has_jd:
        jd_keywords = extract_jd_keywords(job_text, ai_keywords)
        matched, missing, covered = match_keywords(s["text"], jd_keywords)
        # Covered alternatives ("GCP" when you have AWS for "AWS, GCP, or Azure") don't count against you.
        total_w = sum(2 if k["importance"] == "high" else 1 for k in matched + missing)
        got_w = sum(2 if k["importance"] == "high" else 1 for k in matched)
        keyword_score = round(got_w / total_w * 100) if total_w else None
        counted = len(matched) + len(missing)
        keywords = {
            "matched": matched, "missing": missing, "covered": covered,
            "match_rate": round(len(matched) / counted * 100) if counted else 0,
            "total": counted,
        }
        if counted:
            check("Matches 60%+ of job keywords", keywords["match_rate"] >= 60,
                  f"{len(matched)} of {counted} keywords found.", "Keywords")
        hard_missing = [m["term"] for m in missing if m["type"] == "hard"]
        soft_missing = [m["term"] for m in missing if m["type"] == "soft"]
        if hard_missing:
            sev = "critical" if keywords["match_rate"] < 40 else "high"
            n_hm = len(hard_missing)
            issue(sev, "Keywords", f"Missing {n_hm} hard skill{'s' if n_hm != 1 else ''} from the job post",
                  "ATS rank candidates by keyword matches. Missing: " + ", ".join(hard_missing[:10]) + ".",
                  "Add the ones you genuinely have to your Skills section AND mention them in "
                  "experience bullets showing how you used them.")
        if soft_missing:
            issue("low", "Keywords", "Mirror the soft skills the employer asks for",
                  "Not found: " + ", ".join(soft_missing[:6]) + ".",
                  "Demonstrate them inside achievements (e.g. 'Mentored 3 junior developers').")
        if semantic_similarity is not None:
            # text-embedding-3-small: unrelated resume/JD pairs land around 0.30-0.38, strong matches
            # around 0.45-0.55 (short JDs rarely go higher). Map 0.28 -> 0 and 0.55 -> 100.
            semantic_score = round(_clamp((semantic_similarity - 0.28) / 0.27 * 100))
            if semantic_score < 50:
                issue("high", "Relevance", "Resume content is weakly aligned with this role",
                      "The overall wording and experience of your resume differ from what the job "
                      "describes.", "Mirror the job title and responsibilities in your summary and "
                      "most recent role (only where truthful).")

    # ---- Overall
    components = [
        ("keywords", "Keyword Match", keyword_score, 0.30,
         "How many job-post keywords appear in your resume."),
        ("relevance", "Job Relevance", semantic_score, 0.15,
         "AI semantic similarity between your resume and the job."),
        ("impact", "Impact & Achievements", impact_score, 0.18,
         "Quantified results and action-verb bullets."),
        ("structure", "Structure & Sections", structure_score, 0.15,
         "Standard sections ATS look for."),
        ("language", "Language & Tone", language_score, 0.08,
         "Free of weak phrases, clichés and pronouns."),
        ("readability", "Length & Readability", readability_score, 0.07,
         "Length, bullet size and scannability."),
        ("contact", "Contact Info", contact_score, 0.07, "Email, phone, LinkedIn, portfolio."),
    ]
    active = [c for c in components if c[2] is not None]
    total_weight = sum(c[3] for c in active)
    overall = round(sum(c[2] * c[3] for c in active) / total_weight)
    if not readable:
        overall = min(overall, 30)
    rating, rating_key = rating_for(overall)

    issues.sort(key=lambda i: SEVERITY_ORDER[i["severity"]])
    return {
        "overall_score": overall,
        "rating": rating,
        "rating_key": rating_key,
        "has_job_description": has_jd,
        "scores": [{"key": k, "label": l, "score": int(v), "weight": round(w / total_weight * 100),
                    "description": d} for k, l, v, w, d in active],
        "keywords": keywords,
        "sections": s["sections_found"],
        "contact": s["contact"],
        "stats": {
            "word_count": wc,
            "pages": s["pages"],
            "bullet_count": n_b,
            "quantified_bullets": len(s["quantified"]),
            "quantified_ratio": round(q_ratio * 100),
            "action_verb_ratio": round(v_ratio * 100),
        },
        "checks": checks,
        "issues": issues,
    }
