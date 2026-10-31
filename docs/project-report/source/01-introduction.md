<!-- page: c1-overview | Chapter 1: INTRODUCTION -->
# CHAPTER 1 — INTRODUCTION
## 1.1 Overview of the Project

Parkline is a web-based multi-level parking operations and capacity planning application. It presents a garage manager with a consolidated view of parking capacity, occupied bays, available bays, reserved sample records and active vehicle sessions. The application supports several garage locations, each with independent operational data. Within a selected location, the operator can inspect individual floors, search for a bay or registration, register a vehicle arrival, complete a departure and adjust the planned capacity of each floor. The software package is named `multi-level-parking` and its current declared version is `0.1.0` [1, 7].

The implemented application is a functional user-interface and domain-logic minimum viable product, rather than an installed physical parking-control system. Its main page is provided by the Next.js App Router. A React client component owns interactive state, while independent TypeScript functions implement occupancy calculation, Tamil Nadu registration validation, check-in, check-out and protected capacity resizing. Typed sample fixtures supply four initial garage locations. Browser local storage retains planning and operational changes on the same device and origin; no shared database is connected [2–5].

The central engineering contribution is the consistent treatment of parking as a set of controlled state transitions. A vehicle can enter only an available bay. A normalized registration cannot have two active sessions within the selected location. Checking out a session releases its assigned bay. A capacity reduction cannot discard occupied or reserved bays. These rules make the demonstration useful for studying operational integrity without implying the transactional guarantees of a production backend.

This report documents what exists in the reviewed source revision, explains its design, reproduces genuine application screens and records observed verification results. Proposed authentication, server persistence, payment processing, reservation workflows and sensor connectivity are discussed only as future enhancements. Decorative interface labels such as “LIVE” are not interpreted as evidence of a real-time occupancy service.

<!-- page: c1-profile | Chapter 1: INTRODUCTION -->
## 1.2 Background of the Study

A multi-level garage separates a single parking facility into several spatially distinct floors. An operator therefore needs more than a total count: the operator must know which floor contains a usable bay, whether an apparent vacancy is reserved, and which vehicle is associated with an occupied bay. When this information is recorded in different notebooks or spreadsheets, a change at the gate may not be reflected in the floor-level view. The resulting coordination problem motivates a shared visual model, even before physical equipment or network services are introduced.

Parkline addresses this coordination problem at the browser-interaction level. Each location contains levels, bays, sessions and activity. A bay has both an operational status and a physical kind. For example, an EV bay can be available or occupied; EV is not an occupancy state. Similarly, a reserved bay is unavailable for ordinary arrival even though it is not counted as a parked vehicle. This separation prevents a common modeling error in which unrelated properties are combined into one status field.

**Table 1.1: Project identity and verified architectural profile**

| Attribute | Description of the reviewed application |
|---|---|
| Application identity | Parkline; npm package `multi-level-parking`; version 0.1.0 |
| Primary purpose | Operator dashboard, vehicle sessions and capacity planning |
| Framework | Next.js 16.4.3 with React 19.0.0 and TypeScript |
| Initial inventory | Four locations; three floors and 72 bays per seeded location |
| Operational statuses | available, occupied and reserved |
| Physical bay kinds | standard, ev and accessible |
| Persistence | Device-local JSON in browser local storage |
| Domain verification | Nine existing Vitest tests in one test file |
| Browser workflows | Three existing Playwright scenarios |
| Explicit exclusions | No API, authentication, payment service or live sensors |

The initial names and vehicle registrations are demonstration fixtures. They do not establish a relationship with the named commercial sites, confirm a physical site's capacity or identify actual customer visits. The report treats them solely as software test data.

<!-- page: c1-problem | Chapter 1: INTRODUCTION -->
## 1.3 Problem Statement

The project investigates how a browser application can represent parking availability and operator actions coherently across locations and floors. The problem is not to prove that automated parking has been deployed; it is to build and evaluate a correct, understandable software model for the operational tasks within the current scope.

1. **Fragmented visibility:** A garage-wide total is insufficient when an operator must direct a vehicle to a specific floor. The application must expose location totals and floor-specific details without confusing their scopes.
2. **Ambiguous bay availability:** An unoccupied bay may still be reserved. Occupied, reserved and available counts must remain distinct and their sum must equal the actual inventory size.
3. **Invalid vehicle identifiers:** Registration text may contain lowercase characters, spaces or hyphens. Accepted input needs a single normalized form before duplicate checking and display.
4. **Double allocation:** Reusing an occupied or reserved bay would create conflicting operational records. The transition owner must reject an arrival into anything other than an available bay.
5. **Duplicate active vehicles:** A registration already present in the location's active sessions must not receive a second session simply because its formatting differs.
6. **Unsafe capacity changes:** Reducing a floor's capacity must not silently remove a bay that contains a vehicle or a reserved sample record. Expansion must allocate unused bay numbers.
7. **Location contamination:** Switching garages must restore the selected location's own inventory and sessions rather than carry another garage's state into the view.
8. **Unclear persistence expectations:** Browser-local saving can support a demonstration, but it cannot coordinate multiple operators or provide durable enterprise records. This limitation must be visible in both the software explanation and the project evaluation.

The desired outcome is an operator-centered MVP with testable invariants and transparent boundaries. Production concerns such as concurrent gate operators, authorization and payment settlement remain separate problems. Documenting those boundaries is necessary because a visually polished dashboard can otherwise suggest capabilities that the source does not implement.

<!-- page: c1-objectives | Chapter 1: INTRODUCTION -->
## 1.4 Objectives of the Project

The primary objective is to implement and explain an interactive parking dashboard whose visible totals, bay map and active sessions agree after supported operations. Secondary objectives concern input quality, safe planning, maintainable organization and evidence-based evaluation. Objectives are intentionally phrased as demonstrable software behavior rather than claims about traffic reduction, revenue growth or customer satisfaction, none of which has been measured.

**Table 1.2: Objectives and implementation evidence**

| ID | Objective | Evidence in the application |
|---|---|---|
| O1 | Present location and floor occupancy | `occupancyForLevel` and dashboard summary cards |
| O2 | Support visual bay inspection | Floor tabs, bay buttons, legends and status filters |
| O3 | Normalize and validate registrations | `normalizeTamilNaduPlate` in `parking.ts` |
| O4 | Prevent invalid arrival transitions | Available-bay guard and active-session duplicate guard |
| O5 | Release a bay on departure | `checkOut` returns updated bays and sessions |
| O6 | Preserve protected bays during resizing | `resizeLevelBays` protects non-available inventory |
| O7 | Create configurable garage locations | `createManagedLocation` and planning dialog |
| O8 | Keep location operations separate | `operationsByLocation` indexed by location ID |
| O9 | Retain demonstration data locally | Storage key `parkline-garage-planning` |
| O10 | Verify behavior and expose limitations | Unit tests, browser tests and documented observations |

A successful check-in is not judged only by a confirmation message. The target bay must become occupied, a normalized session must appear, the occupied total must increase and the available total must decrease while capacity and reserved counts remain unchanged. Checkout must reverse the occupancy effect without changing the physical kind of the bay.

Capacity planning has a different success criterion: the inventory count changes while existing occupied and reserved bay identities remain present. This distinction is important because a superficially correct capacity number could conceal loss of operational records. The report uses these objective-specific criteria throughout its requirements, design and testing chapters.

<!-- page: c1-scope | Chapter 1: INTRODUCTION -->
## 1.5 Scope of the Project

The project scope is the current browser-local implementation, including its source code, test suite and operator-facing screens. “Implemented” below means that an identifiable code path exists; it does not imply that every edge case has passed testing or that the feature is ready for production use. Verification outcomes and open defects are reported separately in Chapter 7.

**Table 1.3: Functional scope and exclusion matrix**

| Area | Included in the MVP | Outside the implemented scope |
|---|---|---|
| Locations | Switch four seeds; add a named location | Editing or deleting a location; physical-site verification |
| Floor inventory | Configure 1–10 floors at creation | Adding or removing floors on an existing location |
| Bay capacity | Set 1–99 bays per floor; protect non-available bays | Geometric floor-plan editing; structural capacity approval |
| Arrivals | Select an available bay; validate a TN registration | Ticket printing; gate opening; number-plate recognition |
| Departures | Select an active session on the current level | Duration billing; payments; historical session ledger |
| Reservation display | Display seeded reserved bays and notices | Creating, cancelling, expiring or fulfilling reservations |
| EV and accessibility | Display special-kind indicators | Charging telemetry; eligibility verification; charging fees |
| Persistence | Save JSON in the current browser and origin | Shared database, backup, account synchronization |
| Security identity | Static operator presentation only | Login, logout, authorization and audit attribution |
| Analytics | Derive present inventory counts | Historical trends, forecasting and measured utilization |

Search and filtering operate on the currently selected floor. The arrival bay selector can list available bays across the selected location, while the departure selector is restricted to active sessions on the selected level. These details affect operator instructions and are retained in the report rather than replaced with a more ambitious specification.

The documentation includes conceptual data relationships because they help explain the TypeScript model. It does not describe an existing SQL schema or API. Any relational or service-oriented design in the enhancement discussion is explicitly labeled as proposed.

<!-- page: c1-motivation | Chapter 1: INTRODUCTION -->
## 1.6 Project Motivation

Parking is a suitable college-project domain because its rules are easy to demonstrate yet rich enough to expose meaningful software engineering decisions. A bay can hold only one active vehicle, a floor contains a bounded inventory and a departure must release the correct resource. These simple statements produce useful questions about identity, validation, state ownership and error handling. Parkline turns those questions into visible interactions instead of leaving them as isolated algorithms.

Consider an operator working at the Riverside demonstration location. The garage begins with 72 bays across three floors. Its inventory contains 34 occupied, six reserved and 32 available bays. A new vehicle assigned to B1-01 changes only the relevant operational state: capacity stays 72, occupied becomes 35, available becomes 31 and reserved remains six. The same operator can subsequently inspect a different location without altering Riverside's records. This scenario joins a user task with a precise set of data expectations.

Capacity planning introduces another educational dimension. If a floor contains ten occupied and two reserved bays, its capacity cannot safely be reduced below twelve. Available bays may be removed in a deterministic order, but protected records must survive. A new location, by contrast, starts with entirely available standard bays and no sessions. Explaining the difference between these operations demonstrates why business rules should reside in reusable domain functions rather than only in form controls.

The use of a modern frontend stack also supports study of component state, derived values, effects and responsive layout. However, the motivation for using these technologies is maintainable interaction, not the appearance of production infrastructure. A simulated “LIVE” badge or a static manager profile is not a substitute for a network feed or authenticated identity.

The project's academic value therefore lies in a reviewable end-to-end prototype: typed records, focused transition functions, genuine screens, automated checks and a candid account of missing capabilities. This report preserves that emphasis and avoids estimating real-world financial or traffic benefits without deployment evidence.

<!-- page: c1-assumptions | Chapter 1: INTRODUCTION -->
## 1.7 Assumptions and Constraints

The reviewed MVP assumes one operator's effective working state in a browser tab. It can retain data after a reload, subject to browser storage availability and the implementation's restoration behavior, but it does not provide a synchronization protocol. Two devices do not share a garage state, and two tabs can overwrite the same local-storage record without transaction coordination. For this reason, the no-duplicate-session rule is a local application invariant rather than a database-backed global guarantee.

**Table 1.4: Assumptions, constraints and their consequences**

| Assumption or constraint | Consequence for interpretation |
|---|---|
| Registration policy accepts `TN` plus two digits, two letters and four digits | Syntactic validation only; not verification against a transport authority |
| Bay numbers use a two-digit suffix from 01 to 99 | A floor cannot exceed 99 bays under the current helper |
| Location creation permits 1–10 floors | Maximum newly created inventory is 990 bays |
| Operations are passed for one selected location | Duplicate checking is not global across locations |
| Dates originate from the browser clock | Timestamps are not trusted server audit times |
| Seed arrival ages are generated at module evaluation | Demonstration times vary between runs |
| Activity stores human-readable time strings | “Just now” and seed relative times do not continuously age |
| Saved JSON has only shallow restoration checks | Corrupt or incompatible stored shapes may not recover safely |
| No reservation transition is implemented | Reserved samples remain protected but cannot be managed end to end |

The interface also contains static decorative values: the manager name, the displayed date, the yesterday comparison, the next-arrival message and the EV charging summary. They are not derived historical or telemetry outputs. Treating them as measured results would be inaccurate.

These constraints shape the evaluation method. The report measures no physical garage performance, claims no regulatory certification and does not infer security from visual polish. It records executed checks and distinguishes source-level reasoning, observed browser behavior and future design recommendations.

<!-- page: c1-organization | Chapter 1: INTRODUCTION -->
## 1.8 Organization of the Report

This report follows the supplied college-project reference: formal preliminary pages, an abstract, contents, lists of figures and tables, abbreviations, eight numbered chapters, references and appendices. The cover treatment, serif typography, chapter presentation, running headings and Roman/Arabic page-numbering distinction are adapted from that document. The subject matter has been rewritten for Parkline rather than transferred from the reference's healthcare application.

Chapter 1 establishes the problem, objectives, scope and constraints. Chapter 2 reviews relevant software-engineering approaches and official technical guidance. Chapter 3 converts the observed behavior into functional requirements, quality considerations and feasibility analysis. Chapter 4 presents architecture, data flow, behavioral diagrams, conceptual relationships and the actual TypeScript data dictionary. Chapter 5 explains the technologies and tools used. Chapter 6 walks through implementation and authentic screen outputs. Chapter 7 reports tests, observed defects and evaluation limits. Chapter 8 concludes the study and proposes a staged enhancement roadmap.

## 1.9 Documentation Method and Evidence Boundary

The principal evidence is the checked-out application at commit `aa4b73016f271a7e0778c6c8bbd6c17346f52346`, reviewed on 31 October 2026. The implementation was inspected directly, dependencies were installed from the lockfile and the application was built for screen capture. Unit, lint, type and production-build commands were executed. Existing Playwright scenarios and additional documentation-focused browser checks were also exercised. Machine-readable results accompany the report source.

The evidence distinguishes three categories. **Implemented behavior** is supported by a source path and explained algorithm. **Observed behavior** is supported by a recorded check or screen capture. **Proposed behavior** describes a future change and is never presented as already deployed. No stakeholder interviews, field measurements, payment transactions or physical sensor experiments were performed.

Candidate names, registration numbers and signatory details remain editable placeholders because the reference's personal identities cannot safely be assumed to apply to this project. The certificate and declaration are submission templates requiring the candidate's review and the institution's actual approval; no signature or endorsement has been manufactured.
