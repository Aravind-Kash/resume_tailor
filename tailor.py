"""LLM-powered resume tailoring using Groq via OpenAI-compatible REST API.

We hit the Groq REST endpoint directly with `requests`.
No SDK, just plain HTTP.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import requests

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# ---------------------------------------------------------------------------
# Tailoring rules (mirrors TAILOR_PROMPT.md, embedded so the deployed app
# has no file-path dependencies)
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTIONS = """
You are an expert resume writer, LaTeX specialist, and senior hiring manager at a top tech company.
Your task: tailor the provided LaTeX resume to a specific job description.

=== HARD RULES (never break these) ===

1. NEVER invent experience. Only reword, reorder, re-emphasize, or drop content
   already in the resume. Do not add skills, tools, employers, dates,
   certifications, metrics, or accomplishments not already present.
2. NEVER change any number or metric. Copy them verbatim.
3. Preserve all facts: job titles, company names, employment dates, degrees, locations.
4. Output must be valid, compilable LaTeX. Preserve the document class, preamble,
   packages, and custom commands. Only edit content inside existing environments.
   Properly escape LaTeX special characters in any new prose.
5. No hallucinated keywords. If a JD skill isn't in the resume anywhere, don't add it.

=== HIRING MANAGER LENS (fix these using only existing content) ===

- Replace duty-listing bullets ("Responsible for...", "Worked on...", "Helped...",
  "Assisted...") with achievement-framed bullets using strong active verbs.
- Every bullet should answer "so what?" — surface the outcome if it exists in
  the original.
- Remove or compress clearly irrelevant bullets to reduce noise.
- Rewrite the summary (if present) to lead with the most JD-relevant differentiator,
  backed by evidence already in the resume.
- Ensure all bullets in past roles use past tense; current role uses present tense.

=== ATS OPTIMIZATION ===

- Use the JD's exact phrases (not paraphrases) wherever the content supports it.
  ATS does exact-match scoring.
- Spell out acronyms at first use per section: e.g. "Machine Learning (ML)".
- Ensure every JD must-have/nice-to-have skill that genuinely appears anywhere in
  the resume is also listed explicitly in the Skills section.
- Prioritize JD-critical keywords in: (1) summary, (2) first bullet per role,
  (3) skills section.
- Reorder bullets within each role so the most JD-relevant appear first.
- Reorder the skills section so JD-relevant skills appear first.

=== OUTPUT FORMAT ===

You MUST return exactly this structure and nothing else:

<TAILORED_RESUME>
[complete tailored LaTeX — must be the full, compilable .tex file]
</TAILORED_RESUME>

<CHANGES>
## Role Tailored For
[Role title and company if visible in JD]

## JD Requirement Coverage
| Requirement | Status | Resume Evidence |
|---|---|---|
[one row per key JD requirement: Status = Supported / Partial / Missing]

## Edits Made
[bullet list — each edit with a one-line justification citing the original content]

## ATS Keyword Coverage
[bullet list — each major JD keyword and where it now appears in the resume]

## Honest Gaps
[JD requirements the resume genuinely cannot support — so the candidate knows]
</CHANGES>
""".strip()


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class TailorResult:
    ok: bool
    tailored_tex: str
    changes_md: str
    error: str = ""


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def tailor_resume(
    resume_tex: str,
    jd_text: str,
    api_key: str,
    model: str = "llama-3.3-70b-versatile",
) -> TailorResult:
    """Call Groq REST API to tailor the resume. Returns TailorResult."""

    if not api_key:
        return TailorResult(False, "", "", "No API key provided.")
    if not resume_tex.strip():
        return TailorResult(False, "", "", "Resume is empty.")
    if not jd_text.strip():
        return TailorResult(False, "", "", "Job description is empty.")

    user_message = f"""
=== JOB DESCRIPTION ===
{jd_text.strip()}

=== CURRENT RESUME (LaTeX) ===
{resume_tex.strip()}

Tailor the resume to the job description following all rules above.
Return the full tailored LaTeX and the changes report in the exact format specified.
""".strip()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.2,
        "max_tokens": 8192,
    }

    try:
        resp = requests.post(
            GROQ_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )
    except requests.RequestException as exc:
        return TailorResult(False, "", "", f"Network error calling Groq: {exc}")

    if resp.status_code != 200:
        try:
            err = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            err = resp.text
        return TailorResult(
            False, "", "",
            f"Groq API error (HTTP {resp.status_code}): {err}",
        )

    try:
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return TailorResult(
                False, "", "",
                f"Groq returned no choices. Full response: {data}",
            )
        raw = choices[0].get("message", {}).get("content", "")
    except Exception as exc:
        return TailorResult(False, "", "", f"Could not parse Groq response: {exc}")

    if not raw.strip():
        return TailorResult(False, "", "", "Gemini returned an empty response.")

    # Parse the two tagged sections
    tex_match = re.search(
        r"<TAILORED_RESUME>\s*(.*?)\s*</TAILORED_RESUME>",
        raw, re.DOTALL,
    )
    changes_match = re.search(
        r"<CHANGES>\s*(.*?)\s*</CHANGES>",
        raw, re.DOTALL,
    )

    if not tex_match:
        # Fallback: maybe the model forgot the tags; try to find \documentclass
        doc_match = re.search(r"(\\documentclass.*\\end\{document\})", raw, re.DOTALL)
        if doc_match:
            tailored_tex = doc_match.group(1).strip()
        else:
            return TailorResult(
                False, "", "",
                "Could not parse LaTeX from model response. First 2000 chars:\n\n" + raw[:2000],
            )
    else:
        tailored_tex = tex_match.group(1).strip()

    changes_md = (
        changes_match.group(1).strip()
        if changes_match
        else "(No changes report generated.)"
    )

    # Basic sanity check
    if "\\documentclass" not in tailored_tex or "\\end{document}" not in tailored_tex:
        return TailorResult(
            False, tailored_tex, changes_md,
            "Model returned incomplete LaTeX (missing \\documentclass or \\end{document}).",
        )

    return TailorResult(True, tailored_tex, changes_md)
