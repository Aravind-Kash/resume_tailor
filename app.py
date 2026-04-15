"""Resume Personalizer — single-page Streamlit app.

Paste a job description + upload your LaTeX resume → get a tailored PDF.
No switching between apps. Works locally and when deployed to Streamlit Cloud.

LLM: Google Gemini Flash (free tier, 1,500 req/day).
PDF: pdflatex / latexmk / tectonic (whichever is installed).
"""
from __future__ import annotations

import os
import streamlit as st

from tailor import tailor_resume
from compile_pdf import compile_latex

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Resume Personalizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("📄 Resume Personalizer")
st.caption(
    "Paste a job description, upload your LaTeX resume, and get a tailored PDF — "
    "all on this page. Powered by Google Gemini Flash (free)."
)

# ---------------------------------------------------------------------------
# API key — from Streamlit secrets (deployed) or manual input (local)
# ---------------------------------------------------------------------------
api_key = ""
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    pass

if not api_key:
    with st.expander("🔑 Enter your free Gemini API key", expanded=True):
        st.markdown(
            "Get a free key at [ai.google.dev](https://ai.google.dev) "
            "(takes ~1 minute, no credit card). "
            "On Streamlit Cloud, add it as a secret named `GEMINI_API_KEY`."
        )
        api_key = st.text_input(
            "Gemini API key",
            type="password",
            placeholder="AIza...",
            help="Never stored. Used only for this session.",
        )

# ---------------------------------------------------------------------------
# Main two-column layout
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("Your Resume")

    # Keep resume in session state so re-runs don't lose it
    if "resume_tex" not in st.session_state:
        st.session_state.resume_tex = ""
    if "resume_filename" not in st.session_state:
        st.session_state.resume_filename = ""

    uploaded = st.file_uploader(
        "Upload your LaTeX resume (.tex)",
        type=["tex"],
        help="Uploaded once per session — no need to re-upload when switching jobs.",
    )
    if uploaded:
        st.session_state.resume_tex = uploaded.read().decode("utf-8")
        st.session_state.resume_filename = uploaded.name
        st.success(f"✅ Loaded: **{uploaded.name}**")
    elif st.session_state.resume_tex:
        st.info(f"Using cached resume: **{st.session_state.resume_filename}**")

with col_right:
    st.subheader("Job Description")
    jd_text = st.text_area(
        "Paste the full job description here",
        height=320,
        placeholder=(
            "Paste the complete job description text.\n\n"
            "For LinkedIn: open the job → click 'See more' → select all text → copy → paste here."
        ),
        label_visibility="collapsed",
    )

# ---------------------------------------------------------------------------
# Tailor button — centred
# ---------------------------------------------------------------------------
st.divider()
_, btn_col, _ = st.columns([2, 1, 2])
with btn_col:
    tailor_clicked = st.button(
        "✨ Tailor My Resume",
        type="primary",
        use_container_width=True,
        disabled=not (api_key and st.session_state.resume_tex and jd_text.strip()),
    )

if not api_key:
    st.warning("Enter your Gemini API key above to get started.")
elif not st.session_state.resume_tex:
    st.info("Upload your .tex resume on the left.")
elif not jd_text.strip():
    st.info("Paste the job description on the right.")

# ---------------------------------------------------------------------------
# Tailoring pipeline
# ---------------------------------------------------------------------------
if tailor_clicked:
    with st.status("Tailoring your resume…", expanded=True) as status:

        st.write("🤖 Sending to Gemini for analysis and tailoring…")
        tailor_result = tailor_resume(
            resume_tex=st.session_state.resume_tex,
            jd_text=jd_text,
            api_key=api_key,
        )

        if not tailor_result.ok:
            status.update(label="❌ Tailoring failed", state="error")
            st.error(tailor_result.error)
            st.stop()

        st.write("📄 Compiling PDF…")
        compile_result = compile_latex(tailor_result.tailored_tex)

        if compile_result.ok:
            status.update(label="✅ Done! Your tailored resume is ready.", state="complete")
        else:
            status.update(label="⚠️ Tailored — but PDF compilation failed.", state="error")

    # ── Results ──────────────────────────────────────────────────────────
    st.subheader("Results")
    dl_col1, dl_col2, dl_col3 = st.columns(3)

    with dl_col1:
        if compile_result.ok:
            st.download_button(
                label="⬇️ Download PDF",
                data=compile_result.pdf_bytes,
                file_name="resume_tailored.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
        else:
            st.error("PDF compilation failed — download the .tex and compile manually.")
            if compile_result.log:
                with st.expander("LaTeX error log"):
                    st.code(compile_result.log[-3000:], language="text")

    with dl_col2:
        st.download_button(
            label="⬇️ Download .tex",
            data=tailor_result.tailored_tex,
            file_name="resume_tailored.tex",
            mime="text/plain",
            use_container_width=True,
        )

    with dl_col3:
        st.download_button(
            label="⬇️ Download changes report",
            data=tailor_result.changes_md,
            file_name="CHANGES.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.divider()
    st.subheader("What changed & why")
    st.markdown(tailor_result.changes_md)
