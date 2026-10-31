<!-- page: c4-principles | Chapter 4: SYSTEM DESIGN -->
# CHAPTER 4 — SYSTEM DESIGN
## 4.1 Design Overview and Architectural Principles

System design translates the analysis into component boundaries, data structures and valid state changes. Parkline uses a browser-centered architecture with a small server-rendered application shell. The key design principle is to distinguish the physical inventory from active use of that inventory, then derive visible outputs from the current operational collections rather than maintain unrelated counters.

**Separation of concerns.** The route and root layout compose the application. `ParkingDashboard` handles interaction and presentation. `parking.ts` owns reusable transition rules. `parking-data.ts` defines fixtures and managed-location construction. `parking.ts` in the types directory declares the shared data contracts. This separation allows the domain module to be tested independently of the UI.

**Explicit state ownership.** The dashboard owns a locations collection and an `operationsByLocation` object. The selected location ID determines which bays, sessions and activity are in scope. The selected level determines which map and departure choices are displayed. Inputs and dialog selections are separate view state; they do not become operational records until a valid operation completes.

**Conservation of inventory.** Arrival and departure change status, not capacity. Occupancy summaries use the actual bay array. The invariant is total equals occupied plus reserved plus available. Planning is the controlled exception that changes total inventory while preserving non-available bays.

**Immutable transformations.** Helpers return new arrays or preserve an unchanged array rather than mutate the input collections in place. This makes operation results straightforward to inspect and reduces the risk that a failed operation partially changes React state. It is not a substitute for a database transaction across independent clients.

**Transparent boundaries.** The design contains no parking API, authentication service, live sensor feed or payment processor. Local storage is a browser copy of application state, not an authoritative multi-operator store. Architectural diagrams in this chapter reflect that boundary. Proposed production mechanisms are discussed only after the implemented model has been described.

These principles favor a teachable MVP. Improve runtime validation and persistence coordination first, then introduce server authority for shared operations.

<!-- page: c4-architecture | Chapter 4: SYSTEM DESIGN -->
## 4.2 System Architecture

The application has three practical execution areas: Next.js composition, interactive browser state and pure domain/data modules. The route at `/` imports the dashboard. The root layout sets page metadata, imports global styles and declares English as the document language. The dashboard is the only major client component and contains the hooks, browser effects and event handlers [5, 8].

![Figure 4.1: Implemented browser-centered application architecture](assets/diagrams/04-01-architecture.png)

The domain helpers are ordinary TypeScript functions. They receive the collections and identifiers required for an operation and return new collections or throw an error. They do not call React setters, local storage, HTTP endpoints or a database. This keeps the business rules reusable and enables focused tests.

Fixture creation belongs to a separate module. Four seed locations provide initial inventory, while `createManagedLocation` constructs a new empty location from validated input. After initialization, the dashboard's operational map is the working source for sessions, bays and activity. The location objects still contain nested collections, which means stored JSON contains some duplicated representations. Chapter 7 discusses the consistency risk.

The dashed persistence connection in the figure represents client effects rather than a remote service. A browser can save its current state and later attempt to restore it, but no process arbitrates changes from another browser. That distinction is central to the architecture's trust and concurrency limits.

<!-- page: c4-dfd0 | Chapter 4: SYSTEM DESIGN -->
## 4.3 Data Flow Diagrams
### 4.3.1 Level 0 — System Context

The context diagram treats Parkline as a single local application. The external actor is an operator who supplies manually observed vehicle and bay information. The application responds with occupancy summaries, map states, validation messages and activity. The only persistent store in the implemented design is browser local storage.

![Figure 4.2: Level 0 data flow and the actual system boundary](assets/diagrams/04-02-context-dfd.png)

Operator input includes location selection, floor selection, search text, status filters, registration, vehicle description, selected bay, selected active session and planning values. The output includes both stateful facts and presentation feedback. For example, the occupied count is derived from bay records, while a confirmation message explains the result of the latest action.

Local storage is shown separately because it survives a normal page lifecycle, but it remains inside the browser's operational environment. It is not an independent organization or a network backend. A developer-tool edit to the saved value is outside the intended operator workflow yet is possible because the browser owns the data.

The absence of other actors is deliberate. There is no authenticated administrator, customer account, payment gateway, sensor controller or transport-authority validation service in the reviewed code. Adding such an actor would create new trust boundaries and requirements. The current context diagram therefore supports accurate scoping rather than the visual appearance of a larger connected platform.

<!-- page: c4-dfd1 | Chapter 4: SYSTEM DESIGN -->
### 4.3.2 Level 1 — Functional Decomposition

The main process decomposes into inspection, session start, session end, inventory planning and rendering. Inspection changes view state but does not alter a bay. Session operations change bays and active sessions. Planning changes location structure and inventory. Rendering derives cards, floor summaries and map output from the selected scope.

![Figure 4.3: Level 1 functional decomposition and local data stores](assets/diagrams/04-03-level-one-dfd.png)

The working state store contains `garageLocations`, `operationsByLocation` and the relevant selections. This is a conceptual data-flow store, not a separate service. The operational map is keyed by location ID so that switching locations retrieves a different collection rather than resetting all garages to a common inventory.

The rendering process does not independently persist a count. It computes selected-floor statistics and reduces statistics across the selected location's levels. This reduces the risk of an occupied counter drifting away from the bay records. Search and filter predicates affect only which current-floor bays are shown; they do not change the statistics or the underlying inventory.

The local-storage connection is an effect after state changes. That placement keeps storage operations out of pure transition helpers, but it introduces ordering and recovery responsibilities at the UI boundary. The existing implementation needs stronger coordination of loading and writing, as shown by the reload test finding. The diagram describes intended data movement without asserting that every restoration sequence is reliable.

<!-- page: c4-dfd2 | Chapter 4: SYSTEM DESIGN -->
### 4.3.3 Level 2 — Vehicle Arrival

Arrival is expanded because it combines user input, validation, resource allocation and feedback. The domain function first looks up the target bay and normalizes the registration. It then verifies the bay's available state and checks for an equivalent active registration. Only after those guards does it construct a new active session and changed bay array.

![Figure 4.4: Arrival validation, collection transformation and UI commit](assets/diagrams/04-04-arrival-dfd.png)

The session stores the bay and level identifiers, normalized plate, trimmed vehicle description and supplied start timestamp. A blank description becomes “Vehicle”. The bay retains its physical kind while gaining occupied status, plate and `since` timestamp. The dashboard commits the returned collections together in its location operation state and prepends an arrival activity item.

Any thrown error is displayed as feedback while the successful-state update is skipped. The function does not reserve a bay while the form is open, and the browser copy is not protected against another tab changing the same resource. Consequently, the diagram represents a local transition, not a concurrent reservation or transactional server workflow.

<!-- page: c4-usecase-diagram | Chapter 4: SYSTEM DESIGN -->
## 4.4 Use Case Diagram and Actor Specification

The implemented actor is an operator using the dashboard. The visible profile says “Garage manager”, but there is no sign-in or permission check. All supported actions are available to a user who can open the application. The diagram therefore uses one actor rather than inventing authenticated administrator and customer roles.

![Figure 4.5: Operator use cases within the local MVP boundary](assets/diagrams/04-05-use-cases.png)

UC-01 covers observing location and floor occupancy. UC-02 covers current-floor search and status filtering. UC-03 starts a session only after the registration and bay guards pass. UC-04 ends a selected active session. UC-05 changes planned bay counts while preserving protected resources. UC-06 creates a new location or changes the selected garage.

Viewing reserved inventory is included within inspection. There is no use case for making a reservation because no such transition is implemented. Similarly, EV and accessible icons describe bay kind; the application does not verify driver eligibility or manage charging sessions.

The use cases define the current educational demonstration. A future production actor model should be determined through stakeholder requirements, such as gate operator, capacity planner, supervisor and auditor. Those responsibilities cannot safely be inferred from the present static profile.

<!-- page: c4-uc-arrival | Chapter 4: SYSTEM DESIGN -->
### 4.4.1 Detailed Use Case — Inspect and Start a Session

Inspection provides the context for arrival. The operator should confirm the selected location and floor before assigning a vehicle. Clicking an available bay preselects that bay in the arrival dialog. The global “New arrival” button chooses the first available bay on the current level when possible, while the dialog's selector lists available bays from the selected location.

**Table 4.1: Use case UC-03 — Check in a vehicle**

| Element | Specification |
|---|---|
| Primary actor | Operator; no authenticated role is enforced |
| Trigger | “New arrival” button or click on an available bay |
| Preconditions | Selected location exists; target bay is available; plate meets TN policy |
| Input | Registration, optional vehicle description, bay ID |
| Main step 1 | Open arrival dialog and preselect a suitable bay |
| Main step 2 | Normalize registration by removing spaces/hyphens and uppercasing |
| Main step 3 | Reject a missing/non-available bay or an active duplicate registration |
| Main step 4 | Create a session and map the chosen bay to occupied |
| Main step 5 | Commit collections; prepend arrival activity; show confirmation |
| Success postcondition | One additional active session; occupied +1; available −1 |
| Conserved values | Total capacity, reserved count, bay ID and bay kind |
| Failure postcondition | Domain exception is shown; successful-state commit is skipped |
| Persistence boundary | Later effect saves locally; no server transaction or gate action |

An important alternate flow is a validly formatted registration that is already active. The UI does not close the dialog; it shows the duplicate message. Another alternate flow is a bay that is no longer available in the collection supplied to the helper. The helper rejects it even if the form was opened earlier with that bay selected.

These guards protect consistency only within the input snapshot. A future backend must check current authoritative state and commit the bay/session association atomically. The local use case remains valuable as an executable specification for that future transaction.

<!-- page: c4-uc-departure | Chapter 4: SYSTEM DESIGN -->
### 4.4.2 Detailed Use Case — Complete a Departure

Departure is initiated by the top-level “Check out” action or an occupied bay. The dashboard tries to select a session associated with the clicked bay, then falls back to a session on the current level. The visible selector lists only sessions whose `levelId` matches the selected level. An operator must switch floors to check out a session from another level through this UI.

**Table 4.2: Use case UC-04 — Check out an active session**

| Element | Specification |
|---|---|
| Primary actor | Operator |
| Trigger | “Check out” action or occupied-bay click |
| Preconditions | An active session is available on the current level |
| Input | Selected active session ID |
| Main step 1 | Resolve the selected session from current location operations |
| Main step 2 | Call `checkOut` with the current bay and session collections |
| Main step 3 | Mark the session's bay available and clear plate/since fields |
| Main step 4 | Remove the active session from the returned session list |
| Main step 5 | Prepend departure activity, show confirmation and close dialog |
| Success postcondition | Occupied −1; available +1; session no longer active |
| Conserved values | Total inventory, reserved count and physical bay kind |
| No-session path | Display a hint and disable completion on a level with no sessions |
| Missing-ID path | Reject an unknown active session |
| Explicit exclusions | No fee, payment, receipt or completed-session archive |

The helper assumes a reasonably consistent input model. It finds the session but does not independently throw if its referenced bay is missing; mapping an unrelated bay list would simply leave that list unchanged while removing the session. This is a useful runtime-validation and test gap, not a behavior to hide behind the ideal use-case description.

A future model should record departure time and preserve a completed session rather than delete its historical record. It should also validate the bay/session relationship within a transaction. Those changes are proposals and are not included in the current use case.

<!-- page: c4-uc-capacity | Chapter 4: SYSTEM DESIGN -->
### 4.4.3 Detailed Use Cases — Capacity and Location Planning

UC-05 accepts draft capacities for all current levels. The save handler calculates prospective bays and levels before committing them. Any error prevents the final update. Within each floor, the helper rejects a target below the protected count, removes highest-numbered available bays when shrinking and fills the lowest unused numeric suffixes when expanding.

![Figure 4.6: Protected capacity-resizing decision workflow](assets/diagrams/04-11-capacity-workflow.png)

UC-06 creates a trimmed, non-blank location name with validated floor and per-floor counts. The dashboard separately rejects case-insensitive duplicate names. A successful creation adds both a location object and an operational-map entry, selects the new location, resets the current floor/search/filter and displays its total capacity. Every new bay begins as standard and available; sessions and activity begin empty.

Capacity changes do not add or remove floors from an existing location. New-location creation is the only implemented way to choose a different floor count. A reduction can leave gaps in bay numbering because protected bays retain their original identities. That is an intentional safety consequence, not an instruction to renumber active resources.

<!-- page: c4-class | Chapter 4: SYSTEM DESIGN -->
## 4.5 Object-Oriented and Behavioral Models
### 4.5.1 Domain Interface / UML Class View

The source uses TypeScript interfaces rather than class instances with methods. The UML-style view below is therefore a structural model of record shapes, not a claim that the application instantiates an object-oriented service hierarchy. Locations aggregate arrays of levels, bays, sessions and activity [2].

![Figure 4.7: Actual TypeScript domain records and location-scoped references](assets/diagrams/04-06-domain-model.png)

A level has a stable identifier and separate presentation labels. A bay has its own identifier and `levelId`, while a session stores both `bayId` and `levelId` for display and filtering. Activity references a bay by text and stores a human-readable time label. These relationships are resolved by array lookup rather than database foreign keys.

The model's optional fields provide flexibility for available and reserved bays, but the interface alone does not enforce a state-dependent record shape. For example, TypeScript does not require an occupied bay to carry a plate. A stronger future design could use discriminated unions or a runtime schema to express that relationship. It would still require consistency checks between a bay and its session collection.

<!-- page: c4-sequence | Chapter 4: SYSTEM DESIGN -->
### 4.5.2 Sequence Model — Arrival and Local Save

The sequence diagram separates operator interaction, dashboard orchestration, pure domain processing and browser persistence. It highlights that saving is an effect following a state change, not a prerequisite that the domain helper awaits.

![Figure 4.8: Arrival sequence from form submission to local snapshot](assets/diagrams/04-07-arrival-sequence.png)

The dashboard generates a current ISO timestamp for the UI-driven arrival and supplies it to `checkIn`. The helper constructs an identifier using the bay ID and parsed time. If validation succeeds, the dashboard updates the selected location's operations, adds activity and closes the dialog. The user sees a confirmation identifying both plate and bay.

If normalization or a transition guard fails, an exception returns control to the dashboard's catch block. No successful collection update is performed. The same structural pattern applies to departure, although departure resolves a session rather than validates a new plate.

The storage effect can fail independently of the visible transition. Its catch path logs a warning, and the UI does not roll back the action or present an explicit save-failure banner. As a result, a successful check-in notice should not be interpreted as proof that durable persistence succeeded. A future implementation should define persistence status, recovery and authoritative commit semantics explicitly.

<!-- page: c4-state | Chapter 4: SYSTEM DESIGN -->
### 4.5.3 Bay State Machine and Invariants

The operational state machine is deliberately small. `checkIn` changes available to occupied, and `checkOut` changes the session's bay to available. Reserved is represented in fixtures and display logic, but there is no implemented reservation lifecycle. Drawing a reserve/cancel arrow would therefore misstate the code.

![Figure 4.9: Implemented bay-state transitions and reserved-state boundary](assets/diagrams/04-08-bay-state-machine.png)

For a level with total T, occupied O and reserved R, the helper derives available A as T − O − R. Occupancy percentage is round(100 × O / T), with zero used when T is zero. Reserved bays do not contribute to parked-vehicle occupancy. This distinction makes a floor with many reservations appear less occupied while still correctly limiting available bays.

The intended consistency invariant is that each active session refers to one occupied bay within its location, and a normalized plate occurs at most once in that location's active sessions. The helper guards support these invariants for valid input snapshots. They do not repair arbitrary inconsistent data restored from storage, nor do they coordinate simultaneous clients.

Bay kind is independent of the state machine. An accessible or EV bay remains that kind after arrival or departure. Capacity expansion creates standard bays only, while shrinking can remove any available bay kind because no separate protection rule for accessible or EV inventory is implemented. A production planning policy would need to define such protection explicitly.

<!-- page: c4-er | Chapter 4: SYSTEM DESIGN -->
## 4.6 Conceptual Entity Relationships

The project has no relational database. The following ER-style view explains logical relationships already represented in arrays and identifiers. It should not be read as an implemented SQL schema, a migration plan or evidence of enforced database constraints.

![Figure 4.10: Conceptual relationships of the in-memory parking model](assets/diagrams/04-09-conceptual-er.png)

A location contains many levels and bays. A level can be associated with many bays. A bay is intended to have zero or one active session, while a session identifies one bay and one normalized registration. Activity is a lightweight local collection referencing a bay; it is not a complete immutable event ledger.

Identity is scoped carefully. Seeded locations reuse identifiers such as B1 and B1-01. The location ID selects the collection in which those identifiers are meaningful. A production relational design would need either globally unique keys or composite uniqueness that includes location. Creating a single global bay table keyed only by B1-01 would incorrectly collapse separate garage inventories.

Session IDs are also demonstration identifiers rather than distributed unique IDs. Initial fixtures and newly generated sessions use different construction patterns. A future authoritative service should choose an identity strategy and validate foreign-key relationships rather than assume browser-generated strings are globally collision-free.

The conceptual diagram is useful because it exposes missing guarantees without pretending they already exist. It also gives a foundation for future database design after operational policies, retention and concurrency requirements are agreed.

<!-- page: c4-dict-location | Chapter 4: SYSTEM DESIGN -->
## 4.7 Data Dictionary of Implemented Records
### 4.7.1 ParkingLocation and ParkingLevel

The data dictionary records exact interface field names and their current interpretation. It is a TypeScript/in-memory dictionary, not a table specification for an existing database. All identifiers are strings, capacities are numbers and collections are JavaScript arrays.

**Table 4.3: Data dictionary — location and level records**

| Record / field | Type | Meaning and current constraint |
|---|---|---|
| ParkingLocation.id | string | Key used to select operational collections; new values use current time |
| ParkingLocation.name | string | Display name; new names trimmed and checked for non-blank input |
| ParkingLocation.levels | ParkingLevel[] | Floor definitions and planned capacities |
| ParkingLocation.bays | ParkingBay[] | Nested initial/planning inventory; operational map may be newer |
| ParkingLocation.sessions | ParkingSession[] | Nested sessions; working sessions are read from operations map |
| ParkingLocation.activity | ParkingActivity[] | Nested activity; working activity is read from operations map |
| ParkingLevel.id | string | B1 or L-number in managed creation; scoped to a location |
| ParkingLevel.label | string | Compact tab label such as B1, 01 or 02 |
| ParkingLevel.name | string | Basement, Ground floor or generated Level name |
| ParkingLevel.capacity | number | Planned bay count; validated as 1–99 during supported changes |

The distinction between nested location collections and `operationsByLocation` matters. Session handlers update the operational map, not every nested copy inside `garageLocations`. Capacity saving updates nested location levels and bays and also changes the operational map's bays. Saving both representations can therefore retain a mixture of newer operational data and older nested values.

The dashboard normally reads the operational map for the selected location, falling back to nested collections when no entry exists. The fallback is convenient but raises consistency questions. A future format should define one canonical source and derive redundant views.

At creation, floor count is validated once and used to generate all levels and bays. Existing locations do not expose a floor-count editing operation, so the dictionary should not be interpreted as implying arbitrary structural editing.

<!-- page: c4-dict-bay | Chapter 4: SYSTEM DESIGN -->
### 4.7.2 ParkingBay, BayStatus and BayKind

The bay is the core resource record. It combines identity, floor association, current availability state and a physical classification. Optional vehicle fields are present when fixtures or successful arrivals populate them and are cleared during departure.

**Table 4.4: Data dictionary — bay fields and enumerated values**

| Field or type | Type / values | Interpretation |
|---|---|---|
| ParkingBay.id | string | Location-scoped floor ID plus two-digit bay suffix |
| ParkingBay.levelId | string | Identifier of the associated floor |
| ParkingBay.status | BayStatus | Operational availability category |
| ParkingBay.kind | BayKind | Physical classification, separate from status |
| ParkingBay.plate | optional string | Vehicle registration shown for occupied seed/arrival records |
| ParkingBay.since | optional string | ISO timestamp used for the current occupancy start |
| BayStatus | available | Can be selected for an ordinary arrival |
| BayStatus | occupied | Represents a currently parked vehicle |
| BayStatus | reserved | Unavailable sample reservation; no lifecycle controls |
| BayKind | standard | Default kind, including all newly created bays |
| BayKind | ev | Visual EV indicator; no charging integration |
| BayKind | accessible | Visual accessible indicator; no eligibility enforcement |

The ID suffix allocation rule is bounded by 99. Expansion scans candidate suffixes from one upward and skips those already in use. Shrinking sorts available bays by descending numeric suffix and removes the required number. The algorithm preserves protected bay IDs and does not compact numbering after a reduction.

Optional fields do not amount to a state-dependent schema. An externally modified saved record could claim occupied status without a plate or point to an unknown level. Such states are not created by the intended successful helper paths, but the restoration code does not comprehensively reject them. Runtime validation is therefore a material future requirement.

The current resize policy does not preserve a minimum number of EV or accessible bays. It protects status, not kind. That is acceptable as a documented prototype rule but requires stakeholder review before any real capacity-planning decision is based on the application.

<!-- page: c4-dict-session | Chapter 4: SYSTEM DESIGN -->
### 4.7.3 ParkingSession and ParkingActivity

An active session represents present occupancy, not a permanent visit history. Checkout removes the session from the active array. Activity provides a recent-event display, but it lacks the structured timestamps and actor attribution needed for an audit ledger.

**Table 4.5: Data dictionary — active session record**

| Field | Type | Meaning |
|---|---|---|
| id | string | Session selector key; new IDs contain bay ID and parsed start time |
| bayId | string | Bay occupied by the session within the selected location |
| levelId | string | Floor used for display and departure filtering |
| plate | string | Normalized registration; locally unique among active sessions |
| vehicle | string | Trimmed description or fallback “Vehicle” |
| startedAt | string | Supplied ISO-style start timestamp; helper does not validate it |

**Table 4.6: Data dictionary — recent activity record**

| Field | Type / values | Meaning |
|---|---|---|
| id | string | UI list key; new event IDs use current time |
| type | arrival / departure / reservation | Determines event label and icon |
| plate | string | Registration or sample display text such as “Reserved” |
| bayId | string | Bay reference displayed beside the event |
| time | string | Human-readable text such as “Just now” or “2 min ago” |

The activity panel shows only the first five items using an array slice, although the underlying collection can continue growing. New events are prepended, so recent user operations displace older items from the visible list without deleting them from storage. There is no pagination or historical export.

A future history model should separate a structured event time from its localized display label, record actor identity and preserve completed sessions. It should also define retention and deletion policies for registration data. These are proposed changes, not additional fields already present in the current interfaces.

<!-- page: c4-storage | Chapter 4: SYSTEM DESIGN -->
### 4.7.4 Browser Storage Structure and Restoration

The storage key contains one serialized object with locations, operational collections and the selected location ID. The selected floor, search text and status filter are not persisted; restoration chooses the saved location's first level. The schema has no explicit version field.

```json
{
  "locations": ["ParkingLocation records"],
  "operationsByLocation": {
    "riverside": { "bays": [], "sessions": [], "activity": [] }
  },
  "locationId": "riverside"
}
```

![Figure 4.11: Current local-storage load/write lifecycle and review concern](assets/diagrams/04-10-storage-lifecycle.png)

The illustration is schematic: real saved arrays contain full records, not the descriptive string in the example. The read effect catches parse failures and attempts to remove the key. The write effect catches save failures and logs a warning. Neither path is a complete recovery protocol, and shallow shape checks cannot establish referential consistency. Restoration/write ordering is a review concern supported by the failed browser reload scenario.

<!-- page: c4-input-output | Chapter 4: SYSTEM DESIGN -->
## 4.8 Input and Output Design

Input design constrains operator entry while preserving clear error recovery. Forms use native required fields and numeric bounds, but business rules remain in domain helpers. An arrival's registration input permits common spacing within a maximum length, then normalizes before validation. Vehicle description is optional. Planning values are converted from string drafts into numbers only when the form is submitted.

**Table 4.7: Input controls, derived outputs and interpretation**

| Area | Input / control | Output and scope |
|---|---|---|
| Garage selection | Native location select | Selected site's totals, first floor and operations |
| Floor selection | Tabs and next-level button | Current-floor map and active departure choices |
| Search | Trimmed lowercase substring | Current-floor ID/plate matches only |
| Status filter | all / available / occupied / reserved | Current-floor matching bays; no data mutation |
| Arrival | Plate, description, available-bay select | Occupied bay, active session and arrival notice |
| Departure | Active session from current level | Released bay and departure notice |
| Capacity | Integer draft for each existing level | Updated planned capacities and actual bay inventory |
| New location | Name, floor count, bays per floor | New empty location and total-capacity preview |

Output design distinguishes derived values from decoration. Total, occupied, available and reserved cards derive from current bay records. Floor occupancy percentage excludes reserved bays. The EV charging note, yesterday comparison, next-arrival message, manager name and displayed date include static content. They are not historical analysis or connected telemetry.

The empty-search state explicitly says that no bays match the search. A reserved-bay click reports the reserved state rather than opening an arrival. Success notices identify the affected registration or capacity, and validation errors remain close to the corresponding form. These patterns support operational clarity, while the static labels remain a transparency improvement opportunity.

<!-- page: c4-ui | Chapter 4: SYSTEM DESIGN -->
## 4.9 User Interface Design System

The interface uses a neutral canvas, white panels, green primary actions and amber reservation accents. Its source of visual truth is `src/app/globals.css`, with Tailwind directives available through the build pipeline. Many application-specific components are styled through ordinary CSS class selectors rather than large inline utility strings.

**Table 4.8: Implemented visual tokens and layout conventions**

| Token or convention | Source value / behavior | Purpose |
|---|---|---|
| Main ink | `#1b2825` | Primary text |
| Soft ink | `#485752` | Supporting text |
| Muted | `#88938f` | Secondary labels |
| Canvas | `#f5f7f5` | Dashboard background |
| Paper | `#ffffff` | Cards and panels |
| Primary green | `#157b5b` | Main actions and active navigation |
| Bright green | `#46c692` | Accent line and positive details |
| Amber | `#c58229` | Reservation-related emphasis |
| Radius | `10px` base token | Consistent panel corners |
| Desktop sidebar | 238-pixel base width | Branding, garage selector and navigation |
| Bay grid | Six columns normally; four at narrow width | Compact visual inventory |
| Responsive breakpoints | 1150, 900 and 620 pixels | Reduce sidebar and stack panels |

The primary actions are grouped at the page heading: planning, checkout and arrival. The parking map is the main working panel, while floor summaries and recent activity provide context. Native selects are used where a set of choices must remain explicit, such as location, status and session.

The bay grid is a visual inventory, not an accurate architectural drawing of a physical floor. It has no coordinate geometry, obstruction data or navigation routing. The one-way lane graphic is a visual cue rather than a model of validated circulation. This distinction matters if the application is later extended into genuine facility planning.

Animations and hover effects support feedback, and a reduced-motion media query shortens animation and transition durations. These styling provisions improve presentation but do not by themselves demonstrate accessibility conformance or mobile usability; the recorded overflow finding remains open.

<!-- page: c4-accessibility | Chapter 4: SYSTEM DESIGN -->
## 4.10 Accessibility, Responsive Design and Design Limitations

The design includes useful foundations: semantic buttons, native selects, associated labels, visible focus outlines, text alternatives in bay names, status feedback and alert-marked form errors. Floor and planning controls declare tab semantics, and dialogs declare modal roles with labelled headings. These are source-backed implementation facts, not a complete accessibility audit.

**Table 4.9: Accessibility and responsive review by interaction**

| Interaction | Implemented support | Remaining limitation |
|---|---|---|
| Bay inspection | Accessible name includes ID/status/plate | Color contrast and screen-reader experience not comprehensively audited |
| Forms | Visible labels, required fields and native controls | Error association could be more explicit |
| Dialogs | Dialog role, modal flag, autofocus on selected fields | No focus trap, Escape close or focus return implementation |
| Floor tabs | Tablist and selected-state semantics | No full arrow-key / roving-tabindex pattern |
| Feedback | Status notices and alert errors | Save failure is only a console warning |
| Motion | Reduced-motion stylesheet | No user study of animation effects |
| Narrow layout | Panels stack; sidebar collapses; four-column bay grid | Location selector hidden; 390-pixel overflow observed |

The mobile observation is specific and measurable: in the documentation run, a 390-pixel viewport had a document width of 457 pixels. The heading's primary action button extended to the right edge of that wider document. The report preserves the captured mobile screen and does not label the interface “fully responsive” solely because media queries exist.

The design also contains intentionally limited controls. Notification, account and activity-options buttons do not implement full menus or back-office functions. Sidebar links navigate to sections of the same page rather than separate management routes. These choices are acceptable within the MVP if they are described accurately.

The next design iteration should prioritize dialog interaction, narrow-width action wrapping, visible location selection and honest sample-data labeling. A later shared-service iteration should then add authorization, server authority and durable history. Keeping those stages separate avoids treating visual cleanup as a substitute for operational safety.
