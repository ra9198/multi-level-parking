# Parkline project-review presentation

## Deliverable

- **[`Parkline_Project_Review.pptx`](Parkline_Project_Review.pptx)** — an editable **30-slide, 16:9** PowerPoint deck for a comprehensive project review.

All headings, body copy, cards, tables, diagrams and progress indicators are native PowerPoint shapes and text. Genuine application screenshots and source-grounded report diagrams are embedded as images. Every slide includes speaker notes with presentation guidance.

## Coverage

| Section | Slides | Main elements |
|---|---:|---|
| 01 · Context | 04–07 | Project identity, problem, 10 objectives, literature review, feasibility, included/excluded scope |
| 02 · Requirements | 08–09 | Operator journey, six use cases, FR-01–FR-18, NFR-01–NFR-10, traceability |
| 03 · Design & build | 10–17 | Architecture, TypeScript domain model, bay state machine, workflows, validation, source code, persistence, stack, UI/accessibility |
| 04 · Product demo | 18–22 | Overview, floor map/search/filter, arrival/departure/validation, capacity/new locations, mobile finding |
| 05 · Verification | 23–27 | Check scoreboard, unit/E2E/supplemental traceability, defect register, achievements, limitations, security/privacy |
| 06 · Outlook | 28–30 | Four-stage roadmap, review decisions/Q&A, evidence gallery and reproduction commands |

The deck deliberately preserves the project's honest boundaries: browser-local persistence, no authentication, no shared database, no payment/reservation/sensor integration, one failed reload scenario and one failed 390 px mobile-overflow check. Decorative `LIVE` and trend labels are identified as presentation content rather than telemetry.

## Sources used

The deck is grounded in repository evidence rather than generic parking-system claims:

- `README.md` and the application source under `src/`, `e2e/`.
- [`docs/project-report/Parkline_BCA_Project_Report.pdf`](../project-report/Parkline_BCA_Project_Report.pdf) and its editable Word source.
- Numbered Markdown chapters in `docs/project-report/source/`.
- Real Chromium captures and deterministic diagrams in `docs/project-report/assets/`.
- Machine-readable `unit-results.json`, `e2e-results.json`, `browser-evidence.json`, `verification-summary.json` and dependency evidence.

The reviewed application source hashes in `verification-summary.json` match the current checkout. The report's reviewed commit is recorded as `aa4b730`; the report was reviewed on 31 October 2026.

## Before presenting

1. Replace `[Student Name]`, `[Register Number]` and `[Project Guide Name]` on slide 1.
2. Confirm institution, degree and guide wording against approved submission particulars. No institutional approval is asserted by the deck.
3. Use slides 18–22 for the live walkthrough. Slide 30 is an optional evidence appendix.
4. If exact typography matters, open on a system with **Arial** and **Consolas** available; fonts are not embedded.

## Regenerate

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r docs/project-review/requirements.txt
.venv/bin/python scripts/build-project-review-pptx.py
```

To render approximate PNG layout previews and a contact sheet for visual QA:

```bash
.venv/bin/python scripts/build-project-review-pptx.py --previews
```

Previews are written to the ignored `.cache/project-review/` directory. The preview renderer is a QA aid based on the deck's shape geometry; PowerPoint remains the authoritative renderer.

The generator performs a text-fit audit during preview generation and writes the final PPTX to `docs/project-review/Parkline_Project_Review.pptx`.
