"""Plant document library: upload, store, and search factory documentation.

Answers are assembled only from uploaded files. Alarm codes outrank ordinary
words. A local language model may phrase the reply when one is loaded; the
passages are still the source.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import math
import re
import threading
import uuid
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .plant_extract import build_passages, extract_file, extension_of, size_label
from .plant_text import code_norms, fault_code_labels, language_of, normalize_code, tokens

log = logging.getLogger("plant")

MAX_FILES = 40
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_BATCH_BYTES = 80 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".xlsm",
    ".pptx",
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".tsv",
    ".log",
    ".html",
    ".htm",
    ".json",
    ".xml",
    ".rtf",
    ".odt",
    ".zip",
}

KIND_LABELS = {
    "fault_list": "Hibajegyzék",
    "procedure": "Munkautasítás",
    "datasheet": "Adatlap",
    "manual": "Kézikönyv",
    "log": "Napló",
    "table": "Táblázat",
    "presentation": "Bemutató",
    "document": "Dokumentum",
}

_IMAGE_MESSAGE = (
    "A képen lévő szöveget nem olvassuk. Mentse a lapot szöveges PDF-be vagy Wordbe."
)
_LEGACY = {
    ".doc": "A régi Word .doc nem olvasható. Mentse .docx formátumba, és úgy töltse fel.",
    ".xls": "A régi Excel .xls nem olvasható. Mentse .xlsx formátumba, és úgy töltse fel.",
    ".ppt": "A régi PowerPoint .ppt nem olvasható. Mentse .pptx formátumba, és úgy töltse fel.",
    ".png": _IMAGE_MESSAGE,
    ".jpg": _IMAGE_MESSAGE,
    ".jpeg": _IMAGE_MESSAGE,
    ".tif": _IMAGE_MESSAGE,
    ".tiff": _IMAGE_MESSAGE,
    ".bmp": _IMAGE_MESSAGE,
    ".gif": _IMAGE_MESSAGE,
    ".webp": _IMAGE_MESSAGE,
}

_ID = re.compile(r"^[a-f0-9]{32}$")


class PlantStore:
    def __init__(self, root: Path, embedder=None):
        self.root = Path(root)
        self._embedder = embedder
        self._docs: list[dict] = []
        self._entries: list[dict] = []
        self._bm25 = _Bm25([])
        self._lock = threading.Lock()

    def load(self) -> None:
        folder = self.root / "documents"
        folder.mkdir(parents=True, exist_ok=True)
        loaded: list[dict] = []
        for path in folder.glob("*.json"):
            try:
                loaded.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                log.exception("Skipping unreadable plant document %s", path)
        loaded.sort(key=lambda doc: doc.get("uploadedAt") or "", reverse=True)
        with self._lock:
            self._docs = loaded
            self._rebuild()
        log.info("Plant library: %s document(s)", len(loaded))

    def summary(self) -> dict:
        with self._lock:
            codes = {
                normalize_code(code)
                for doc in self._docs
                for code in doc.get("faultCodes") or []
            }
            return {
                "documents": len(self._docs),
                "passages": sum(len(doc.get("passages") or []) for doc in self._docs),
                "faultCodes": len(codes),
                "lastUpload": self._docs[0].get("uploadedAt") if self._docs else None,
            }

    def list_documents(self) -> list[dict]:
        with self._lock:
            return [_public_doc(doc) for doc in self._docs]

    def ingest_many(self, files: list[tuple[str, bytes]], area: str = "") -> list[dict]:
        clean_area = " ".join((area or "").split())[:80]
        items = _queue(files)
        jobs: list[tuple[str, dict]] = []
        accepted = 0
        running = 0
        for kind, name, data in items:
            if kind == "reject":
                jobs.append(("reject", data))  # type: ignore[arg-type]
                continue
            if accepted >= MAX_FILES:
                jobs.append(("reject", _file_result(
                    name,
                    "rejected",
                    "Egyszerre legfeljebb 40 fájl tölthető fel. Ezt már nem vettem fel.",
                )))
                continue
            if len(data) > MAX_FILE_BYTES:
                jobs.append(("reject", _file_result(
                    name,
                    "rejected",
                    "A fájl nagyobb 25 MB-nál. Ossza kisebb részekre, vagy hagyja ki a képeket.",
                )))
                continue
            if running + len(data) > MAX_BATCH_BYTES:
                jobs.append(("reject", _file_result(
                    name,
                    "rejected",
                    "A feltöltés összesen nagyobb 80 MB-nál. A többit egy következő körben töltse fel.",
                )))
                continue
            accepted += 1
            running += len(data)
            jobs.append(self._prepare(name, data, clean_area))

        results: list[dict] = []
        with self._lock:
            for kind, payload in jobs:
                if kind == "reject":
                    results.append(payload)
                else:
                    results.append(self._commit(payload))
            self._rebuild()
        return results

    def delete(self, document_id: str) -> bool:
        if not _ID.match(document_id or ""):
            return False
        with self._lock:
            kept = [doc for doc in self._docs if doc.get("id") != document_id]
            if len(kept) == len(self._docs):
                return False
            self._docs = kept
            path = self._path(document_id)
            if path.exists():
                path.unlink()
            self._rebuild()
            return True

    def ask(self, question: str, answer_with_model=None) -> dict:
        text = " ".join((question or "").split())
        lang = language_of(text)
        with self._lock:
            if not self._docs:
                return _answer(_empty_message(lang), found=False, library_empty=True)
            hits = self._search_unlocked(text)
            context = _context(hits)
            sources = [_source(hit) for hit in hits]
        if not hits:
            return _answer(_miss_message(lang), found=False, library_empty=False)
        if answer_with_model is not None:
            try:
                model_text = (answer_with_model(text, context, lang) or "").strip()
            except Exception:
                log.exception("Plant model answer failed")
                model_text = ""
            if _grounded(model_text, hits):
                return _answer(model_text, found=True, library_empty=False, mode="model", sources=sources)
        return _answer(
            _extractive(text, hits, lang),
            found=True,
            library_empty=False,
            sources=sources,
        )

    def _prepare(self, filename: str, data: bytes, area: str) -> tuple[str, dict]:
        ext = extension_of(filename)
        if ext in _LEGACY:
            return "reject", _file_result(filename, "rejected", _LEGACY[ext])
        if ext not in ALLOWED_EXTENSIONS or ext == ".zip":
            shown = ext or "nincs kiterjesztés"
            return "reject", _file_result(
                filename,
                "rejected",
                f"Ezt a típust nem tudom beolvasni ({shown}). "
                "PDF, Word, Excel, PowerPoint, szöveg, CSV vagy ezek zip csomagja jó.",
            )
        if not data:
            return "reject", _file_result(filename, "rejected", "A fájl üres.")
        try:
            extracted = extract_file(filename, data)
        except ValueError as exc:
            message = str(exc).strip() or "A fájl nem olvasható."
            return "reject", _file_result(filename, "rejected", message)
        except Exception:
            log.exception("Failed to read %s", filename)
            return "reject", _file_result(
                filename,
                "rejected",
                "A fájlt nem sikerült beolvasni. Próbálja szöveges PDF, Word vagy Excel formában.",
            )
        passages = build_passages(extracted)
        if not passages:
            return "reject", _file_result(
                filename,
                "rejected",
                "Nem találtam olvasható szöveget. Szkennelt képet nem olvasunk: "
                "szöveges PDF, Word vagy Excel kell.",
                warnings=extracted.warnings,
            )
        stored = []
        codes: list[str] = []
        seen: set[str] = set()
        for passage in passages:
            item = {
                "body": passage.body,
                "kind": passage.kind,
                "page": passage.page,
                "section": passage.section,
                "sheet": passage.sheet,
                "slide": passage.slide,
                "faultCodes": passage.fault_codes,
            }
            vector = self._embed(passage.body)
            if vector is not None:
                item["vector"] = vector
            stored.append(item)
            for label in passage.fault_codes:
                norm = normalize_code(label)
                if norm not in seen:
                    seen.add(norm)
                    codes.append(label)
        doc = {
            "filename": filename,
            "title": _title(filename),
            "kind": extracted.kind,
            "kindLabel": KIND_LABELS.get(extracted.kind, "Dokumentum"),
            "area": area,
            "uploadedAt": _now(),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "sizeLabel": size_label(extracted, len(stored)),
            "warnings": list(extracted.warnings),
            "faultCodes": codes[:200],
            "passages": stored,
        }
        return "ok", doc

    def _commit(self, doc: dict) -> dict:
        for existing in self._docs:
            if existing.get("sha256") == doc["sha256"]:
                return _file_result(
                    doc["filename"],
                    "duplicate",
                    "Ez a fájl már a tudástárban van, nem tettem be mégegyszer.",
                    document_id=existing.get("id"),
                    kind=existing.get("kind") or "",
                    kind_label=existing.get("kindLabel") or "",
                    size_label=existing.get("sizeLabel") or "",
                    passages=len(existing.get("passages") or []),
                    fault_codes=existing.get("faultCodes") or [],
                )
        if any(existing.get("filename", "").lower() == doc["filename"].lower() for existing in self._docs):
            doc["warnings"] = list(doc["warnings"]) + [
                "Van már ilyen nevű dokumentum a tudástárban. Ha ez a friss változat, a régit az Áttekintésben törölje."
            ]
        doc["id"] = uuid.uuid4().hex
        self._docs.insert(0, doc)
        self._write(doc)
        log.info(
            "Plant added %s (%s, %s passages)",
            doc["filename"],
            doc["kind"],
            len(doc["passages"]),
        )
        return _file_result(
            doc["filename"],
            "added",
            "Bekerült a tudástárba.",
            document_id=doc["id"],
            kind=doc["kind"],
            kind_label=doc["kindLabel"],
            size_label=doc["sizeLabel"],
            passages=len(doc["passages"]),
            fault_codes=doc["faultCodes"],
            warnings=doc["warnings"],
        )

    def _search_unlocked(self, question: str) -> list[dict]:
        query_tokens = tokens(question)
        query_codes = code_norms(fault_code_labels(question))
        if not query_tokens and not query_codes:
            return []
        scores = self._bm25.score(query_tokens)
        query_vector = self._embed(question)
        ranked: list[tuple[float, dict]] = []
        for index, entry in enumerate(self._entries):
            lexical = scores[index] if index < len(scores) else 0.0
            semantic = _dot(query_vector, entry.get("vector"))
            passage_codes = _entry_codes(entry)
            code_hit = bool(query_codes and query_codes & passage_codes)
            if query_codes and not code_hit:
                continue
            if not code_hit and not _word_hit(query_tokens, entry["tokens"], lexical, semantic):
                continue
            final = lexical + (3.0 * semantic if semantic > 0.2 else 0.0) + (8.0 if code_hit else 0.0)
            ranked.append((final, entry))
        ranked.sort(key=lambda item: item[0], reverse=True)
        picked: list[dict] = []
        for score, entry in ranked:
            hit = {"doc": entry["doc"], "passage": entry["passage"], "score": score}
            if _too_similar(hit, picked):
                continue
            picked.append(hit)
            if len(picked) >= 4:
                break
        return picked

    def _rebuild(self) -> None:
        entries: list[dict] = []
        for doc in self._docs:
            for passage in doc.get("passages") or []:
                entries.append(
                    {
                        "doc": doc,
                        "passage": passage,
                        "tokens": tokens(_search_text(doc, passage)),
                        "codes": code_norms(passage.get("faultCodes") or []),
                        "vector": passage.get("vector"),
                    }
                )
        self._entries = entries
        self._bm25 = _Bm25([entry["tokens"] for entry in entries])

    def _embed(self, text: str):
        if self._embedder is None or not (text or "").strip():
            return None
        try:
            vector = self._embedder.embed(text[:500])
        except Exception:
            log.exception("Plant embedding failed")
            return None
        values = vector.tolist() if hasattr(vector, "tolist") else list(vector)
        return [round(float(value), 5) for value in values]

    def _write(self, doc: dict) -> None:
        path = self._path(doc["id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)

    def _path(self, document_id: str) -> Path:
        return self.root / "documents" / f"{document_id}.json"


class _Bm25:
    def __init__(self, docs: list[list[str]]):
        self._tf = [Counter(doc) for doc in docs]
        self._dl = [float(len(doc)) for doc in docs]
        self._n = len(docs)
        self._avg = (sum(self._dl) / self._n) if self._n else 0.0
        df: dict[str, int] = {}
        for counts in self._tf:
            for term in counts:
                df[term] = df.get(term, 0) + 1
        self._df = df

    def score(self, query: list[str]) -> list[float]:
        scores = [0.0] * self._n
        if not self._n or self._avg <= 0:
            return scores
        k1 = 1.2
        b = 0.65
        for term in dict.fromkeys(query):
            df = self._df.get(term, 0)
            if not df:
                continue
            idf = math.log(1.0 + (self._n - df + 0.5) / (df + 0.5))
            for index, counts in enumerate(self._tf):
                freq = counts.get(term, 0)
                if not freq:
                    continue
                denom = freq + k1 * (1.0 - b + b * self._dl[index] / self._avg)
                scores[index] += idf * (freq * (k1 + 1.0)) / denom
        return scores


def _queue(files: list[tuple[str, bytes]]) -> list[tuple]:
    items = []
    for name, data in files:
        safe = _safe_name(name)
        if extension_of(safe) == ".zip":
            try:
                for inner_name, inner_data in _unzip(data):
                    items.append(("file", inner_name, inner_data))
            except ValueError as exc:
                items.append(("reject", safe, _file_result(safe, "rejected", str(exc))))
            continue
        items.append(("file", safe, data))
    return items


def _unzip(data: bytes) -> list[tuple[str, bytes]]:
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("A tömörített fájl nagyobb 25 MB-nál.")
    try:
        package = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ValueError("A tömörített fájl nem nyitható meg.") from exc
    found: list[tuple[str, bytes]] = []
    total = 0
    with package:
        for info in package.infolist():
            if info.is_dir():
                continue
            base = _safe_name(info.filename)
            lowered = base.lower()
            if not base or base.startswith(".") or lowered in {"thumbs.db", "desktop.ini"}:
                continue
            if lowered.startswith("__macosx"):
                continue
            if info.flag_bits & 0x1:
                raise ValueError("A tömörített fájl jelszavas, így nem olvasható.")
            if info.file_size > MAX_FILE_BYTES or total + info.file_size > MAX_BATCH_BYTES:
                raise ValueError("A tömörített fájl kibontva túl nagy (legfeljebb 80 MB).")
            total += info.file_size
            found.append((base, package.read(info)))
            if len(found) > MAX_FILES:
                raise ValueError("A tömörített fájlban túl sok fájl van (legfeljebb 40).")
    if not found:
        raise ValueError("A tömörített fájlban nincs dokumentum.")
    return found


def _safe_name(name: str) -> str:
    base = Path(str(name or "")).name.replace("\x00", "").strip()
    if not base or base in {".", ".."}:
        return "dokumentum"
    return base[:180]


def _title(filename: str) -> str:
    stem = Path(filename).stem.replace("_", " ").replace("-", " ")
    stem = " ".join(stem.split())
    return stem[:120] or "Dokumentum"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _search_text(doc: dict, passage: dict) -> str:
    return " ".join(
        part
        for part in (
            doc.get("area") or "",
            doc.get("filename") or "",
            doc.get("title") or "",
            passage.get("section") or "",
            passage.get("sheet") or "",
            passage.get("body") or "",
            " ".join(passage.get("faultCodes") or []),
        )
        if part
    )


def _entry_codes(entry: dict) -> set[str]:
    norms = set(entry.get("codes") or [])
    for token in entry.get("tokens") or []:
        if any(ch.isdigit() for ch in token) and any(ch.isalpha() for ch in token):
            norms.add(token.upper())
    return norms


def _word_hit(query: list[str], passage: list[str], lexical: float, semantic: float) -> bool:
    if semantic >= 0.48:
        return True
    have = set(passage)
    overlap = [token for token in dict.fromkeys(query) if token in have]
    if not overlap or lexical <= 0:
        return False
    longest = max(len(token) for token in overlap)
    return len(overlap) >= 2 or longest >= 5


def _too_similar(hit: dict, picked: list[dict]) -> bool:
    current = set(tokens(hit["passage"].get("body") or ""))
    if not current:
        return False
    for previous in picked:
        if previous["doc"].get("id") != hit["doc"].get("id"):
            continue
        other = set(tokens(previous["passage"].get("body") or ""))
        if not other:
            continue
        if len(current & other) / len(current | other) >= 0.72:
            return True
    return False


def _dot(left, right) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return float(sum(a * b for a, b in zip(left, right)))


def _context(hits: list[dict]) -> str:
    parts: list[str] = []
    total = 0
    for hit in hits[:4]:
        piece = _location(hit) + "\n" + (hit["passage"].get("body") or "")
        if total + len(piece) > 1600:
            room = 1600 - total
            if room > 200:
                parts.append(piece[:room])
            break
        parts.append(piece)
        total += len(piece) + 2
    return "\n\n".join(parts)


def _extractive(question: str, hits: list[dict], lang: str) -> str:
    codes = fault_code_labels(question)
    if lang == "en":
        if len(codes) == 1:
            lead = f"The uploaded documents describe {codes[0]} as follows."
        elif codes:
            lead = "The uploaded documents describe these codes: " + ", ".join(codes) + "."
        else:
            lead = "From the uploaded documents:"
        related = "Related passage"
        tail = "The text above is from the uploaded documents. Nothing else was added."
        area_label = "Area"
    else:
        if len(codes) == 1:
            lead = f"A(z) {codes[0]} kód a feltöltött dokumentumokban így szerepel."
        elif codes:
            lead = "Ezek a kódok a feltöltött dokumentumokban így szerepelnek: " + ", ".join(codes) + "."
        else:
            lead = "A feltöltött dokumentumok alapján:"
        related = "Kapcsolódó rész"
        tail = "A fenti szöveg a dokumentumból van. Más lépést a tudástár nem tartalmaz."
        area_label = "Terület"
    lines = [lead, ""]
    for index, hit in enumerate(hits[:3]):
        if index:
            lines.append(related)
        lines.append(_location(hit))
        area = (hit["doc"].get("area") or "").strip()
        if area:
            lines.append(f"{area_label}: {area}")
        lines.append(_format_body(hit["passage"].get("body") or ""))
        lines.append("")
    lines.append(tail)
    return "\n".join(lines).strip()


def _format_body(body: str) -> str:
    if " | " in body and body.count(":") >= 2:
        return "\n".join(part.strip() for part in body.split("|") if part.strip())
    return body.strip()


def _location(hit: dict) -> str:
    doc = hit["doc"]
    passage = hit["passage"]
    bits = [doc.get("filename") or doc.get("title") or "Dokumentum"]
    if passage.get("page"):
        bits.append(f"{passage['page']}. oldal")
    elif passage.get("slide"):
        bits.append(f"{passage['slide']}. dia")
    sheet = (passage.get("sheet") or "").strip()
    if sheet:
        bits.append(sheet)
    section = (passage.get("section") or "").strip()
    if section and section not in bits and section != sheet:
        bits.append(section)
    return " — ".join(bits)


def _source(hit: dict) -> dict:
    passage = hit["passage"]
    doc = hit["doc"]
    return {
        "documentId": doc.get("id"),
        "title": doc.get("title") or "",
        "filename": doc.get("filename") or "",
        "kindLabel": doc.get("kindLabel") or "",
        "page": passage.get("page"),
        "slide": passage.get("slide"),
        "section": passage.get("section") or "",
        "sheet": passage.get("sheet") or "",
        "location": _location(hit),
        "excerpt": (passage.get("body") or "")[:900],
        "faultCodes": passage.get("faultCodes") or [],
        "score": round(float(hit.get("score") or 0.0), 3),
    }


def _grounded(answer: str, hits: list[dict]) -> bool:
    text = (answer or "").strip()
    if len(text) < 40:
        return False
    lowered = text.lower()
    if "i do not know" in lowered:
        return False
    if "nem tartalmaz" in lowered and "dokumentum" in lowered:
        return False
    if "do not contain" in lowered or "does not contain" in lowered:
        return False
    blob: set[str] = set()
    hit_codes: set[str] = set()
    for hit in hits:
        blob.update(tokens(hit["passage"].get("body") or ""))
        hit_codes.update(code_norms(hit["passage"].get("faultCodes") or []))
    if code_norms(fault_code_labels(text)) & hit_codes:
        return True
    overlap = [token for token in tokens(text) if len(token) >= 5 and token in blob]
    return len(set(overlap)) >= 2


def _empty_message(lang: str) -> str:
    if lang == "en":
        return (
            "There is no document in the library yet. "
            "Upload a manual, a fault list, or a work instruction first."
        )
    return (
        "Még nincs dokumentum a tudástárban. "
        "Először töltse fel a gépkönyvet, a hibajegyzéket vagy a munkautasítást. "
        "Utána ide írhatja a hibát."
    )


def _miss_message(lang: str) -> str:
    if lang == "en":
        return (
            "The uploaded documents do not contain a matching passage. "
            "Type the alarm code as it appears on the machine, or upload the manual for this equipment."
        )
    return (
        "A feltöltött dokumentumokban nincs ehhez illő rész. "
        "Írja be a hibakódot úgy, ahogy a gépen látszik, vagy töltsön fel olyan anyagot, "
        "amelyik ezt a berendezést írja le."
    )


def _answer(
    text: str,
    *,
    found: bool,
    library_empty: bool,
    mode: str = "documents",
    sources: list[dict] | None = None,
) -> dict:
    return {
        "answer": text,
        "mode": mode,
        "found": found,
        "libraryEmpty": library_empty,
        "sources": sources or [],
    }


def _public_doc(doc: dict) -> dict:
    codes = doc.get("faultCodes") or []
    return {
        "id": doc.get("id"),
        "filename": doc.get("filename") or "",
        "title": doc.get("title") or "",
        "kind": doc.get("kind") or "document",
        "kindLabel": doc.get("kindLabel") or "Dokumentum",
        "area": doc.get("area") or "",
        "uploadedAt": doc.get("uploadedAt"),
        "sizeLabel": doc.get("sizeLabel") or "",
        "passageCount": len(doc.get("passages") or []),
        "faultCodes": codes[:12],
        "faultCodeCount": len(codes),
        "warnings": doc.get("warnings") or [],
    }


def _file_result(
    filename: str,
    status: str,
    message: str,
    *,
    document_id: str | None = None,
    kind: str = "",
    kind_label: str = "",
    size_label: str = "",
    passages: int = 0,
    fault_codes: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict:
    codes = fault_codes or []
    return {
        "filename": filename,
        "status": status,
        "message": message,
        "documentId": document_id,
        "kind": kind,
        "kindLabel": kind_label,
        "sizeLabel": size_label,
        "passages": passages,
        "faultCodes": codes[:12],
        "faultCodeCount": len(codes),
        "warnings": warnings or [],
    }
