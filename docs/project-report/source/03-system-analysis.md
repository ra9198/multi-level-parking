<!-- page: c3-existing | Chapter 3: SYSTEM ANALYSIS -->
# CHAPTER 3 — SYSTEM ANALYSIS
## 3.1 Existing Workflow Analysis

System analysis identifies the information and rules needed to support parking operations. The baseline considered here is a generic manual or loosely connected tracking workflow, not a surveyed installation. In that baseline, an operator receives a vehicle, identifies a free bay, records a registration and later marks the vehicle as departed. A separate capacity plan may state how many spaces exist on each level. Unless those records are reconciled, a capacity summary can disagree with actual assignments.

Parkline makes these relationships explicit. A location groups its floors and operational collections. A level identifies a floor and its planned capacity. A bay identifies one physical resource within a level. An active session associates a normalized registration and vehicle description with one bay. Activity provides a lightweight recent-events display. This model supports analysis of each operation's preconditions and postconditions before discussing implementation details.

Three information scopes must remain separate. **Location scope** determines the relevant garage and duplicate-session collection. **Level scope** determines the current map, occupancy strip and departure selector. **Bay scope** determines whether a specific arrival or departure action is valid. Many interface errors can be understood as accidental mixing of those scopes, for example showing another floor's sessions or preserving an old floor after changing locations.

The project also has two distinct forms of change. Operational changes alter status and sessions without changing physical inventory. Planning changes alter inventory size while preserving existing non-available resources. This distinction drives both the design and the tests: an arrival conserves total capacity, whereas expansion increases total capacity while conserving occupied and reserved counts.

The analysis is derived from the checked-out code and executable workflows. It includes no claim that the named demonstration locations currently operate this application. The following sections translate the observed functions into a requirements specification and identify the conditions under which those functions remain safe.

<!-- page: c3-limitations | Chapter 3: SYSTEM ANALYSIS -->
## 3.2 Limitations of a Disconnected Tracking Workflow

A disconnected workflow can be adequate for a small, supervised operation, but it creates recurring opportunities for inconsistent records. The analysis below identifies general failure modes relevant to the prototype. It does not assign incident rates, average waiting times or financial losses because those quantities were not measured.

**Table 3.1: Workflow weaknesses, effects and MVP responses**

| Weakness | Potential effect | Response within Parkline's scope |
|---|---|---|
| Separate occupancy and session records | A bay appears free while a session still exists | Transition helpers return both updated collections |
| Unnormalized registration entry | Equivalent text is treated as different vehicles | Spaces and hyphens removed; letters uppercased |
| No explicit reserved state | Reserved inventory is offered to an arrival | Reserved bays are excluded from available choices |
| Manual capacity editing | Active assignments are accidentally removed | Non-available bays are protected during resizing |
| A single undifferentiated garage count | Operator cannot identify the relevant floor | Floor tabs, summaries and map filtering |
| Shared labels without scoped identity | Similar bay IDs from different sites are confused | Operations are indexed by location ID |
| Unclear save location | Operators expect unavailable cross-device data | Local-browser persistence is documented explicitly |
| Static dashboard decoration mistaken for facts | Unmeasured trends are interpreted as analytics | Report identifies decorative values and provenance |

The response column describes the intended implemented mechanism, not an assertion of complete reliability. For example, the storage mechanism exists, but a browser reload scenario failed during verification. Similarly, native controls support basic keyboard use, but dialog focus management remains incomplete. These distinctions prevent the requirements chapter from concealing defects beneath feature descriptions.

A production operation would also need procedures for lost tickets, disputed registrations, emergency closures, inaccessible spaces and overlapping operator actions. Those procedures cannot be inferred from this frontend code. They require stakeholder decisions before a server-side specification can be finalized.

The immediate analysis goal is therefore narrower: identify what the current system must maintain after a supported local action, then test that relationship with observable evidence.

<!-- page: c3-proposed | Chapter 3: SYSTEM ANALYSIS -->
## 3.3 Proposed System and Operator Workflow

For the academic project, the proposed system is the implemented Parkline MVP. The operator first selects a garage and inspects the overall capacity cards. The operator can then choose a floor, inspect bay colors and labels, search within that floor or filter by status. A bay click routes the operator toward the action appropriate to its state: available opens arrival, occupied opens departure and reserved displays an explanatory notice.

During arrival, the operator enters a Tamil Nadu registration and optional vehicle description, then chooses an available bay. The domain helper normalizes the registration, validates the format, verifies bay availability and rejects an already-active registration in the selected location. Only a successful result is committed to operational state. A new arrival activity item is prepended and a status message identifies the registration and bay.

During departure, the operator selects an active session from the current level. The domain helper finds that session, makes its bay available, clears its vehicle-specific fields and removes it from the active collection. A departure event is displayed. The prototype does not calculate a tariff, collect money, print a receipt or retain a completed-session ledger.

Capacity planning opens a separate management dialog. Existing floor capacities can be changed within allowed limits. The application computes prospective changes before committing updated levels and bays. An additional tab creates a new location with a trimmed name, one to ten floors and one to ninety-nine standard available bays per floor. The UI also rejects a duplicate name case-insensitively.

## 3.4 Advantages within the Defined Scope

The main advantages are coherent visual feedback, reusable local rules, deterministic bay allocation during resizing and a small deployment footprint. These properties make the application suitable for demonstrations and iterative design review. They are not evidence of reduced congestion, increased revenue or secure multi-user operation.

The system's key trade-off is simplicity versus authority. Keeping state in the browser lowers setup effort, but the browser cannot arbitrate competing operators. Future work must introduce a trusted service if the same physical inventory is to be managed by multiple clients.

<!-- page: c3-fr-operations | Chapter 3: SYSTEM ANALYSIS -->
## 3.5 Software Requirements Specification
### 3.5.1 Functional Requirements — Operational Dashboard

The following requirements describe observable behavior in the current design. “Implemented” denotes a source-backed feature. An associated test can still fail, and a missing test must not be inferred from the status. Each requirement has an identifier used again in the traceability and evaluation sections.

**Table 3.2: Operational functional requirements FR-01 to FR-10**

| ID | Requirement and acceptance condition | Principal implementation |
|---|---|---|
| FR-01 | Select a garage and display only its operational data | `changeLocation`; `operationsByLocation` |
| FR-02 | Show total, occupied, reserved and available counts whose sum reconciles | `occupancyForLevel`; total reduction |
| FR-03 | Select a floor and show its matching bay inventory | Level state and floor tabs |
| FR-04 | Search bay IDs or plates on the selected floor, case-insensitively | `filteredBays` calculation |
| FR-05 | Filter selected-floor bays by all/available/occupied/reserved | Status select and predicate |
| FR-06 | Normalize and validate registrations before starting a session | `normalizeTamilNaduPlate` |
| FR-07 | Reject an arrival unless the chosen bay exists and is available | `checkIn` bay guard |
| FR-08 | Reject a normalized registration already active in this location | `checkIn` session guard |
| FR-09 | Complete an active-session departure and release its bay | `checkOut`; `submitDeparture` |
| FR-10 | Display recent arrival/departure activity and outcome feedback | Activity list and status notice |

The dashboard derives most counts from bay records rather than trusting separately entered totals. This is an important requirement interpretation: the planned `capacity` field helps describe the floor plan, but the occupancy helper counts the actual records passed to it. Keeping those two representations synchronized is part of capacity planning.

FR-04 does not normalize spaces inside a search registration; it trims and lowercases the query and performs substring matching. FR-09's UI selector is limited to the current level even though the pure helper itself accepts a session ID from the collection supplied to it. These details are reflected in the user guide so that expected behavior matches the source.

<!-- page: c3-fr-planning | Chapter 3: SYSTEM ANALYSIS -->
### 3.5.2 Functional Requirements — Planning and Local Persistence

Planning requirements are separated from session operations because they change inventory structure. A capacity value is accepted only when it is an integer from one to ninety-nine. When reducing a floor, the resulting capacity must remain at least the count of occupied plus reserved bays. Existing protected IDs are retained even if the remaining numbering is no longer contiguous.

**Table 3.3: Planning and persistence requirements FR-11 to FR-18**

| ID | Requirement and acceptance condition | Principal implementation |
|---|---|---|
| FR-11 | Expand a floor with unused numbered standard available bays | `resizeLevelBays` addition branch |
| FR-12 | Shrink a floor by removing only available bays | `resizeLevelBays` removal branch |
| FR-13 | Preserve all occupied and reserved bay identities during resizing | Protected-count guard and removal filter |
| FR-14 | Create a location with 1–10 floors and 1–99 bays per floor | `createManagedLocation` |
| FR-15 | Reject a blank or duplicate location name in the UI | Helper trim check; UI name comparison |
| FR-16 | Save locations, operations and selected location in this browser | Persistence effect and storage key |
| FR-17 | Attempt to restore a saved plan on reload | Initial storage-reading effect |
| FR-18 | Reset floor, search, filter and session dialog when switching sites | `changeLocation` state resets |

FR-16 and FR-17 are deliberately written as local persistence behavior, not cloud synchronization. The recorded reload failure means that persistence needs further engineering and regression testing before it can be accepted as reliable. A successful supplemental reload check establishes only that one exercised sequence worked in that run.

Location creation does not support an arbitrary custom floor-naming scheme. The first floor is B1/Basement, the second is L1/Ground floor and later floors use incrementing level identifiers. New bays are standard; the planning form does not designate EV or accessible bays. Duplicate-name prevention is enforced in the dashboard rather than in the reusable creation helper, so direct helper callers must supply their own uniqueness policy.

These qualifications are part of the requirements baseline. They prevent a generic “manage locations” statement from implying edit, delete, special-bay assignment or multi-user uniqueness features that are absent from the implementation.

<!-- page: c3-nfr | Chapter 3: SYSTEM ANALYSIS -->
### 3.5.3 Non-Functional Requirements and Quality Expectations

Non-functional requirements describe desirable qualities and the evidence needed to evaluate them. Some are partially supported by the current design; others remain targets. The table avoids presenting an untested target as an achieved guarantee.

**Table 3.4: Quality requirements, evidence and current boundaries**

| ID | Quality expectation | Evidence and qualification |
|---|---|---|
| NFR-01 | Maintainable separation of rules and presentation | Pure helpers and shared types exist; dashboard remains large |
| NFR-02 | Predictable local state transitions | Nine unit tests pass for selected cases; broader boundaries untested |
| NFR-03 | Responsive presentation | CSS breakpoints exist; 390-pixel overflow check failed |
| NFR-04 | Understandable keyboard and assistive feedback | Native labels, focus styles and roles exist; no full accessibility audit |
| NFR-05 | Reliable reload restoration | Save/restore effects exist; one existing browser scenario failed |
| NFR-06 | Honest information provenance | Browser-local limitations documented; some UI labels remain decorative |
| NFR-07 | Protection of registration data | No authentication or retention policy; fictional demo data recommended |
| NFR-08 | Reproducible verification | Lockfile, scripts and report evidence retained |
| NFR-09 | Bounded planning input | Integer checks constrain floors and bays |
| NFR-10 | Safe concurrent physical allocation | Not satisfied by a browser-only architecture; future server required |

No response-time threshold is claimed as achieved because endpoint benchmarking was not performed and no parking API exists. Similarly, a successful build does not establish availability, backup recovery or cross-browser compatibility. Those qualities would need a deployment specification and an evaluation environment.

For this project, the strongest current evidence concerns understandable local behavior and domain rules. The weakest areas concern persistence reliability, narrow-screen interaction, runtime validation of restored data and shared operational authority. Making that distinction explicit helps prioritize improvements rather than treating all quality attributes as equally complete.

The requirements also carry a privacy implication. A registration may identify or be linked to a vehicle user. Even in a prototype, demonstrations should avoid unnecessary personal data, and a future production system should specify access, masking, retention and deletion policies before collecting real customer records.

<!-- page: c3-technical | Chapter 3: SYSTEM ANALYSIS -->
## 3.6 Feasibility Study
### 3.6.1 Technical Feasibility

The current prototype is technically feasible within a standard web-development environment. It requires Node.js 20.9 or newer according to the repository README, npm and a modern browser. The documentation run used Node.js 22.22.3 and npm 10.9.8. The dependency lockfile installed successfully, and the application passed linting, type checking and production compilation. These results establish that the reviewed revision can be built in the tested environment; they do not certify every operating system or browser.

The architecture is intentionally compact. A single application route renders a client dashboard. Data is represented as arrays of typed records, and domain helpers use filtering, mapping and bounded number allocation. A newly created location can contain at most 990 bays under the current limits. This upper bound makes the chosen collection-based design plausible for a demonstration, although no maximum-size performance benchmark was performed.

A production version would be a materially different engineering project. It would need an authoritative data store, authenticated requests, conflict handling and server-side validation. Existing pure functions provide a useful specification, but browser-only duplicate checks cannot simply be promoted to concurrency guarantees. Session and bay updates would need to be committed atomically, with a database constraint or equivalent mechanism preventing multiple active assignments to the same bay.

**Table 3.5: Technical feasibility assessment by capability**

| Capability | Feasibility within the reviewed MVP |
|---|---|
| Local demonstration and classroom review | Supported by successful installation and build |
| Domain-rule regression tests | Supported by the passing Vitest suite |
| Browser workflow verification | Available; one existing scenario failed in the recorded run |
| Single-device saved planning | Implemented but needs restoration-race and corruption hardening |
| Multiple synchronized operators | Not supported without a new authoritative backend |
| Sensor or gate integration | Requires hardware protocol, identity and failure-mode design |

The conclusion is therefore conditional: the local educational application is feasible and demonstrable, while production feasibility depends on additional requirements, infrastructure and safety controls not present in this repository.

<!-- page: c3-economic | Chapter 3: SYSTEM ANALYSIS -->
### 3.6.2 Economic Feasibility

The repository uses a standard open-source web stack and requires no paid parking API or database subscription for the current local demonstration. This lowers setup effort, but development, equipment, review and future support still have costs.

No currency-denominated return on investment is calculated because the project has no measured deployment baseline, operator-time study, revenue records or hosting quotation. The analysis therefore identifies cost categories and evidence needed for a future budget instead of inventing annual savings.

**Table 3.6: Economic feasibility categories and estimation inputs**

| Cost or benefit category | Current demonstration position | Evidence needed for a production estimate |
|---|---|---|
| Development tools | npm and editor-based workflow | Team licenses and organizational tooling policy |
| Hosting | Local production server used for evidence | Deployment size, bandwidth and availability target |
| Persistence | Browser storage only | Database capacity, backup and retention requirements |
| Identity and security | Not implemented | User count, authentication method and review effort |
| Operator training | User-guide walkthrough can be demonstrated | Number of staff, shift patterns and training duration |
| Equipment integration | No hardware expense within scope | Sensor/gate inventory, protocol and installation quote |
| Operational benefit | Better local visibility is demonstrable | Measured baseline and post-deployment task timings |

### 3.6.3 Operational Feasibility

The operator workflow uses recognizable actions: choose a garage, choose a floor, inspect a bay, check in, check out and plan capacity. Labels and confirmation notices support demonstration without a complex setup process. However, the interface has no authenticated role separation, so “garage manager” is a presentation label rather than an enforced permission.

Operational adoption would require procedures for incorrect entry, lost browser data, disputed departures, inaccessible bays, overrides and emergency shutdowns. The current dashboard does not define those procedures. It is therefore suitable for supervised demonstration and requirements discovery, but not as the sole record of a real garage's operations.

<!-- page: c3-validation | Chapter 3: SYSTEM ANALYSIS -->
## 3.7 Input Validation and Error Analysis

Validation occurs at two levels. Native HTML controls communicate required fields and numeric ranges. Domain helpers then enforce the important transition rules even when called independently of the form. This layered approach is necessary because presentation constraints alone can be bypassed or become inconsistent with other callers.

**Table 3.7: Validation rules and rejection behavior**

| Input or action | Rule | Rejection or handling |
|---|---|---|
| Registration | Remove spaces/hyphens, uppercase, match `^TN\d{2}[A-Z]{2}\d{4}$` | Explain required TN format |
| Arrival bay | Must exist and be available | Ask the operator to choose an available bay |
| Active registration | Must not already occur in the location's sessions | Report an existing active session |
| Departure session | Must exist in the supplied active list | Report that an active session was not found |
| Capacity | Integer, 1–99 | Explain the allowed bay range |
| Reduced capacity | At least occupied plus reserved count | Reject removal of protected inventory |
| Location name | Trimmed non-empty string | Ask for a location name |
| Duplicate location | Case-insensitive match blocked in UI | Report an existing name |
| Floors at creation | Integer, 1–10 | Explain the allowed floor range |

Several validation gaps remain. The domain helper does not validate the `startedAt` string before parsing it into a session identifier. Restored JSON is not checked against a complete runtime schema. The model does not enforce EV or accessible eligibility, because no eligibility data is collected. The helper that creates a location does not itself enforce a unique name across a location list.

The UI shows domain errors without committing successful-state updates. Nevertheless, user feedback and security are different concerns: an error message does not create authorization. A future server must validate the same business conditions against trusted current data and return a conflict response if another operator has already changed the bay.

The analysis recommends preserving precise error messages and adding tests for each rejection path, including boundary values, malformed timestamps and incompatible saved records. These recommendations are recorded as future quality work rather than silently added behavior.

<!-- page: c3-risk-trace | Chapter 3: SYSTEM ANALYSIS -->
## 3.8 Risk Assessment and Acceptance Traceability

Risks combine source review and recorded observations. Priorities are qualitative, not statistically estimated failure probabilities.

**Table 3.8: Principal risks and proposed mitigations**

| Risk | Current significance | Proposed mitigation |
|---|---|---|
| Reload loses the selected added-location plan | Observed in one existing browser scenario | Coordinate restoration and saving; add repeated reload regression |
| Mobile horizontal overflow | Observed at 390 CSS pixels | Identify wide descendants; test narrow viewports |
| Multiple tabs overwrite each other's state | Architectural limitation | Add synchronization or an authoritative server |
| Stored JSON has incompatible structure | Shallow validation only | Versioned schema and runtime validation |
| Vehicle registrations remain on a shared device | No access or retention controls | Use fictional demo data; define privacy policy |
| Static labels suggest live telemetry | Interpretation risk | Mark sample values and remove unsupported live claims |
| Dialog keyboard focus escapes | Missing focus-management implementation | Adopt a tested accessible dialog pattern |

**Table 3.9: Acceptance mapping from requirements to evidence**

| Requirement group | Evidence source | Acceptance interpretation |
|---|---|---|
| FR-02, FR-06 to FR-09 | Existing domain tests | Selected scenarios passed, not exhaustive proof |
| FR-11 to FR-14 | Resize and creation tests | Valid expansion, protection and creation cases passed |
| FR-01, FR-18 | Existing location-switch browser test | Passed in the recorded browser run |
| FR-14, FR-16, FR-17 | Existing add/resize/reload browser test | Failed after reload; remains an open issue |
| FR-04, FR-05, FR-10, FR-15 | Supplemental report browser checks | Exercised selected interactions, distinct from original suite |
| NFR-03 | Supplemental geometry assertion | Failed at 390 pixels; not accepted as overflow-free |

The analysis concludes with an actionable baseline: the model and core local transitions are demonstrable, while reliable persistence, narrow-screen behavior and production controls require further work. Chapter 4 shows how those observations arise from the actual architecture and data structures.
