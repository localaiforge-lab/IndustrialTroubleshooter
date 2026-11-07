"""Lightweight Google Translate helper for the web tester (and optional clients).

The Flutter phone app still translates on-device via the `translator` package.
This endpoint exists so a browser SPA on Firebase Hosting can do Hu↔En without
CORS issues calling Google directly.
"""

from __future__ import annotations

import logging
from urllib.parse import quote

import httpx

log = logging.getLogger("api.translate")

_GTX = "https://translate.googleapis.com/translate_a/single"


def translate_text(text: str, *, source: str, target: str) -> str:
    """Translate `text` from `source` to `target` (ISO 639-1 codes)."""
    q = text.strip()
    if not q:
        return q
    if source == target:
        return q

    url = (
        f"{_GTX}?client=gtx&sl={quote(source)}&tl={quote(target)}"
        f"&dt=t&q={quote(q)}"
    )
    try:
        with httpx.Client(timeout=12.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
        # Response shape: [[["translated", "original", ...], ...], ...]
        parts: list[str] = []
        if isinstance(data, list) and data and isinstance(data[0], list):
            for chunk in data[0]:
                if isinstance(chunk, list) and chunk and isinstance(chunk[0], str):
                    parts.append(chunk[0])
        out = "".join(parts).strip()
        return out or q
    except Exception as exc:  # noqa: BLE001 – fallback to original for resilience
        log.warning("translate %s→%s failed: %s", source, target, exc)
        return q
