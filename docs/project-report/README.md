# Parkline college project report

## Deliverables

- **[Parkline_BCA_Project_Report.pdf](Parkline_BCA_Project_Report.pdf)** — verified **111-page** fixed-layout report: 13 preliminary pages and 98 numbered main/reference/appendix pages.
- **[Parkline_BCA_Project_Report.docx](Parkline_BCA_Project_Report.docx)** — editable Word version of the same authored content, with embedded fonts and explicit page starts. Word pagination can vary by viewer; use the PDF as the submission pagination reference.

The report follows `Example Docs/IMS_BCA_Project_Report.pdf`: double-bordered institutional cover, certificate, declaration, acknowledgement, abstract, contents, figure/table lists, abbreviations, eight chapters, references and appendices. It uses the reference's SRM BCA institution/department wording, A4 dimensions, serif typography, chapter headings, running headers and Roman/Arabic numbering.

**Contents:** 19 figures (11 source-grounded diagrams and 8 printed application screenshots), 49 numbered tables, requirements/traceability matrices, actual TypeScript data dictionary, implementation explanations, test evidence, limitations, future roadmap and source-code/operator-guide appendices. Additional supporting screenshots remain in `assets/screenshots/`.

## Complete these before submission

Edit [`source/metadata.json`](source/metadata.json):

- Student name and registration number.
- Project guide name, qualifications and designation.
- Head/programme coordinator name.
- Submission month and institutional wording, if your approved particulars differ.

Names from the reference were **not** assumed to identify the Parkline candidate or signatories. Certificates/declarations are unsigned templates: review their wording and obtain actual institutional approval. Review acknowledgements to reflect support actually received. You can edit the Word file directly, but changing the metadata and rebuilding keeps both versions synchronized.

## Technical truth and verification

Application baseline: `aa4b73016f271a7e0778c6c8bbd6c17346f52346`, reviewed **31 October 2026**. The application was not changed to repair findings while documenting it.

The report accurately describes a **browser-local UI/domain MVP**. It does not claim authentication, a shared database, payment processing, a reservation lifecycle, gate control, ANPR or live sensor integration. Location names/registrations are fixtures. Static manager/date/trend/charging labels are distinguished from derived counts. Future-service diagrams and suggestions are explicitly proposed, not implemented.

Recorded results:

| Check | Recorded outcome |
|---|---|
| Existing unit suite | **9 passed** |
| ESLint | **Passed** |
| TypeScript | **Passed** |
| Production build | **Passed** |
| Existing Playwright scenarios | **2 passed, 1 failed** — added/expanded location selection not retained after reload |
| Supplemental report browser assertions | **15 passed, 1 failed** — document width 457 px at a 390 px viewport |

The supplemental capture script deliberately records failed assertions and continues collecting evidence; its process exit is **not** an all-tests-passed signal. Successful reloads in the supplemental sequence do not erase the original persistence failure. No field trial, stakeholder UAT, latency benchmark, security audit or WCAG certification is claimed.

Machine-readable evidence:

- [`source/unit-results.json`](source/unit-results.json)
- [`source/e2e-results.json`](source/e2e-results.json)
- [`source/browser-evidence.json`](source/browser-evidence.json)
- [`source/dependency-versions.json`](source/dependency-versions.json)
- [`source/verification-summary.json`](source/verification-summary.json)
- [`source/document-validation.json`](source/document-validation.json)

## Rebuild PDF and Word

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r docs/project-report/requirements.txt
.venv/bin/python scripts/build-project-report.py
.venv/bin/python scripts/verify-project-report.py
```

The build reads the numbered Markdown sources and metadata. It rejects overflowing authored pages, checks the minimum 90-page requirement, validates the fixed PDF page count and writes a validation summary. Code blocks are visually soft-wrapped without changing the underlying application source. Contents/list page references are generated from the PDF's authored page map; after substantial edits, regenerate instead of assuming existing references remain correct.

The bundled fonts are licensed redistributable resources; their notices are in `assets/fonts/`. Compatible Word viewers can use the embedded fonts. The PDF embeds its print fonts. Report generation does not require Microsoft Word or LibreOffice.

To regenerate diagrams independently:

```bash
.venv/bin/python scripts/generate-report-diagrams.py
```

The diagram utility creates vector intermediate files in the ignored `.cache/` directory and retained high-resolution PNG assets. Diagrams describe the actual local architecture, except explicitly labelled proposals in the report text.

## Recreate browser evidence

Start the built application in one terminal:

```bash
npm ci
npm run build
npm run start -- --hostname 0.0.0.0 --port 3000
```

In a second terminal, with a compatible Playwright browser installed:

```bash
npx playwright install chromium
node scripts/capture-report-evidence.mjs
```

Optional environment variables:

- `REPORT_BASE_URL`: application origin (default `http://127.0.0.1:3000`, for the **local automation process**, not browser-facing API code).
- `REPORT_CHROMIUM_PATH`: an alternative installed Chromium executable.
- `REPORT_BROWSER_ARGS`: JSON array of launch arguments required by that environment.

The recorded documentation run used Chromium 153.0.8010.0 supplied through an environment-specific launcher and the production server. The original three Playwright scenario definitions were unchanged. An initial launcher setup timeout was excluded from the subsequent complete-run summary; the final three-scenario result, including its reload assertion failure, is retained.

The mobile report figure uses the upper 750 image-pixel rows (500 CSS pixels at 1.5 scale) of the full mobile capture at its **full captured width**, preserving the overflow. `11-mobile-overview.png` retains the uncropped image. If captures are refreshed, regenerate that print excerpt with:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from PIL import Image
p = Path('docs/project-report/assets/screenshots/11-mobile-overview.png')
with Image.open(p) as image:
    image.crop((0, 0, image.width, min(750, image.height))).save(
        p.with_name('11-mobile-upper-view.png')
    )
PY
```

After changes, re-run verification and review the report claims rather than simply overwriting the previous evidence. The original application defects remain follow-up work, not changes made by this documentation task.
