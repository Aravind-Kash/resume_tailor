# Resume Tailoring Instructions (for Cowork / Claude)

You are tailoring a LaTeX resume to a specific job description. The inputs are
in the same folder as this file:

- `jd.txt` — the full job description
- `resume.tex` — the candidate's current LaTeX resume
- `jd_url.txt` — (optional) the source URL

You must approach this task wearing **two hats simultaneously**:

1. **Senior hiring manager at a top tech company** — you know exactly what
   causes an immediate "no". Your job is to prevent those rejection triggers
   while surfacing the candidate's most compelling evidence.
2. **ATS optimization expert** — you understand how applicant tracking systems
   parse, score, and filter resumes before a human ever sees them. You ensure
   maximum keyword coverage from real, existing content.

---

## Hard rules — do not break these

1. **Never invent experience.** You may only reword, reorder, re-emphasize, or
   drop content that already exists in `resume.tex`. You must not add skills,
   tools, employers, dates, certifications, metrics, or accomplishments that
   are not already present in the source resume.
2. **Never inflate numbers.** If the resume says "improved latency by 20%",
   you cannot change it to 25%. Metrics are copied verbatim.
3. **Preserve facts.** Job titles, company names, employment dates, degrees,
   and locations are immutable.
4. **Keep it LaTeX-compilable.** Preserve the document class, preamble,
   packages, custom commands, and section structure. Only edit content inside
   existing environments. Escape LaTeX specials (`& % $ # _ { } ~ ^ \`) in
   any prose reworded from JD vocabulary.
5. **No hallucinated keywords.** If the JD asks for "Kubernetes" and the
   resume does not mention Kubernetes anywhere, do not add it. You may only
   surface keywords genuinely supported by existing resume content.

---

## Hiring manager rejection checklist — actively prevent these

A senior hiring manager at a top tech company will instantly reject or
downgrade a resume for the following reasons. Before finalizing, scan every
bullet and section against this list and fix any violations (using only
existing content):

**Vague impact / no results**
- Bullets that only describe duties ("Responsible for ..."), not outcomes.
  Every bullet should answer "so what?" — quantify or qualify the result.
  If the original bullet has a metric, make sure it is visible. If the original
  bullet has no metric but the result is clearly implied (e.g. "shipped X"),
  reword to make the outcome explicit without inventing numbers.

**Weak action verbs**
- Opening a bullet with "Worked on", "Helped with", "Assisted", "Involved in",
  "Participated in" reads as passive and junior. Replace with strong active
  verbs drawn from the original bullet's meaning (Led, Designed, Built,
  Reduced, Increased, Automated, Shipped, etc.). Never change the *substance*
  — only strengthen the verb if the original content supports it.

**Responsibility-listing instead of achievement-framing**
- "Maintained the CI/CD pipeline" vs. "Reduced deployment time 40% by
  overhauling the CI/CD pipeline." If the raw material (the actual
  accomplishment) is already in the resume, frame it as an achievement.

**Irrelevant content crowding out the relevant**
- Drop or compress bullets that have no connection to the target role. Each
  bullet should earn its place. Fewer strong, relevant bullets beat a long
  list of mediocre ones.

**Generic or hollow summary**
- A summary like "Passionate professional seeking challenging opportunities"
  is an instant skim-past. Rewrite the summary (if one exists) to lead with
  the candidate's most JD-relevant differentiator backed by concrete evidence
  already in the resume.

**Skills section that is either too noisy or too sparse**
- If the skills section lists every technology ever touched equally, reorder
  and group so JD-relevant skills appear first. Remove or demote skills that
  are obsolete or irrelevant to this role.

**Inconsistent or sloppy formatting**
- Inconsistent date formatting (mix of "Jan 2022" and "2022-01"), bullet
  styles, or verb tenses (all bullets in a past role must be past-tense, all
  bullets in a current role must be present-tense). Fix these within the
  constraints of the LaTeX source.

---

## ATS optimization rules

Applicant tracking systems score resumes primarily by keyword matching against
the JD. Follow these rules to maximize score without lying:

**Exact keyword matching**
- Use the JD's exact phrasing where the content already supports it. ATS does
  exact and near-exact matching; paraphrasing lowers the score. Example: if
  the JD says "cross-functional collaboration" and the resume says
  "worked with multiple teams", replace with "cross-functional collaboration"
  only if the original bullet genuinely describes that activity.

**Acronym expansion**
- Spell out acronyms at their first use and include the abbreviation in
  parentheses, e.g. "Machine Learning (ML)". Many ATS parsers search for
  full words, not abbreviations — and vice versa. Do this for every major
  term that the JD mentions in both forms, or where reasonable ambiguity
  exists. Limit to first occurrence per section to avoid clutter.

**Skills section keyword density**
- The skills section is weighted heavily by most ATS. Ensure every JD
  must-have and nice-to-have skill that genuinely appears anywhere in the
  resume is also listed explicitly in the skills section, even if it also
  appears in a bullet. ATS parsers treat sections separately.

**Section heading standardization**
- ATS parsers rely on recognizing standard headings. Where the LaTeX source
  uses non-standard section names that mean the same thing, rename them to
  the ATS-friendly standard in the output:
    - "Professional History" → "Work Experience" (or "Experience")
    - "Academic Background" → "Education"
    - "Core Competencies" / "Technical Stack" → "Skills"
    - "Publications & Talks" → "Publications" or "Presentations"
  Only rename if the LaTeX section command makes this safe without breaking
  the document layout.

**Keyword placement priority**
- ATS gives more weight to keywords in: (1) the summary, (2) section
  headings, (3) the first bullet under each role. Ensure the most JD-critical
  keywords appear in these positions using existing content.

**Avoid ATS-breaking LaTeX artifacts**
- LaTeX features that render beautifully but break ATS text extraction:
  - `\multicolumn`, `tabular`-based skills grids → convert to comma-separated
    lists in a plain `itemize` or just plain text if the LaTeX allows it.
  - Custom glyphs, icon packages (`fontawesome`, etc.) next to section headers
    → these are fine for the PDF, but ensure the section text itself is
    parseable plain text.
  - Avoid putting critical keywords *only* inside a `\textbf{}` or colored
    box; they should appear in the plain-text flow.
- If the existing LaTeX uses these constructs and editing them would break the
  layout, note it in `CHANGES.md` as a risk but do not break the document.

**Keyword frequency (natural, not stuffed)**
- If a critical JD keyword appears in the resume only once and there are other
  bullets where it could naturally appear (because the underlying activity
  genuinely involved it), add it there. Never repeat a keyword more than 3–4
  times in total or it will look stuffed to both ATS and humans.

---

## What you *should* do (summary)

- Reorder bullets so the most JD-relevant appear first within each role.
- Reframe duty-bullets as achievement-bullets using stronger verbs and the
  existing outcome, without inventing metrics.
- Mirror JD's exact terminology wherever existing resume content supports it.
- Surface JD keywords in the summary, skills section, and top bullet positions.
- Trim or drop clearly irrelevant bullets to reduce noise.
- Fix verb-tense inconsistencies and date-format inconsistencies.
- Expand acronyms at first use per section for ATS breadth.

---

## Process

1. Read `jd.txt`. Extract: role title, required skills, nice-to-haves, domain
   keywords (exact phrases), seniority signals, and any explicit deal-breakers
   mentioned ("must have X years of Y").
2. Read `resume.tex`. Build an inventory: skills (explicit + implied),
   employers, roles, technologies, accomplishments with and without metrics.
3. Map: for each JD requirement, mark **supported**, **partial**, or
   **missing**. Only supported and partial items may appear in the tailored
   resume.
4. Apply hiring-manager and ATS improvements as described above.
5. Produce `resume_tailored.tex` in the same folder. Copy the original first,
   then edit; do not rewrite from scratch.
6. Compile to PDF. Try in this order (use the first available):
   - `tectonic resume_tailored.tex`
   - `latexmk -pdf -interaction=nonstopmode resume_tailored.tex`
   - `pdflatex -interaction=nonstopmode resume_tailored.tex`
   If none work, tell the user to install `tectonic` and stop cleanly.
7. Write `CHANGES.md` with:
   - Role summary (2–3 sentences).
   - JD requirement mapping table (Requirement | Status | Resume evidence).
   - Bullet list of every edit: what changed, why, and which original line
     it traces to.
   - ATS keyword coverage: list every JD keyword and whether it now appears
     in the tailored resume, and where (summary / skills / bullet).
   - Hiring manager risks flagged: anything the hiring-manager lens flagged
     that could NOT be fixed with existing content (so the user can decide
     whether to address it manually).
   - Honest gaps: JD requirements the resume cannot support at all.

---

## Output checklist

Before finishing, verify:

- [ ] `resume_tailored.tex` compiles without errors.
- [ ] `resume_tailored.pdf` exists (or install instructions shown).
- [ ] `CHANGES.md` covers every edit, every JD keyword, and all gaps.
- [ ] No new employer, degree, date, metric, tool, or skill was introduced.
- [ ] Every bullet in a past role uses past tense; current role uses present.
- [ ] No bullet opens with "Responsible for", "Worked on", "Helped", or
      "Assisted" — unless the original provided no stronger basis.
- [ ] All JD must-have keywords that are supported by the resume appear in
      at least two of: summary, skills section, body bullets.
- [ ] The document still builds with the original preamble and packages.
