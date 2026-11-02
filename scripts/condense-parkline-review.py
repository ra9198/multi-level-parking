#!/usr/bin/env python3
"""Create a <=20-slide PPTX source deck from the 30-slide project review.

The resulting PPTX is an intermediate artifact for conversion to the legacy
binary .ppt format requested by the user. The final deliverable is
docs/project-review/Parkline PPT.ppt.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "project-review" / "Parkline_Project_Review.pptx"
INTERMEDIATE = ROOT / ".cache" / "Parkline PPT.pptx"
EXISTING_BUILDER = ROOT / "scripts" / "build-project-review-pptx.py"

# 1-based slide numbers from the source deck, chosen to keep the broadest
# project-review coverage within a 20-slide cap.
KEEP = [1, 2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 21, 23, 25, 28, 29]

TEXT_REPLACEMENTS = [
    (
        "Use slides 18–22 for the live walkthrough; skip slide 30 if time is short.",
        "Use the demo slides for the live walkthrough; keep Q&A for the end.",
    ),
    (
        "If time is short, spend most time on slides 10–17 and 23–29. Slides 18–22 are the visual demo; slide 30 is an evidence appendix.",
        "If time is short, spend most time on the design and verification slides. The demo slides are the visual walkthrough; keep Q&A for the end.",
    ),
    ("30-slide", "20-slide"),
    ("slides 18–22", "the demo slides"),
    ("Slides 18–22", "The demo slides"),
    ("slide 30", "the appendix"),
    ("slides 10–17 and 23–29", "the design and verification slides"),
]


def apply_replacements(text: str) -> str:
    for old, new in TEXT_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def patch_text_frame(text_frame) -> None:
    for paragraph in text_frame.paragraphs:
        for run in paragraph.runs:
            if run.text:
                run.text = apply_replacements(run.text)


def delete_slides(prs: Presentation, keep_one_based: list[int]) -> None:
    keep_zero_based = {number - 1 for number in keep_one_based}
    slide_id_list = prs.slides._sldIdLst
    for index in reversed(range(len(slide_id_list))):
        if index in keep_zero_based:
            continue
        slide_id = slide_id_list[index]
        relationship_id = slide_id.rId
        prs.part.drop_rel(relationship_id)
        slide_id_list.remove(slide_id)


def renumber_and_patch(prs: Presentation) -> None:
    footer_pattern = re.compile(r"^\s*\d{2}\s*/\s*30\s*$")
    for number, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if not getattr(shape, "has_text_frame", False):
                continue
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if footer_pattern.match(run.text):
                        run.text = f"{number:02d} / 20"
                    else:
                        run.text = apply_replacements(run.text)
        if slide.has_notes_slide:
            patch_text_frame(slide.notes_slide.notes_text_frame)


def load_builder_module():
    spec = importlib.util.spec_from_file_location("parkline_review_builder", EXISTING_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load existing deck builder module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previews", action="store_true", help="render approximate PNG previews of the condensed deck")
    args = parser.parse_args()

    INTERMEDIATE.parent.mkdir(parents=True, exist_ok=True)
    prs = Presentation(SOURCE)
    delete_slides(prs, KEEP)
    renumber_and_patch(prs)

    props = prs.core_properties
    props.title = "Parkline PPT"
    props.subject = "Condensed 20-slide project review presentation"
    props.comments = "Generated from the codebase-grounded 30-slide review deck and condensed to 20 slides."
    prs.save(INTERMEDIATE)
    print(f"Wrote {INTERMEDIATE} ({INTERMEDIATE.stat().st_size:,} bytes, {len(prs.slides)} slides)")

    if args.previews:
        module = load_builder_module()
        renderer = module.PreviewRenderer(prs)
        contact, paths = renderer.render_all()
        print(f"Wrote {len(paths)} previews and {contact}")
        if renderer.warnings:
            print(f"Layout audit: {len(renderer.warnings)} possible overflow(s)")
            for warning in renderer.warnings[:20]:
                print("  " + warning)
        else:
            print("Layout audit: no obvious text overflow in preview renderer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
