"""Keyless DuckDuckGo HTML search (curriculum-oriented English snippets)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

log = logging.getLogger("web_search")

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


@dataclass
class WebHit:
    title: str
    url: str
    snippet: str
    score: float
    term_hits: int

    @property
    def good_enough(self) -> bool:
        return (
            len(self.snippet.strip()) >= 60
            and self.term_hits >= 2
            and self.score >= 2.5
        )


def search_curriculum(english_question: str, hungarian_question: str = "") -> WebHit | None:
    q = english_question.strip()
    if not q:
        return None
    query = f"{q} based on the Hungarian curriculum"
    try:
        raw = _ddg(query)
    except Exception as e:  # noqa: BLE001
        log.warning("web search failed: %s", e)
        return None
    if not raw:
        return None

    match_blob = f"{q} {hungarian_question}".strip()
    terms = _terms(match_blob)
    best: WebHit | None = None
    for title, url, snippet in raw:
        focused, score, n = _focus(f"{title}. {snippet}", terms, 520)
        if not focused:
            continue
        hit = WebHit(title=title, url=url, snippet=focused, score=score, term_hits=n)
        if best is None or hit.score > best.score:
            best = hit
    if best is None or not best.good_enough:
        log.info("web hit not good enough")
        return None
    log.info("web best=%s score=%.2f", best.title[:60], best.score)
    return best


def _ddg(query: str) -> list[tuple[str, str, str]]:
    url = "https://html.duckduckgo.com/html/"
    with httpx.Client(timeout=12.0, follow_redirects=True, headers={"User-Agent": _UA}) as client:
        r = client.get(url, params={"q": query, "kl": "us-en"})
        r.raise_for_status()
        html = r.text
    # Very small HTML scrape – titles + snippets.
    blocks = re.findall(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'class="result__snippet"[^>]*>(.*?)</(?:a|td|div)',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    out: list[tuple[str, str, str]] = []
    for href, title_html, snip_html in blocks[:8]:
        title = _strip_tags(title_html)
        snip = _strip_tags(snip_html)
        if title and snip:
            out.append((title, href, snip))
    return out


def _strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _fold(s: str) -> str:
    table = str.maketrans(
        {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ö": "o",
            "ő": "o",
            "ú": "u",
            "ü": "u",
            "ű": "u",
        }
    )
    return s.lower().translate(table)


def _terms(text: str) -> list[str]:
    stop = {
        "a",
        "az",
        "the",
        "and",
        "of",
        "in",
        "to",
        "for",
        "was",
        "were",
        "who",
        "what",
        "when",
        "where",
        "volt",
        "ki",
        "mit",
        "mikor",
    }
    out: list[str] = []
    for part in re.split(r"[^\wÁÉÍÓÖŐÚÜŰáéíóöőúüű]+", text, flags=re.UNICODE):
        t = _fold(part)
        if len(t) >= 3 and t not in stop:
            out.append(t)
    return out


def _focus(text: str, terms: list[str], max_chars: int) -> tuple[str, float, int]:
    folded = _fold(text)
    hits = [t for t in terms if t in folded]
    if len(hits) < 2:
        return "", 0.0, len(hits)
    # Anchor on longest match.
    anchor = -1
    alen = 0
    for t in hits:
        i = folded.find(t)
        if i >= 0 and len(t) >= alen:
            anchor, alen = i, len(t)
    if anchor < 0:
        return "", 0.0, len(hits)
    half = max(40, (max_chars - alen) // 2)
    start = max(0, anchor - half)
    end = min(len(text), start + max_chars)
    excerpt = text[start:end].strip()
    score = float(len(hits)) + min(2.0, alen / 8.0)
    return excerpt, score, len(hits)
