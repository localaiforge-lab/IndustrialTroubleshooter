#!/usr/bin/env python3
"""Minimal Markdown → DOCX for the developer architecture note."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

REPO = Path(__file__).resolve().parents[1]


def set_run_font(run, size=None, bold=False, italic=False, color=None, mono=False):
    run.font.name = "Consolas" if mono else "Calibri"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), run.font.name)
    if size:
        run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color


def add_inline(paragraph, text, *, size=11, mono=False, color=None):
    pattern = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`)")
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            run = paragraph.add_run(text[pos : match.start()])
            set_run_font(run, size=size, mono=mono, color=color)
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            set_run_font(run, size=size, bold=True, mono=mono, color=color)
        else:
            run = paragraph.add_run(token[1:-1])
            set_run_font(run, size=max(9, size - 1), mono=True, color=color or RGBColor(0x1A, 0x3A, 0x5C))
        pos = match.end()
    if pos < len(text):
        run = paragraph.add_run(text[pos:])
        set_run_font(run, size=size, mono=mono, color=color)


def add_table(doc, rows: list[list[str]]) -> None:
    if not rows:
        return
    cols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=cols)
    table.style = "Table Grid"
    for r_i, row in enumerate(rows):
        for c_i in range(cols):
            cell = table.rows[r_i].cells[c_i]
            cell.text = ""
            val = row[c_i] if c_i < len(row) else ""
            add_inline(cell.paragraphs[0], val, size=10, color=None)
            if r_i == 0:
                for run in cell.paragraphs[0].runs:
                    run.bold = True
    doc.add_paragraph()


def convert(md_path: Path, out_path: Path) -> None:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    doc.core_properties.title = "LUMEEI AI Mind — szoftverarchitektúra"
    doc.core_properties.subject = "Fejlesztői és agent dokumentáció"
    doc.core_properties.language = "hu-HU"
    doc.core_properties.category = "Architektúra"

    i = 0
    first_h1 = True
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        if line.startswith("```"):
            i += 1
            buf: list[str] = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.space_before = Pt(2)
            run = p.add_run("\n".join(buf))
            set_run_font(run, size=9, mono=True, color=RGBColor(0x1A, 0x3A, 0x5C))
            continue

        if line.startswith("# "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if first_h1 else WD_ALIGN_PARAGRAPH.LEFT
            add_inline(
                p,
                line[2:].strip(),
                size=22 if first_h1 else 16,
                color=RGBColor(0x1A, 0x3A, 0x5C),
            )
            for run in p.runs:
                run.bold = True
            first_h1 = False
            i += 1
            continue

        if line.startswith("## "):
            p = doc.add_heading(line[3:].strip().replace("`", ""), level=1)
            for run in p.runs:
                set_run_font(run, size=16, bold=True, color=RGBColor(0x1A, 0x3A, 0x5C))
            i += 1
            continue

        if line.startswith("### "):
            p = doc.add_heading(line[4:].strip().replace("`", ""), level=2)
            for run in p.runs:
                set_run_font(run, size=13, bold=True, color=RGBColor(0x2C, 0x4A, 0x6E))
            i += 1
            continue

        if line.startswith("|"):
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].startswith("|"):
                raw = lines[i].strip().strip("|")
                cells = [c.strip() for c in raw.split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) or set(c) <= set("-: ") for c in cells):
                    rows.append(cells)
                i += 1
            add_table(doc, rows)
            continue

        if line.startswith("- "):
            while i < len(lines) and lines[i].startswith("- "):
                p = doc.add_paragraph(style="List Bullet")
                p.paragraph_format.space_after = Pt(3)
                add_inline(p, lines[i][2:].strip())
                i += 1
            continue

        if re.match(r"\d+\. ", line.strip()):
            while i < len(lines) and re.match(r"\d+\. ", lines[i].strip()):
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.left_indent = Cm(0.75)
                add_inline(p, lines[i].strip())
                i += 1
            continue

        buf = [line.strip()]
        i += 1
        while (
            i < len(lines)
            and lines[i].strip()
            and not lines[i].startswith(("#", "-", "|", "```"))
            and not re.match(r"\d+\. ", lines[i].strip())
        ):
            buf.append(lines[i].strip())
            i += 1
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.line_spacing = 1.15
        add_inline(p, " ".join(buf))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")


def main() -> int:
    src = REPO / "docs" / "Szoftver_Architektura.md"
    dst = REPO / "docs" / "Szoftver_Architektura.docx"
    if len(sys.argv) >= 3:
        src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    convert(src, dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
