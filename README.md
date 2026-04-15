# Resume Personalizer

A tiny, fully-free resume tailoring agent. A local Streamlit UI collects a job
posting URL + your LaTeX resume, and Cowork (Claude desktop) does the actual
tailoring and PDF compilation. No API keys, no paid services.

## How it works

```
[ Streamlit UI ]  --writes-->  jobs/job_<ts>/{jd.txt, resume.tex, INSTRUCTIONS.md}
                                        |
                                        v
                               [ Cowork / Claude ]
                                        |
                                        v
                   resume_tailored.tex + resume_tailored.pdf + CHANGES.md
```

The LLM is whichever Claude session you are already running inside Cowork, so
there is no additional cost.

## One-time setup

```bash
cd Resume_personalizer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

For PDF compilation you need a LaTeX engine. The lightest option is
[tectonic](https://tectonic-typesetting.github.io/) (a single binary, free):

```bash
# macOS
brew install tectonic
# or Linux
cargo install tectonic
```

`pdflatex` / `latexmk` from a TeX Live install also work.

## Running

```bash
streamlit run app.py
```

Then:

1. Paste the job posting URL.
2. Upload your `.tex` resume.
3. If the URL cannot be scraped (LinkedIn, Workday and most ATS pages won't
   work with a plain HTTP fetch), paste the JD into the fallback textarea.
4. Click **Create job packet**.
5. Open Cowork in this same workspace folder and tell it:

   > Tailor my resume using the packet at `Resume_personalizer/jobs/job_<ts>`.
   > Follow the rules in `INSTRUCTIONS.md` exactly — do not invent any
   > experience.

   Cowork will produce `resume_tailored.tex`, `resume_tailored.pdf`, and
   `CHANGES.md` inside the packet folder.

## Guarantees against inflation

The tailoring prompt (`TAILOR_PROMPT.md`, copied into every packet as
`INSTRUCTIONS.md`) forbids:

- adding skills, tools, employers, dates, degrees, or certifications that are
  not already in the source resume,
- changing any metric or number,
- introducing JD keywords that have no basis in the existing resume content.

The only allowed edits are reordering, rewording supported bullets with the
JD's vocabulary, trimming irrelevant content, and tweaking an existing summary
section. `CHANGES.md` documents every edit with a justification you can audit.

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit UI |
| `fetch_jd.py` | Best-effort JD scraper with a manual-paste fallback |
| `TAILOR_PROMPT.md` | The tailoring rules Cowork follows |
| `requirements.txt` | Python deps |
| `jobs/` | One subfolder per job packet |
