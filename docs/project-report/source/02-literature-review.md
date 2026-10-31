<!-- page: c2-introduction | Chapter 2: LITERATURE REVIEW -->
# CHAPTER 2 — LITERATURE REVIEW
## 2.1 Introduction and Review Method

The literature review places Parkline within established approaches to small operational web applications. It is a technical and design-oriented review, not a field survey of commercial parking installations. The available evidence does not include vendor demonstrations, customer interviews or a systematic collection of experimental papers. Accordingly, the chapter compares architectural alternatives and consults recognized software-engineering and web-platform references without inventing performance statistics or product claims.

The review is organized around six questions. How should a resource-allocation domain be represented? Where should interactive state live? Which constraints can static types enforce? What guarantees does browser storage provide? How should the interface communicate status accessibly? How can tests distinguish a correct transition from a merely plausible screen? These questions map directly to the code and to the limitations that must be addressed before production adoption.

Software-engineering texts support decomposition, requirements traceability and verification [18, 19]. Next.js and React guidance explain the server/client boundary and component state [8, 9]. The TypeScript Handbook informs the interpretation of union types, interfaces and compile-time checks [10]. Web Storage guidance is relevant because the application persists its only saved copy in local storage [11]. WCAG and OWASP guidance supply evaluation lenses for accessibility and browser-resident data risks [12, 13]. Testing-tool documentation supports the separation of unit and browser evidence [14, 15].

The repository and installed Next.js documentation were inspected directly. External standards and official documentation in the bibliography are supplied as authoritative reader resources; this report does not claim a live retrieval or independent certification against every external document. The review links design principles to the observed implementation rather than presenting citations as proof that Parkline complies with all recommendations.

The resulting research gap is practical: a compact frontend prototype can demonstrate correct local parking transitions and safe capacity planning, but production coordination, durable history and identity remain unresolved. This boundary guides the comparative analysis in the following sections.

<!-- page: c2-manual | Chapter 2: LITERATURE REVIEW -->
## 2.2 Review of Existing Approaches and Related Guidance
### 2.2.1 Manual Registers and Spreadsheet-Based Tracking

A manual register can record a vehicle registration, entry time and assigned floor with almost no technical setup. It is understandable to an operator and can remain usable during a network outage. Its weakness is not that paper is inherently unusable, but that cross-record consistency depends on the operator: the count of occupied bays, the assignment list and the visible floor inventory are not automatically reconciled.

Spreadsheets improve search and counting, but a general-purpose grid does not by itself enforce the same transition rules as a domain model. A cell marked “available” can disagree with a separate sheet listing an active session. A row can be deleted while it still represents an occupied bay. Formulas and protected sheets may reduce these risks, yet the protection depends on the spreadsheet design and user discipline rather than on a single reusable transition function.

Parkline's distinction is its explicit operation boundary. `checkIn` simultaneously returns a changed bay collection and an extended session collection; `checkOut` releases the relevant bay and removes the selected active session. `resizeLevelBays` treats occupied and reserved bays as protected resources. This organization follows the broader principle of locating domain rules where state changes are authorized [18, 19]. It does not, however, make browser state transactional across devices.

**Table 2.1: General workflow alternatives and applicable trade-offs**

| Approach | Useful property | Limitation relevant to this project |
|---|---|---|
| Paper register | Low setup effort; human-readable record | Counts and bay assignments require manual reconciliation |
| Spreadsheet | Flexible tabulation and ad hoc search | Cross-sheet invariants require additional design discipline |
| Browser-local dashboard | Immediate visual feedback and reusable rules | State remains local and can be overwritten or cleared |
| Server-backed operations system | Can coordinate shared records and authorization | Requires backend design, deployment and operational controls |

These are category-level observations, not a measured comparison of named products. The current project deliberately occupies the third category so that interaction and domain correctness can be evaluated before introducing a shared service.

<!-- page: c2-components | Chapter 2: LITERATURE REVIEW -->
### 2.2.2 Component-Based Interactive Web Applications

React models an interface as a function of state. In Parkline, changing the selected location, floor, filter, search text or dialog mode causes the visible dashboard to be recalculated. This is preferable to manually editing unrelated DOM elements after each operator action: the metric cards, grid and session selector can be derived from the same state snapshot. The model is especially useful when an arrival must update several visible outputs together [9].

Next.js adds route composition, document metadata, build tooling and the server/client component boundary. The page route itself contains very little logic; it renders `ParkingDashboard`. That dashboard begins with the `use client` directive because it uses hooks, event handlers and browser local storage. The presence of a Next.js runtime does not mean the application has a parking API. There are no application route handlers or database calls in the reviewed source tree [5, 8].

The selected architecture keeps a simple deployment surface for a demonstration. It also concentrates many responsibilities in one component: form state, dialog coordination, local persistence, location switching and visual rendering. This is acceptable for a small MVP but creates a maintainability consideration. As the application grows, hooks or smaller components could separate persistence, planning and session interaction without relocating the business invariants into presentation-only code.

The review therefore supports a two-level separation. Pure domain helpers should describe valid parking transitions independently of React. UI components should translate operator input into helper calls, commit the returned state and present success or failure. This separation allows Vitest tests to inspect transition results without launching a browser, while Playwright verifies that labels, selectors and forms are connected correctly.

A client-side design also has a clear trust limit. All data and checks can be inspected or altered by the browser user. A future server must repeat validation and authorize operations; it cannot treat successful client validation as a security boundary. This remains an architectural requirement for future work rather than a feature of the current dashboard.

<!-- page: c2-types | Chapter 2: LITERATURE REVIEW -->
### 2.2.3 Typed Domain Models and Immutable Transformations

The TypeScript model uses union types to restrict `BayStatus` to `available`, `occupied` or `reserved`, and `BayKind` to `standard`, `ev` or `accessible`. Interfaces describe locations, levels, bays, sessions and activity. These declarations improve editor feedback and make the intended structure explicit. They also reduce accidental spelling differences between the domain module and dashboard rendering [2, 10].

Static types cannot prove every business rule. A `ParkingBay` interface permits optional `plate` and `since` fields, so the compiler does not establish that every occupied bay has a valid active session. Likewise, parsing local-storage JSON and asserting that it has a TypeScript shape does not validate its runtime content. This distinction is essential when discussing reliability: source-level types provide useful constraints, but untrusted or corrupted data still requires runtime schema checking.

The transition helpers favor immutable collection updates. `checkIn` maps the bay collection and appends a new session; `checkOut` maps the assigned bay and filters the session collection. Resizing returns the original bay array when no size change is needed, otherwise it returns filtered or extended arrays. This approach makes before-and-after states easy to compare in tests and helps React detect changed state references.

**Table 2.2: Compile-time assistance versus runtime guarantees**

| Concern | Assistance already provided | Additional runtime responsibility |
|---|---|---|
| Status vocabulary | String-literal union | Reject invalid restored JSON values |
| Record fields | Typed interfaces | Verify required values in imported or saved records |
| Registration shape | A string parameter | Normalize and match the required regular expression |
| Bay availability | Typed bay status | Check actual status at the transition boundary |
| Duplicate vehicle | Typed session array | Compare normalized plate against active sessions |
| Capacity bounds | Numeric parameter | Require an integer within 1–99 |

The lesson drawn from the review is that types, transition guards and tests complement one another. None replaces the others, and none supplies the multi-operator atomicity that would require a server-side authority.

<!-- page: c2-storage | Chapter 2: LITERATURE REVIEW -->
### 2.2.4 Browser Storage and Persistence Semantics

Web Storage provides an origin-scoped key/value interface accessible to browser JavaScript [11]. Parkline serializes its planning and operational data into a single JSON value under `parkline-garage-planning`. This is a practical choice for a classroom demonstration because it needs no database installation and allows an operator to revisit a plan in the same browser. It is not equivalent to durable shared storage.

A saved value belongs to the current browser profile and origin. Clearing site data can remove it. Private-browsing behavior, storage policies, quota limits or unavailable storage can affect it. A second device starts with its own data rather than inheriting the first device's plan. Multiple tabs can hold different React state snapshots and overwrite the same key without a transaction or conflict protocol. These properties directly limit the operational claims that can be made about the MVP.

The implementation restores data in an effect after initial render and writes later state changes in another effect. The load path performs only shallow checks for a non-empty locations collection and an operations object. The design needs stronger runtime validation and a versioned saved-data schema if it is to survive structural changes safely. It also needs carefully coordinated hydration and saving; Chapter 7 records a browser-test failure in which the selected added location was not retained after reload.

OWASP guidance is relevant because local storage is readable by scripts executing in the application's origin [13]. Vehicle registrations should therefore be treated as potentially identifying operational data, not as harmless configuration. The browser copy has no implemented access-control, retention or encryption policy. This report recommends fictional data for demonstrations and does not treat local storage as an appropriate location for credentials or payment details.

The review supports retaining local storage for prototype convenience while naming its limitations explicitly. Migration to a production service would require data ownership, authorization, transactional updates, schema migration, backup and conflict handling—not merely replacing `setItem` with a network call.

<!-- page: c2-accessibility | Chapter 2: LITERATURE REVIEW -->
### 2.2.5 Accessible Status-Oriented Interfaces

Parking interfaces must communicate more than color. A user should be able to identify the selected location, determine a bay's state and understand the effect of an action through labels, text and keyboard-operable controls. WCAG 2.2 provides a relevant framework for reviewing perceivability, operability and understandable feedback [12]. This report uses that framework as guidance, not as a claim of audited conformance.

Parkline uses native buttons, inputs and selects, associated form labels, accessible bay names and visible focus styling. A bay button's accessible name includes its ID, status and registration when present. Metric values and a textual legend supplement the bay colors. Success notices use a status role, while form errors use an alert role. These choices support non-visual interpretation of changes and make browser tests less dependent on fragile CSS selectors.

The implementation also exposes gaps that should not be concealed by the presence of ARIA attributes. Dialogs declare `role=dialog` and `aria-modal=true`, but the reviewed code does not implement a focus trap, Escape-key closing or restoration of focus to the invoking control. Floor tabs use tab roles without a complete roving-tabindex and arrow-key interaction pattern. At narrower widths, the location switcher is hidden. A mobile overflow check at 390 CSS pixels also failed in the documentation run.

### 2.2.6 Visual Design and Operational Honesty

The interface uses a coherent green, amber and neutral palette with spacing tokens, subtle panels and Lucide icons. However, operational language must remain aligned with data provenance. A “Live operations” label, an “8.4%” yesterday comparison or an EV station count can be mistaken for telemetry if the report describes them without qualification. In this MVP, those elements include static presentation content.

The review therefore recommends two complementary criteria: make actions understandable and make the source of displayed information clear. Accessible controls improve interaction quality, while honest labeling prevents a polished demonstration from being interpreted as a connected physical system.

<!-- page: c2-testing | Chapter 2: LITERATURE REVIEW -->
### 2.2.7 Automated Verification and Test Layering

Vitest runs the domain tests in a Node environment, using an alias that resolves `@` to the source directory. This makes it suitable for deterministic checks of counts, validation errors, immutable updates and fixture consistency. The existing nine tests cover key transition rules and managed-location creation. They are useful evidence, but they are not a complete boundary or property-based test suite [6, 14].

Playwright exercises the browser-facing application. The three existing scenarios switch garage locations, create and resize a location with a reload, and perform an arrival followed by departure. They verify that accessible labels and controls are connected to the intended behavior. The documentation also includes a separate capture script that executes sixteen supplemental checks and saves authentic screen images. These checks are identified separately so that they are not misrepresented as original repository tests [15].

A healthy verification strategy combines static checks, unit tests, browser workflows and human review. Linting can detect problematic patterns but cannot prove a session invariant. Type checking can validate source relationships but cannot establish that saved JSON is trustworthy. A production build confirms compilation and route generation but does not prove persistence behavior. Browser tests can expose integration failures that all three earlier checks miss.

**Table 2.3: Verification layers and the questions they answer**

| Layer | Principal question | Important boundary |
|---|---|---|
| ESLint | Does source conform to configured checks? | Not a functional test |
| TypeScript | Are declared source types consistent? | Does not validate storage JSON |
| Vitest | Do domain functions satisfy tested cases? | Does not inspect actual DOM interaction |
| Production build | Can the application compile and generate routes? | Does not prove runtime user journeys |
| Playwright | Do browser workflows produce expected outcomes? | Limited to exercised environment and cases |
| Review | Are semantics, privacy and scope honestly represented? | Requires judgment and additional evidence |

The review supports evidence-based reporting: a failed integration check is recorded as a finding, not overwritten by a statement that all tests passed because the unit suite was green.

<!-- page: c2-gaps | Chapter 2: LITERATURE REVIEW -->
## 2.3 Comparative Study of Related Approaches

**Table 2.4: Architectural comparison without vendor-specific claims**

| Criterion | Manual / spreadsheet workflow | Current Parkline MVP | Proposed shared system |
|---|---|---|---|
| Floor visibility | Operator-maintained representation | Derived floor totals and bay map | Shared authoritative inventory |
| Transition rules | Human discipline or custom formulas | Pure TypeScript guards | Server guards plus transactional constraints |
| Persistence | Physical files or document storage | One browser-local JSON value | Managed durable database and backups |
| Concurrent operators | Manual reconciliation | No safe coordination mechanism | Versioning, locking or transactional conflict handling |
| Identity | External organizational process | Static profile only | Authentication and role-based authorization |
| Reservation lifecycle | Manual booking process | Reserved samples only | Explicit create, expire, cancel and consume transitions |
| Verification | Manual review | Unit and browser checks | Broader integration, recovery and security testing |

## 2.4 Gaps Identified

The first gap is shared correctness: another operator can work from a different snapshot despite local duplicate guards. The second is durable history: departure deletes the active session instead of retaining a completed visit. The third is trust: browser edits are not authorized business actions, and the static profile does not identify an operator.

The fourth gap is evidence breadth. A small suite can demonstrate expected cases while leaving malformed storage, maximum capacity, date validity, accessibility interaction and repeated reload behavior insufficiently tested. Observed mobile and persistence failures show why the quality discussion must be separated from the implementation inventory.

## 2.5 Summary of Literature Review

The reviewed approaches justify the MVP's typed local model, component-driven interface and layered tests as an appropriate educational foundation. They also establish that a production parking platform needs additional architecture and operational controls. The next chapter converts that foundation into explicit requirements and acceptance criteria, preserving a distinction between current functionality, defects and future proposals.
