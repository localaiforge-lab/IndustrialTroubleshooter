"""In-memory RAG over prebuilt curriculum indexes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .embedder import Embedder
from .rag_index import Chunk, DocumentPack, load_manifest, load_prebuilt_index
from .translate import expand_terms


@dataclass
class Retrieved:
    chunk: Chunk
    score: float  # lower = better (cosine distance-ish)


_STOP = {
    "a",
    "az",
    "es",
    "és",
    "vagy",
    "hogy",
    "mi",
    "mit",
    "ki",
    "kit",
    "hol",
    "mikor",
    "miert",
    "miért",
    "hogyan",
    "volt",
    "voltak",
    "van",
    "nem",
    "egy",
    "is",
    "who",
    "what",
    "when",
    "where",
    "was",
    "were",
    "the",
    "and",
    "of",
    "in",
    "to",
    "for",
    "that",
    "this",
}


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


def _terms(*texts: str) -> list[str]:
    out: set[str] = set()
    for text in texts:
        for part in re.split(r"[^\wÁÉÍÓÖŐÚÜŰáéíóöőúüű]+", text, flags=re.UNICODE):
            t = _fold(part)
            if len(t) >= 3 and t not in _STOP:
                out.add(t)
    return list(out)


def _passage(chunk: Chunk) -> str:
    try:
        meta = json.loads(chunk.metadata_json or "{}")
    except json.JSONDecodeError:
        meta = {}
    canonical = (meta.get("canonical_text_en") or "").strip()
    return canonical if canonical else chunk.text


def _focus_excerpt(text: str, terms: list[str], max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    folded = _fold(text)
    anchor = -1
    anchor_len = 0
    for term in terms:
        t = _fold(term)
        if not t:
            continue
        from_idx = 0
        while True:
            i = folded.find(t, from_idx)
            if i < 0:
                break
            if len(t) >= anchor_len:
                anchor = i
                anchor_len = len(t)
            from_idx = i + len(t)
    if anchor < 0:
        return ""
    half = (max_chars - anchor_len) // 2
    start = max(0, anchor - half)
    end = min(len(text), start + max_chars)
    if end - start < max_chars and start > 0:
        start = max(0, end - max_chars)
    excerpt = text[start:end].strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{excerpt}{suffix}"


class RagStore:
    def __init__(self, materials_dir: Path, embedder: Embedder):
        self._embedder = embedder
        self._packs: dict[str, DocumentPack] = {}
        self._catalog: list[dict] = []
        self._load(materials_dir)

    def _load(self, materials_dir: Path) -> None:
        materials = load_manifest(materials_dir)
        for m in materials:
            directory = m.get("dir")
            document_id = m.get("documentId")
            prebuilt = m.get("prebuiltIndex") or "prebuilt_index.bin"
            if not directory or not document_id:
                continue
            path = materials_dir / directory / prebuilt
            if not path.exists():
                continue
            pack = load_prebuilt_index(path)
            # Prefer UI title from manifest.
            title = (m.get("title") or pack.title or document_id).strip()
            pack.title = title
            for c in pack.chunks:
                c.document_title = title
            self._packs[document_id] = pack
            self._catalog.append(
                {
                    "documentId": document_id,
                    "title": title,
                    "chunkCount": len(pack.chunks),
                }
            )

    @property
    def catalog(self) -> list[dict]:
        return list(self._catalog)

    def retrieve(
        self,
        *,
        english_query: str,
        hungarian_query: str,
        document_id: str | None,
        top_k: int = 4,
        max_context_chars: int = 1400,
    ) -> tuple[list[Retrieved], str, list[str]]:
        pack = self._packs.get(document_id or "")
        if pack is None:
            # Fallback: search all books (should be rare).
            candidates_packs = list(self._packs.values())
        else:
            candidates_packs = [pack]

        terms = expand_terms(_terms(english_query, hungarian_query))
        q = self._embedder.embed(english_query)

        scored: list[Retrieved] = []
        for p in candidates_packs:
            if not p.chunks:
                continue
            mat = p.matrix
            # cosine similarity since vectors are L2-normalized → distance = 1 - sim
            sims = mat @ q
            # lexical boost
            for i, chunk in enumerate(p.chunks):
                hay = _fold(_passage(chunk) + " " + chunk.text)
                term_hits = sum(1 for t in terms if t in hay)
                # lower score is better (aligned with mobile ObjectBox distance)
                dist = float(1.0 - sims[i])
                if term_hits:
                    dist *= 1.0 / (1.0 + 0.45 * term_hits)
                scored.append(Retrieved(chunk=chunk, score=dist))

        scored.sort(key=lambda r: r.score)

        # Deduplicate by record_id when present.
        picked: list[Retrieved] = []
        seen: set[str] = set()
        for hit in scored:
            try:
                meta = json.loads(hit.chunk.metadata_json or "{}")
            except json.JSONDecodeError:
                meta = {}
            key = meta.get("record_id") or hit.chunk.id
            if key in seen:
                continue
            # Prefer hits with term overlap; DistilUSE passages are English.
            hay = _fold(_passage(hit.chunk))
            if terms and not any(t in hay for t in terms):
                continue
            seen.add(key)
            picked.append(hit)
            if len(picked) >= top_k:
                break

        # If translation failed / terms are Hungarian-only, lexical filter can
        # wipe every semantic hit – fall back to pure embedding top-k.
        if not picked:
            seen.clear()
            for hit in scored:
                try:
                    meta = json.loads(hit.chunk.metadata_json or "{}")
                except json.JSONDecodeError:
                    meta = {}
                key = meta.get("record_id") or hit.chunk.id
                if key in seen:
                    continue
                # Still require a reasonably strong embedding match.
                if hit.score > 0.55:
                    continue
                seen.add(key)
                picked.append(hit)
                if len(picked) >= top_k:
                    break

        context = self._build_context(picked[:2] or picked, terms, max_context_chars)
        return picked, context, terms

    def _build_context(
        self, hits: list[Retrieved], terms: list[str], max_chars: int
    ) -> str:
        buf: list[str] = []
        remaining = max_chars
        for hit in hits:
            page = ""
            try:
                meta = json.loads(hit.chunk.metadata_json or "{}")
                page = str(meta.get("page_start") or "")
            except json.JSONDecodeError:
                page = ""
            header = (
                f"[{hit.chunk.document_title} p.{page}]\n"
                if page
                else f"[{hit.chunk.document_title} #{hit.chunk.chunk_index}]\n"
            )
            room = remaining - len(header) - 2
            if room < 120:
                break
            passage = _passage(hit.chunk)
            excerpt = _focus_excerpt(passage, terms, room)
            if not excerpt.strip():
                continue
            block = f"{header}{excerpt}\n\n"
            buf.append(block)
            remaining -= len(block)
        return "".join(buf).strip()
