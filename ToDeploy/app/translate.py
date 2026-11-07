"""Hu↔En is done on the Flutter client. Server only expands RAG terms."""

from __future__ import annotations

# Bilingual term expansion for RAG lexical matching (folded lowercase).
TERM_ALIASES: dict[str, list[str]] = {
    "bolcsesseg": ["wisdom", "athena", "athene", "minerva"],
    "istenno": ["goddess", "athena", "athene"],
    "istennoje": ["goddess", "athena", "athene"],
    "olimpia": ["olympics", "olympic", "olympia"],
    "olimpiak": ["olympics", "olympic"],
    "elso": ["first"],
    "szent": ["saint"],
    "istvan": ["stephen", "istvan"],
    "koppany": ["koppany", "cupan"],
    "athene": ["athena", "athene", "wisdom", "goddess"],
    "athena": ["athena", "athene", "wisdom", "goddess"],
    "zeus": ["zeus", "zeusz"],
    "zeusz": ["zeus", "zeusz"],
}


def expand_terms(terms: list[str]) -> list[str]:
    out: set[str] = set()
    for t in terms:
        out.add(t)
        for a in TERM_ALIASES.get(t, []):
            out.add(a)
    return list(out)
