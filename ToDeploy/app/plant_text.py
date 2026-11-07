"""Shared text helpers for the plant library.

Factory documents stay in their original language. Search folds Hungarian
accents and treats alarm codes (E-204, F12, ALM 100) as exact keys.
"""

from __future__ import annotations

import re

_FOLD = str.maketrans(
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

_STOP = {
    "a",
    "az",
    "es",
    "vagy",
    "hogy",
    "mi",
    "mit",
    "ki",
    "hol",
    "mikor",
    "miert",
    "hogyan",
    "milyen",
    "volt",
    "van",
    "nincs",
    "nem",
    "egy",
    "is",
    "ezt",
    "azt",
    "kell",
    "tegyek",
    "tegyunk",
    "jelent",
    "jelenti",
    "kerem",
    "kerek",
    "legyen",
    "the",
    "and",
    "for",
    "what",
    "how",
    "does",
    "did",
    "with",
    "from",
    "this",
    "that",
    "are",
    "was",
    "were",
    "you",
    "your",
    "please",
    "can",
    "could",
    "who",
    "when",
    "where",
}

# Letter group plus at least two digits, with an optional separator: E-204, ALM 12, 12F.
_CODE = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?:[A-Za-z]{1,6}[\s\-_/]*\d{2,5}|\d{2,5}[\s\-_/]*[A-Za-z]{1,4})"
    r"(?![A-Za-z0-9])"
)

_HU_MARKERS = set("áéíóöőúüűÁÉÍÓÖŐÚÜŰ")
_HU_WORDS = {"hiba", "hibat", "gep", "gepen", "sor", "utasitas", "kezikonyv", "jelzett"}
_EN_WORDS = {"fault", "machine", "alarm", "manual", "reset", "motor", "pump"}


def fold(text: str) -> str:
    return text.lower().translate(_FOLD)


def normalize_code(raw: str) -> str:
    return "".join(ch for ch in raw.upper() if ch.isalnum())


def fault_code_labels(text: str) -> list[str]:
    """First spelling of each alarm code, in reading order."""
    found: list[str] = []
    seen: set[str] = set()
    for match in _CODE.finditer(text or ""):
        label = re.sub(r"\s+", " ", match.group(0)).strip()
        norm = normalize_code(label)
        if not _plausible_code(norm) or norm in seen:
            continue
        seen.add(norm)
        found.append(label)
    return found


def code_norms(labels: list[str]) -> set[str]:
    return {normalize_code(label) for label in labels if normalize_code(label)}


def _plausible_code(norm: str) -> bool:
    if len(norm) < 3 or len(norm) > 12:
        return False
    letters = sum(ch.isalpha() for ch in norm)
    digits = sum(ch.isdigit() for ch in norm)
    return letters >= 1 and digits >= 2


def tokens(text: str) -> list[str]:
    """Search tokens. Alarm codes are indexed compact (E204) and by their digit run."""
    folded = fold(text or "")
    raw = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", folded)
    out: list[str] = []
    for tok in raw:
        compact = tok.replace("-", "")
        if tok in _STOP or compact in _STOP:
            continue
        if any(ch.isdigit() for ch in compact):
            if len(compact) < 2:
                continue
            out.append(compact)
            if compact != tok:
                out.append(tok)
            for run in re.findall(r"\d{3,}", compact):
                if run != compact:
                    out.append(run)
            continue
        if len(tok) >= 3:
            out.append(tok)
    return out


def language_of(text: str) -> str:
    if any(ch in _HU_MARKERS for ch in text):
        return "hu"
    folded_tokens = set(tokens(text))
    hu = len(folded_tokens & _HU_WORDS)
    en = len(folded_tokens & _EN_WORDS)
    if en > hu:
        return "en"
    return "hu"


def looks_like_heading(line: str) -> bool:
    text = " ".join(line.strip().split())
    if not text or len(text) > 90:
        return False
    if text[-1] in ".;,:":
        return False
    words = text.split()
    if len(words) > 12:
        return False
    if re.match(r"^\d+(?:\.\d+){0,3}\s+\S", text):
        return True
    letters = [ch for ch in text if ch.isalpha()]
    if len(letters) >= 4 and all(ch.isupper() for ch in letters):
        return True
    return False
