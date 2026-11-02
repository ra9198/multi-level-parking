#!/usr/bin/env python3
"""Build the editable Parkline project-review PowerPoint deck.

The deck is grounded in the repository README, application source, 111-page
project report, diagrams, real Chromium screenshots and JSON verification
evidence. All slide text and vector shapes remain editable in PowerPoint;
existing report screenshots/diagrams are embedded as images.

Usage:
    python scripts/build-project-review-pptx.py
    python scripts/build-project-review-pptx.py --previews
"""

from __future__ import annotations

import argparse
import io
import math
import os
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_FILL
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "project-review"
REPORT = ROOT / "docs" / "project-report"
SHOTS = REPORT / "assets" / "screenshots"
DIAGRAMS = REPORT / "assets" / "diagrams"
CACHE = ROOT / ".cache" / "project-review"
ASSETS = CACHE / "assets"
OUT = DOCS / "Parkline_Project_Review.pptx"

EMU_PER_INCH = 914400
SLIDE_W_IN = 13.333333
SLIDE_H_IN = 7.5
TOTAL_SLIDES = 30
PREVIEW_SCALE = 120  # px per inch

FONT = "Arial"
MONO = "Consolas"
SANS_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO_REG = str(REPORT / "assets" / "fonts" / "DejaVuSansMono.ttf")
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

INK = "172823"
DARK = "0C211C"
DARK_2 = "12362D"
MUTED = "52615B"
SOFT = "88938F"
CANVAS = "F5F7F5"
WHITE = "FFFFFF"
GREEN = "157B5B"
GREEN_2 = "46C692"
PALE_GREEN = "E6F4EE"
PALE_GREEN_2 = "F1F9F5"
AMBER = "C58229"
PALE_AMBER = "FFF3DF"
RED = "B94747"
PALE_RED = "FCEBEB"
BLUE = "2E6F8E"
PALE_BLUE = "EAF3F7"
BORDER = "D9E2DD"
PALE = "EEF2EF"
SHADOW = "E2E9E4"
CODE_BG = "122923"
CODE_INK = "E8F1ED"

SECTIONS = [
    "CONTEXT",
    "REQUIREMENTS",
    "DESIGN & BUILD",
    "PRODUCT DEMO",
    "VERIFICATION",
    "OUTLOOK",
]


def rgb(value: str) -> RGBColor:
    return RGBColor.from_string(value.lstrip("#"))


def hex_tuple(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def rgb_tuple(color: RGBColor) -> tuple[int, int, int]:
    text = str(color)
    return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def px(value) -> int:
    """Convert a python-pptx Length (EMU) to preview pixels."""
    return int(round(float(value) / EMU_PER_INCH * PREVIEW_SCALE))


class Deck:
    def __init__(self) -> None:
        self.prs = Presentation()
        self.prs.slide_width = Inches(SLIDE_W_IN)
        self.prs.slide_height = Inches(SLIDE_H_IN)
        self.blank = self.prs.slide_layouts[6]
        self.asset_counter = 0
        CACHE.mkdir(parents=True, exist_ok=True)
        ASSETS.mkdir(parents=True, exist_ok=True)
        DOCS.mkdir(parents=True, exist_ok=True)

    # ---------- low-level primitives ----------

    def set_bg(self, slide, color: str) -> None:
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = rgb(color)

    def rect(
        self,
        slide,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = WHITE,
        line: str | None = None,
        line_width: float = 0.8,
        rounded: bool = False,
    ):
        kind = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
        shape = slide.shapes.add_shape(
            kind, Inches(x), Inches(y), Inches(w), Inches(h)
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill)
        if line:
            shape.line.color.rgb = rgb(line)
            shape.line.width = Pt(line_width)
        else:
            shape.line.fill.background()
        if rounded:
            try:
                shape.adjustments[0] = 0.10
            except Exception:
                pass
        return shape

    def oval(self, slide, x: float, y: float, w: float, h: float, fill: str, line: str | None = None):
        shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill)
        if line:
            shape.line.color.rgb = rgb(line)
            shape.line.width = Pt(0.8)
        else:
            shape.line.fill.background()
        return shape

    def hline(self, slide, x: float, y: float, w: float, color: str = BORDER, h: float = 0.012):
        return self.rect(slide, x, y, w, h, fill=color)

    def vline(self, slide, x: float, y: float, h: float, color: str = BORDER, w: float = 0.012):
        return self.rect(slide, x, y, w, h, fill=color)

    def text(
        self,
        slide,
        x: float,
        y: float,
        w: float,
        h: float,
        value: str,
        size: float = 12,
        color: str = INK,
        bold: bool = False,
        align: str = "left",
        valign: str = "top",
        font: str = FONT,
        line_spacing: float = 1.08,
        space_after: float = 0,
        italic: bool = False,
        word_wrap: bool = True,
    ):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.clear()
        tf.word_wrap = word_wrap
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = 0
        tf.margin_right = 0
        tf.margin_top = 0
        tf.margin_bottom = 0
        tf.vertical_anchor = {
            "top": MSO_ANCHOR.TOP,
            "middle": MSO_ANCHOR.MIDDLE,
            "bottom": MSO_ANCHOR.BOTTOM,
        }[valign]
        alignment = {
            "left": PP_ALIGN.LEFT,
            "center": PP_ALIGN.CENTER,
            "right": PP_ALIGN.RIGHT,
            "justify": PP_ALIGN.JUSTIFY,
        }[align]
        lines = value.split("\n")
        for index, line in enumerate(lines):
            para = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
            para.alignment = alignment
            para.space_after = Pt(space_after)
            para.line_spacing = line_spacing
            run = para.add_run()
            run.text = line
            run.font.name = font
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.italic = italic
            run.font.color.rgb = rgb(color)
        return box

    def card(
        self,
        slide,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = WHITE,
        border: str | None = BORDER,
        shadow: bool = True,
    ):
        if shadow:
            self.rect(slide, x + 0.035, y + 0.045, w, h, fill=SHADOW, rounded=True)
        return self.rect(slide, x, y, w, h, fill=fill, line=border, rounded=True)

    def pill(self, slide, x: float, y: float, w: float, h: float, label: str, fill: str = PALE_GREEN, color: str = GREEN, size: float = 9.5):
        self.rect(slide, x, y, w, h, fill=fill, rounded=True)
        self.text(slide, x + 0.08, y, w - 0.16, h, label, size=size, color=color, bold=True, align="center", valign="middle")

    def badge(self, slide, x: float, y: float, label: str, fill: str = GREEN, color: str = WHITE, w: float = 1.25, h: float = 0.28, size: float = 8.5):
        self.rect(slide, x, y, w, h, fill=fill, rounded=True)
        self.text(slide, x + 0.06, y, w - 0.12, h, label, size=size, color=color, bold=True, align="center", valign="middle")

    def bullet_card(
        self,
        slide,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        items: list[str],
        accent: str = GREEN,
        fill: str = WHITE,
        title_size: float = 13,
        body_size: float = 10.5,
        step: float | None = None,
    ):
        self.card(slide, x, y, w, h, fill=fill)
        self.rect(slide, x, y, 0.055, h, fill=accent)
        self.text(slide, x + 0.22, y + 0.16, w - 0.42, 0.34, title, size=title_size, bold=True)
        available = h - 0.62
        step = step or min(0.52, available / max(1, len(items)))
        for i, item in enumerate(items):
            cy = y + 0.58 + i * step
            self.oval(slide, x + 0.23, cy + 0.12, 0.075, 0.075, fill=accent)
            self.text(
                slide,
                x + 0.40,
                cy,
                w - 0.62,
                max(0.30, step - 0.03),
                item,
                size=body_size,
                color=MUTED,
                line_spacing=1.05,
            )

    def stat_card(self, slide, x: float, y: float, w: float, h: float, value: str, label: str, detail: str = "", accent: str = GREEN, fill: str = WHITE):
        self.card(slide, x, y, w, h, fill=fill)
        self.rect(slide, x, y, w, 0.055, fill=accent)
        self.text(slide, x + 0.18, y + 0.22, w - 0.36, 0.55, value, size=27, color=accent, bold=True)
        self.text(slide, x + 0.18, y + 0.82, w - 0.36, 0.34, label, size=11.5, bold=True)
        if detail:
            self.text(slide, x + 0.18, y + 1.14, w - 0.36, h - 1.22, detail, size=9.5, color=MUTED, line_spacing=1.08)

    def callout(self, slide, x: float, y: float, w: float, h: float, label: str, body: str, fill: str = PALE_GREEN, accent: str = GREEN, label_color: str | None = None):
        self.card(slide, x, y, w, h, fill=fill, border=None, shadow=False)
        self.rect(slide, x, y, 0.07, h, fill=accent)
        if h < 0.82:
            label_w = min(2.15, max(0.85, 0.075 * len(label) + 0.35))
            self.pill(slide, x + 0.15, y + max(0.04, (h - 0.24) / 2), label_w, 0.24, label, fill=WHITE, color=label_color or accent, size=7.3)
            self.text(
                slide,
                x + 0.22 + label_w,
                y + 0.02,
                max(0.8, w - label_w - 0.38),
                max(0.22, h - 0.04),
                body,
                size=8.0,
                color=INK,
                valign="middle",
                line_spacing=1.0,
            )
            return
        self.text(slide, x + 0.20, y + 0.12, w - 0.35, 0.25, label, size=9.5, color=label_color or accent, bold=True)
        self.text(slide, x + 0.20, y + 0.40, w - 0.35, h - 0.50, body, size=10.5, color=INK, line_spacing=1.08)

    def table(self, slide, x: float, y: float, w: float, headers: list[str], rows: list[list[str]], col_fracs: list[float], row_h: float = 0.43, header_h: float = 0.38, font_size: float = 9.5):
        widths = [w * f for f in col_fracs]
        self.rect(slide, x, y, w, header_h, fill=PALE_GREEN, line=BORDER, rounded=True)
        cx = x
        for i, head in enumerate(headers):
            self.text(slide, cx + 0.10, y, widths[i] - 0.20, header_h, head, size=9.2, color=GREEN, bold=True, valign="middle")
            cx += widths[i]
        for r, row in enumerate(rows):
            ry = y + header_h + r * row_h
            fill = WHITE if r % 2 == 0 else PALE_GREEN_2
            self.rect(slide, x, ry, w, row_h, fill=fill, line=BORDER)
            cx = x
            for c, cell in enumerate(row):
                color = INK if c == 0 else MUTED
                self.text(slide, cx + 0.10, ry + 0.02, widths[c] - 0.20, row_h - 0.04, cell, size=font_size, color=color, bold=(c == 0), valign="middle", line_spacing=1.0)
                cx += widths[c]

    def progress_bar(self, slide, x: float, y: float, w: float, label: str, value: int, maximum: int, color: str = GREEN, note: str = ""):
        self.text(slide, x, y, w * 0.45, 0.26, label, size=10.5, bold=True)
        self.text(slide, x + w * 0.45, y, w * 0.55, 0.26, note, size=9.5, color=MUTED, align="right")
        by = y + 0.30
        self.rect(slide, x, by, w, 0.13, fill=PALE, rounded=True)
        if maximum:
            self.rect(slide, x, by, w * min(1.0, value / maximum), 0.13, fill=color, rounded=True)

    def node(self, slide, x: float, y: float, w: float, h: float, title: str, body: str, fill: str = WHITE, accent: str = GREEN, title_size: float = 12, body_size: float = 9.5):
        self.card(slide, x, y, w, h, fill=fill)
        self.rect(slide, x, y, w, 0.055, fill=accent)
        self.text(slide, x + 0.16, y + 0.11, w - 0.32, 0.34, title, size=title_size, bold=True, align="center")
        self.text(slide, x + 0.16, y + 0.46, w - 0.32, max(0.20, h - 0.52), body, size=body_size, color=MUTED, align="center", line_spacing=1.0)

    def arrow(self, slide, x: float, y: float, w: float, h: float, glyph: str = "→", color: str = GREEN, size: float = 22):
        self.text(slide, x, y, w, h, glyph, size=size, color=color, bold=True, align="center", valign="middle")

    def code_card(self, slide, x: float, y: float, w: float, h: float, filename: str, code: str, size: float = 9.2):
        self.card(slide, x, y, w, h, fill=CODE_BG, border=None, shadow=True)
        self.pill(slide, x + 0.16, y + 0.13, min(w - 0.32, 2.8), 0.27, filename, fill="21483E", color=GREEN_2, size=8.2)
        self.text(slide, x + 0.18, y + 0.52, w - 0.36, h - 0.64, code, size=size, color=CODE_INK, font=MONO, line_spacing=1.12)

    # ---------- images ----------

    def _asset_path(self, stem: str) -> Path:
        self.asset_counter += 1
        return ASSETS / f"{stem}-{self.asset_counter:03d}.png"

    def image(
        self,
        slide,
        path: Path,
        x: float,
        y: float,
        w: float,
        h: float,
        mode: str = "contain",
        centering: tuple[float, float] = (0.5, 0.5),
        bg: str = WHITE,
        alt: str = "",
    ):
        target = (max(1, int(w * PREVIEW_SCALE)), max(1, int(h * PREVIEW_SCALE)))
        with Image.open(path) as source:
            source = source.convert("RGB")
            if mode == "fit":
                prepared = ImageOps.fit(source, target, method=Image.Resampling.LANCZOS, centering=centering)
            else:
                canvas = Image.new("RGB", target, hex_tuple(bg))
                contained = ImageOps.contain(source, target, method=Image.Resampling.LANCZOS)
                canvas.paste(contained, ((target[0] - contained.width) // 2, (target[1] - contained.height) // 2))
                prepared = canvas
            output = self._asset_path(path.stem)
            prepared.save(output)
        picture = slide.shapes.add_picture(str(output), Inches(x), Inches(y), Inches(w), Inches(h))
        if alt:
            try:
                cnvpr = picture._element.xpath(".//p:cNvPr")[0]
                cnvpr.set("descr", alt)
            except Exception:
                pass
        return picture

    def screenshot(self, slide, path: Path, x: float, y: float, w: float, h: float, caption: str, mode: str = "contain", centering: tuple[float, float] = (0.5, 0.5)):
        self.card(slide, x, y, w, h)
        self.image(slide, path, x + 0.08, y + 0.08, w - 0.16, h - 0.42, mode=mode, centering=centering, alt=caption)
        self.text(slide, x + 0.12, y + h - 0.34, w - 0.24, 0.26, caption, size=8.2, color=MUTED, align="center", valign="middle")

    # ---------- slide chrome ----------

    def cover_background(self) -> Path:
        width, height = 1600, 900
        image = Image.new("RGB", (width, height), hex_tuple(DARK))
        draw = ImageDraw.Draw(image)
        for xpos in range(width):
            t = xpos / width
            base = (
                int(hex_tuple(DARK)[0] * (1 - t) + hex_tuple(DARK_2)[0] * t),
                int(hex_tuple(DARK)[1] * (1 - t) + hex_tuple(DARK_2)[1] * t),
                int(hex_tuple(DARK)[2] * (1 - t) + hex_tuple(DARK_2)[2] * t),
            )
            draw.line((xpos, 0, xpos, height), fill=base)
        # Subtle parking-bay pattern on the title side.
        for row in range(5):
            for col in range(7):
                bx = 55 + col * 88
                by = 85 + row * 160
                draw.rounded_rectangle((bx, by, bx + 68, by + 118), radius=10, outline=(25, 71, 59), width=2)
        with Image.open(SHOTS / "01-overview.png") as shot:
            shot = shot.convert("RGB")
            panel = ImageOps.fit(shot, (700, height), method=Image.Resampling.LANCZOS, centering=(0.58, 0.45))
        image.paste(panel, (900, 0))
        fade = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        fade_draw = ImageDraw.Draw(fade)
        for i in range(260):
            alpha = int(155 * (1 - i / 260))
            fade_draw.line((900 + i, 0, 900 + i, height), fill=(7, 28, 23, alpha))
        image = Image.alpha_composite(image.convert("RGBA"), fade).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.rectangle((896, 0, 904, height), fill=hex_tuple(GREEN_2))
        draw.rectangle((900, 820, 1600, 900), fill=(10, 35, 29))
        output = CACHE / "cover-background.png"
        image.save(output)
        return output

    def add_cover(self):
        slide = self.prs.slides.add_slide(self.blank)
        self.set_bg(slide, DARK)
        self.cover_bg_path = self.cover_background()
        self.image(slide, self.cover_bg_path, 0, 0, SLIDE_W_IN, SLIDE_H_IN, mode="fit", alt="Dark green title background with a real Parkline dashboard capture on the right")
        # Wordmark.
        self.rect(slide, 0.78, 0.62, 0.46, 0.46, fill=GREEN, rounded=True)
        for i, offset in enumerate((0.13, 0.20, 0.27)):
            self.rect(slide, 0.88 + i * 0.025, 0.62 + offset, 0.24 - i * 0.025, 0.055, fill=WHITE, rounded=True)
        self.text(slide, 1.34, 0.63, 2.3, 0.42, "parkline.", size=20, color=WHITE, bold=True, valign="middle")
        self.text(slide, 10.65, 0.68, 1.9, 0.25, "PROJECT REVIEW", size=9.5, color=GREEN_2, bold=True, align="right")
        self.pill(slide, 0.82, 1.55, 2.15, 0.32, "ACADEMIC PROJECT · 2026", fill="1B4B3E", color=GREEN_2, size=8.5)
        self.text(slide, 0.80, 2.05, 6.30, 1.75, "Multi-Level Parking\nOperations & Capacity\nPlanning", size=34, color=WHITE, bold=True, line_spacing=1.02)
        self.text(slide, 0.82, 3.98, 6.20, 0.40, "Parkline · Functional UI / domain-logic MVP", size=15.5, color=GREEN_2, bold=True)
        self.hline(slide, 0.82, 4.55, 5.7, color="2E6B58", h=0.018)
        self.text(slide, 0.82, 4.78, 6.20, 0.78, "A codebase-grounded review of requirements, architecture,\nimplementation, live screens, verification and roadmap.", size=12.5, color="D9E8E1", line_spacing=1.20)
        self.text(slide, 0.82, 6.22, 6.30, 0.30, "Presented by [Student Name] · [Register Number]", size=10.5, color=WHITE, bold=True)
        self.text(slide, 0.82, 6.58, 6.30, 0.28, "Guided by [Project Guide Name] · November 2026", size=9.5, color="B9CFC5")
        self.text(slide, 0.82, 7.02, 6.30, 0.22, "Version 0.1.0 · 4 seeded sites · 72 bays/site · browser-local persistence", size=8.5, color="A8C1B5")
        self.rect(slide, 9.72, 7.00, 2.45, 0.34, fill="123A2F", rounded=True)
        self.text(slide, 9.80, 7.00, 2.29, 0.34, "Actual built UI · captured from build", size=8.0, color="D9E8E1", align="center", valign="middle")
        slide.notes_slide.notes_text_frame.text = (
            "Opening slide. Replace the student, register number and guide placeholders before submission. "
            "State clearly that Parkline is a browser-local MVP, not an installed parking-control system. "
            "The right-hand image is a genuine capture of the built application, not a mockup."
        )
        return slide

    def progress(self, slide, section_index: int):
        x, y, w, h = 0.0, 7.44, SLIDE_W_IN, 0.06
        gap = 0.025
        seg = (w - gap * (len(SECTIONS) - 1)) / len(SECTIONS)
        for i in range(len(SECTIONS)):
            color = GREEN if i + 1 == section_index else "DCE6E0"
            self.rect(slide, x + i * (seg + gap), y, seg, h, fill=color)

    def standard_slide(self, section_index: int, title: str, subtitle: str, notes: str = ""):
        slide = self.prs.slides.add_slide(self.blank)
        self.set_bg(slide, CANVAS)
        number = len(self.prs.slides)
        self.text(slide, 0.68, 0.30, 4.0, 0.20, "PARKLINE / PROJECT REVIEW", size=8.2, color=SOFT, bold=True)
        self.text(slide, 9.4, 0.30, 3.25, 0.20, f"{section_index:02d} / {SECTIONS[section_index - 1]}", size=8.2, color=GREEN, bold=True, align="right")
        self.rect(slide, 0.48, 0.60, 0.065, 0.58, fill=GREEN)
        self.text(slide, 0.68, 0.57, 11.9, 0.62, title, size=26.5, color=INK, bold=True)
        self.text(slide, 0.68, 1.19, 11.9, 0.32, subtitle, size=11.2, color=MUTED)
        self.hline(slide, 0.68, 1.62, 11.95, color=BORDER)
        self.text(slide, 0.68, 7.10, 6.8, 0.20, "Parkline · Project Review | Source-grounded MVP", size=8.0, color=SOFT)
        self.text(slide, 11.25, 7.10, 1.4, 0.20, f"{number:02d} / {TOTAL_SLIDES:02d}", size=8.0, color=SOFT, align="right")
        self.progress(slide, section_index)
        if notes:
            slide.notes_slide.notes_text_frame.text = notes
        return slide

    @staticmethod
    def set_thumbnail(pptx_path: Path, image_path: Path) -> None:
        """Replace the default template thumbnail with the generated cover art."""
        thumbnail = CACHE / "cover-thumbnail.jpeg"
        with Image.open(image_path) as source:
            source.convert("RGB").save(thumbnail, "JPEG", quality=88, optimize=True)
        thumbnail_bytes = thumbnail.read_bytes()
        temp = pptx_path.with_suffix(".pptx.tmp")
        with zipfile.ZipFile(pptx_path, "r") as source_zip, zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as target_zip:
            for item in source_zip.infolist():
                data = thumbnail_bytes if item.filename == "docProps/thumbnail.jpeg" else source_zip.read(item.filename)
                target_zip.writestr(item, data)
        os.replace(temp, pptx_path)

    def save(self):
        props = self.prs.core_properties
        props.title = "Parkline — Multi-Level Parking Operations | Project Review"
        props.subject = "Comprehensive project review of the Parkline browser-local MVP"
        props.author = "Parkline project review deck generator"
        props.keywords = "Parkline, multi-level parking, project review, Next.js, TypeScript, MVP"
        props.category = "Project review presentation"
        props.comments = "Generated from repository source, report, diagrams, screenshots and verification evidence."
        self.prs.save(OUT)
        if getattr(self, "cover_bg_path", None):
            self.set_thumbnail(OUT, self.cover_bg_path)
        return OUT


# ---------- preview rendering ----------

class PreviewRenderer:
    def __init__(self, prs: Presentation):
        self.prs = prs
        self.width = int(SLIDE_W_IN * PREVIEW_SCALE)
        self.height = int(SLIDE_H_IN * PREVIEW_SCALE)
        self.warnings: list[str] = []

    def font_for(self, name: str | None, size_pt: float, bold: bool) -> ImageFont.FreeTypeFont:
        name = (name or FONT).lower()
        pixel = max(8, int(round(size_pt * PREVIEW_SCALE / 72)))
        if "mono" in name or "consol" in name:
            path = MONO_BOLD if bold else MONO_REG
        else:
            path = SANS_BOLD if bold else SANS_REG
        try:
            return ImageFont.truetype(path, pixel)
        except Exception:
            return ImageFont.load_default()

    @staticmethod
    def shape_fill(shape):
        try:
            if shape.fill.type == MSO_FILL.SOLID:
                return rgb_tuple(shape.fill.fore_color.rgb)
        except Exception:
            pass
        return None

    @staticmethod
    def shape_line(shape):
        try:
            color = rgb_tuple(shape.line.color.rgb)
            width = max(1, int(round(shape.line.width.pt * PREVIEW_SCALE / 72)))
            return color, width
        except Exception:
            return None, 1

    def wrap(self, text: str, draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        if max_width <= 10:
            return [text]
        words = text.split(" ")
        lines: list[str] = []
        current = ""
        for word in words:
            trial = (current + " " + word).strip()
            if not current or draw.textlength(trial, font=font) <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        if current or not lines:
            lines.append(current)
        return lines

    def layout_text(self, shape, draw: ImageDraw.ImageDraw):
        tf = shape.text_frame
        x = px(shape.left) + px(tf.margin_left)
        y = px(shape.top) + px(tf.margin_top)
        w = px(shape.width) - px(tf.margin_left) - px(tf.margin_right)
        h = px(shape.height) - px(tf.margin_top) - px(tf.margin_bottom)
        blocks = []
        total_height = 0.0
        max_line_width = 0.0
        for para in tf.paragraphs:
            text = "".join(run.text for run in para.runs)
            run = para.runs[0] if para.runs else None
            size_pt = float(run.font.size.pt) if run and run.font.size else 12.0
            bold = bool(run.font.bold) if run else False
            font_name = run.font.name if run else FONT
            font = self.font_for(font_name, size_pt, bold)
            color = hex_tuple(INK)
            if run:
                try:
                    color = rgb_tuple(run.font.color.rgb)
                except Exception:
                    pass
            font = self.font_for(font_name, size_pt, bold)
            ascent, descent = font.getmetrics()
            line_px = ascent + descent
            spacing = para.line_spacing
            if isinstance(spacing, (int, float)):
                line_height = line_px * float(spacing or 1.0)
            else:
                try:
                    line_height = px(spacing)
                except Exception:
                    line_height = line_px
            space_before = px(para.space_before) if para.space_before else 0
            space_after = px(para.space_after) if para.space_after else 0
            lines = self.wrap(text, draw, font, w)
            for line in lines:
                max_line_width = max(max_line_width, draw.textlength(line, font=font))
            blocks.append({
                "lines": lines,
                "font": font,
                "color": color,
                "line_height": line_height,
                "space_before": space_before,
                "space_after": space_after,
                "align": para.alignment,
            })
            total_height += space_before + len(lines) * line_height + space_after
        anchor = tf.vertical_anchor
        if anchor == MSO_ANCHOR.MIDDLE:
            start_y = y + max(0, (h - total_height) / 2)
        elif anchor == MSO_ANCHOR.BOTTOM:
            start_y = y + max(0, h - total_height)
        else:
            start_y = y
        return x, y, w, h, start_y, total_height, max_line_width, blocks

    def draw_text(self, canvas: Image.Image, shape):
        draw = ImageDraw.Draw(canvas)
        x, y, w, h, start_y, total_height, max_line_width, blocks = self.layout_text(shape, draw)
        slide_no = getattr(self, "current_index", 0)
        if total_height > h + 4 or max_line_width > w + 8:
            self.warnings.append(
                f"slide {slide_no}: possible text overflow ({total_height:.0f}>{h} px high, {max_line_width:.0f}>{w} px wide): "
                + shape.text_frame.text.replace("\n", " / ")[:90]
            )
        cursor = start_y
        for block in blocks:
            cursor += block["space_before"]
            font = block["font"]
            for line in block["lines"]:
                line_width = draw.textlength(line, font=font)
                align = block["align"]
                if align == PP_ALIGN.CENTER:
                    lx = x + max(0, (w - line_width) / 2)
                elif align == PP_ALIGN.RIGHT:
                    lx = x + max(0, w - line_width)
                else:
                    lx = x
                draw.text((lx, cursor), line, font=font, fill=block["color"])
                cursor += block["line_height"]
            cursor += block["space_after"]

    def render_slide(self, slide, index: int, output: Path):
        self.current_index = index
        background = hex_tuple(CANVAS)
        try:
            background = rgb_tuple(slide.background.fill.fore_color.rgb)
        except Exception:
            pass
        canvas = Image.new("RGB", (self.width, self.height), background)
        for shape in slide.shapes:
            sx, sy, sw, sh = px(shape.left), px(shape.top), px(shape.width), px(shape.height)
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                with Image.open(io.BytesIO(shape.image.blob)) as picture:
                    picture = picture.convert("RGB").resize((max(1, sw), max(1, sh)), Image.Resampling.LANCZOS)
                    canvas.paste(picture, (sx, sy))
                continue
            if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                fill = self.shape_fill(shape)
                outline, outline_width = self.shape_line(shape)
                draw = ImageDraw.Draw(canvas)
                if fill:
                    try:
                        if shape.auto_shape_type == MSO_SHAPE.OVAL:
                            draw.ellipse((sx, sy, sx + sw, sy + sh), fill=fill, outline=outline, width=outline_width)
                        elif shape.auto_shape_type == MSO_SHAPE.ROUNDED_RECTANGLE:
                            draw.rounded_rectangle((sx, sy, sx + sw, sy + sh), radius=max(4, min(18, sh // 5)), fill=fill, outline=outline, width=outline_width)
                        else:
                            draw.rectangle((sx, sy, sx + sw, sy + sh), fill=fill, outline=outline, width=outline_width)
                    except Exception:
                        draw.rectangle((sx, sy, sx + sw, sy + sh), fill=fill, outline=outline, width=outline_width)
            if getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip():
                self.draw_text(canvas, shape)
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output)

    def render_all(self):
        paths = []
        for index, slide in enumerate(self.prs.slides, start=1):
            path = CACHE / f"slide-{index:02d}.png"
            self.render_slide(slide, index, path)
            paths.append(path)
        cols = 4
        thumb_w, thumb_h = 400, 225
        rows = math.ceil(len(paths) / cols)
        sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), hex_tuple(WHITE))
        for i, path in enumerate(paths):
            with Image.open(path) as image:
                thumb = image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(thumb, ((i % cols) * thumb_w, (i // cols) * thumb_h))
        contact = CACHE / "contact-sheet.png"
        sheet.save(contact)
        return contact, paths


# ---------- content ----------

def build_deck() -> Deck:
    d = Deck()

    # 01 — Cover
    d.add_cover()

    # 02 — Executive snapshot
    s = d.standard_slide(
        1,
        "Review at a glance",
        "What the MVP proves, what the checks show, and where the review boundary sits",
        "Use this slide to frame the review: the local domain model works, static and unit checks are green, but browser persistence and narrow-screen quality remain open. Avoid calling it production-ready.",
    )
    d.callout(s, 0.68, 1.86, 11.95, 0.72, "REVIEW POSITION", "A functional browser-local MVP with coherent, testable state rules — suitable for academic review and demonstration, not for production deployment.", fill=PALE_GREEN, accent=GREEN)
    stats = [
        ("4 × 72", "seeded bays", "Riverside + 3 Chennai mall sites; 3 floors × 24 bays each", GREEN),
        ("3 × 3", "status × kind", "available / occupied / reserved; standard / EV / accessible", BLUE),
        ("13 / 13", "unit + static", "9 Vitest cases; lint, typecheck and production build pass", GREEN),
        ("2", "open findings", "Reload persistence + 390 px mobile overflow", AMBER),
    ]
    for i, (value, label, detail, color) in enumerate(stats):
        d.stat_card(s, 0.68 + i * 3.04, 2.78, 2.83, 1.72, value, label, detail, accent=color)
    d.bullet_card(s, 0.68, 4.76, 3.84, 2.10, "What is strong", [
        "Totals, floor map and active sessions derive from one bay collection",
        "Pure helpers own validation and immutable transitions",
        "Occupied/reserved bays survive capacity reduction",
    ], accent=GREEN)
    d.bullet_card(s, 4.73, 4.76, 3.84, 2.10, "What is bounded", [
        "One browser and origin; no shared database or login",
        "Reserved samples are displayed, not managed end-to-end",
        "Static LIVE/trend/EV labels are not telemetry",
    ], accent=BLUE)
    d.bullet_card(s, 8.78, 4.76, 3.85, 2.10, "What needs hardening", [
        "Added-location reload selection failed in one E2E scenario",
        "390 px viewport measured 457 px document width",
        "Dialog focus, schema validation and concurrency are open",
    ], accent=AMBER)

    # 03 — Agenda
    s = d.standard_slide(
        1,
        "Review map",
        "Six sections move from project context to evidence, decisions and reproducible artifacts",
        "If time is short, spend most time on slides 10–17 and 23–29. Slides 18–22 are the visual demo; slide 30 is an evidence appendix.",
    )
    agenda = [
        ("01", "Context & goals", "Slides 04–07", "Identity, problem, objectives, literature, scope"),
        ("02", "Requirements", "Slides 08–09", "Actor journey, use cases, FR/NFR map"),
        ("03", "Design & build", "Slides 10–17", "Architecture, model, workflows, code, stack, UI"),
        ("04", "Product demo", "Slides 18–22", "Real captures: overview, map, sessions, planning, mobile"),
        ("05", "Verification", "Slides 23–27", "Checks, traceability, defects, achievements, privacy"),
        ("06", "Outlook", "Slides 28–30", "Roadmap, review decisions, evidence gallery"),
    ]
    for i, (num, title, pages, body) in enumerate(agenda):
        col, row = i % 3, i // 3
        x, y = 0.68 + col * 4.05, 1.95 + row * 2.45
        d.card(s, x, y, 3.82, 2.18)
        d.oval(s, x + 0.22, y + 0.22, 0.50, 0.50, fill=PALE_GREEN)
        d.text(s, x + 0.22, y + 0.22, 0.50, 0.50, num, size=13, color=GREEN, bold=True, align="center", valign="middle")
        d.text(s, x + 0.88, y + 0.22, 2.65, 0.34, title, size=15, bold=True)
        d.pill(s, x + 0.88, y + 0.64, 1.22, 0.26, pages, fill=PALE_BLUE, color=BLUE, size=8.2)
        d.text(s, x + 0.24, y + 1.10, 3.34, 0.82, body, size=10.5, color=MUTED, line_spacing=1.15)

    # 04 — Project identity
    s = d.standard_slide(
        1,
        "Project identity & product snapshot",
        "Parkline turns a multi-level garage into a location-scoped, floor-aware operator dashboard",
        "Emphasize that named sites and registrations are fixtures. The dashboard is a cohesive model of inventory and sessions, not a live feed from those places.",
    )
    d.card(s, 0.68, 1.90, 5.55, 4.92)
    d.text(s, 0.95, 2.15, 4.95, 0.34, "PARKLINE / MULTI-LEVEL PARKING", size=10, color=GREEN, bold=True)
    d.text(s, 0.95, 2.50, 4.95, 0.92, "One selected garage.\nThree scopes that must agree.", size=20, bold=True, line_spacing=1.02)
    d.text(s, 0.95, 3.52, 4.95, 0.78, "Location scope selects the inventory. Level scope selects the map and departure list. Bay scope decides whether an arrival or departure is valid.", size=11.2, color=MUTED, line_spacing=1.12)
    d.hline(s, 0.95, 4.42, 4.95)
    identity_rows = [
        ["Package / version", "multi-level-parking · 0.1.0"],
        ["Primary route", "Next.js App Router / → ParkingDashboard"],
        ["Seed sites", "Riverside, Marina Velachery, VR Anna Nagar, Phoenix OMR"],
        ["Seed floors", "B1 Basement · L1 Ground floor · L2 Upper deck"],
        ["Persistence", "localStorage key parkline-garage-planning"],
    ]
    for i, (label, value) in enumerate(identity_rows):
        yy = 4.62 + i * 0.40
        d.text(s, 0.95, yy, 1.55, 0.28, label, size=9.2, color=GREEN, bold=True)
        d.text(s, 2.55, yy, 3.35, 0.30, value, size=9.2, color=MUTED)
    d.text(s, 0.95, 6.48, 4.95, 0.22, "Reviewed application source matches the recorded SHA-256 evidence set.", size=8.2, color=SOFT)
    d.screenshot(s, SHOTS / "01-overview.png", 6.45, 1.90, 6.18, 4.92, "Actual dashboard capture · Riverside Centre, B1", mode="fit", centering=(0.5, 0.45))

    # 05 — Problem & objectives
    s = d.standard_slide(
        1,
        "Problem statement & measurable objectives",
        "The engineering question is local consistency, not claimed deployment impact",
        "A successful check-in is not just a confirmation message. Ask reviewers to watch the invariant: capacity and reserved stay fixed, occupied rises by one, available falls by one.",
    )
    d.text(s, 0.68, 1.86, 5.7, 0.30, "SEVEN COORDINATION PROBLEMS", size=10, color=GREEN, bold=True)
    problems = [
        "Fragmented floor visibility", "Reserved ≠ available ≠ occupied", "Unnormalized registration input",
        "Double allocation of a bay", "Duplicate active vehicle", "Unsafe capacity reduction", "Cross-location state leakage",
    ]
    for i, item in enumerate(problems):
        col, row = i % 2, i // 2
        x, y = 0.68 + col * 2.88, 2.25 + row * 0.55
        d.card(s, x, y, 2.68, 0.44, fill=WHITE, shadow=False)
        d.text(s, x + 0.16, y, 2.36, 0.44, item, size=9.6, color=INK, valign="middle")
    d.callout(s, 0.68, 4.55, 5.70, 1.08, "CORE QUESTION", "Can a browser app keep totals, map and active sessions consistent after each supported local action?", fill=PALE_BLUE, accent=BLUE)
    d.text(s, 0.68, 5.80, 5.70, 0.90, "Desired outcome: an operator-centred MVP with testable invariants and transparent boundaries — not traffic, revenue or customer-satisfaction claims.", size=10.5, color=MUTED, line_spacing=1.16)
    d.text(s, 6.62, 1.86, 5.9, 0.30, "TEN OBJECTIVES → FOUR OUTCOME GROUPS", size=10, color=GREEN, bold=True)
    objective_groups = [
        ("O1–O2", "Visibility", "Location/floor occupancy; visual map, search and filters"),
        ("O3–O5", "Session integrity", "TN plate normalization; guarded arrivals; departure release"),
        ("O6–O8", "Safe planning", "Protected resize; configurable locations; isolated operations"),
        ("O9–O10", "Evidence", "Browser-local retention; tests and documented limitations"),
    ]
    for i, (ids, title, body) in enumerate(objective_groups):
        y = 2.25 + i * 0.82
        d.card(s, 6.62, y, 6.01, 0.70)
        d.pill(s, 6.78, y + 0.17, 0.85, 0.34, ids, fill=PALE_GREEN, color=GREEN, size=8.5)
        d.text(s, 7.78, y + 0.10, 1.55, 0.28, title, size=11, bold=True)
        d.text(s, 7.78, y + 0.36, 4.55, 0.26, body, size=9.2, color=MUTED)
    d.callout(s, 6.62, 5.65, 6.01, 1.17, "ACCEPTANCE INVARIANTS", "Check-in: T and R unchanged, O +1, A −1. Capacity: inventory count changes while every occupied/reserved bay ID survives.", fill=PALE_GREEN, accent=GREEN)

    # 06 — Literature & feasibility
    s = d.standard_slide(
        1,
        "Design influences, gaps & feasibility",
        "A technical review of approaches — not a survey of commercial parking installations",
        "The literature review supports a typed local model and layered tests, while making clear that shared correctness, durable history and trust require a server authority.",
    )
    d.table(
        s, 0.68, 1.92, 7.55,
        ["Criterion", "Manual / spreadsheet", "Parkline MVP", "Proposed shared system"],
        [
            ["Visibility", "Operator-maintained", "Derived floor totals + bay map", "Shared authoritative inventory"],
            ["Rules", "Human discipline / formulas", "Pure TypeScript guards", "Server guards + constraints"],
            ["Persistence", "Files / documents", "One browser-local JSON value", "Durable DB + backups"],
            ["Concurrency", "Manual reconciliation", "No safe coordination", "Transactions + conflict handling"],
            ["Identity", "External process", "Static profile only", "Auth + role-based access"],
            ["Verification", "Manual review", "Unit + browser checks", "Integration, recovery, security"],
        ],
        [0.18, 0.25, 0.27, 0.30],
        row_h=0.52, header_h=0.42, font_size=8.8,
    )
    d.text(s, 8.48, 1.92, 4.15, 0.30, "FOUR RESEARCH GAPS", size=10, color=GREEN, bold=True)
    gaps = [
        "Shared correctness across operators",
        "Durable visit history after checkout",
        "Trusted identity and authorized edits",
        "Broader recovery, accessibility and reload evidence",
    ]
    for i, gap in enumerate(gaps):
        y = 2.30 + i * 0.52
        d.card(s, 8.48, y, 4.15, 0.42, shadow=False)
        d.text(s, 8.64, y, 3.82, 0.42, f"{i + 1:02d}  {gap}", size=9.5, color=INK, valign="middle")
    d.text(s, 8.48, 4.54, 4.15, 0.30, "FEASIBILITY", size=10, color=GREEN, bold=True)
    feasibility = [
        ("Technical", "Passed install, lint, typecheck, build; Node 20.9+ required", GREEN),
        ("Economic", "Open-source demo stack; no ROI claimed without deployment data", BLUE),
        ("Operational", "Supervised demo and requirements discovery; not sole real record", AMBER),
    ]
    for i, (label, body, color) in enumerate(feasibility):
        y = 4.90 + i * 0.66
        d.rect(s, 8.48, y, 0.055, 0.54, fill=color)
        d.text(s, 8.68, y, 1.15, 0.26, label, size=9.8, color=color, bold=True)
        d.text(s, 9.82, y, 2.80, 0.54, body, size=8.8, color=MUTED, line_spacing=1.05)

    # 07 — Scope
    s = d.standard_slide(
        1,
        "Scope & explicit boundaries",
        "“Implemented” means an identifiable code path — not a production guarantee",
        "This is one of the most important review slides. The polished UI must not be read as evidence of authentication, payments, sensors or a shared database.",
    )
    d.text(s, 0.68, 1.88, 5.82, 0.30, "INCLUDED IN THE MVP", size=10.5, color=GREEN, bold=True)
    included = [
        "Switch four seeded sites; add a named location",
        "Inspect 1–10 floors and 1–99 bays per floor",
        "Search current floor by bay ID or plate; filter by status",
        "Check in/out with TN registration validation",
        "Resize capacity while protecting non-available bays",
        "Display reserved, EV and accessible sample records",
        "Save plan and session changes in this browser",
    ]
    d.bullet_card(s, 0.68, 2.25, 5.82, 3.18, "Implemented capability", included, accent=GREEN, body_size=10.2, step=0.39)
    d.text(s, 6.78, 1.88, 5.85, 0.30, "OUTSIDE IMPLEMENTED SCOPE", size=10.5, color=RED, bold=True)
    excluded = [
        "Login, roles, audit attribution or data retention policy",
        "API, shared database, backup or multi-tab coordination",
        "Reservation creation, expiry, cancellation or fulfilment",
        "Payments, tariffs, billing, receipts or visit history",
        "Gate control, ANPR, sensors, telemetry or charging status",
        "Historical analytics, forecasting or measured utilization",
        "Edit/delete location, geometric floor plans or eligibility rules",
    ]
    d.bullet_card(s, 6.78, 2.25, 5.85, 3.18, "Explicit exclusion", excluded, accent=RED, fill=PALE_RED, body_size=10.2, step=0.39)
    d.callout(s, 0.68, 5.68, 11.95, 1.14, "INTERPRETATION RULE", "Decorative values — manager name, displayed date, yesterday comparison, next arrival, EV charging summary and LIVE badges — are presentation content. Derived counts come from bay records; static labels are not measured results.", fill=PALE_AMBER, accent=AMBER)

    # 08 — Actor & use cases
    s = d.standard_slide(
        2,
        "Operator journey & use cases",
        "One browser operator; the “Garage manager” profile is presentation, not an enforced role",
        "Walk through the journey left to right. Note that search/filter affect only the current floor, while the arrival bay selector lists available bays across the selected location.",
    )
    steps = [
        ("Select site", "Location scope"),
        ("Choose floor", "Level scope"),
        ("Inspect / find", "Current-floor map"),
        ("Start / end", "Bay + session"),
        ("Plan capacity", "Inventory change"),
        ("Review output", "Counts + activity"),
    ]
    for i, (title, body) in enumerate(steps):
        x = 0.68 + i * 2.03
        d.card(s, x, 1.95, 1.82, 1.15, fill=WHITE)
        d.oval(s, x + 0.14, 2.11, 0.34, 0.34, fill=PALE_GREEN)
        d.text(s, x + 0.14, 2.11, 0.34, 0.34, str(i + 1), size=9, color=GREEN, bold=True, align="center", valign="middle")
        d.text(s, x + 0.54, 2.06, 1.16, 0.40, title, size=9.5, bold=True)
        d.text(s, x + 0.14, 2.55, 1.54, 0.36, body, size=8.8, color=MUTED, align="center")
        if i < len(steps) - 1:
            d.arrow(s, x + 1.82, 2.20, 0.21, 0.52, "→", size=15)
    d.text(s, 0.68, 3.38, 11.95, 0.30, "SIX IMPLEMENTED USE CASES", size=10.5, color=GREEN, bold=True)
    use_cases = [
        ("UC-01", "Observe occupancy", "Location cards, floor tabs, occupancy strips and legends"),
        ("UC-02", "Search / filter", "Case-insensitive current-floor ID or plate; status predicate"),
        ("UC-03", "Check in", "Normalize TN plate, guard bay + duplicate, commit session"),
        ("UC-04", "Check out", "Select active session on current level, release its bay"),
        ("UC-05", "Plan capacity", "Change 1–99 per floor, preserve occupied/reserved IDs"),
        ("UC-06", "Manage selection", "Create new location or switch independent inventories"),
    ]
    for i, (uc, title, body) in enumerate(use_cases):
        col, row = i % 3, i // 3
        x, y = 0.68 + col * 4.05, 3.78 + row * 1.40
        d.card(s, x, y, 3.82, 1.22)
        d.pill(s, x + 0.16, y + 0.16, 0.72, 0.28, uc, fill=PALE_GREEN, color=GREEN, size=8.2)
        d.text(s, x + 1.00, y + 0.14, 2.55, 0.30, title, size=11.5, bold=True)
        d.text(s, x + 0.18, y + 0.56, 3.46, 0.52, body, size=9.3, color=MUTED, line_spacing=1.08)
    d.callout(s, 0.68, 6.58, 11.95, 0.38, "BOUNDARY", "No use case creates a reservation, authenticates an administrator or reads a sensor.", fill=PALE_BLUE, accent=BLUE)

    # 09 — Requirements
    s = d.standard_slide(
        2,
        "Requirements map & quality expectations",
        "18 functional requirements and 10 non-functional expectations, grouped for review",
        "Use the IDs to connect requirements to source files and tests. Stress that a passing implementation feature and a fully accepted quality outcome are different claims.",
    )
    d.table(
        s, 0.68, 1.92, 7.25,
        ["Group", "IDs", "Acceptance focus", "Principal source"],
        [
            ["Operations", "FR-01–05", "Location/floor scope; reconciled counts; search/filter", "Dashboard + occupancyForLevel"],
            ["Sessions", "FR-06–10", "TN normalization; guards; departure; activity/feedback", "checkIn / checkOut"],
            ["Capacity", "FR-11–13", "Expand/shrink safely; preserve protected bay IDs", "resizeLevelBays"],
            ["Locations", "FR-14–15", "1–10 floors, 1–99 bays; blank/duplicate name rejected", "createManagedLocation"],
            ["Persistence", "FR-16–18", "Local save/restore; reset view state on site switch", "storage effects / changeLocation"],
        ],
        [0.18, 0.14, 0.42, 0.26],
        row_h=0.66, header_h=0.40, font_size=9.0,
    )
    d.text(s, 8.18, 1.92, 4.45, 0.30, "NON-FUNCTIONAL EXPECTATIONS", size=10.2, color=GREEN, bold=True)
    nfr_groups = [
        ("Maintainability", "NFR-01/02", "Pure helpers + shared types; dashboard remains large", GREEN),
        ("Usability", "NFR-03/04", "Breakpoints and labels exist; overflow and focus gaps remain", AMBER),
        ("Reliability", "NFR-05/08/09", "Save/restore effects, reproducible scripts, bounded inputs", BLUE),
        ("Honesty & privacy", "NFR-06/07", "Document provenance; fictional demo data recommended", AMBER),
        ("Shared safety", "NFR-10", "Concurrent physical allocation not satisfied locally", RED),
    ]
    for i, (label, ids, body, color) in enumerate(nfr_groups):
        y = 2.30 + i * 0.83
        d.card(s, 8.18, y, 4.45, 0.70)
        d.rect(s, 8.18, y, 0.055, 0.70, fill=color)
        d.text(s, 8.35, y + 0.08, 1.75, 0.25, label, size=9.8, bold=True)
        d.pill(s, 10.10, y + 0.10, 1.05, 0.24, ids, fill=PALE, color=color, size=7.0)
        d.text(s, 8.35, y + 0.36, 4.05, 0.27, body, size=8.4, color=MUTED)
    d.callout(s, 0.68, 5.92, 7.25, 0.90, "TRACEABILITY", "FR-02/06–09 → unit tests; FR-11–14 → resize/creation tests; FR-01/18 → location-switch browser test; FR-14/16/17 → failed reload scenario.", fill=PALE_GREEN, accent=GREEN)
    d.callout(s, 8.18, 6.50, 4.45, 0.32, "EVIDENCE RULE", "No response-time, WCAG or security certification is claimed.", fill=PALE_AMBER, accent=AMBER)

    # 10 — Architecture
    s = d.standard_slide(
        3,
        "Implemented architecture",
        "A browser-centred Next.js shell with pure domain rules and one local persistence boundary",
        "Point out the dashed local-storage connection: it is a browser effect, not a network service. There are no parking API route handlers, server actions or database repositories.",
    )
    d.card(s, 0.68, 1.92, 8.35, 4.98)
    d.text(s, 0.95, 2.12, 7.8, 0.26, "EXECUTION AREAS · ACTUAL SOURCE BOUNDARY", size=9.5, color=GREEN, bold=True)
    d.node(s, 1.05, 2.58, 7.60, 0.72, "Operator in a web browser", "Clicks, form entry, status feedback and derived dashboard output", fill=PALE_GREEN_2, accent=GREEN)
    d.arrow(s, 4.55, 3.30, 0.60, 0.34, "↓", size=17)
    d.node(s, 1.05, 3.64, 7.60, 0.72, "Next.js App Router shell", "src/app/page.tsx · layout.tsx · globals.css · prerendered / route", fill=WHITE, accent=BLUE)
    d.arrow(s, 4.55, 4.36, 0.60, 0.34, "↓", size=17)
    d.node(s, 1.05, 4.70, 7.60, 0.82, "ParkingDashboard — React client component", "Selected location/level · operationsByLocation · dialogs · derived cards and bay map", fill=WHITE, accent=GREEN)
    d.arrow(s, 2.55, 5.53, 0.45, 0.30, "↙", size=16)
    d.arrow(s, 6.70, 5.53, 0.45, 0.30, "↘", size=16)
    d.node(s, 1.05, 5.80, 3.55, 0.90, "Pure domain helpers", "occupancy · TN validation · check-in/out · safe resize", fill=PALE_BLUE, accent=BLUE, title_size=10.5, body_size=8.0)
    d.node(s, 5.10, 5.80, 3.55, 0.90, "Typed fixtures & creation", "seed locations · createManagedLocation · shared interfaces", fill=PALE_BLUE, accent=BLUE, title_size=10.5, body_size=8.0)
    d.text(s, 4.30, 6.72, 1.15, 0.16, "save / restore", size=7.5, color=SOFT, align="center")
    d.card(s, 9.28, 1.92, 3.35, 2.05, fill=WHITE)
    d.text(s, 9.50, 2.12, 2.90, 0.28, "DESIGN PRINCIPLES", size=10, color=GREEN, bold=True)
    for i, item in enumerate(["Separation of concerns", "Explicit state ownership", "Conservation of inventory", "Immutable transformations", "Transparent boundaries"]):
        d.oval(s, 9.52, 2.55 + i * 0.26, 0.065, 0.065, fill=GREEN)
        d.text(s, 9.68, 2.48 + i * 0.26, 2.65, 0.22, item, size=9.0, color=MUTED)
    d.image(s, DIAGRAMS / "04-01-architecture.png", 9.40, 4.20, 3.10, 2.18, mode="contain", alt="Source-grounded architecture diagram from the 111-page project report")
    d.text(s, 9.40, 6.45, 3.10, 0.38, "Full architecture diagram retained in the project report.", size=8.2, color=SOFT, align="center")
    d.callout(s, 0.68, 6.98, 8.35, 0.00, "", "", fill=PALE_GREEN, accent=GREEN) if False else None

    # 11 — Domain model
    s = d.standard_slide(
        3,
        "Domain model & data dictionary",
        "Five TypeScript interfaces and two union vocabularies; array lookup replaces database keys",
        "Bay kind is independent of status: an EV bay can be available or occupied. Reserved is unavailable inventory, not a parked vehicle. IDs are location-scoped, not global.",
    )
    model = [
        ("ParkingLocation", "id · name\nlevels · bays\nsessions · activity", GREEN),
        ("ParkingLevel", "id · label · name\ncapacity: 1–99", BLUE),
        ("ParkingBay", "id · levelId\nstatus · kind\nplate? · since?", GREEN),
        ("ParkingSession", "id · bayId · levelId\nplate · vehicle\nstartedAt", BLUE),
        ("ParkingActivity", "id · type · plate\nbayId · time", GREEN),
    ]
    for i, (name, fields, color) in enumerate(model):
        x = 0.68 + i * 2.43
        d.card(s, x, 1.95, 2.22, 1.72)
        d.rect(s, x, 1.95, 2.22, 0.055, fill=color)
        d.text(s, x + 0.14, 2.14, 1.94, 0.30, name, size=10.5, bold=True, align="center")
        d.text(s, x + 0.16, 2.52, 1.90, 1.00, fields, size=9.0, color=MUTED, align="center", line_spacing=1.18)
        if i < 4:
            d.arrow(s, x + 2.22, 2.55, 0.21, 0.40, "→", size=13, color=SOFT)
    d.text(s, 0.68, 3.92, 5.85, 0.30, "VOCABULARIES", size=10.2, color=GREEN, bold=True)
    d.card(s, 0.68, 4.28, 2.82, 1.28)
    d.text(s, 0.88, 4.44, 2.42, 0.26, "BayStatus", size=11, bold=True)
    for i, (label, color) in enumerate([("available", GREEN), ("occupied", RED), ("reserved", AMBER)]):
        d.pill(s, 0.88 + i * 0.82, 4.86, 0.76, 0.28, label, fill=PALE, color=color, size=7.8)
    d.card(s, 3.68, 4.28, 2.82, 1.28)
    d.text(s, 3.88, 4.44, 2.42, 0.26, "BayKind", size=11, bold=True)
    for i, (label, color) in enumerate([("standard", MUTED), ("ev", BLUE), ("accessible", GREEN)]):
        d.pill(s, 3.88 + i * 0.82, 4.86, 0.76, 0.28, label, fill=PALE, color=color, size=7.8)
    d.callout(s, 0.68, 5.70, 5.82, 1.22, "CONCEPTUAL ER, NOT SQL", "No relational database exists. A location has many levels/bays; a bay is intended to have zero or one active session. Composite keys would be required in a shared schema.", fill=PALE_BLUE, accent=BLUE)
    d.image(s, DIAGRAMS / "04-06-domain-model.png", 6.78, 4.00, 5.85, 2.82, mode="contain", alt="Domain model diagram of the five TypeScript record interfaces")
    d.text(s, 6.78, 6.86, 5.85, 0.18, "Source-grounded domain diagram · interfaces, not class instances", size=8.0, color=SOFT, align="center")

    # 12 — State machine
    s = d.standard_slide(
        3,
        "Bay state machine & conservation rules",
        "Only two operational transitions are implemented; reserved is a protected display state",
        "Do not draw reserve/cancel arrows — no reservation lifecycle exists. The invariant is local to one selected location and one input snapshot, not a global database constraint.",
    )
    d.card(s, 0.68, 1.92, 7.55, 3.35)
    d.node(s, 1.05, 2.55, 2.05, 1.10, "AVAILABLE", "Can be selected\nfor ordinary arrival", fill=PALE_GREEN, accent=GREEN, title_size=13, body_size=9.5)
    d.arrow(s, 3.12, 2.78, 0.75, 0.62, "→", size=24)
    d.text(s, 3.05, 3.44, 0.90, 0.22, "checkIn", size=8.2, color=GREEN, align="center")
    d.node(s, 3.88, 2.55, 2.05, 1.10, "OCCUPIED", "One active session\nand plate record", fill=PALE_RED, accent=RED, title_size=13, body_size=9.5)
    d.arrow(s, 5.95, 2.78, 0.75, 0.62, "→", size=24)
    d.text(s, 5.90, 3.44, 0.90, 0.22, "checkOut", size=8.2, color=GREEN, align="center")
    d.node(s, 6.72, 2.55, 1.18, 1.10, "BACK TO\nAVAILABLE", "Bay kind\nis retained", fill=PALE_GREEN, accent=GREEN, title_size=9.0, body_size=7.8)
    d.card(s, 1.05, 4.05, 6.85, 0.82, fill=PALE_AMBER, border=None, shadow=False)
    d.text(s, 1.28, 4.16, 6.38, 0.26, "RESERVED — DISPLAY / FIXTURE ONLY", size=10, color=AMBER, bold=True)
    d.text(s, 1.28, 4.45, 6.38, 0.34, "Unavailable for arrival, excluded from available count, protected during resize; no create/cancel/expire path.", size=8.8, color=MUTED)
    d.text(s, 8.48, 1.92, 4.15, 0.30, "DERIVED VALUES", size=10.2, color=GREEN, bold=True)
    formulas = [
        ("T", "Total bay records on the level"),
        ("O", "Bays with status occupied"),
        ("R", "Bays with status reserved"),
        ("A", "T − O − R"),
        ("%", "round(100 × O / T); 0 when T = 0"),
    ]
    for i, (symbol, body) in enumerate(formulas):
        y = 2.30 + i * 0.52
        d.card(s, 8.48, y, 4.15, 0.42, shadow=False)
        d.pill(s, 8.62, y + 0.07, 0.48, 0.28, symbol, fill=PALE_GREEN, color=GREEN, size=8.5)
        d.text(s, 9.22, y, 3.22, 0.42, body, size=9.2, color=MUTED, valign="middle")
    d.callout(s, 8.48, 5.05, 4.15, 1.77, "LOCAL INVARIANTS", "Each active session points to one occupied bay in its location. A normalized plate occurs at most once in that location’s active sessions. Helpers do not repair corrupted saved data or coordinate simultaneous clients.", fill=PALE_BLUE, accent=BLUE)
    d.image(s, DIAGRAMS / "04-08-bay-state-machine.png", 0.68, 5.48, 7.55, 1.34, mode="contain", bg=WHITE, alt="Implemented bay state machine from the project report")

    # 13 — Core workflows & validation
    s = d.standard_slide(
        3,
        "Core workflows & validation gates",
        "Presentation controls and reusable domain helpers enforce different layers of the same rules",
        "Native HTML controls communicate bounds; pure helpers enforce business rules even when called outside the form. A thrown error prevents the successful-state commit.",
    )
    workflows = [
        ("ARRIVAL", "normalizeTamilNaduPlate → bay exists + available → no duplicate normalized plate → create session → bay occupied → prepend activity", GREEN),
        ("DEPARTURE", "find active session → map its bay to available → clear plate/since → remove session → prepend departure activity", BLUE),
        ("CAPACITY", "integer 1–99 → protected count = occupied + reserved → reject lower capacity → remove available IDs from highest suffix / add unused suffixes", AMBER),
        ("NEW LOCATION", "trim name → 1–10 floors → 1–99 bays/floor → generate all-standard available bays → empty sessions/activity → insert by location ID", GREEN),
    ]
    for i, (title, body, color) in enumerate(workflows):
        y = 1.92 + i * 1.05
        d.card(s, 0.68, y, 7.35, 0.90)
        d.rect(s, 0.68, y, 0.06, 0.90, fill=color)
        d.text(s, 0.90, y + 0.10, 1.35, 0.26, title, size=10, color=color, bold=True)
        d.text(s, 2.30, y + 0.10, 5.48, 0.68, body, size=9.2, color=MUTED, line_spacing=1.10)
    d.text(s, 8.28, 1.92, 4.35, 0.30, "VALIDATION RULE SET", size=10.2, color=GREEN, bold=True)
    rules = [
        "Plate: ^TN\\d{2}[A-Z]{2}\\d{4}$; spaces/hyphens removed, letters uppercased",
        "Arrival bay must exist and be available",
        "Normalized plate must not already be active in this location",
        "Departure session must exist in supplied active list",
        "Capacity: integer 1–99 and ≥ occupied + reserved",
        "Location name: trimmed, non-empty, case-insensitively unique in UI",
        "Floors: integer 1–10; maximum new inventory 990 bays",
    ]
    d.bullet_card(s, 8.28, 2.28, 4.35, 3.62, "Layered rejection", rules, accent=GREEN, body_size=9.2, step=0.48)
    d.callout(s, 0.68, 6.22, 7.35, 0.60, "KNOWN GAP", "startedAt is not validated; restored JSON has shallow checks; EV/accessible eligibility is not enforced.", fill=PALE_AMBER, accent=AMBER)

    # 14 — Domain code
    s = d.standard_slide(
        3,
        "Implementation: the reusable domain core",
        "Ordinary TypeScript functions receive collections and return new collections or throw",
        "This is the strongest engineering contribution: the same rules can be unit-tested without React and later reused as a behavioral specification for a server transaction.",
    )
    d.code_card(
        s, 0.68, 1.92, 3.86, 2.20, "src/lib/parking.ts",
        "export function normalizeTamilNaduPlate(value: string) {\n"
        "  const plate = value.replace(/[\\s-]/g, \"\").toUpperCase();\n"
        "  if (!/^TN\\d{2}[A-Z]{2}\\d{4}$/.test(plate)) {\n"
        "    throw new Error(\"Use TN + 2 digits + 2 letters + 4 digits\");\n"
        "  }\n"
        "  return plate;\n"
        "}",
        size=8.0,
    )
    d.code_card(
        s, 4.73, 1.92, 3.86, 2.20, "src/lib/parking.ts",
        "if (!bay || bay.status !== \"available\") {\n"
        "  throw new Error(\"Choose an available parking bay.\");\n"
        "}\n"
        "if (sessions.some(s => s.plate === normalizedPlate)) {\n"
        "  throw new Error(\"This vehicle already has an active session.\");\n"
        "}\n"
        "// immutable map + append only after all guards pass",
        size=8.0,
    )
    d.code_card(
        s, 8.78, 1.92, 3.85, 2.20, "src/lib/parking.ts",
        "const protectedCount = levelBays\n"
        "  .filter(bay => bay.status !== \"available\").length;\n"
        "if (capacity < protectedCount) {\n"
        "  throw new Error(\"Capacity cannot be below the number\n"
        "    of occupied or reserved bays.\");\n"
        "}\n"
        "// reduce: remove highest available suffixes only",
        size=8.0,
    )
    d.text(s, 0.68, 4.30, 11.95, 0.30, "WHAT THE HELPERS DO — AND DO NOT DO", size=10.2, color=GREEN, bold=True)
    d.bullet_card(s, 0.68, 4.66, 5.82, 2.16, "Implemented", [
        "occupancyForLevel counts actual bay records, not declared capacity",
        "checkIn / checkOut return paired bay and session updates",
        "resizeLevelBays protects all non-available records",
        "No mutation of input arrays; failed operations throw before commit",
    ], accent=GREEN, body_size=10.0, step=0.44)
    d.bullet_card(s, 6.78, 4.66, 5.85, 2.16, "Not implemented in helpers", [
        "HTTP, React setters, localStorage or database calls",
        "Runtime schema validation or malformed timestamp checks",
        "Transactions, locks or cross-client conflict resolution",
        "Special-kind minimums, pricing or completed-session history",
    ], accent=BLUE, fill=PALE_BLUE, body_size=10.0, step=0.44)

    # 15 — Source map & stack
    s = d.standard_slide(
        3,
        "Codebase map & technology stack",
        "A small source tree makes the path from screen → helper → test traceable",
        "The route contains no parking business logic. The dashboard is the only major client component; helpers and fixtures are deliberately separate and testable.",
    )
    d.table(
        s, 0.68, 1.92, 7.15,
        ["Path", "Responsibility"],
        [
            ["src/app/page.tsx", "Home route renders ParkingDashboard"],
            ["src/app/layout.tsx", "Metadata, global CSS, root document"],
            ["src/app/globals.css", "Design tokens, component styles, breakpoints"],
            ["src/components/parking-dashboard.tsx", "State, derived view, handlers, dialogs, output"],
            ["src/types/parking.ts", "Five interfaces + status/kind unions"],
            ["src/lib/parking.ts", "Occupancy, resize, plate, arrival, departure"],
            ["src/lib/parking-data.ts", "Seed inventory + managed-location creation"],
            ["src/lib/parking.test.ts", "Nine existing domain/fixture cases"],
            ["e2e/parking-workflows.spec.ts", "Three existing operator browser scenarios"],
        ],
        [0.40, 0.60], row_h=0.45, header_h=0.38, font_size=8.0,
    )
    d.text(s, 8.08, 1.92, 4.55, 0.30, "DEPENDENCY BASELINE", size=10.2, color=GREEN, bold=True)
    stack = [
        ("Next.js 16.4.3", "App Router, build and prerendered / route"),
        ("React 19.0.0", "Client state, derived values, effects"),
        ("TypeScript 5.7.2", "Interfaces, unions and --noEmit checks"),
        ("Tailwind 3.4 / CSS", "Utility directives + named component classes"),
        ("Lucide React", "SVG icons; not service integrations"),
        ("Vitest 5 / Playwright", "Domain tests and browser workflows"),
        ("ESLint 9 / npm", "Static checks and reproducible scripts"),
    ]
    for i, (name, body) in enumerate(stack):
        y = 2.28 + i * 0.62
        d.card(s, 8.08, y, 4.55, 0.52, shadow=False)
        d.text(s, 8.24, y + 0.04, 1.55, 0.24, name, size=9.2, color=GREEN, bold=True)
        d.text(s, 9.82, y + 0.04, 2.62, 0.42, body, size=8.4, color=MUTED, line_spacing=1.0)
    d.callout(s, 8.08, 6.70, 4.55, 0.12, "", "", fill=PALE_GREEN, accent=GREEN) if False else None

    # 16 — Persistence
    s = d.standard_slide(
        3,
        "Persistence lifecycle & browser boundary",
        "One origin-scoped JSON snapshot; no authoritative service arbitrates competing clients",
        "Explain the two effects: read after mount, then write once storageReady is enabled. The observed reload failure shows that effect presence is not proof of reliable restoration.",
    )
    d.card(s, 0.68, 1.92, 7.55, 3.30)
    d.text(s, 0.95, 2.10, 7.0, 0.26, "LOCAL STORAGE · parkline-garage-planning", size=9.5, color=GREEN, bold=True)
    d.node(s, 1.00, 2.58, 2.05, 0.90, "Initial state", "Seed locations +\noperationsByLocation", fill=WHITE, accent=GREEN, title_size=10.5, body_size=8.5)
    d.arrow(s, 3.05, 2.82, 0.55, 0.40, "→", size=18)
    d.node(s, 3.60, 2.58, 2.05, 0.90, "Read effect", "Parse JSON; shallow\nshape checks", fill=PALE_BLUE, accent=BLUE, title_size=10.5, body_size=8.5)
    d.arrow(s, 5.65, 2.82, 0.55, 0.40, "→", size=18)
    d.node(s, 6.20, 2.58, 1.75, 0.90, "storageReady", "Enable write\nafter load", fill=WHITE, accent=GREEN, title_size=10.5, body_size=8.5)
    d.arrow(s, 4.55, 3.50, 0.60, 0.34, "↓", size=17)
    d.node(s, 1.00, 3.84, 6.95, 0.92, "Write effect serializes locations, operationsByLocation and locationId", "Catch path logs a warning; no rollback, save-failure banner or conflict protocol", fill=PALE_GREEN_2, accent=GREEN, title_size=10.5, body_size=8.6)
    d.code_card(s, 0.68, 5.38, 7.55, 1.52, "Saved JSON shape (schematic)", "{\n  \"locations\": [ /* ParkingLocation records */ ],\n  \"operationsByLocation\": { \"riverside\": { \"bays\": [], \"sessions\": [], \"activity\": [] } },\n  \"locationId\": \"riverside\"\n}", size=8.0)
    d.text(s, 8.48, 1.92, 4.15, 0.30, "WHAT IS SAVED", size=10.2, color=GREEN, bold=True)
    d.bullet_card(s, 8.48, 2.28, 4.15, 2.02, "Included", [
        "Locations and nested collections",
        "Working operations by location ID",
        "Selected location ID",
    ], accent=GREEN, body_size=9.8, step=0.42)
    d.text(s, 8.48, 4.48, 4.15, 0.30, "WHAT IS NOT SAVED / NOT GUARANTEED", size=10.2, color=AMBER, bold=True)
    d.bullet_card(s, 8.48, 4.84, 4.15, 1.98, "Open concerns", [
        "Selected floor, search text or status filter",
        "Versioned schema or referential integrity",
        "Multi-tab coordination, backup or attributed audit",
        "Durable cross-device state or server authority",
    ], accent=AMBER, fill=PALE_AMBER, body_size=9.4, step=0.40)

    # 17 — UI design & accessibility
    s = d.standard_slide(
        3,
        "UI design system & accessibility foundations",
        "A neutral canvas, green primary actions and amber reservation accents; status is not colour-only",
        "The design has good foundations but no formal WCAG audit. Mention the missing focus trap, Escape close, focus return and complete arrow-key tab pattern.",
    )
    d.card(s, 0.68, 1.92, 5.82, 3.05)
    d.text(s, 0.95, 2.10, 5.25, 0.26, "IMPLEMENTED VISUAL TOKENS", size=9.8, color=GREEN, bold=True)
    tokens = [
        ("Main ink", INK), ("Canvas", CANVAS), ("Primary green", GREEN),
        ("Bright green", GREEN_2), ("Amber", AMBER), ("Paper", WHITE),
    ]
    for i, (label, color) in enumerate(tokens):
        col, row = i % 3, i // 3
        x, y = 0.95 + col * 1.75, 2.52 + row * 0.78
        d.rect(s, x, y, 0.48, 0.48, fill=color, line=BORDER, rounded=True)
        d.text(s, x + 0.58, y + 0.06, 1.10, 0.22, label, size=8.6, bold=True)
        d.text(s, x + 0.58, y + 0.28, 1.10, 0.18, f"#{color}", size=7.5, color=SOFT)
    d.text(s, 0.95, 4.22, 5.25, 0.50, "Layout: 238 px desktop sidebar · 6-column bay grid → 4 columns narrow · breakpoints at 1150 / 900 / 620 px · reduced-motion query.", size=9.2, color=MUTED, line_spacing=1.12)
    d.table(
        s, 6.78, 1.92, 5.85,
        ["Interaction", "Implemented support", "Remaining limitation"],
        [
            ["Bay inspection", "Accessible ID/status/plate name", "Contrast / SR experience not audited"],
            ["Forms", "Labels, required, native controls", "Error association could be stronger"],
            ["Dialogs", "Dialog role, modal flag, autofocus", "No focus trap, Escape, focus return"],
            ["Floor tabs", "Tablist + selected semantics", "No full arrow-key / roving tabindex"],
            ["Feedback", "Status notices + alert errors", "Save failure only console warning"],
            ["Narrow layout", "Panels stack; sidebar collapses", "390 px overflow; selector hidden"],
        ],
        [0.22, 0.39, 0.39], row_h=0.56, header_h=0.40, font_size=8.2,
    )
    d.callout(s, 0.68, 5.20, 5.82, 1.62, "DESIGN HONESTY", "The bay grid is a visual inventory, not an architectural floor plan. The one-way lane is a cue, not validated circulation. Notification, account and activity-options buttons are intentionally limited controls.", fill=PALE_BLUE, accent=BLUE)
    d.callout(s, 6.78, 5.72, 5.85, 1.10, "PRIORITY UI FIXES", "Wrap narrow heading actions, keep location selection reachable, complete modal keyboard behaviour and label sample values clearly.", fill=PALE_AMBER, accent=AMBER)

    # 18 — Demo 1
    s = d.standard_slide(
        4,
        "Demo 1 · Garage overview",
        "Derived metric cards, floor status, live-map panel, activity and planning actions",
        "Use the Riverside seed as the demo baseline: 72 total, 34 occupied, 32 available, 6 reserved. Point out the footer that says no live sensors are connected.",
    )
    d.screenshot(s, SHOTS / "01-overview.png", 0.68, 1.90, 8.55, 4.98, "Built application · Riverside Centre overview, B1 selected", mode="fit", centering=(0.5, 0.45))
    d.text(s, 9.48, 1.92, 3.15, 0.30, "READ THE SCREEN", size=10.2, color=GREEN, bold=True)
    read_cards = [
        ("72 / 34 / 32 / 6", "Total, occupied, available, reserved across 3 levels"),
        ("B1 · 10/24", "Floor tab and 42% occupancy strip use the same bay records"),
        ("Bay B1-01", "Available + accessible; click routes to the arrival dialog"),
        ("Recent activity", "Latest five events; human-readable relative times"),
    ]
    for i, (label, body) in enumerate(read_cards):
        y = 2.30 + i * 0.92
        d.card(s, 9.48, y, 3.15, 0.78)
        d.text(s, 9.64, y + 0.08, 2.82, 0.24, label, size=10.2, color=GREEN, bold=True)
        d.text(s, 9.64, y + 0.34, 2.82, 0.38, body, size=8.5, color=MUTED, line_spacing=1.05)
    d.callout(s, 9.48, 6.08, 3.15, 0.74, "REMEMBER", "Trend, next-arrival, date and EV summary include static labels.", fill=PALE_AMBER, accent=AMBER)

    # 19 — Demo 2
    s = d.standard_slide(
        4,
        "Demo 2 · Floor map, search & status filter",
        "Search and filtering change only the visible current-floor bays, never the underlying statistics",
        "The captured Upper deck / Reserved filter returns two bays. An unknown search shows an explicit empty-map message; a reserved bay click reports its state instead of opening arrival.",
    )
    d.screenshot(s, SHOTS / "02-floor-filter.png", 0.68, 1.92, 8.25, 4.35, "Upper deck filtered to Reserved · two bays shown", mode="contain")
    d.text(s, 9.18, 1.92, 3.45, 0.30, "INTERACTION RULES", size=10.2, color=GREEN, bold=True)
    d.bullet_card(s, 9.18, 2.28, 3.45, 2.58, "Current-floor scope", [
        "Search trims/lowercases and matches bay ID or plate substring",
        "Status filter: all / available / occupied / reserved",
        "Counts and occupancy strip remain derived from all floor bays",
        "EV and accessible icons are physical kinds, not statuses",
    ], accent=BLUE, body_size=9.2, step=0.53)
    d.callout(s, 0.68, 6.45, 8.25, 0.37, "EMPTY / RESERVED FEEDBACK", "No bays match this search · B1-05 is reserved.", fill=PALE_GREEN, accent=GREEN)
    d.callout(s, 9.18, 5.10, 3.45, 1.72, "WHY IT MATTERS", "The observable map is a filtered view. A successful session or capacity change must still reconcile the full selected-location inventory.", fill=PALE_BLUE, accent=BLUE)

    # 20 — Demo 3
    s = d.standard_slide(
        4,
        "Demo 3 · Arrival, departure & validation",
        "Real captures of the form, success notice and rejection paths",
        "Demonstrate the formatted plate 'tn 01 aa 3042' becoming TN01AA3042, then duplicate and non-TN rejection. Checkout releases B1-01 and restores the counts.",
    )
    d.screenshot(s, SHOTS / "03-arrival-form.png", 0.68, 1.92, 2.90, 3.72, "Arrival form · formatted TN input", mode="contain")
    d.screenshot(s, SHOTS / "04-arrival-success.png", 3.72, 1.92, 2.90, 3.72, "Success notice + occupied B1-01", mode="fit", centering=(0.5, 0.25))
    d.screenshot(s, SHOTS / "05-departure-form.png", 6.76, 1.92, 2.90, 3.72, "Departure session selector", mode="contain")
    d.screenshot(s, SHOTS / "10-format-validation.png", 9.80, 1.92, 2.83, 3.72, "Invalid registration error", mode="contain")
    d.callout(s, 0.68, 5.78, 3.84, 1.14, "SUCCESS POSTCONDITION", "One new active session; occupied +1, available −1; capacity and reserved unchanged.", fill=PALE_GREEN, accent=GREEN)
    d.callout(s, 4.73, 5.78, 3.84, 1.14, "FAILURE POSTCONDITION", "Domain exception shown; dialog can stay open; successful-state commit is skipped.", fill=PALE_AMBER, accent=AMBER)
    d.callout(s, 8.78, 5.78, 3.85, 1.14, "DEPARTURE", "Bay becomes available; plate/since cleared; session removed. No tariff, receipt or history.", fill=PALE_BLUE, accent=BLUE)

    # 21 — Demo 4
    s = d.standard_slide(
        4,
        "Demo 4 · Capacity planning & new locations",
        "Planning changes inventory size while preserving every occupied and reserved bay identity",
        "The basement input advertises minimum 12 (10 occupied + 2 reserved). New locations start with all-standard available bays and empty sessions/activity.",
    )
    d.screenshot(s, SHOTS / "06-capacity-form.png", 0.68, 1.92, 3.02, 4.35, "Capacity dialog · protected minimums", mode="contain")
    d.screenshot(s, SHOTS / "07-new-location-form.png", 3.86, 1.92, 3.02, 4.35, "New location · floors and bays per floor", mode="contain")
    d.screenshot(s, SHOTS / "09-new-location-result.png", 7.04, 1.92, 5.59, 4.35, "Independent empty inventory after creation", mode="fit", centering=(0.5, 0.38))
    d.callout(s, 0.68, 6.42, 5.87, 0.40, "BOUNDS", "Existing floor capacity 1–99 · new location 1–10 floors × 1–99 bays = max 990 bays.", fill=PALE_GREEN, accent=GREEN)
    d.callout(s, 6.78, 6.42, 5.85, 0.40, "DUPLICATE NAMES", "Blank names and case-insensitive duplicates are rejected in the dashboard UI.", fill=PALE_AMBER, accent=AMBER)

    # 22 — Mobile
    s = d.standard_slide(
        4,
        "Mobile presentation & observed layout defect",
        "A 390 px viewport produced a 457 px document width in the recorded browser run",
        "This is measured evidence, not a general claim about all viewports. The diagnostic identified a primary action button in the heading row as the overflowing element.",
    )
    d.card(s, 0.68, 1.92, 4.05, 4.98)
    d.image(s, SHOTS / "11-mobile-upper-view.png", 0.86, 2.08, 3.69, 4.02, mode="contain", alt="Mobile capture at 390 CSS pixels showing clipped New arrival button")
    d.text(s, 0.86, 6.22, 3.69, 0.46, "Upper 500 CSS px of the full mobile capture; full image is retained in the report assets.", size=8.2, color=SOFT, align="center")
    d.stat_card(s, 4.98, 1.92, 2.25, 1.55, "390 px", "viewport", "innerWidth recorded in Chromium", accent=BLUE)
    d.stat_card(s, 7.40, 1.92, 2.25, 1.55, "457 px", "document", "scrollWidth measured", accent=RED, fill=PALE_RED)
    d.callout(s, 9.88, 1.92, 2.75, 1.55, "DELTA", "+67 px horizontal overflow; New arrival button reaches the right edge.", fill=PALE_AMBER, accent=AMBER)
    d.text(s, 4.98, 3.72, 7.65, 0.30, "WHAT THE STYLESHEET DOES / DOES NOT DO", size=10.2, color=GREEN, bold=True)
    d.table(
        s, 4.98, 4.08, 7.65,
        ["Area", "Implemented", "Observed / remaining"],
        [
            ["Breakpoints", "1150 / 900 / 620 px; panels stack", "Media queries do not guarantee child wrapping"],
            ["Bay grid", "Six columns → four at narrow width", "Heading action row still overflows"],
            ["Garage selector", "Sidebar collapses", "Location selector hidden below breakpoint"],
            ["Dialog keyboard", "Modal roles and autofocus", "No focus trap / Escape / focus return"],
            ["Verification", "Supplemental geometry assertion", "B15 failed; no cross-browser audit"],
        ],
        [0.21, 0.39, 0.40], row_h=0.52, header_h=0.38, font_size=8.4,
    )
    d.callout(s, 4.98, 6.92, 7.65, 0.00, "", "", fill=PALE_GREEN, accent=GREEN) if False else None

    # 23 — Verification scoreboard
    s = d.standard_slide(
        5,
        "Verification scoreboard",
        "Executed checks are reported separately; a green unit suite does not override browser failures",
        "Review the evidence boundary: Chromium 153 in an isolated local production-build context. No field trial, stakeholder UAT, latency benchmark, security audit or WCAG certification was performed.",
    )
    checks = [
        ("Existing Vitest suite", 9, 9, GREEN, "9 passed / 0 failed · selected domain + fixture cases"),
        ("ESLint", 1, 1, GREEN, "Configured static checks passed"),
        ("TypeScript --noEmit", 1, 1, GREEN, "Compile-time source consistency passed"),
        ("Next.js production build", 1, 1, GREEN, "Compilation + route generation passed"),
        ("Existing Playwright scenarios", 2, 3, AMBER, "E2E-02 failed: added location not retained after reload"),
        ("Supplemental browser assertions", 15, 16, AMBER, "B15 failed: 390 px viewport → 457 px document"),
    ]
    for i, (label, value, maximum, color, note) in enumerate(checks):
        y = 1.92 + i * 0.79
        d.progress_bar(s, 0.68, y, 7.75, f"{value}/{maximum}  {label}", value, maximum, color=color, note=note)
    d.callout(s, 8.68, 1.92, 3.95, 1.42, "BASELINE", "Reviewed 31 October 2026 · commit aa4b730 in report evidence · application source hashes match current files · Node 22.22.3 / npm 10.9.8 documentation run.", fill=PALE_BLUE, accent=BLUE)
    d.callout(s, 8.68, 3.52, 3.95, 1.42, "UNCAUGHT ERRORS", "None observed in the supplemental browser sequence. This is not a universal runtime-error guarantee.", fill=PALE_GREEN, accent=GREEN)
    d.callout(s, 8.68, 5.12, 3.95, 1.70, "NOT CLAIMED", "No test coverage %, security score, endpoint latency, availability figure, field trial or formal acceptance study was collected.", fill=PALE_AMBER, accent=AMBER)

    # 24 — Test traceability
    s = d.standard_slide(
        5,
        "Test coverage & acceptance traceability",
        "Nine unit cases, three original browser scenarios and sixteen supplemental assertions",
        "The supplemental capture script intentionally continues after failures; its process exit is not an all-tests-passed signal. Keep original tests and documentation checks distinct.",
    )
    d.text(s, 0.68, 1.88, 3.84, 0.30, "EXISTING VITEST · 9 PASS", size=10.2, color=GREEN, bold=True)
    unit = [
        "UT-01 occupancy excludes reservations",
        "UT-02 check-in normalizes TN plate",
        "UT-03 duplicate / unavailable bay rejected",
        "UT-04 non-TN formats rejected",
        "UT-05 checkout releases bay",
        "UT-06 safe expand / reduce capacity",
        "UT-07 protection + 100-bay rejection",
        "UT-08 four consistent seed locations",
        "UT-09 requested floor / bay creation",
    ]
    d.bullet_card(s, 0.68, 2.24, 3.84, 4.58, "Domain + fixture cases", unit, accent=GREEN, body_size=9.2, step=0.46)
    d.text(s, 4.73, 1.88, 3.84, 0.30, "PLAYWRIGHT · 2 PASS / 1 FAIL", size=10.2, color=AMBER, bold=True)
    e2e = [
        ("E2E-01 PASS", "Switch Marina, VR and Phoenix locations"),
        ("E2E-02 FAIL", "Add 2×15 Harbour Point, resize to 18, reload → selector returns riverside"),
        ("E2E-03 PASS", "Check TN01AA3042 into B1-01 and back out"),
    ]
    for i, (status, body) in enumerate(e2e):
        y = 2.24 + i * 1.12
        d.card(s, 4.73, y, 3.84, 0.96, fill=PALE_RED if "FAIL" in status else WHITE)
        d.pill(s, 4.90, y + 0.12, 1.08, 0.26, status, fill=PALE_RED if "FAIL" in status else PALE_GREEN, color=RED if "FAIL" in status else GREEN, size=7.6)
        d.text(s, 4.90, y + 0.46, 3.48, 0.40, body, size=8.8, color=MUTED, line_spacing=1.05)
    d.callout(s, 4.73, 5.64, 3.84, 1.18, "TRACE", "FR-02/06–09 → unit tests. FR-01/18 → E2E-01. FR-14/16/17 → E2E-02 open. FR-04/05/10/15 → supplemental checks.", fill=PALE_BLUE, accent=BLUE)
    d.text(s, 8.78, 1.88, 3.85, 0.30, "SUPPLEMENTAL · 15 PASS / 1 FAIL", size=10.2, color=AMBER, bold=True)
    d.bullet_card(s, 8.78, 2.24, 3.85, 3.12, "B01–B16 evidence", [
        "B01 seed counts 72/34/32/6",
        "B02–B04 floor filter, reserved click, empty search",
        "B05–B08 arrival, reload, duplicate, checkout",
        "B09–B12 capacity, new site, independent switch",
        "B13–B14 format + duplicate-name errors",
        "B15 FAIL 390 px geometry; B16 no uncaught errors",
    ], accent=AMBER, fill=PALE_AMBER, body_size=9.0, step=0.45)
    d.callout(s, 8.78, 5.56, 3.85, 1.26, "NEXT TESTS", "Repeated reloads, malformed storage, integer boundaries, timestamps, keyboard dialogs and narrow-width action reachability.", fill=PALE_GREEN, accent=GREEN)

    # 25 — Defects & risks
    s = d.standard_slide(
        5,
        "Open defects & risk register",
        "Observed failures are separated from source-level quality gaps and architectural limits",
        "D-01 and D-02 are concrete browser findings. D-05 is not a bug to patch in the UI: it is the reason a future authoritative service is needed.",
    )
    d.table(
        s, 0.68, 1.92, 11.95,
        ["ID", "Class", "Finding", "Suggested closure evidence"],
        [
            ["D-01", "Observed browser failure", "Added/expanded location not retained as selected after reload", "Repeated E2E-02 passes with verified stored content"],
            ["D-02", "Observed layout failure", "390 px viewport produced 457 px document width", "Width assertions + reachable actions across narrow widths"],
            ["D-03", "Source quality gap", "Dialog focus lifecycle incomplete", "Keyboard and assistive-technology tests"],
            ["D-04", "Integrity gap", "Saved JSON lacks complete runtime validation", "Versioned schema + corruption/recovery tests"],
            ["D-05", "Architectural limit", "Browser snapshots cannot coordinate operators", "Transactional server + stale-write conflict tests"],
            ["D-06", "Presentation limit", "Static values / LIVE labels can imply telemetry", "Every operational claim has an explicit data source"],
        ],
        [0.07, 0.20, 0.39, 0.34], row_h=0.62, header_h=0.40, font_size=9.0,
    )
    d.text(s, 0.68, 5.98, 11.95, 0.30, "RISK PRIORITIES FROM SOURCE REVIEW", size=10.2, color=GREEN, bold=True)
    risks = [
        ("HIGH", "Reload + mobile geometry", RED, PALE_RED),
        ("HIGH", "Multi-tab overwrite / no shared authority", RED, PALE_RED),
        ("MEDIUM", "Saved JSON shape and registration privacy", AMBER, PALE_AMBER),
        ("MEDIUM", "Dialog keyboard behaviour and static labels", AMBER, PALE_AMBER),
    ]
    for i, (priority, label, color, fill) in enumerate(risks):
        x = 0.68 + i * 3.04
        d.card(s, x, 6.34, 2.83, 0.48, fill=fill, border=None, shadow=False)
        d.pill(s, x + 0.10, 6.42, 0.68, 0.30, priority, fill=WHITE, color=color, size=7.6)
        d.text(s, x + 0.88, 6.34, 1.84, 0.48, label, size=8.2, color=INK, valign="middle")

    # 26 — Achievements & limitations
    s = d.standard_slide(
        5,
        "Achievements against objectives & current limitations",
        "A source-backed feature is not automatically a fully accepted quality outcome",
        "The reusable domain core and transparent documentation are the strongest achievements. The largest limitation is authority: browser state can be cleared, edited or overwritten.",
    )
    d.text(s, 0.68, 1.88, 5.82, 0.30, "O1–O10 · OUTCOME ASSESSMENT", size=10.2, color=GREEN, bold=True)
    achievements = [
        ("O1–O2", "Implemented + demonstrated", "Counts are local records; search is current-floor only"),
        ("O3–O5", "Implemented + tested", "TN syntax only; no concurrent-client guarantee"),
        ("O6–O8", "Implemented + demonstrated", "Protection is by status, not special-kind minimum"),
        ("O9", "Save/restore exists", "Reload reliability finding remains open"),
        ("O10", "Tests + failures recorded", "No field deployment or formal acceptance study"),
    ]
    for i, (ids, outcome, qualification) in enumerate(achievements):
        y = 2.24 + i * 0.82
        d.card(s, 0.68, y, 5.82, 0.68)
        d.pill(s, 0.84, y + 0.18, 0.78, 0.30, ids, fill=PALE_GREEN, color=GREEN, size=8.0)
        d.text(s, 1.70, y + 0.05, 2.60, 0.28, outcome, size=9.4, bold=True)
        d.text(s, 1.70, y + 0.35, 4.55, 0.25, qualification, size=8.2, color=MUTED)
    d.callout(s, 0.68, 6.44, 5.82, 0.38, "STRONGEST CONTRIBUTION", "Typed records + explicit guards + immutable updates + derived outputs.", fill=PALE_GREEN, accent=GREEN)
    d.text(s, 6.78, 1.88, 5.85, 0.30, "PRINCIPAL LIMITATIONS", size=10.2, color=RED, bold=True)
    limitations = [
        "Authority: browser state is not a shared, durable operational record",
        "Persistence: one reload scenario failed; root cause unconfirmed",
        "History: checkout deletes the active session; no completed visit ledger",
        "Interface: narrow-width overflow, hidden selector, incomplete modal focus",
        "Scope: no login, reservations, tariffs, payments, sensors or ANPR",
        "Evaluation: no stakeholder interviews, field trial or ROI measurement",
    ]
    d.bullet_card(s, 6.78, 2.24, 5.85, 3.38, "Where conclusions stop", limitations, accent=RED, fill=PALE_RED, body_size=9.4, step=0.50)
    d.callout(s, 6.78, 5.82, 5.85, 1.00, "REVIEW LANGUAGE", "Functional educational MVP — not a production parking system. The limitations define the roadmap rather than negate the prototype’s value.", fill=PALE_BLUE, accent=BLUE)

    # 27 — Security & privacy
    s = d.standard_slide(
        5,
        "Security & privacy review",
        "Source-level observations, not a penetration test or certification",
        "A login screen alone would not repair client-side trust or concurrency. Start with a threat model and data policy, then add server authority and access controls.",
    )
    d.table(
        s, 0.68, 1.92, 11.95,
        ["Concern", "Current observation", "Recommended production control"],
        [
            ["Operator identity", "No sign-in or role checks; static manager profile", "Authenticate users and authorize every operation"],
            ["Registration data", "Plain JSON in browser storage", "Minimize, restrict access, define retention/deletion"],
            ["Data integrity", "Client can edit collections and storage", "Server-side validation + transactional constraints"],
            ["Concurrent allocation", "No shared authority", "Atomic bay/session updates + conflict responses"],
            ["Auditability", "Activity lacks actor and structured event time", "Append-only, attributed audit events"],
            ["Storage corruption", "Shallow restoration checks", "Versioned runtime schema + recovery path"],
            ["Credentials / payments", "Not collected or integrated", "Compliant providers; never store secrets locally"],
            ["Connected devices", "No device protocol or identity", "Device auth, stale-data handling, manual override"],
        ],
        [0.22, 0.39, 0.39], row_h=0.50, header_h=0.40, font_size=8.8,
    )
    d.callout(s, 0.68, 6.18, 5.82, 0.64, "VALIDATION ≠ IDENTITY", "The TN regex checks syntax, not ownership, existence or accessible-space eligibility.", fill=PALE_AMBER, accent=AMBER)
    d.callout(s, 6.78, 6.18, 5.85, 0.64, "DEMO PRACTICE", "Use fictional registrations, especially on shared computers; clearing site data is not governed deletion.", fill=PALE_GREEN, accent=GREEN)

    # 28 — Roadmap
    s = d.standard_slide(
        6,
        "Staged enhancement roadmap",
        "Reliability and clarity come first; shared authority, commercial rules and hardware follow",
        "None of these production capabilities is implemented. Each stage has an acceptance gate so the project does not expand the domain before the local foundation is trustworthy.",
    )
    stages = [
        ("1", "MVP HARDENING", ["Fix restoration/write coordination", "Canonical versioned saved schema", "Runtime validation + repeated reload tests"], "Repeated reload + corrupt-storage tests pass", GREEN),
        ("1", "INTERFACE QUALITY", ["Wrap narrow action controls", "Keep mobile location selection reachable", "Complete modal focus / Escape / return"], "Geometry, keyboard and accessibility review", BLUE),
        ("1", "HONEST PRESENTATION", ["Mark or remove static trends", "Clarify LIVE, next-arrival and EV labels", "Separate fixture data from derived counts"], "Every operational claim has a data source", AMBER),
        ("2", "SHARED AUTHORITY", ["Server API + durable database", "Atomic bay/session operations", "Auth, authorization, attribution, retention", "Completed sessions + structured events"], "Concurrency, access-control and recovery tests", GREEN),
        ("3", "DOMAIN RULES", ["Reservation create/cancel/expire/consume", "Tariffs, grace periods, compliant payments"], "Conflict, expiry, idempotent settlement tests", BLUE),
        ("4", "PHYSICAL INTEGRATION", ["Device identity and stale sensor policy", "Manual overrides and monitoring"], "Hardware failure + safe fallback exercises", AMBER),
    ]
    for i, (stage, title, bullets, gate, color) in enumerate(stages):
        col, row = i % 3, i // 3
        x, y = 0.68 + col * 4.05, 1.92 + row * 2.45
        d.card(s, x, y, 3.82, 2.22)
        d.rect(s, x, y, 0.06, 2.22, fill=color)
        d.oval(s, x + 0.20, y + 0.18, 0.40, 0.40, fill=PALE_GREEN if color == GREEN else PALE_BLUE if color == BLUE else PALE_AMBER)
        d.text(s, x + 0.20, y + 0.18, 0.40, 0.40, stage, size=11, color=color, bold=True, align="center", valign="middle")
        d.text(s, x + 0.72, y + 0.20, 2.85, 0.30, title, size=11.2, bold=True)
        for j, bullet in enumerate(bullets):
            d.oval(s, x + 0.24, y + 0.68 + j * 0.27, 0.055, 0.055, fill=color)
            d.text(s, x + 0.38, y + 0.61 + j * 0.27, 3.20, 0.24, bullet, size=8.2, color=MUTED)
        d.rect(s, x + 0.18, y + 1.78, 3.46, 0.30, fill=PALE, rounded=True)
        d.text(s, x + 0.28, y + 1.78, 3.26, 0.30, f"GATE  {gate}", size=7.8, color=color, bold=True, valign="middle")

    # 29 — Decisions
    s = d.standard_slide(
        6,
        "Review decisions & discussion",
        "Four decisions turn the mixed verification outcome into an actionable next iteration",
        "Close by asking reviewers to accept the MVP within its stated boundary and prioritize Stage 1 before any production feature discussion.",
    )
    decisions = [
        ("01", "Accept the academic MVP", "Recognize the typed local model, real screens and honest evidence; do not label it production-ready.", GREEN),
        ("02", "Prioritize Stage 1", "Fix reload/persistence coordination and narrow-width layout before expanding scope.", AMBER),
        ("03", "Keep scope claims explicit", "No authentication, shared DB, reservation lifecycle, payments or sensors are implied by the UI.", BLUE),
        ("04", "Approve evidence-led roadmap", "Add runtime schema, accessibility tests, then server authority and transactional operations.", GREEN),
    ]
    for i, (num, title, body, color) in enumerate(decisions):
        y = 1.92 + i * 1.10
        d.card(s, 0.68, y, 7.55, 0.94)
        d.oval(s, 0.88, y + 0.21, 0.50, 0.50, fill=PALE_GREEN if color == GREEN else PALE_BLUE if color == BLUE else PALE_AMBER)
        d.text(s, 0.88, y + 0.21, 0.50, 0.50, num, size=11, color=color, bold=True, align="center", valign="middle")
        d.text(s, 1.55, y + 0.10, 3.20, 0.30, title, size=10.5, bold=True)
        d.text(s, 1.55, y + 0.44, 6.42, 0.40, body, size=9.2, color=MUTED, line_spacing=1.05)
    d.card(s, 8.48, 1.92, 4.15, 4.62, fill=DARK, border=None)
    d.text(s, 8.76, 2.18, 3.60, 0.34, "DISCUSSION PROMPTS", size=11, color=GREEN_2, bold=True)
    prompts = [
        "Which operational rules require stakeholder sign-off?",
        "What is the retention policy for registration data?",
        "When should a shared backend replace browser storage?",
        "Which accessibility tests define “done” for Stage 1?",
        "Should reservations, pricing and sensors stay out of v1?",
    ]
    for i, prompt in enumerate(prompts):
        y = 2.68 + i * 0.70
        d.oval(s, 8.78, y + 0.10, 0.07, 0.07, fill=GREEN_2)
        d.text(s, 8.98, y, 3.34, 0.56, prompt, size=9.4, color="DCEAE3", line_spacing=1.08)
    d.hline(s, 8.76, 6.18, 3.60, color="2E6B58")
    d.text(s, 8.76, 6.28, 3.60, 0.22, "Q&A", size=13, color=WHITE, bold=True)
    d.callout(s, 0.68, 6.52, 7.55, 0.30, "DEMO TIP", "Use slides 18–22 for the live walkthrough; skip slide 30 if time is short.", fill=PALE_GREEN, accent=GREEN)

    # 30 — Appendix
    s = d.standard_slide(
        6,
        "Appendix · evidence gallery & reproduction",
        "Editable PPTX, full report, diagrams, genuine captures and machine-readable results",
        "This appendix is for reviewers who want provenance. The PPTX does not replace the 111-page report; it summarizes it for presentation and keeps source claims traceable.",
    )
    gallery = [
        (SHOTS / "01-overview.png", "Overview", "fit"),
        (SHOTS / "08-duplicate-validation.png", "Duplicate rejection", "contain"),
        (SHOTS / "09-new-location-result.png", "New location", "fit"),
        (SHOTS / "11-mobile-upper-view.png", "Mobile finding", "contain"),
        (DIAGRAMS / "04-01-architecture.png", "Architecture", "contain"),
        (DIAGRAMS / "04-06-domain-model.png", "Domain model", "contain"),
        (DIAGRAMS / "04-08-bay-state-machine.png", "State machine", "contain"),
        (DIAGRAMS / "04-11-capacity-workflow.png", "Capacity workflow", "contain"),
    ]
    for i, (path, caption, mode) in enumerate(gallery):
        col, row = i % 4, i // 4
        x, y = 0.68 + col * 3.04, 1.92 + row * 2.16
        d.card(s, x, y, 2.83, 1.92)
        d.image(s, path, x + 0.07, y + 0.07, 2.69, 1.52, mode=mode, centering=(0.5, 0.45), alt=caption)
        d.text(s, x + 0.10, y + 1.66, 2.63, 0.20, caption, size=8.2, color=MUTED, align="center")
    d.card(s, 0.68, 6.28, 11.95, 0.54, fill=PALE_GREEN, border=None, shadow=False)
    d.text(s, 0.88, 6.32, 11.55, 0.22, "REPRODUCE", size=8.5, color=GREEN, bold=True)
    d.text(s, 1.85, 6.32, 10.55, 0.22, "npm ci · npm test · npm run lint · npm run typecheck · npm run build · npm run dev   |   Full report: docs/project-report/ · Evidence JSON: source/", size=8.2, color=INK, font=MONO, align="right")
    d.text(s, 0.88, 6.56, 11.55, 0.18, "Assets: 11 source-grounded diagrams, 12 Chromium captures, editable DOCX + 111-page PDF, speaker notes in this PPTX.", size=7.8, color=MUTED)

    return d


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previews", action="store_true", help="render approximate PNG previews into .cache/project-review")
    args = parser.parse_args()

    deck = build_deck()
    output = deck.save()
    print(f"Wrote {output} ({output.stat().st_size:,} bytes, {len(deck.prs.slides)} slides)")

    if args.previews:
        renderer = PreviewRenderer(deck.prs)
        contact, paths = renderer.render_all()
        print(f"Wrote {len(paths)} slide previews and {contact}")
        if renderer.warnings:
            print(f"Layout audit: {len(renderer.warnings)} possible overflow(s)", file=sys.stderr)
            for warning in renderer.warnings[:40]:
                print("  " + warning, file=sys.stderr)
        else:
            print("Layout audit: no obvious text overflow in preview renderer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
