"""Shortlistly - Streamlit frontend.

User journey:  Upload  ->  1. Your score  ->  2. Fix it  ->  3. Download (+ cover letter / interview prep)
"""
import re
import uuid

import streamlit as st

import api
import exporters
import ui

st.set_page_config(page_title=f"{ui.APP_NAME} · {ui.TAGLINE}", page_icon="⚡", layout="wide",
                   initial_sidebar_state="collapsed")
ui.inject_css()

STEPS = ["① Your score", "② Fix it", "③ Download"]
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TOP_FIXES = 5

ss = st.session_state
for key, default in {"client_id": uuid.uuid4().hex, "report": None, "rewrite": None,
                     "rewrite_score": None, "cover": None, "questions": None, "done": set(),
                     "step_nav": STEPS[0], "last_step": STEPS[0]}.items():
    ss.setdefault(key, default)


# --------------------------------------------------------------------------- state helpers
def reset_outputs():
    ss.rewrite = ss.rewrite_score = ss.cover = ss.questions = None
    ss.done = set()
    ss.step_nav = ss.last_step = STEPS[0]
    for k in list(ss.keys()):
        if k in ("rewrite_edit", "cover_edit") or str(k).startswith("done_"):
            del ss[k]


def new_scan():
    ss.report = None
    reset_outputs()


def go_to(step_index):
    ss.step_nav = ss.last_step = STEPS[step_index]


def on_step_change():
    # A segmented control can be "un-selected"; keep the current step instead.
    if ss.step_nav is None:
        ss.step_nav = ss.last_step
    ss.last_step = ss.step_nav


def open_scan(analysis_id):
    data, err = api.load(analysis_id, ss.client_id)
    if err:
        st.toast(f"Could not open this scan: {err}", icon="⚠️")
        return
    ss.report = data
    reset_outputs()


@st.cache_data(ttl=20, show_spinner=False)
def cached_health():
    return api.health()


def slug(text, default="resume"):
    return re.sub(r"[^A-Za-z0-9]+", "_", text or "").strip("_")[:40] or default


health, health_err = cached_health()
ai_on = bool(health and health.get("ai_enabled"))


# =========================================================================== landing
def landing():
    ui.nav(health is not None, ai_on)
    ui.hero()

    with st.container(key="card_scan"):
        left, right = st.columns([1, 1.2], gap="large")
        with left:
            ui.label("01", "Your resume")
            file = st.file_uploader("Resume", type=["pdf", "docx"], label_visibility="collapsed",
                                    help="PDF or DOCX, max 10 MB")
            st.caption("PDF or Word · max 10 MB · 🔒 private")
        with right:
            ui.label("02", "Job description", optional="optional")
            jd = st.text_area("Job description", height=158, label_visibility="collapsed",
                              placeholder="Paste the job post here for a match score and tailored tips.\n\n"
                                          "No job yet? Leave it empty for a general resume check.")
        scan = st.button("Scan my resume  →", type="primary", width="stretch", key="scan_btn",
                         disabled=health is None)

    if health is None:
        st.error(f"The Shortlistly API is not reachable. {health_err or ''}\n\n"
                 "Start the app with `.\\run.ps1` from the project folder.", icon=":material/cloud_off:")

    if scan:
        if not file:
            st.toast("Add your resume first 👆", icon="📄")
        else:
            with st.status("Scanning your resume...", expanded=True) as status:
                st.write("Reading your resume...")
                st.write("Running ATS checks and matching keywords...")
                if ai_on:
                    st.write("AI recruiter is reviewing it (about 20 seconds)...")
                data, err = api.analyze(file.name, file.getvalue(), file.type, jd, ss.client_id)
                if err:
                    status.update(label="Scan failed", state="error")
                    st.error(err)
                else:
                    status.update(label="Done!", state="complete")
                    ss.report = data
                    reset_outputs()
                    st.rerun()

    ui.how_it_works()

    history, _ = api.history(ss.client_id) if health else ([], None)
    if history:
        st.write("")
        st.caption("YOUR RECENT SCANS (only visible to you)")
        cols = st.columns(min(len(history), 5))
        for col, item in zip(cols, history):
            label = item.get("target_role") or item.get("filename") or "Resume"
            col.button(f"{item['score']} · {label[:22]}", key=f"h_{item['id']}", width="stretch",
                       on_click=open_scan, args=(item["id"],))
    ui.footer()


# =========================================================================== step 1: score
def step_score(r):
    ai = r.get("ai") or {}
    c1, c2 = st.columns([1.3, 1], gap="medium")
    with c1, st.container(border=True, height="stretch"):
        ui.score_card(r)
    with c2, st.container(border=True, height="stretch"):
        ui.score_bars(r["scores"])

    kw = r.get("keywords")
    k1, k2 = st.columns([1.6, 1], gap="medium")
    with k1, st.container(border=True, height="stretch"):
        if kw and kw.get("total"):
            ui.section(f"Keywords · {len(kw['matched'])} of {kw['total']} found",
                       "Recruiters' software searches resumes for these words from the job post. "
                       "Add the missing ones you really have.")
            st.progress(kw["match_rate"] / 100, text=f"{kw['match_rate']}% match · aim for 70%+")
            covered = kw.get("covered") or []
            st.html('<div class="riq-sub" style="margin:.6rem 0 .4rem">Missing from your resume</div>'
                    + (ui.chips(kw["missing"], "bad") if kw["missing"] else
                       '<span class="riq-sub" style="color:#6ee7b7">🎉 Nothing missing. You have every keyword.</span>')
                    + '<div class="riq-sub" style="margin:1rem 0 .4rem">Already in your resume</div>'
                    + ui.chips(kw["matched"], "ok")
                    + ('<div class="riq-sub" style="margin:1rem 0 .4rem">Not needed: the job asks for '
                       '<i>one of</i> these, and you already have an alternative</div>'
                       + ui.chips(covered, "alt") if covered else ""))
        else:
            ui.section("Keywords", "Add a job description to see which keywords you're missing for a specific job.")
            st.button("Scan again with a job description", icon=":material/add:", on_click=new_scan)
    with k2, st.container(border=True, height="stretch"):
        strengths = ai.get("strengths") or [c["label"] for c in r.get("checks", []) if c["passed"]][:5]
        ui.checklist_items("What's working", strengths)

    st.write("")
    n = len(fix_items(r))
    if n == 0:
        st.button("Nothing to fix. Go to download  →", type="primary", width="stretch", on_click=go_to, args=(2,))
    else:
        label = "Next: see the 1 fix" if n == 1 else f"Next: see your {n} fixes"
        st.button(f"{label}  →", type="primary", width="stretch", on_click=go_to, args=(1,))


# =========================================================================== step 2: fix
def fix_items(r):
    ai = r.get("ai") or {}
    items = [{"severity": s["priority"], "category": s["category"], "title": s["title"],
              "detail": s["detail"], "fix": "", "example": s.get("example", "")}
             for s in ai.get("suggestions", [])]
    items += r.get("issues", [])
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(items, key=lambda i: order.get(i["severity"], 2))


def render_fix(idx, item):
    done = idx in ss.done
    chk, card = st.columns([0.05, 0.95], vertical_alignment="center")
    with chk:
        checked = st.checkbox("Done", value=done, key=f"done_{idx}", label_visibility="collapsed",
                              help="Mark as done")
        if checked != done:
            (ss.done.add if checked else ss.done.discard)(idx)
            st.rerun()
    with card:
        ui.fix_card(item, idx + 1, done)


def step_fix(r):
    ai = r.get("ai") or {}
    items = fix_items(r)
    with st.container(border=True):
        important = [i for i in items if i["severity"] in ("critical", "high", "medium")]
        if not items:
            ui.section("🎉 Nothing to fix",
                       "Your resume passed every ATS check and our AI reviewer found no real problems. "
                       "It's ready to send.")
        else:
            done_n = len(ss.done)
            if not important:
                ui.section(f"Looking good · {len(items)} optional polish item{'s' if len(items) > 1 else ''}",
                           "No real problems found. These small tweaks are optional.")
            else:
                ui.section(f"Your fix list · {len(items)} item{'s' if len(items) > 1 else ''}",
                           "Only real issues found in your resume, sorted by impact. "
                           "Tick each one when you've updated your resume.")
            st.progress(done_n / len(items), text=f"{done_n} of {len(items)} done")
            for idx, item in enumerate(items[:TOP_FIXES]):
                render_fix(idx, item)
            if len(items) > TOP_FIXES:
                with st.expander(f"Show {len(items) - TOP_FIXES} smaller fixes"):
                    for idx, item in enumerate(items[TOP_FIXES:], start=TOP_FIXES):
                        render_fix(idx, item)

    rewrites = ai.get("bullet_rewrites") or []
    if rewrites:
        with st.container(border=True):
            ui.section("Rewrite these weak lines",
                       "Copy the improved version into your resume. Replace any [X] with your real numbers.")
            for b in rewrites:
                ui.compare(b["original"], b["improved"], b.get("why"))
                st.code(b["improved"], language=None, wrap_lines=True)

    if ai.get("recommended_summary"):
        with st.container(border=True):
            ui.section("A better summary for the top of your resume", "Tailored to this role. Click the copy icon.")
            st.code(ai["recommended_summary"], language=None, wrap_lines=True)

    st.write("")
    st.button("Short on time? Let AI rewrite the whole resume  →", type="primary", width="stretch",
              on_click=go_to, args=(2,))


# =========================================================================== step 3: download
def persistent_text_area(label, store, key, **kwargs):
    """A text box whose content survives switching steps.

    Streamlit discards a widget's state when it isn't drawn (e.g. while the user looks at
    another step), which used to leave the box - and every download - empty. The text is
    therefore also kept in ``ss[store]`` and restored into the box when it comes back.
    """
    ss[key] = ss.get(store) or ""          # always refill the box from the permanent copy

    def save():                             # every edit goes straight to the permanent copy
        ss[store] = ss[key]

    return st.text_area(label, key=key, on_change=save, **kwargs)


def downloads(text, base, kind):
    if not text.strip():
        st.warning("The text box is empty, so there is nothing to download yet.", icon=":material/warning:")
        return
    pdf_fn = exporters.resume_pdf if kind == "resume" else exporters.letter_pdf
    docx_fn = exporters.resume_docx if kind == "resume" else exporters.letter_docx
    c1, c2, c3 = st.columns([1.2, 1, 1])
    c1.download_button("Download PDF", pdf_fn(text), f"{base}.pdf", "application/pdf", type="primary",
                       icon=":material/download:", width="stretch", on_click="ignore", key=f"{kind}_pdf")
    c2.download_button("Word (.docx)", docx_fn(text), f"{base}.docx", DOCX_MIME, width="stretch",
                       on_click="ignore", key=f"{kind}_docx")
    c3.download_button("Text (.txt)", text.encode("utf-8"), f"{base}.txt", "text/plain", width="stretch",
                       on_click="ignore", key=f"{kind}_txt")


def generate_rewrite(r):
    """Button callback (runs before the page renders, so it may reset the text box)."""
    missing = [k["term"] for k in (r.get("keywords") or {}).get("missing", [])]
    with st.spinner("AI is rewriting your resume... (about 30 seconds)"):
        data, err = api.rewrite(r["resume_text"], r.get("job_description", ""), missing, "professional")
        ss.rewrite_err = err
        if err:
            return
        ss.rewrite = ss.rewrite_edit = data["rewritten_resume"]
        ss.rewrite_score, _ = api.score(ss.rewrite, r.get("job_description", ""), r.get("jd_keywords"))


def step_download(r):
    ai = r.get("ai") or {}
    name = slug(ai.get("candidate_name"), "resume")
    with st.container(border=True):
        ui.section("Your improved resume",
                   "AI rewrites your resume in a clean, ATS-friendly format, tailored to the job. "
                   "It only uses your real experience.")
        if ss.get("rewrite_err"):
            st.error(ss.rewrite_err)
        if not ai_on:
            st.info("This needs an OpenAI API key in the `.env` file.", icon=":material/key_off:")
        elif not ss.rewrite:
            st.button("✨ Create my improved resume", type="primary", width="stretch", on_click=generate_rewrite,
                      args=(r,))
        else:
            if ss.rewrite_score:
                ui.delta(r["overall_score"], ss.rewrite_score["overall_score"])
                still_missing = [k["term"] for k in (ss.rewrite_score.get("keywords") or {}).get("missing", [])]
                if still_missing:
                    st.info(f"**Not added on purpose:** {', '.join(still_missing)}. The AI only adds skills your "
                            "resume shows you have, so you won't be caught out in an interview. If you do have "
                            "these skills, add them yourself in the box below.", icon=":material/verified_user:")
                st.write("")
            text = persistent_text_area("Edit before downloading", "rewrite", "rewrite_edit", height=420,
                                        help="You can edit anything here. Downloads use this text.")
            if "[X]" in text:
                st.warning(f"Replace the {text.count('[X]')} **[X]** placeholder(s) with your real numbers "
                           "before downloading.", icon=":material/edit:")
            downloads(text, f"{name}_resume", "resume")
            st.button("Try again", icon=":material/refresh:", on_click=generate_rewrite, args=(r,))

    st.write("")
    ui.section("Applying for this job? Two more things that help")
    with st.expander("✉️  Write a cover letter", expanded=False):
        if not ai_on:
            st.info("Needs an OpenAI API key.", icon=":material/key_off:")
        elif not r.get("has_job_description"):
            st.info("A cover letter needs the job description. Start a new scan and paste the job post.")
        else:
            company = st.text_input("Company name", placeholder="e.g. Acme Inc.")
            if st.button("Write my cover letter", type="primary"):
                with st.spinner("Writing..."):
                    data, err = api.cover_letter(r["resume_text"], r["job_description"], company, "",
                                                 "professional", "medium")
                if err:
                    st.error(err)
                else:
                    ss.cover = ss.cover_edit = data["cover_letter"]
            if ss.cover:
                text = persistent_text_area("Cover letter", "cover", "cover_edit", height=360,
                                            label_visibility="collapsed")
                downloads(text, f"{name}_cover_letter", "letter")

    with st.expander("🎤  Practice likely interview questions", expanded=False):
        if not ai_on:
            st.info("Needs an OpenAI API key.", icon=":material/key_off:")
        else:
            if not ss.questions and st.button("Show me the questions", type="primary"):
                with st.spinner("Preparing questions..."):
                    data, err = api.interview(r["resume_text"], r.get("job_description", ""))
                if err:
                    st.error(err)
                else:
                    ss.questions = data["questions"]
            for i, q in enumerate(ss.questions or [], 1):
                st.markdown(f"**{i}. {q['question']}**")
                st.caption(f"{q['type']} · Why they ask: {q['why']}")
                st.success(f"**How to answer:** {q['tip']}", icon=":material/lightbulb:")

    st.write("")
    st.download_button("Download my full score report (PDF)", exporters.report_pdf(r), f"{name}_ATS_report.pdf",
                       "application/pdf", icon=":material/summarize:", on_click="ignore")


# =========================================================================== results page
def results():
    r = ss.report
    left, right = st.columns([4, 1], vertical_alignment="center")
    with left:
        ui.nav(True, ai_on, show_status=False)
    with right:
        st.button("New scan", icon=":material/add:", width="stretch", on_click=new_scan)

    ai = r.get("ai") or {}
    role = ai.get("target_role") if r.get("has_job_description") else "General resume check"
    st.caption(f"{r.get('filename', '')}  ·  {role or ''}")
    if not r.get("ai_available"):
        st.warning("AI feedback is unavailable right now (check the OpenAI key). Your score comes from the "
                   "built-in ATS checks.", icon=":material/info:")

    st.segmented_control("Step", STEPS, key="step_nav", label_visibility="collapsed",
                         on_change=on_step_change, width="stretch")
    st.write("")
    step = STEPS.index(ss.step_nav or ss.last_step)
    [step_score, step_fix, step_download][step](r)
    ui.footer()


if ss.report:
    results()
else:
    landing()
