#!/usr/bin/env python3
"""Validate the generated report package without claiming Word-engine pagination."""
from pathlib import Path
from zipfile import ZipFile
import json

from lxml import etree
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/project-report"
VALIDATION = BASE / "source/document-validation.json"


def main():
    validation = json.loads(VALIDATION.read_text())
    front = validation["frontMatterPages"]
    expected = validation["pdfPages"]
    assert expected >= 90
    with pymupdf.open(BASE / "Parkline_BCA_Project_Report.pdf") as pdf:
        assert len(pdf) == expected
        assert all(abs(p.rect.width - 595.2756) < .1 and abs(p.rect.height - 841.8898) < .1 for p in pdf)
        for number, page in enumerate(pdf[front:], 1):
            footer = page.get_text(clip=pymupdf.Rect(0, 784, page.rect.width, page.rect.height)).strip()
            assert footer == f"Page {number}", (number, footer)
        for page in pdf:
            assert len(page.get_text().strip()) >= 50
            for link in page.get_links():
                if link.get("kind") == pymupdf.LINK_GOTO:
                    assert 0 <= link["page"] < len(pdf)
        print(f"PDF: {expected} A4 pages; consecutive main footers; no blank pages; internal links valid")

    with ZipFile(BASE / "Parkline_BCA_Project_Report.docx") as archive:
        ns = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        }
        document = etree.fromstring(archive.read("word/document.xml"))
        sections = document.findall(".//w:sectPr", ns)
        assert len(document.findall(".//w:pgBorders", ns)) == 1
        starts = [s.find("w:pgNumType", ns).get("{" + ns["w"] + "}start") for s in sections]
        assert starts[:3] == ["1", "2", "1"] and all(s is None for s in starts[3:]), starts
        # Count explicit authored starts, NOT a measured Word rendering page count.
        page_starts = 1 + len(document.findall(".//w:pageBreakBefore", ns)) + len(sections) - 1
        assert page_starts == expected, page_starts
        for name in archive.namelist():
            if name.endswith(".xml"):
                etree.fromstring(archive.read(name))
        font_table = etree.fromstring(archive.read("word/fontTable.xml"))
        rels = etree.fromstring(archive.read("word/_rels/fontTable.xml.rels"))
        relmap = {e.get("Id"): e.get("Target") for e in rels}
        count = 0
        for family in font_table:
            for embed in family:
                if "embed" not in etree.QName(embed).localname:
                    continue
                key = embed.get("{" + ns["w"] + "}fontKey")
                rid = embed.get("{" + ns["r"] + "}id")
                target = relmap[rid]
                decoded = bytearray(archive.read("word/" + target))
                mask = bytes.fromhex(key.strip("{}").replace("-", ""))[::-1]
                for i in range(32):
                    decoded[i] ^= mask[i % 16]
                filename = Path(target).name.removesuffix(".odttf")
                assert bytes(decoded) == (BASE / "assets/fonts" / filename).read_bytes(), filename
                count += 1
        assert count == 5
        print(f"Word: {page_starts} explicit page starts; continuous section numbering; cover-only border; XML/fonts valid")

    validation.update({
        "pdfConsecutiveMainFootersVerified": True,
        "pdfInternalLinksVerified": True,
        "docxExplicitPageStarts": page_starts,
        "docxPackageXmlValidated": True,
        "docxEmbeddedFontsValidated": count,
        "docxCoverOnlyBorderVerified": True,
        "docxSectionNumberingVerified": True,
    })
    VALIDATION.write_text(json.dumps(validation, indent=2) + "\n")


if __name__ == "__main__":
    main()
