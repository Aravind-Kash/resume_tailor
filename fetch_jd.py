"""Best-effort job description fetcher.

Tries a plain HTTP GET with a browser-ish User-Agent and extracts visible
text from the page. Works for most static job boards. Login-walled or
JS-rendered pages (LinkedIn, Workday, Greenhouse) will fail gracefully —
the caller should then fall back to a manual paste.

No paid services, no extra dependencies beyond requests + beautifulsoup4.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class FetchResult:
    ok: bool
    text: str
    note: str
    method: str = "http"


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    candidates: list[str] = []
    for selector in ["main", "article", "[role=main]"]:
        for node in soup.select(selector):
            t = node.get_text("\n", strip=True)
            if len(t) > 300:
                candidates.append(t)

    if not candidates and soup.body:
        candidates.append(soup.get_text("\n", strip=True))

    best = max(candidates, key=len) if candidates else ""
    best = re.sub(r"[ \t]+", " ", best)
    best = re.sub(r"\n{3,}", "\n\n", best)
    return best.strip()


def fetch_jd(url: str, timeout: int = 20) -> FetchResult:
    if not url or not url.startswith(("http://", "https://")):
        return FetchResult(False, "", "Not a valid http(s) URL.")

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        return FetchResult(False, "", f"Network error: {exc}")

    if resp.status_code >= 400:
        return FetchResult(
            False, "",
            f"HTTP {resp.status_code} — site requires login or blocks scraping. "
            "Please paste the JD manually.",
        )

    text = _extract_text(resp.text)
    if len(text) < 300:
        return FetchResult(
            False, text,
            "Page returned too little text — likely login-walled or JS-rendered. "
            "Please paste the JD manually.",
        )

    return FetchResult(True, text, f"Fetched {len(text):,} chars from {resp.url}")


if __name__ == "__main__":
    r = fetch_jd(sys.argv[1])
    print(f"ok={r.ok} | {r.note}")
    if r.ok:
        print("---")
        print(r.text[:3000])
