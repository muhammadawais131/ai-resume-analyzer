"""Dark 'tech' design system and HTML components for the ResumeIQ UI."""
import html

import streamlit as st

APP_NAME = "ResumeIQ"
TAGLINE = "AI Resume Scanner"

# severity -> (label, color)
SEVERITY = {
    "critical": ("Critical", "#f87171"),
    "high": ("High", "#fb923c"),
    "medium": ("Medium", "#fbbf24"),
    "low": ("Low", "#38bdf8"),
}


def esc(v) -> str:
    return html.escape(str(v or ""))


def score_color(score: float) -> str:
    if score >= 85:
        return "#34d399"
    if score >= 70:
        return "#a3e635"
    if score >= 55:
        return "#fbbf24"
    return "#f87171"


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
  --bg: #070b14; --panel: rgba(15, 22, 38, .78); --line: rgba(148, 163, 184, .14); --line-2: rgba(148, 163, 184, .24);
  --ink: #f1f5f9; --ink-2: #cbd5e1; --muted: #8b9ab3;
  --cyan: #22d3ee; --violet: #8b5cf6; --green: #34d399; --red: #f87171;
  --grad: linear-gradient(135deg, #22d3ee 0%, #8b5cf6 100%);
  --mono: 'JetBrains Mono', ui-monospace, monospace;
}
html, body, .stApp, .stMarkdown, button, input, textarea, select, p, label {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif !important;
}
.stApp {
  background:
    radial-gradient(900px 500px at 10% -10%, rgba(139, 92, 246, .20), transparent 60%),
    radial-gradient(800px 500px at 100% 0%, rgba(34, 211, 238, .13), transparent 60%),
    linear-gradient(rgba(148, 163, 184, .045) 1px, transparent 1px) 0 0 / 44px 44px,
    linear-gradient(90deg, rgba(148, 163, 184, .045) 1px, transparent 1px) 0 0 / 44px 44px,
    var(--bg);
}
.block-container { padding-top: 1.2rem; padding-bottom: 4rem; max-width: 1180px; }
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }

/* Cards = bordered containers */
[data-testid="stVerticalBlockBorderWrapper"], div[class*="st-key-card"] {
  background: var(--panel) !important; border: 1px solid var(--line) !important; border-radius: 18px !important;
  backdrop-filter: blur(10px); box-shadow: 0 20px 50px -20px rgba(0, 0, 0, .6);
}
div.st-key-card_scan { border: 1px solid rgba(139, 92, 246, .35) !important;
  box-shadow: 0 0 0 1px rgba(34, 211, 238, .06), 0 30px 80px -30px rgba(139, 92, 246, .45) !important; }

/* Buttons */
.stButton button, .stDownloadButton button { border-radius: 12px; font-weight: 600; transition: all .18s ease; }
.stButton button[kind="secondary"], .stDownloadButton button[kind="secondary"] {
  background: rgba(148, 163, 184, .06); border: 1px solid var(--line-2); color: var(--ink-2); }
.stButton button[kind="secondary"]:hover, .stDownloadButton button[kind="secondary"]:hover {
  border-color: var(--cyan); color: var(--cyan); background: rgba(34, 211, 238, .06); }
.stButton button[kind="primary"], .stDownloadButton button[kind="primary"] {
  background: var(--grad); border: 0; color: #fff; box-shadow: 0 10px 30px -8px rgba(139, 92, 246, .6); }
.stButton button[kind="primary"]:hover, .stDownloadButton button[kind="primary"]:hover {
  transform: translateY(-1px); box-shadow: 0 14px 36px -8px rgba(34, 211, 238, .55); filter: brightness(1.08); }
.st-key-scan_btn button { height: 3.3rem; font-size: 1.05rem; letter-spacing: .01em; }

/* Inputs */
[data-testid="stFileUploaderDropzone"] {
  background: rgba(34, 211, 238, .03); border: 1.5px dashed rgba(34, 211, 238, .35); border-radius: 14px; padding: 1.5rem 1rem; }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--cyan); background: rgba(34, 211, 238, .07); }
.stTextArea textarea, .stTextInput input { border-radius: 12px !important; font-size: .95rem; line-height: 1.55; }
.stTextArea textarea:focus, .stTextInput input:focus { border-color: var(--violet) !important; }

/* Step navigation (segmented control) */
.st-key-step_nav [data-testid="stButtonGroup"] > div { width: 100%; display: flex; }
.st-key-step_nav button { flex: 1; height: 3rem; font-weight: 700; font-size: .95rem; }
.st-key-step_nav button[kind*="Active"] { background: var(--grad) !important; color: #fff !important; border-color: transparent !important; }

[data-testid="stExpander"] details { border-radius: 14px; border-color: var(--line); background: rgba(15, 22, 38, .55); }
[data-testid="stExpander"] summary { font-weight: 600; }
[data-testid="stCode"] pre, .stCode pre { border-radius: 12px; border: 1px solid var(--line); }
.stProgress > div > div > div > div { background: var(--grad); }

/* ---------- components ---------- */
.riq-nav { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.riq-brand { display: flex; align-items: center; gap: .65rem; }
.riq-logo { width: 2.3rem; height: 2.3rem; border-radius: 11px; background: var(--grad); display: grid; place-items: center;
  font-family: var(--mono); font-weight: 700; color: #fff; box-shadow: 0 0 24px rgba(139, 92, 246, .5); }
.riq-brand .nm { font-weight: 800; font-size: 1.15rem; color: var(--ink); letter-spacing: -.02em; line-height: 1.1; }
.riq-brand .tg { font-family: var(--mono); font-size: .68rem; color: var(--muted); letter-spacing: .08em; text-transform: uppercase; }
.riq-status { display: inline-flex; align-items: center; gap: .45rem; font-family: var(--mono); font-size: .72rem; font-weight: 700;
  padding: .35rem .75rem; border-radius: 999px; border: 1px solid; letter-spacing: .04em; text-transform: uppercase; }
.riq-status .dot { width: .45rem; height: .45rem; border-radius: 50%; box-shadow: 0 0 10px currentColor; background: currentColor; }

.riq-hero { text-align: center; padding: 2.6rem 1rem 1.8rem; }
.riq-kicker { font-family: var(--mono); font-size: .78rem; color: var(--cyan); letter-spacing: .14em; text-transform: uppercase; }
.riq-hero h1 { font-size: clamp(2.1rem, 5vw, 3.6rem); font-weight: 800; letter-spacing: -.035em; color: var(--ink);
  line-height: 1.06; margin: .8rem 0 .9rem; padding: 0; }
.riq-hero h1 span { background: var(--grad); -webkit-background-clip: text; background-clip: text; color: transparent; }
.riq-hero p { color: var(--muted); font-size: 1.1rem; max-width: 600px; margin: 0 auto; line-height: 1.6; }

.riq-label { display: flex; align-items: center; gap: .55rem; margin-bottom: .55rem; }
.riq-label .n { font-family: var(--mono); font-size: .72rem; font-weight: 700; color: var(--cyan); border: 1px solid rgba(34, 211, 238, .4);
  border-radius: 6px; padding: .05rem .4rem; }
.riq-label .t { font-weight: 700; color: var(--ink); }
.riq-label .o { font-family: var(--mono); font-size: .66rem; color: var(--muted); border: 1px solid var(--line-2); border-radius: 999px;
  padding: .05rem .5rem; text-transform: uppercase; letter-spacing: .06em; }

.riq-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 2.4rem; }
.riq-stepc { border: 1px solid var(--line); border-radius: 16px; padding: 1.1rem 1.2rem; background: rgba(15, 22, 38, .5); }
.riq-stepc .n { font-family: var(--mono); font-size: .8rem; font-weight: 700; background: var(--grad); -webkit-background-clip: text;
  background-clip: text; color: transparent; }
.riq-stepc h4 { margin: .35rem 0 .25rem; color: var(--ink); font-size: 1rem; font-weight: 700; padding: 0; }
.riq-stepc p { margin: 0; color: var(--muted); font-size: .88rem; line-height: 1.5; }
@media (max-width: 760px) { .riq-steps { grid-template-columns: 1fr; } }

.riq-h { font-size: 1.02rem; font-weight: 700; color: var(--ink); margin: 0 0 .25rem; display: flex; align-items: center; gap: .5rem; }
.riq-sub { color: var(--muted); font-size: .87rem; line-height: 1.5; margin: 0 0 .8rem; }
.riq-p { color: var(--ink-2); line-height: 1.65; margin: 0; }
.riq-mono { font-family: var(--mono); }

.riq-score { display: flex; gap: 1.5rem; align-items: center; }
.riq-ring { position: relative; flex: none; filter: drop-shadow(0 0 18px rgba(139, 92, 246, .25)); }
.riq-ring .val { position: absolute; inset: 0; display: grid; place-items: center; text-align: center; }
.riq-ring .num { font-family: var(--mono); font-size: 2.8rem; font-weight: 700; line-height: 1; color: var(--ink); }
.riq-ring .of { font-family: var(--mono); font-size: .68rem; color: var(--muted); letter-spacing: .08em; margin-top: .2rem; }
.riq-tag { display: inline-block; font-family: var(--mono); font-weight: 700; font-size: .72rem; padding: .25rem .65rem; border-radius: 999px;
  letter-spacing: .06em; text-transform: uppercase; border: 1px solid; }
.riq-verdict { font-size: 1.12rem; font-weight: 700; color: var(--ink); line-height: 1.4; margin: .6rem 0 .4rem; }
@media (max-width: 760px) { .riq-score { flex-direction: column; text-align: center; } }

.riq-bars { display: flex; flex-direction: column; gap: .8rem; }
.riq-bar .top { display: flex; justify-content: space-between; font-size: .87rem; margin-bottom: .3rem; }
.riq-bar .lbl { color: var(--ink-2); font-weight: 600; }
.riq-bar .sc { font-family: var(--mono); font-weight: 700; }
.riq-bar .track { height: .45rem; background: rgba(148, 163, 184, .12); border-radius: 999px; overflow: hidden; }
.riq-bar .fill { height: 100%; border-radius: 999px; box-shadow: 0 0 12px currentColor; }

.riq-chips { display: flex; flex-wrap: wrap; gap: .45rem; }
.riq-chip { display: inline-flex; align-items: center; gap: .35rem; padding: .32rem .7rem; border-radius: 8px; font-size: .84rem;
  font-weight: 600; border: 1px solid; font-family: var(--mono); }
.riq-chip.ok { background: rgba(52, 211, 153, .08); color: #6ee7b7; border-color: rgba(52, 211, 153, .3); }
.riq-chip.bad { background: rgba(248, 113, 113, .08); color: #fca5a5; border-color: rgba(248, 113, 113, .3); }
.riq-chip.alt { background: rgba(148, 163, 184, .06); color: var(--muted); border-color: var(--line-2); border-style: dashed; }

.riq-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: .55rem; }
.riq-list li { display: flex; gap: .6rem; color: var(--ink-2); line-height: 1.5; font-size: .93rem; }
.riq-list li .b { flex: none; color: var(--green); font-weight: 800; }

.riq-fix { border: 1px solid var(--line); border-radius: 14px; padding: .95rem 1.1rem; background: rgba(15, 22, 38, .6); position: relative; overflow: hidden; }
.riq-fix::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--c); box-shadow: 0 0 14px var(--c); }
.riq-fix .hd { display: flex; align-items: center; gap: .6rem; flex-wrap: wrap; margin-bottom: .3rem; }
.riq-fix .tt { font-weight: 700; color: var(--ink); font-size: 1rem; }
.riq-fix .dt { color: var(--ink-2); font-size: .91rem; line-height: 1.55; margin: 0; }
.riq-fix .fx { margin-top: .6rem; font-size: .88rem; color: #c4b5fd; background: rgba(139, 92, 246, .1);
  border: 1px solid rgba(139, 92, 246, .25); padding: .5rem .75rem; border-radius: 10px; line-height: 1.5; }
.riq-fix.done { opacity: .45; }
.riq-fix.done .tt { text-decoration: line-through; }

.riq-compare { display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; }
.riq-compare .side { border-radius: 12px; padding: .8rem .95rem; font-size: .92rem; line-height: 1.55; border: 1px solid; }
.riq-compare .before { background: rgba(248, 113, 113, .06); border-color: rgba(248, 113, 113, .25); color: #fecaca; }
.riq-compare .after { background: rgba(52, 211, 153, .06); border-color: rgba(52, 211, 153, .3); color: #d1fae5; }
.riq-compare .lab { font-family: var(--mono); font-size: .66rem; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; margin-bottom: .35rem; opacity: .8; }
@media (max-width: 760px) { .riq-compare { grid-template-columns: 1fr; } }

.riq-delta { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; padding: 1rem 1.2rem; border-radius: 16px;
  background: linear-gradient(135deg, rgba(52, 211, 153, .1), rgba(139, 92, 246, .1)); border: 1px solid rgba(52, 211, 153, .3); }
.riq-delta .n { font-family: var(--mono); font-size: 2rem; font-weight: 700; }
.riq-delta .arrow { font-size: 1.4rem; color: var(--muted); }

.riq-footer { text-align: center; color: var(--muted); font-size: .78rem; margin-top: 3rem; font-family: var(--mono); letter-spacing: .03em; }
</style>
"""


def inject_css():
    st.html(CSS)


# --------------------------------------------------------------------------- shared
def nav(ok: bool, ai: bool, show_status=True):
    if not ok:
        color, text = "#f87171", "API offline"
    elif not ai:
        color, text = "#fbbf24", "AI key missing"
    else:
        color, text = "#34d399", "System online"
    status = (f'<span class="riq-status" style="color:{color};border-color:{color}55"><span class="dot"></span>{text}</span>'
              if show_status else "")
    st.html(f"""<div class="riq-nav"><div class="riq-brand"><div class="riq-logo">R</div>
      <div><div class="nm">{APP_NAME}</div><div class="tg">{TAGLINE}</div></div></div>{status}</div>""")


def footer():
    st.html(f'<div class="riq-footer">{APP_NAME} · your resume is only used to generate your report · '
            'AI can make mistakes, always review before sending</div>')


# --------------------------------------------------------------------------- landing
def hero():
    st.html("""<div class="riq-hero"><div class="riq-kicker">// ATS resume scanner</div>
      <h1>Will your resume pass<br>the <span>ATS filter?</span></h1>
      <p>Upload your resume and get your score in about 30 seconds. Then let AI fix it for you.</p></div>""")


def label(n, title, optional=None):
    opt = f'<span class="o">{esc(optional)}</span>' if optional else ""
    st.html(f'<div class="riq-label"><span class="n">{n}</span><span class="t">{esc(title)}</span>{opt}</div>')


def how_it_works():
    steps = [("01", "Upload", "Drop your resume. Add the job post for a more precise match."),
             ("02", "Get your score", "See your ATS score, missing keywords and what's holding you back."),
             ("03", "Fix & download", "Follow the fix list, or let AI rewrite it, then download PDF or Word.")]
    cards = "".join(f'<div class="riq-stepc"><div class="n">{n}</div><h4>{t}</h4><p>{d}</p></div>' for n, t, d in steps)
    st.html(f'<div class="riq-steps">{cards}</div>')


# --------------------------------------------------------------------------- results
def section(title, sub=None):
    st.html(f'<div class="riq-h">{title}</div>' + (f'<p class="riq-sub">{sub}</p>' if sub else ""))


def ring(score: int, size=164, stroke=12):
    r = (size - stroke) / 2
    circ = 2 * 3.14159 * r
    off = circ * (1 - max(0, min(100, score)) / 100)
    c = score_color(score)
    return f"""<div class="riq-ring" style="width:{size}px;height:{size}px">
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      <defs><linearGradient id="rg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c}"/>
      <stop offset="1" stop-color="{c}" stop-opacity=".55"/></linearGradient></defs>
      <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="rgba(148,163,184,.12)" stroke-width="{stroke}"/>
      <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="url(#rg)" stroke-width="{stroke}"
        stroke-linecap="round" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{off:.1f}"
        transform="rotate(-90 {size/2} {size/2})"/>
    </svg><div class="val"><div><div class="num">{score}</div><div class="of">/ 100</div></div></div></div>"""


VERDICTS = {
    "excellent": "Your resume is ready to send.",
    "good": "Good resume. A few fixes will put you near the top.",
    "fair": "You may pass some filters, but there are clear gaps.",
    "poor": "This resume is likely to be filtered out. Let's fix it.",
}


def score_card(report):
    score = report["overall_score"]
    c = score_color(score)
    ai = report.get("ai") or {}
    verdict = ai.get("verdict") or VERDICTS[report["rating_key"]]
    summary = ai.get("summary") or ""
    kind = "ATS match score" if report.get("has_job_description") else "ATS readiness score"
    st.html(f"""<div class="riq-score">{ring(score)}<div>
      <div class="riq-mono" style="font-size:.7rem;color:var(--muted);letter-spacing:.1em;text-transform:uppercase">{kind}</div>
      <div style="margin-top:.45rem"><span class="riq-tag" style="color:{c};border-color:{c}66;background:{c}14">{esc(report['rating'])}</span></div>
      <div class="riq-verdict">{esc(verdict)}</div>
      <p class="riq-p" style="font-size:.9rem;color:var(--muted)">{esc(summary)}</p></div></div>""")


def score_bars(scores):
    rows = []
    for s in scores:
        c = score_color(s["score"])
        rows.append(f"""<div class="riq-bar" title="{esc(s['description'])}"><div class="top">
        <span class="lbl">{esc(s['label'])}</span><span class="sc" style="color:{c}">{s['score']}</span></div>
        <div class="track"><div class="fill" style="width:{max(3, s['score'])}%;background:{c};color:{c}"></div></div></div>""")
    st.html(f'<div class="riq-h">Score breakdown</div><p class="riq-sub">Hover a bar to see what it measures.</p>'
            f'<div class="riq-bars">{"".join(rows)}</div>')


def chips(items, kind):
    if not items:
        return '<span class="riq-sub">None</span>'
    icon = {"ok": "✓", "bad": "+", "alt": "≈"}.get(kind, "")
    return '<div class="riq-chips">' + "".join(
        f'<span class="riq-chip {kind}">{icon} {esc(i["term"] if isinstance(i, dict) else i)}</span>' for i in items) + "</div>"


def checklist_items(title, items):
    lis = "".join(f'<li><span class="b">✓</span><span>{esc(i)}</span></li>' for i in items)
    st.html(f'<div class="riq-h">{title}</div><ul class="riq-list" style="margin-top:.6rem">{lis}</ul>')


def fix_card(item, number, done=False):
    name, c = SEVERITY.get(item.get("severity"), SEVERITY["medium"])
    fix = item.get("fix") or item.get("example") or ""
    fix_label = "Example" if not item.get("fix") and item.get("example") else "How to fix"
    fix_html = f'<div class="fx"><b>{fix_label}:</b> {esc(fix)}</div>' if fix else ""
    st.html(f"""<div class="riq-fix {'done' if done else ''}" style="--c:{c}">
      <div class="hd"><span class="riq-mono" style="color:var(--muted);font-size:.75rem">#{number:02d}</span>
      <span class="riq-tag" style="color:{c};border-color:{c}55;background:{c}12;font-size:.64rem">{name}</span>
      <span class="riq-mono" style="color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.06em">{esc(item.get('category'))}</span></div>
      <div class="tt">{esc(item['title'])}</div><p class="dt">{esc(item.get('detail'))}</p>{fix_html}</div>""")


def compare(original, improved, why=""):
    why_html = f'<p class="riq-sub" style="margin:.5rem 0 0">💡 {esc(why)}</p>' if why else ""
    st.html(f"""<div class="riq-compare">
      <div class="side before"><div class="lab">Before</div>{esc(original)}</div>
      <div class="side after"><div class="lab">After</div>{esc(improved)}</div></div>{why_html}""")


def delta(before, after):
    diff = after - before
    c = "#34d399" if diff >= 0 else "#f87171"
    st.html(f"""<div class="riq-delta"><span class="riq-mono" style="color:var(--muted);font-size:.75rem;letter-spacing:.08em">NEW SCORE</span>
      <span class="n" style="color:{score_color(before)}">{before}</span><span class="arrow">→</span>
      <span class="n" style="color:{score_color(after)}">{after}</span>
      <span class="riq-tag" style="color:{c};border-color:{c}66;background:{c}14">{'+' if diff >= 0 else ''}{diff} points</span></div>""")
