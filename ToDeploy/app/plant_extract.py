"""Turn one uploaded factory file into structured blocks.

Supported: PDF, Word, Excel, PowerPoint, text, CSV, HTML, JSON, XML, RTF, ODT.
Spreadsheets and tables become one record per row so a fault code stays attached
to its symptom and action. Prose keeps headings and page numbers.
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from .plant_text import fault_code_labels, fold, looks_like_heading

MAX_PDF_PAGES = 400
MAX_SHEET_ROWS = 5000
MAX_SHEET_COLS = 30
MAX_EXTRACT_CHARS = 1_500_000


@dataclass
class Block:
    text: str
    kind: str  # prose | heading | record | slide
    page: int | None = None
    section: str = ""
    sheet: str = ""
    slide: int | None = None


@dataclass
class Extracted:
    blocks: list[Block] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    page_count: int = 0
    slide_count: int = 0
    row_count: int = 0
    kind: str = "document"


@dataclass
class Passage:
    body: str
    kind: str
    page: int | None = None
    section: str = ""
    sheet: str = ""
    slide: int | None = None
    fault_codes: list[str] = field(default_factory=list)


_GENERIC_SHEET = {"sheet1", "sheet2", "sheet3", "munka1", "munkalap1"}


def extension_of(filename: str) -> str:
    return Path(filename or "").suffix.lower()


def extract_file(filename: str, data: bytes) -> Extracted:
    ext = extension_of(filename)
    if ext == ".pdf":
        extracted = _pdf(data)
    elif ext == ".docx":
        extracted = _docx(data)
    elif ext in {".xlsx", ".xlsm"}:
        extracted = _xlsx(data)
    elif ext == ".pptx":
        extracted = _pptx(data)
    elif ext in {".txt", ".md", ".markdown", ".log"}:
        extracted = _plaintext(data, markdown=ext in {".md", ".markdown"})
    elif ext in {".csv", ".tsv"}:
        extracted = _csv(data, forced="\t" if ext == ".tsv" else None)
    elif ext in {".html", ".htm"}:
        extracted = _html(data)
    elif ext == ".json":
        extracted = _json(data)
    elif ext == ".xml":
        extracted = _xml(data)
    elif ext == ".rtf":
        extracted = _rtf(data)
    elif ext == ".odt":
        extracted = _odt(data)
    else:
        raise ValueError(ext)
    extracted.kind = _guess_kind(filename, extracted)
    _cap_chars(extracted)
    return extracted


def build_passages(extracted: Extracted) -> list[Passage]:
    """Pack prose under headings. Keep each table row intact."""
    passages: list[Passage] = []
    section = ""
    buf: list[str] = []
    buf_page: int | None = None
    buf_len = 0

    def flush(*, overlap: bool) -> None:
        nonlocal buf, buf_len, buf_page
        text = "\n".join(part.strip() for part in buf if part.strip()).strip()
        if text:
            _append_passage(
                passages,
                Passage(body=text, kind="prose", page=buf_page, section=section),
            )
        if overlap and text:
            tail = text[-140:].strip()
            buf = [tail] if tail else []
            buf_len = len(tail)
        else:
            buf = []
            buf_len = 0
            buf_page = None

    for block in extracted.blocks:
        if block.kind == "heading":
            flush(overlap=False)
            section = block.text.strip() or section
            continue
        if block.kind in {"record", "slide"}:
            flush(overlap=False)
            _append_passage(
                passages,
                Passage(
                    body=block.text.strip(),
                    kind=block.kind,
                    page=block.page,
                    section=block.section or section,
                    sheet=block.sheet,
                    slide=block.slide,
                ),
            )
            continue
        if block.section and block.section != section and buf_len > 0:
            flush(overlap=False)
            section = block.section
        elif block.section:
            section = block.section
        piece = block.text.strip()
        if not piece:
            continue
        if buf and buf_len + len(piece) > 1000:
            flush(overlap=True)
        if buf_page is None:
            buf_page = block.page
        buf.append(piece)
        buf_len += len(piece)
    flush(overlap=False)
    return [p for p in passages if p.body.strip()]


def size_label(extracted: Extracted, passage_count: int) -> str:
    if extracted.page_count:
        return f"{extracted.page_count} oldal"
    if extracted.slide_count:
        return f"{extracted.slide_count} dia"
    if extracted.row_count:
        return f"{extracted.row_count} sor"
    return f"{passage_count} rész"


def _append_passage(passages: list[Passage], passage: Passage) -> None:
    body = passage.body.strip()
    if len(body) > 2500:
        body = body[:2500].rsplit(" ", 1)[0].strip()
    if len(body) < 8:
        return
    if passage.kind == "prose" and len(body) < 12 and not fault_code_labels(body):
        return
    passage.body = body
    passage.fault_codes = fault_code_labels(body)
    passages.append(passage)


def _cap_chars(extracted: Extracted) -> None:
    total = 0
    kept: list[Block] = []
    for block in extracted.blocks:
        total += len(block.text)
        if total > MAX_EXTRACT_CHARS:
            extracted.warnings.append(
                "A dokumentum nagyon hosszú, az elejétől számítva került be."
            )
            break
        kept.append(block)
    extracted.blocks = kept


def _guess_kind(filename: str, extracted: Extracted) -> str:
    name = fold(Path(filename).stem)
    ext = extension_of(filename)
    records = sum(1 for block in extracted.blocks if block.kind == "record")
    slides = sum(1 for block in extracted.blocks if block.kind == "slide")
    sample = "\n".join(block.text for block in extracted.blocks[:300])
    codes = fault_code_labels(sample)
    if ext == ".pptx" or slides:
        return "presentation"
    prose = sum(1 for block in extracted.blocks if block.kind == "prose")
    if name in {"hiba", "hibak", "fault", "faults", "alarm", "alarms", "riasztas", "riasztasok"}:
        return "fault_list"
    if any(key in name for key in ("hibajegyz", "hibalista", "fault", "alarm", "riaszt", "hibakod")):
        return "fault_list"
    if records >= 2 and len(codes) >= 2 and records >= prose:
        return "fault_list"
    if any(key in name for key in ("utasit", "eljaras", "procedure", "sop", "munka")):
        return "procedure"
    if any(key in name for key in ("adatlap", "datasheet", "specifik")):
        return "datasheet"
    if "naplo" in name or name.endswith("log") or ext == ".log":
        return "log"
    if ext in {".xlsx", ".xlsm", ".csv", ".tsv"} or records >= 3:
        return "table"
    if ext in {".pdf", ".docx", ".odt", ".rtf"}:
        return "manual"
    return "document"


def _decode(data: bytes) -> str:
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16")
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig")
    for encoding in ("utf-8", "cp1250", "iso-8859-2", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _lines_to_blocks(text: str, *, markdown: bool, page: int | None = None) -> list[Block]:
    blocks: list[Block] = []
    section = ""
    buf: list[str] = []

    def flush() -> None:
        if buf:
            blocks.append(
                Block(text="\n".join(buf).strip(), kind="prose", page=page, section=section)
            )
            buf.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        heading = ""
        if markdown:
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                heading = match.group(2).strip()
        if not heading and looks_like_heading(line):
            heading = line
        if heading:
            flush()
            section = heading
            blocks.append(Block(text=heading, kind="heading", page=page, section=section))
            continue
        buf.append(line)
    flush()
    return [block for block in blocks if block.text]


def _plaintext(data: bytes, *, markdown: bool) -> Extracted:
    text = _decode(data)
    return Extracted(blocks=_lines_to_blocks(text, markdown=markdown))


def _pdf(data: bytes) -> Extracted:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    warnings: list[str] = []
    total = len(reader.pages)
    page_count = min(total, MAX_PDF_PAGES)
    if total > MAX_PDF_PAGES:
        warnings.append(f"Az első {MAX_PDF_PAGES} oldal került be, a többi nem.")
    blocks: list[Block] = []
    sparse = 0
    for index in range(page_count):
        raw = reader.pages[index].extract_text() or ""
        raw = re.sub(r"(\w)-\n(\w)", r"\1\2", raw)
        text = raw.strip()
        if len(text) < 30:
            sparse += 1
            continue
        blocks.extend(_lines_to_blocks(text, markdown=False, page=index + 1))
    if sparse and sparse < page_count:
        warnings.append(
            f"{sparse} oldalról nem jött szöveg, ezek valószínűleg szkennelt képek. "
            "A szöveges oldalak bekerültek."
        )
    return Extracted(blocks=blocks, warnings=warnings, page_count=page_count)


def _docx(data: bytes) -> Extracted:
    from docx import Document
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = Document(io.BytesIO(data))
    blocks: list[Block] = []
    section = ""
    row_count = 0
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            paragraph = Paragraph(child, document)
            text = paragraph.text.strip()
            if not text:
                continue
            style = ""
            if paragraph.style is not None and paragraph.style.name:
                style = paragraph.style.name.lower()
            if style.startswith("heading") or style.startswith("címsor"):
                section = text
                blocks.append(Block(text=text, kind="heading", section=section))
            else:
                blocks.append(Block(text=text, kind="prose", section=section))
        elif child.tag == qn("w:tbl"):
            table = Table(child, document)
            records, added = _table_records(_docx_rows(table), section=section)
            blocks.extend(records)
            row_count += added
    return Extracted(blocks=blocks, row_count=row_count)


def _docx_rows(table) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.rows:
        cells: list[str] = []
        for cell in row.cells:
            value = " ".join(cell.text.split())
            if cells and cells[-1] == value:
                continue
            cells.append(value)
        if any(cells):
            rows.append(cells)
    return rows


def _xlsx(data: bytes) -> Extracted:
    cached = _xlsx_blocks(data, data_only=True)
    if cached.row_count == 0:
        return _xlsx_blocks(data, data_only=False)
    return cached


def _xlsx_blocks(data: bytes, *, data_only: bool) -> Extracted:
    from openpyxl import load_workbook

    workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=data_only)
    try:
        blocks: list[Block] = []
        warnings: list[str] = []
        row_count = 0
        for sheet in workbook.worksheets:
            state = getattr(sheet, "sheet_state", "visible")
            if state and state != "visible":
                continue
            rows = _sheet_rows(sheet)
            if len(rows) > MAX_SHEET_ROWS:
                warnings.append(
                    f"A(z) „{sheet.title}” lapból az első {MAX_SHEET_ROWS} sor került be."
                )
                rows = rows[:MAX_SHEET_ROWS]
            sheet_name = "" if sheet.title.strip().lower() in _GENERIC_SHEET else sheet.title.strip()
            records, added = _table_records(rows, section=sheet_name, sheet=sheet_name)
            blocks.extend(records)
            row_count += added
        return Extracted(blocks=blocks, warnings=warnings, row_count=row_count)
    finally:
        workbook.close()


def _sheet_rows(sheet) -> list[list[str]]:
    rows: list[list[str]] = []
    for raw in sheet.iter_rows(max_col=MAX_SHEET_COLS, values_only=True):
        values = [_cell_text(value) for value in raw]
        while values and not values[-1]:
            values.pop()
        if any(values):
            rows.append(values)
    return rows


def _cell_text(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        text = value.isoformat()
        return text[:10] if "T" in text else text
    return str(value).strip()


def _csv(data: bytes, *, forced: str | None) -> Extracted:
    text = _decode(data)
    delimiter = forced or _delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows: list[list[str]] = []
    for raw in reader:
        values = [cell.strip() for cell in raw]
        while values and not values[-1]:
            values.pop()
        if any(values):
            rows.append(values[:MAX_SHEET_COLS])
        if len(rows) >= MAX_SHEET_ROWS:
            break
    records, added = _table_records(rows)
    warnings = []
    if len(rows) >= MAX_SHEET_ROWS:
        warnings.append(f"Az első {MAX_SHEET_ROWS} sor került be.")
    return Extracted(blocks=records, warnings=warnings, row_count=added)


def _delimiter(text: str) -> str:
    first = ""
    for line in text.splitlines():
        if line.strip():
            first = line
            break
    counts = {";": first.count(";"), ",": first.count(","), "\t": first.count("\t")}
    best = max(counts, key=counts.get)
    if counts[best] == 0:
        return ","
    return best


def _table_records(
    rows: list[list[str]],
    *,
    section: str = "",
    sheet: str = "",
) -> tuple[list[Block], int]:
    if not rows:
        return [], 0
    headers = _headers(rows[0]) if _row_is_header(rows[0]) else []
    start = 1 if headers else 0
    if not headers:
        width = max(len(row) for row in rows)
        headers = [f"Oszlop {i + 1}" for i in range(width)]
    blocks: list[Block] = []
    for row in rows[start:]:
        text = _record_text(headers, row)
        if not text:
            continue
        blocks.append(Block(text=text, kind="record", section=section, sheet=sheet))
    return blocks, len(blocks)


def _row_is_header(row: list[str]) -> bool:
    filled = [cell for cell in row if cell.strip()]
    if len(filled) < 2:
        return False
    textual = 0
    for cell in filled:
        compact = cell.replace(" ", "")
        if compact.isdigit():
            continue
        if re.fullmatch(r"\d+[.,]\d+", compact):
            continue
        textual += 1
    return textual >= max(1, len(filled) // 2)


def _headers(row: list[str]) -> list[str]:
    headers = []
    for index, cell in enumerate(row):
        label = " ".join(cell.split())
        headers.append(label or f"Oszlop {index + 1}")
    return headers


def _record_text(headers: list[str], values: list[str]) -> str:
    parts: list[str] = []
    for index, value in enumerate(values):
        value = " ".join(value.split())
        if not value:
            continue
        header = headers[index] if index < len(headers) and headers[index] else f"Oszlop {index + 1}"
        parts.append(f"{header}: {value}")
    return " | ".join(parts)


def _pptx(data: bytes) -> Extracted:
    from pptx import Presentation

    presentation = Presentation(io.BytesIO(data))
    blocks: list[Block] = []
    row_count = 0
    for number, slide in enumerate(presentation.slides, start=1):
        title = ""
        if slide.shapes.title is not None and slide.shapes.title.text:
            title = " ".join(slide.shapes.title.text.split())
        body_parts: list[str] = []
        for shape in slide.shapes:
            try:
                has_table = bool(shape.has_table)
            except Exception:
                has_table = False
            if has_table:
                rows = []
                for row in shape.table.rows:
                    rows.append([" ".join(cell.text.split()) for cell in row.cells])
                records, added = _table_records(rows, section=title, sheet="")
                for record in records:
                    record.slide = number
                blocks.extend(records)
                row_count += added
                continue
            if not getattr(shape, "has_text_frame", False):
                continue
            text = " ".join(shape.text_frame.text.split()) if shape.text_frame else ""
            if not text or text == title:
                continue
            body_parts.append(text)
        slide_text = "\n".join(part for part in ([title] if title else []) + body_parts)
        if slide_text.strip():
            blocks.append(
                Block(text=slide_text.strip(), kind="slide", section=title, slide=number)
            )
    return Extracted(blocks=blocks, slide_count=len(presentation.slides), row_count=row_count)


class _HtmlText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, str]] = []
        self._skip = 0
        self._buf: list[str] = []
        self._heading = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip += 1
        if tag in {"h1", "h2", "h3", "h4"}:
            self._flush(prose=True)
            self._heading = True
        if tag in {"p", "div", "br", "li", "tr", "section"}:
            self._buf.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1
        if tag in {"h1", "h2", "h3", "h4"}:
            self._flush(prose=False)
            self._heading = False
        if tag in {"p", "div", "li", "tr"}:
            self._buf.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self._buf.append(data)

    def close(self) -> None:
        super().close()
        self._flush(prose=not self._heading)

    def _flush(self, *, prose: bool) -> None:
        text = " ".join("".join(self._buf).split())
        self._buf = []
        if text:
            self.blocks.append(("prose" if prose else "heading", text))


def _html(data: bytes) -> Extracted:
    parser = _HtmlText()
    parser.feed(_decode(data))
    parser.close()
    blocks: list[Block] = []
    section = ""
    for kind, text in parser.blocks:
        if kind == "heading":
            section = text
            blocks.append(Block(text=text, kind="heading", section=section))
        else:
            blocks.append(Block(text=text, kind="prose", section=section))
    return Extracted(blocks=blocks)


def _json(data: bytes) -> Extracted:
    try:
        payload = json.loads(_decode(data))
    except json.JSONDecodeError as exc:
        raise ValueError("A JSON fájl nem olvasható.") from exc
    records = _json_records(payload)
    if records is not None:
        blocks, added = _table_records(records)
        return Extracted(blocks=blocks, row_count=added)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    return Extracted(blocks=_lines_to_blocks(text, markdown=False))


def _json_records(payload) -> list[list[str]] | None:
    rows = None
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        for key in ("rows", "items", "data", "records", "hibak"):
            if isinstance(payload.get(key), list):
                rows = payload[key]
                break
    if not rows or not all(isinstance(row, dict) for row in rows):
        return None
    keys: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in keys:
                keys.append(str(key))
    table = [keys]
    for row in rows:
        table.append([_cell_text(row.get(key)) for key in keys])
    return table


def _xml(data: bytes) -> Extracted:
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        raise ValueError("Az XML fájl nem olvasható.") from exc
    children = list(root)
    if len(children) >= 2 and len({_local(child.tag) for child in children}) == 1:
        rows: list[list[str]] = []
        for child in children:
            pairs = []
            for element in child.iter():
                if element is child or not element.text or not element.text.strip():
                    continue
                pairs.append((_local(element.tag), " ".join(element.text.split())))
            if pairs:
                if not rows:
                    rows.append([key for key, _ in pairs])
                rows.append([value for _, value in pairs])
        if len(rows) > 1:
            blocks, added = _table_records(rows)
            return Extracted(blocks=blocks, row_count=added)
    text = "\n".join(part.strip() for part in root.itertext() if part and part.strip())
    return Extracted(blocks=_lines_to_blocks(text, markdown=False))


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _rtf(data: bytes) -> Extracted:
    raw = data.decode("latin-1", errors="ignore")

    def unicode_char(match: re.Match[str]) -> str:
        value = int(match.group(1))
        if value < 0:
            value += 65536
        return chr(value)

    raw = re.sub(r"\\u(-?\d+)\??", unicode_char, raw)
    raw = re.sub(
        r"\\'([0-9a-fA-F]{2})",
        lambda match: bytes.fromhex(match.group(1)).decode("cp1250", errors="ignore"),
        raw,
    )
    raw = raw.replace("\\par", "\n").replace("\\line", "\n").replace("\\tab", " ")
    raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", raw)
    raw = raw.replace("{", "").replace("}", "")
    return Extracted(blocks=_lines_to_blocks(raw, markdown=False))


def _odt(data: bytes) -> Extracted:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            xml = package.read("content.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ValueError("A Word-szerű ODT fájl nem olvasható.") from exc
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise ValueError("A Word-szerű ODT fájl nem olvasható.") from exc
    text = "\n".join(part.strip() for part in root.itertext() if part and part.strip())
    return Extracted(blocks=_lines_to_blocks(text, markdown=False))
