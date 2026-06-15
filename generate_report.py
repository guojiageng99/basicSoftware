#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate the final Word report (.docx) from report_data.json."""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "report_data.json"
OUTPUT_FILE = BASE / "大作业报告.docx"


def load_report_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def setup_document(doc):
    """Configure page margins and default font."""
    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

    style = doc.styles["Normal"]
    style.font.name = "Microsoft YaHei"
    style.font.size = Pt(12)
    style.paragraph_format.line_spacing = 1.5


def font(run, name="Microsoft YaHei", size=12, bold=False, color=None):
    """Apply font settings to a run."""
    run.font.name = name
    if size:
        run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = color


def add_heading(doc, text, level=1):
    """Add a heading with consistent styling."""
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        font(r, name="Microsoft YaHei", bold=True)
    return h


def add_paragraph(doc, text, size=12, align=None, space_after=6, bold=False):
    """Add a paragraph with consistent styling."""
    p = doc.add_paragraph()
    r = p.add_run(text)
    font(r, name="Microsoft YaHei", size=size, bold=bold)
    p.paragraph_format.space_after = Pt(space_after)
    if align:
        p.alignment = align
    return p


def add_bullet(doc, text, level=0, size=11):
    """Add a bullet point item."""
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.left_indent = Cm(1.2 + level * 0.8)
    p.paragraph_format.space_after = Pt(3)
    for r in p.runs:
        font(r, name="Microsoft YaHei", size=size)
    return p


def add_table(doc, data, col_count=0):
    """
    Add a table from a list of lists.
    data[0] is the header row.
    Style: Light Grid Accent 1.
    Uses max column count across all rows, padding shorter rows.
    """
    ncols = max(len(row) for row in data) if data else 1
    t = doc.add_table(rows=len(data), cols=ncols)
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER

    for i, row in enumerate(data):
        for j, cell_text in enumerate(row):
            if j >= ncols:
                break
            cell = t.rows[i].cells[j]
            cell.text = ""
            run = cell.paragraphs[0].add_run(cell_text)
            font(run, name="Microsoft YaHei", size=10, bold=(i == 0))
    return t


def build_report(data):
    doc = Document()
    setup_document(doc)

    # --- Cover page ---
    for _ in range(5):
        doc.add_paragraph()

    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = tp.add_run(data["title"])
    font(r, size=22, bold=True)

    doc.add_paragraph()

    sp = doc.add_paragraph()
    sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sp.add_run("—— " + data["subtitle"])
    font(r, size=14)

    ip = doc.add_paragraph()
    ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ip.paragraph_format.space_before = Pt(30)

    # Process authors (handle \n in authors field)
    lines = [l for l in data["authors"].split("\n") if l.strip()]
    for i, line in enumerate(lines):
        ar = ip.add_run(line)
        font(ar, size=12)
        if i < len(lines) - 1:
            doc.add_paragraph()  # blank line between author lines

    doc.add_page_break()

    # --- TOC placeholder ---
    add_heading(doc, "目  录", level=1)
    p = doc.add_paragraph()
    r = p.add_run("（请手动插入目录：引用 → 索引和目录 → 自动目录）")
    font(r, size=11, bold=False)
    doc.add_page_break()

    # --- Report sections ---
    for section in data["sections"]:
        add_heading(doc, section["heading"], level=section.get("level", 1))

        for para_text in section.get("paragraphs", []):
            add_paragraph(doc, para_text)

        for bullet_text in section.get("bullets", []):
            add_bullet(doc, bullet_text)

        for table_data in section.get("table", []):
            add_table(doc, table_data)

        for sub in section.get("subsections", []):
            add_heading(doc, sub["heading"], level=sub.get("level", 2))

            for para_text in sub.get("paragraphs", []):
                add_paragraph(doc, para_text)

            for bullet_text in sub.get("bullets", []):
                add_bullet(doc, bullet_text)

            for table_data in sub.get("table", []):
                add_table(doc, table_data)

        doc.add_page_break()

    # Remove trailing page break
    doc.paragraphs[-1].clear()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT_FILE))
    print(f"[OK] Report saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    print("Generating Word report from report_data.json ...")
    data = load_report_data()
    build_report(data)
    print("Done!")
