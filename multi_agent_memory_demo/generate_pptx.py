#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate the defense PPT (.pptx) from pptx_data.json."""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from pptx import Presentation
from pptx.util import Inches as PptInches, Pt as PptPt
from pptx.dml.color import RGBColor as PptRGB

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "pptx_data.json"
OUTPUT_FILE = BASE.parent / "答辩PPT.pptx"

# Color palette matching the template
BG_CREAM = PptRGB(244, 241, 234)
GREEN_ACCENT = PptRGB(25, 107, 84)
TEXT_BLACK = PptRGB(24, 34, 31)
TEXT_GRAY = PptRGB(102, 112, 107)


def load_ppt_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def create_blank_slide(prs):
    """Create a blank slide with cream background and green accent bar."""
    layout = prs.slide_layouts[6]  # Blank layout
    slide = prs.slides.add_slide(layout)

    # Cream background
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = BG_CREAM

    # Green accent bar at top
    bar = slide.shapes.add_shape(
        1,  # rectangle
        PptInches(0), PptInches(0),
        PptInches(13.333), PptInches(0.06)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = GREEN_ACCENT
    bar.line.fill.background()

    return slide


def add_title_bar(slide, text):
    """Add a green-accented title bar at the top."""
    tb = slide.shapes.add_textbox(
        PptInches(0.7), PptInches(0.25),
        PptInches(11.5), PptInches(0.9)
    )
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = text
    r.font.size = PptPt(26)
    r.bold = True
    r.font.color.rgb = GREEN_ACCENT
    r.font.name = "微软雅黑"
    return slide


def add_bullets(slide, items, top=1.4):
    """Add bullet-point items below the title."""
    tb = slide.shapes.add_textbox(
        PptInches(0.7), PptInches(top),
        PptInches(11.5), PptInches(5.5)
    )
    tf = tb.text_frame
    tf.word_wrap = True

    for idx, item in enumerate(items):
        if idx == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.space_after = PptPt(8)
        r = p.add_run()
        r.text = "• " + item
        r.font.size = PptPt(15)
        r.font.color.rgb = TEXT_BLACK
        r.font.name = "微软雅黑"

    return slide


def build_ppt(data):
    prs = Presentation()
    prs.slide_width = PptInches(13.333)
    prs.slide_height = PptInches(7.5)

    # --- Slide 1: Cover ---
    slide = create_blank_slide(prs)
    add_title_bar(slide, data["title"])

    # Subtitle + authors
    sb = slide.shapes.add_textbox(
        PptInches(1), PptInches(4.8),
        PptInches(11), PptInches(0.6)
    )
    sf = sb.text_frame
    r = sf.paragraphs[0].add_run()
    r.text = "—— 2026春《国产基础软件技术及应用》课程大作业"
    r.font.size = PptPt(14)
    r.font.color.rgb = TEXT_GRAY
    r.font.name = "微软雅黑"

    # --- Slides 2-9: Content slides ---
    current_top = 1.5
    for slide_data in data["slides"]:
        add_title_bar(create_blank_slide(prs), slide_data["title"])
        add_bullets(prs.slides[-1], slide_data["items"], top=current_top)
        current_top += 0.1  # slight offset for longer titles

    # --- Last slide: Thank you ---
    slide = create_blank_slide(prs)
    tb = slide.shapes.add_textbox(
        PptInches(2), PptInches(3.0),
        PptInches(9), PptInches(1.5)
    )
    tf = tb.text_frame
    tf.word_wrap = True
    r = tf.paragraphs[0].add_run()
    r.text = "感谢聆听"
    r.font.size = PptPt(36)
    r.bold = True
    r.font.color.rgb = GREEN_ACCENT
    r.font.name = "微软雅黑"

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT_FILE))
    print(f"[OK] PPT saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    print("Generating PPT from pptx_data.json ...")
    data = load_ppt_data()
    build_ppt(data)
    print("Done!")
