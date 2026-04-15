"""Compiles a LaTeX string to PDF bytes using the first available engine.

Works locally (if pdflatex/tectonic is installed) and on Streamlit Cloud
(where texlive is installed via packages.txt).
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import pathlib
from dataclasses import dataclass


@dataclass
class CompileResult:
    ok: bool
    pdf_bytes: bytes
    log: str
    error: str = ""


def compile_latex(tex_source: str, filename: str = "resume") -> CompileResult:
    """
    Write tex_source to a temp dir, compile to PDF, return PDF bytes.
    Tries pdflatex → latexmk → tectonic in that order.
    """
    engines = _available_engines()
    if not engines:
        return CompileResult(
            False, b"", "",
            "No LaTeX engine found. Install pdflatex (BasicTeX / TeX Live) "
            "or tectonic, then try again."
        )

    with tempfile.TemporaryDirectory() as tmp:
        tex_path = pathlib.Path(tmp) / f"{filename}.tex"
        tex_path.write_text(tex_source, encoding="utf-8")

        for engine, cmd_fn in engines:
            cmd = cmd_fn(str(tex_path), tmp)
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=tmp,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                log = proc.stdout + proc.stderr
                pdf_path = pathlib.Path(tmp) / f"{filename}.pdf"
                if pdf_path.exists() and pdf_path.stat().st_size > 0:
                    return CompileResult(True, pdf_path.read_bytes(), log)
                # Engine ran but no PDF — try next
            except subprocess.TimeoutExpired:
                continue
            except FileNotFoundError:
                continue

        # All engines tried but none produced a PDF — return the log
        return CompileResult(
            False, b"", log,
            f"LaTeX compilation failed. Check the log for errors.\n\n{log[-3000:]}"
        )


def _available_engines() -> list[tuple[str, callable]]:
    """Return list of (name, cmd_builder) for engines that exist on PATH."""
    candidates = []

    if shutil.which("pdflatex"):
        def _pdflatex(tex: str, cwd: str):
            return [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory", cwd,
                tex,
            ]
        candidates.append(("pdflatex", _pdflatex))

    if shutil.which("latexmk"):
        def _latexmk(tex: str, cwd: str):
            return [
                "latexmk", "-pdf",
                "-interaction=nonstopmode",
                f"-output-directory={cwd}",
                tex,
            ]
        candidates.append(("latexmk", _latexmk))

    if shutil.which("tectonic"):
        def _tectonic(tex: str, cwd: str):
            return ["tectonic", "--outdir", cwd, tex]
        candidates.append(("tectonic", _tectonic))

    return candidates
