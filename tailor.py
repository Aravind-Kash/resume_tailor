"""LLM-powered resume tailoring using Groq via OpenAI-compatible REST API.

We hit the Groq REST endpoint directly with `requests`.
No SDK, just plain HTTP.
"""
from __future__ import annotations

import re

import requests

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# ---------------------------------------------------------------------------
# Tailoring rules (mirrors TAILOR_PROMPT.md, embedded so the deployed app
# has no file-path dependencies)
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTIONS = """
You are an expert resume writer, LaTeX specialist, and senior hiring manager at a top tech company.
Your task: tailor the provided LaTeX resume BODY to a specific job description.

IMPORTANT: You will receive ONLY the content between \\begin{document} and \\end{document}.
You must return ONLY that body content — do NOT include \\documentclass, \\usepackage,
\\newcommand definitions, or any preamble. Do NOT include \\begin{document} or \\end{document} tags.
The preamble will be reattached automatically.

=== HARD RULES (never break these) ===

1. NEVER invent experience. Only reword, reorder, re-emphasize, or drop content
   already in the resume. Do not add skills, tools, employers, dates,
   certifications, metrics, or accomplishments not already present.
2. NEVER change any number or metric. Copy them verbatim.
3. Preserve all facts: job titles, company names, employment dates, degrees, locations.
4. Only edit content inside existing environments. Properly escape LaTeX special
   characters in any new prose. Never modify or redefine any custom commands.
5. No hallucinated keywords. If a JD skill isn't in the resume anywhere, don't add it.
6. PRESERVE ALL \\textbf{} keyword highlighting from the original body verbatim.
   Every word or phrase that was wrapped in \\textbf{} in the original MUST remain
   wrapped in \\textbf{} in the output. Additionally, wrap any important JD keywords
   you introduce or promote into bullet positions with \\textbf{} as well.

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

<TAILORED_BODY>
[tailored LaTeX body content only — everything that goes between \\begin{document} and \\end{document}]
</TAILORED_BODY>

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
# Preamble helpers
# ---------------------------------------------------------------------------

def _split_preamble_body(tex: str) -> tuple[str, str]:
    """Split a .tex file into (preamble_with_begin_doc, body).

    preamble includes everything up to and including \\begin{document}.
    body is everything between \\begin{document} and \\end{document}.
    Returns (preamble, body); if no \\begin{document} found returns ("", tex).
    """
    begin_match = re.search(r"\\begin\{document\}", tex)
    end_match = re.search(r"\\end\{document\}", tex)
    if not begin_match or not end_match:
        return "", tex
    preamble = tex[: begin_match.end()]  # up to and including \begin{document}
    body = tex[begin_match.end() : end_match.start()].strip()
    return preamble, body


def _rejoin(preamble: str, body: str) -> str:
    return preamble + "\n" + body + "\n\\end{document}\n"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

class TailorResult:
    def __init__(self, ok: bool, tailored_tex: str, changes_md: str, error: str = ""):
        self.ok = ok
        self.tailored_tex = tailored_tex
        self.changes_md = changes_md
        self.error = error


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

    # Split preamble so the model only sees (and can only corrupt) the body
    preamble, body = _split_preamble_body(resume_tex)
    if not preamble:
        # Fallback: send the whole file if we can't detect structure
        preamble = ""
        body = resume_tex

    user_message = f"""
=== JOB DESCRIPTION ===
{jd_text.strip()}

=== CURRENT RESUME BODY (LaTeX — content between \\begin{{document}} and \\end{{document}}) ===
{body}

Tailor the resume body to the job description following all rules above.
Return ONLY the body content (no preamble, no \\begin{{document}}/\\end{{document}} tags)
inside <TAILORED_BODY> tags, plus the changes report.
""".strip()

    payload = {
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
            json={**payload, "model": model},
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
        return TailorResult(False, "", "", "Groq returned an empty response.")

    # Parse the two tagged sections
    tex_match = re.search(
        r"<TAILORED_BODY>\s*(.*?)\s*</TAILORED_BODY>",
        raw, re.DOTALL,
    )
    changes_match = re.search(
        r"<CHANGES>\s*(.*?)\s*</CHANGES>",
        raw, re.DOTALL,
    )

    if not tex_match:
        return TailorResult(
            False, "", "",
            "Could not parse tailored body from model response. First 2000 chars:\n\n" + raw[:2000],
        )

    tailored_body = tex_match.group(1).strip()

    # Reattach the original preamble so custom commands are always intact
    if preamble:
        tailored_tex = _rejoin(preamble, tailored_body)
    else:
        tailored_tex = tailored_body

    changes_md = (
        changes_match.group(1).strip()
        if changes_match
        else "(No changes report generated.)"
    )

    # Basic sanity check
    if "\\end{document}" not in tailored_tex:
        return TailorResult(
            False, tailored_tex, changes_md,
            "Assembled LaTeX is missing \\end{document}.",
        )

    return TailorResult(True, tailored_tex, changes_md)
