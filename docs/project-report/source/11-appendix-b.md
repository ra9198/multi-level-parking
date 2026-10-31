<!-- page: app-b-install | Appendix B: OPERATIONAL GUIDE AND PROPOSED EXTENSION -->
# APPENDIX B — OPERATIONAL GUIDE AND PROPOSED EXTENSION
## B.1 Installation and Demonstration Setup

This guide reproduces the current browser-local demonstration. Use fictional vehicle information. Do not treat the application as the sole operational record of a real garage, because it lacks shared authority, authenticated access and durable recovery.

1. Install Node.js 20.9 or newer and npm. The report run used Node.js 22.22.3.
2. Open the repository and install the locked dependencies with `npm ci`.
3. Run the unit, lint and type checks. Build the application before production serving.
4. Start the application and open its served address in a modern browser.
5. Confirm the local-browser/no-sensor footer and the initial Riverside metrics.

```bash
npm ci
npm test
npm run lint
npm run typecheck
npm run build
npm run start -- --hostname 0.0.0.0 --port 3000
```

For ordinary development, `npm run dev` is also available. If serving through a remote preview, use the preview's address in the browser; a user's device cannot reach the sandbox by calling its own localhost. Browser tests require a configured Playwright browser and operating-system libraries in addition to npm dependencies.

**Table B.1: Current route and interaction inventory — no parking API exists**

| Address / anchor | Purpose | Security interpretation |
|---|---|---|
| `/` | Dashboard and all dialogs | No login or role gate |
| `/#overview` | Main overview section | Same page, not another service |
| `/#parking-layout` | Bay map section | Same client state |
| `/#activity` | Recent activity section | Not a historical audit endpoint |

The browser may restore an earlier local plan, so initial counts can differ if this origin already has saved data. For a clean fictional-data demonstration, use a fresh browser profile or clear only this application's site data after confirming that no wanted local records will be lost. There is no implemented export, backup or undo workflow.

<!-- page: app-b-sessions | Appendix B: OPERATIONAL GUIDE AND PROPOSED EXTENSION -->
## B.2 Operator Guide — Inspect, Arrive and Depart

### B.2.1 Inspect the Correct Scope

Select the garage first, then the floor. Read the capacity cards for the selected location and the occupancy strip for the selected level. Use the legend to distinguish available, occupied and reserved. EV and accessible icons indicate kind, not separate availability states. Search applies to the current floor only; change floors if a registration is not found.

### B.2.2 Start a Demonstration Session

1. Click an available bay or choose “New arrival”.
2. Enter a fictional TN registration, for example `TN01AA3042`.
3. Optionally enter a short vehicle description.
4. Check the selected bay; the dropdown can include other levels of this location.
5. Submit and confirm the registration/bay notice, occupied bay and changed totals.
6. If an error appears, correct the input. Do not assume a session began merely because the dialog was opened.

### B.2.3 Complete a Departure

Select the floor containing the active session. Click “Check out” or its occupied bay, choose the matching registration/bay/description and complete checkout. Confirm the bay is available again. No payment or receipt follows because neither is implemented.

**Table B.2: Common operator messages and appropriate response**

| Message or symptom | Meaning | Response |
|---|---|---|
| TN format error | Input does not match the project policy | Correct spacing/content; other-state formats remain outside scope |
| Already active session | Normalized plate already exists at this location | Locate the existing session rather than allocate again |
| Choose an available bay | Target is missing or not available | Select a currently available option |
| No active sessions on this level | Departure list is floor-scoped | Switch to the relevant floor |
| No bays match this search | Current predicates return no records | Clear the query/filter or select another floor |
| Bay is reserved | Sample reserved inventory is protected | Do not attempt ordinary arrival; no reservation workflow exists |

A success notice confirms a local transition, not durable server storage. Reload behavior has an open finding, so preserve the distinction during demonstrations and evaluation.

<!-- page: app-b-planning | Appendix B: OPERATIONAL GUIDE AND PROPOSED EXTENSION -->
## B.3 Operator Guide — Capacity, Locations and Local Data

Open “Plan capacity” to edit existing floor bay counts. Each row shows occupied and reserved totals and the protected minimum. Enter a whole number within one to ninety-nine and do not reduce below that minimum. Saving computes a complete valid plan before committing it. Expansion creates standard available bays; reduction removes highest-numbered available bays and retains protected IDs.

To add a site, choose the “Add location” tab, enter a non-blank unique name, choose one to ten floors and one to ninety-nine bays per floor, review the preview and submit. New locations begin empty and standard. The current UI does not edit a location name, delete a location or change the number of floors after creation.

### B.3.1 Saved Data and Safe Reset

Planning and session changes are serialized under `parkline-garage-planning` for the current origin. The data is not synchronized to another computer. A different preview hostname is a different origin and may therefore show a different plan. Clearing site data discards the browser copy; no server backup will restore it.

If a clean demonstration is required, first confirm that only fictional disposable data is present. Close other tabs for this origin, then use browser site-data controls to clear this application and reload. Do not clear unrelated sites or assume there is an undo. For investigation, inspect the saved JSON before resetting so that a persistence defect is not erased without evidence.

**Table B.3: Demonstration and submission checklist**

| Review item | Required action |
|---|---|
| Candidate identity | Replace student name and register-number placeholders |
| Institutional wording | Confirm degree, department and guide details with the institution |
| Certificate/signatures | Obtain actual approval; no generated endorsement is valid |
| Data privacy | Use fictional registrations and avoid shared-device personal records |
| Test presentation | Retain both passing results and open findings |
| Pagination | Use the generated PDF as the fixed-page reference |
| Editable copy | Review Word layout after fonts or content are changed |

The documentation tooling can regenerate the report from source and metadata. Rebuilding the document does not fix application defects or automatically update institutional approval. Both require separate review.

<!-- page: app-b-proposal | Appendix B: OPERATIONAL GUIDE AND PROPOSED EXTENSION -->
## B.4 Proposed Shared-Service Design — Not Implemented

This future-design sketch has no implemented API routes, tables, migrations or access-control handlers. Operational rules and privacy requirements must be agreed before implementation.

**Table B.4: Proposed authoritative records and invariants — future design only**

| Proposed record | Possible identity / fields | Invariant to enforce |
|---|---|---|
| Location | Stable location key, name, revision | Authorized site scope and unique policy-defined name |
| Level | Location key plus level key, approved capacity | Capacity agrees with approved active inventory |
| Bay | Location-scoped unique key, level, kind, status, revision | One current authoritative state per physical bay |
| Visit | Stable key, bay, plate, arrival, departure, lifecycle | At most one active visit per bay and scoped registration |
| Operational event | Event key, actor, location, event time, action | Attributed append-only history with defined retention |

### B.4.1 Proposed Transaction Boundary

A future arrival request should authenticate an operator, authorize the location, normalize and validate input, acquire or conditionally update the current bay, check active-registration uniqueness and commit the visit plus bay state atomically. A stale client should receive a conflict and refresh authoritative state rather than overwrite another operator's work. Departure should preserve completed history and be safe under repeated submission.

Capacity reduction should verify current protected occupancy inside the same transaction as inventory modification. Browser-calculated counts are informative, not authoritative. If a future API accepts an expected revision or idempotency key, the server must define its exact semantics and test retries and conflicts.

### B.4.2 Proposed Integration Gates

Authentication, database recovery and privacy controls should precede payments or sensors. Reservation work needs explicit timing and state-transition policy. Sensor work needs device identity, stale-data detection and manual override ownership. Payment work needs tariff rules, idempotency and reconciliation. These are separate acceptance gates, not capabilities created by this appendix.

This is an enhancement sketch only; the documented implementation remains the browser-local frontend/domain prototype.
