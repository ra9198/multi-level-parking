<!-- page: c6-inventory | Chapter 6: SYSTEM IMPLEMENTATION -->
# CHAPTER 6 — SYSTEM IMPLEMENTATION
## 6.1 Implementation Overview and Source Inventory

The implementation is intentionally small enough to trace an operator action from the screen into a domain function. The source inventory below identifies the files that actually contribute to the parking application. It does not imply separate deployable services or modules beyond the Next.js application.

**Table 6.1: Application and test source inventory**

| Source path | Responsibility |
|---|---|
| `src/app/page.tsx` | Home route rendering `ParkingDashboard` |
| `src/app/layout.tsx` | Root document, metadata and stylesheet import |
| `src/app/globals.css` | Design tokens, component styles and breakpoints |
| `src/components/parking-dashboard.tsx` | State, derived view, handlers, dialogs and output |
| `src/types/parking.ts` | Five record interfaces and status/kind unions |
| `src/lib/parking.ts` | Occupancy, resizing, registration, arrival and departure helpers |
| `src/lib/parking-data.ts` | Seed inventory and managed-location creation |
| `src/lib/parking.test.ts` | Nine existing domain/fixture test cases |
| `e2e/parking-workflows.spec.ts` | Three existing operator browser scenarios |

The five interfaces are `ParkingLevel`, `ParkingBay`, `ParkingSession`, `ParkingActivity` and `ParkingLocation`. Two supporting union aliases define the status and kind vocabularies. The dictionary in Chapter 4 uses those exact names, and the pure domain functions consume these shared record contracts rather than separate UI-specific copies.

A typical interaction has four stages: a control updates view state, a form handler supplies current operational collections, a helper computes a valid result or throws, and the dashboard commits the result and feedback. Local saving is a subsequent effect. The remainder of the chapter follows that flow before presenting actual output screens.

The screenshots were captured from the built application, not generated as design mockups. The browser-evidence source records the source commit, Chromium version, viewports and individual supplemental assertion outcomes. Sample registrations and location names remain demonstration data.

<!-- page: c6-initialization | Chapter 6: SYSTEM IMPLEMENTATION -->
## 6.2 Application Initialization and State Composition

The home route returns the dashboard without business logic. At initial client state construction, `garageLocations` uses the seed locations and `operationsByLocation` is built by mapping each location ID to its bays, sessions and activity. The initially selected location and level are the first seeded entries. Search is empty, the status filter is “all” and no session or planning dialog is open.

The storage-reading effect attempts to restore a saved JSON object. When its shallow conditions pass, it schedules updates to locations and operational collections, finds the saved selected location or falls back to the first saved location, and selects that location's first level. It does not restore the last floor, search query or filter. The readiness flag is enabled after the load attempt.

The dashboard then resolves a selected location and operations. It prefers the operational map's current record; if no entry exists, it falls back to the nested collections in the selected location. The selected level is looked up in that location, and the current-level bay list is filtered from the working bay array. Because the selected-level lookup assumes success, malformed restored records can cause problems that compile-time types do not prevent.

### 6.2.1 View State versus Operational State

View state includes dialog mode, selected bay/session, text inputs, filter, search and planning drafts. Operational state includes bays, sessions and activity. Keeping these categories separate means that opening a form or typing a plate does not itself allocate a bay. Only a successful submit handler changes the operational collection.

The management dialog uses a different state variable from the session dialog. Opening planning closes the session dialog, and changing location closes the session dialog and clears selected view conditions. Native controls keep draft strings until submission, when number conversion and helper validation occur.

This state composition is compact but complex enough to justify future extraction into dedicated hooks and smaller components. Any refactor should preserve the distinction between uncommitted drafts and authoritative local operation results.

<!-- page: c6-seeds | Chapter 6: SYSTEM IMPLEMENTATION -->
## 6.3 Seed Inventory and Managed Location Construction

The default floor definitions are B1/Basement, L1/Ground floor and L2/Upper deck, each with 24 bays. The base fixture assigns selected IDs to occupied or reserved status, while unspecified bays are available. Accessible and EV sets determine physical kind independently. Occupied fixtures receive registrations and generated start times, then become active-session records.

Additional locations use a deterministic arithmetic status roll based on bay index and a seed value. Their registrations are constructed in the accepted TN pattern. This supplies independent sample inventories without a network request. It does not model actual occupancy at the named sites.

**Table 6.2: Initial inventory counts derived from the seed code**

| Location / floor | Total | Occupied | Reserved | Available |
|---|---:|---:|---:|---:|
| Riverside Centre — B1 | 24 | 10 | 2 | 12 |
| Riverside Centre — L1 | 24 | 14 | 2 | 8 |
| Riverside Centre — L2 | 24 | 10 | 2 | 12 |
| Riverside Centre — all floors | 72 | 34 | 6 | 32 |
| Marina Mall, Velachery | 72 | 39 | 11 | 22 |
| VR Mall, Anna Nagar | 72 | 37 | 12 | 23 |
| Phoenix Mall, OMR | 72 | 37 | 12 | 23 |

New locations follow a different path. `createManagedLocation` trims and validates a name, checks integer floor and bay bounds, generates floor definitions, and creates an all-available standard inventory. It returns empty sessions and activity. The dashboard supplies duplicate-name checking and inserts the resulting location into both the locations collection and operational map.

The helper's ID uses `Date.now()`, which is convenient for local creation but not a distributed uniqueness strategy. Generated fixture times also vary between module evaluations. These details matter for testing: counts, bounds and relational consistency are stable expectations, while exact time-based IDs and relative ages should not be treated as fixed constants.

<!-- page: c6-counts-plates | Chapter 6: SYSTEM IMPLEMENTATION -->
## 6.4 Occupancy Calculation and Registration Normalization

`occupancyForLevel` filters the bay array by the requested level, counts occupied and reserved records, derives available by subtraction and rounds the occupied percentage. An unknown level returns a zero total and a zero percentage rather than dividing by zero. The function does not consult the level's declared capacity; it counts actual records [3].

```typescript
return {
  total: levelBays.length,
  occupied,
  reserved,
  available: levelBays.length - occupied - reserved,
  percent: levelBays.length === 0 ? 0
    : Math.round((occupied / levelBays.length) * 100),
};
```

For Riverside B1, occupied percentage is round(10 / 24 × 100), or 42. Reserved bays remain excluded from parked-vehicle occupancy. The dashboard reduces these per-level counts to derive the selected location's total cards. Filtering the visible map does not alter the underlying statistics.

Registration normalization removes whitespace and hyphens, then uppercases. The accepted policy is exactly TN, two digits, two letters and four digits. It is a syntactic project policy, not a lookup against government registration records.

```typescript
const plate = value.replace(/[\s-]/g, "").toUpperCase();
if (!/^TN\d{2}[A-Z]{2}\d{4}$/.test(plate)) {
  throw new Error(
    "Use TN + 2 digits + 2 letters + 4 digits, for example TN01AA1234.",
  );
}
return plate;
```

For example, `tn 01 aa 3042` becomes `TN01AA3042`, while `KA01AA1234` is rejected. Normalization occurs before duplicate checking, so formatting variations do not evade the active-registration rule. Search has a different implementation: it lowercases and trims but does not perform the same full normalization.

<!-- page: c6-checkin | Chapter 6: SYSTEM IMPLEMENTATION -->
## 6.5 Vehicle Check-In Implementation

The `checkIn` helper receives bay/session arrays, target bay ID, registration, vehicle description and start time. It looks up the bay and normalizes the registration before checking availability. This ordering means an invalid plate may be reported before an unavailable-bay error when both inputs are wrong. Error precedence is an implementation detail worth preserving in tests.

```typescript
const bay = bays.find((item) => item.id === bayId);
const normalizedPlate = normalizeTamilNaduPlate(plate);
if (!bay || bay.status !== "available") {
  throw new Error("Choose an available parking bay.");
}
if (sessions.some((session) => session.plate === normalizedPlate)) {
  throw new Error("This vehicle already has an active parking session.");
}
```

After validation, the function constructs a session with the bay and level references, normalized plate, trimmed description or “Vehicle”, and supplied start time. The new ID combines bay ID with `Date.parse(startedAt)`. The helper does not validate that timestamp; UI callers supply `new Date().toISOString()`, but other callers could provide malformed content.

The return value maps the target bay to occupied status while retaining its other properties, then appends the session to the active list. The input arrays are not mutated. The existing test explicitly checks that the original available bay remains unchanged after a successful result.

The dashboard uses the returned collections and prepends an arrival activity record. It then shows a confirmation and closes the dialog. This is a local state commit, not a server acknowledgment. Save failure can occur later in the storage effect without rolling back the visible operation.

The function checks duplicate registrations only in the supplied session array, which the dashboard scopes to one location. It does not enforce a global rule across independent garages. Nor does it verify accessible/EV eligibility, authenticate the operator or open a physical gate. Those are future policy and integration requirements.

<!-- page: c6-checkout | Chapter 6: SYSTEM IMPLEMENTATION -->
## 6.6 Vehicle Check-Out Implementation

`checkOut` finds a session by ID and rejects an unknown ID. It maps the bay referenced by the session to available, clears `plate` and `since`, then filters the session out of the active collection. The bay's kind and identity are preserved.

```typescript
const session = sessions.find((item) => item.id === sessionId);
if (!session) throw new Error("Active parking session not found.");

return {
  bays: bays.map((bay) => bay.id === session.bayId
    ? { ...bay, status: "available", plate: undefined,
        since: undefined }
    : bay),
  sessions: sessions.filter((item) => item.id !== sessionId),
};
```

The dashboard performs an additional selected-session check before calling the helper, then prepends a departure activity item and displays the normalized registration and released bay in a status notice. The session dialog closes after success. On a level with no sessions, a hint is displayed and completion is disabled.

### 6.6.1 Meaning of Departure in the Current Model

A departure ends active occupancy only. It does not retain a completed visit with an end time, calculate duration, charge a fee, generate a receipt or post a financial transaction. Activity is not a substitute for that ledger: it stores a human-readable time string and only the first five items are shown in the panel.

The helper also assumes that the session's bay exists and corresponds to a valid occupancy. If the supplied data is corrupt, a missing bay is not explicitly rejected by the mapping operation. This is another reason to validate restored data and strengthen relationship tests before relying on the prototype operationally.

For the normal valid path, the expected count effect is occupied minus one and available plus one, with total and reserved unchanged. The existing unit test and browser arrival/departure test exercise this relationship. They do not cover all corrupt-state or repeated-submission cases.

<!-- page: c6-capacity | Chapter 6: SYSTEM IMPLEMENTATION -->
## 6.7 Capacity Resizing and Plan Commit

The resizing helper first rejects non-integer values or capacities outside one to ninety-nine. It filters the target level and rejects an unknown/empty level. It counts all non-available bays as protected and refuses a requested capacity below that count. This protects occupied and reserved records without needing to know their vehicle details.

For a reduction, available bays are sorted by descending numeric suffix, and the required number of IDs is removed from the overall array. Protected bays remain even if their suffix is high. For expansion, the helper collects existing suffixes, scans one through ninety-nine and creates unused IDs until it reaches the required difference.

```typescript
const protectedCount = levelBays
  .filter((bay) => bay.status !== "available").length;
if (capacity < protectedCount) {
  throw new Error(
    "Capacity cannot be below the number of occupied or reserved bays.",
  );
}
const difference = capacity - levelBays.length;
if (difference === 0) return bays;
```

New records are standard available bays. The algorithm does not automatically restore an EV or accessible designation for a previously removed suffix. It also does not renumber surviving records. These policies make the behavior deterministic but leave special-kind inventory policy as future work.

The dashboard saves all floor drafts as one logical plan. It computes `nextBays` and `nextLevels` through the selected location's levels before calling setters. If any helper throws, the final commit is skipped and the management error is shown. On success, both location planning information and operational bays are updated, and a total-capacity notice appears.

The method is safe against partial local state updates within that handler's normal execution. It is not an atomic multi-user transaction: another tab can still hold an old plan, and saved JSON has no revision check. A production implementation must enforce the same protection rule against current server data.

<!-- page: c6-persistence | Chapter 6: SYSTEM IMPLEMENTATION -->
## 6.8 Browser Persistence Implementation

The storage implementation uses two effects and the fixed key `parkline-garage-planning`. The first reads a value, parses JSON and checks that a locations array has length and an operations object exists. If accepted, it schedules restoration of locations, operations, selected location and that location's first floor. A catch path removes the saved key, while a finally path enables storage readiness.

The second effect runs after relevant state changes when readiness is true. It serializes locations, operations and selected location ID. A save failure is caught and logged as a browser warning. There is no user-visible “unsaved changes” state and no export or backup workflow.

```typescript
window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
  locations: garageLocations,
  operationsByLocation,
  locationId,
}));
```

The saved format duplicates some data because location objects contain nested bays, sessions and activity while the operational map also contains them. Session handlers update the operational map, so nested location collections may be older. The normal dashboard read prefers the operational map, but inconsistent or incomplete stored values could expose stale fallback data.

The restoration guard is not a schema validator. It does not confirm valid statuses, matching level references, array shapes in every location, unique IDs or session/bay consistency. Even the key-removal operation in the catch path assumes storage access remains usable. More robust recovery would isolate storage failures, validate a versioned schema and choose a single canonical representation.

The browser evidence is mixed rather than uniformly successful. Supplemental arrival and new-location reload checks passed in their exercised sequence, while the existing add/resize/reload scenario returned to `riverside` instead of the added location. This suggests a timing-sensitive restoration problem requiring investigation; it does not justify a claim that every reload fails or that persistence is reliable.

<!-- page: c6-interaction | Chapter 6: SYSTEM IMPLEMENTATION -->
## 6.9 Location Switching, Search and Dialog Coordination

`changeLocation` resolves the requested location, selects its first floor, clears search and status filtering, closes the session dialog and clears the notice. Operational collections are not copied between locations. Instead, subsequent rendering selects the appropriate entry from `operationsByLocation`. Similar bay IDs can therefore exist in different garages without sharing status.

Search trims the query and converts it to lowercase. A bay matches when its ID or optional plate contains that query and its status also matches the selected filter. The calculation applies only to `levelBays`, so a registration on another floor is not found until that floor is selected. When no records match, the grid displays an explicit empty-state message.

Dialog opening depends on context. Arrival selects the clicked bay or the first available current-floor bay; the selector itself lists available bays from the entire location. Departure selects a matching bay's session or the first current-floor session. Close buttons and backdrop clicks dismiss the modal, but no Escape-key listener or focus trap is implemented in the reviewed component.

### 6.9.1 Planning Dialog Coordination

Opening capacity planning closes a session dialog, copies the current capacities into string drafts and resets management errors. Switching to “Add location” changes the management view while preserving number drafts. A successful creation selects the new location and resets the relevant map view conditions. The name field has a UI maximum length, while the reusable helper mainly validates trimming and non-blank content.

A reserved bay click does not open either session form; it displays a reserved notice. Notification, profile and activity-options controls remain presentation-level affordances without full workflows. The activity footer simply shows a notice that recent activity is being displayed.

These interaction details are important for evaluation because a dashboard can contain many clickable controls without implementing the larger service implied by their labels. The screenshot commentary that follows describes only the demonstrated behavior.

<!-- page: c6-screen-overview | Chapter 6: SYSTEM IMPLEMENTATION -->
## 6.10 Output Screens — Garage Overview

![Figure 6.1: Authentic Riverside overview with derived inventory and sample presentation labels](assets/screenshots/01-overview.png)

The overview shows the initial Riverside inventory: 72 total, 34 occupied, 32 available and six reserved. The basement map contains 24 bays, with a 42% occupied indicator derived from ten occupied records. Floor cards summarize the same underlying bay collection, while recent activity displays fixture events. The sidebar selects the garage and links to sections of this page.

The metric totals are working outputs, but not every label is data-driven. “Live operations”, “8.4% vs. this time yesterday”, the next-arrival message, the manager profile and EV charging summary include static content. No sensor or historical analytics service produced them. The footer correctly identifies a local browser plan and says no live sensors are connected.

This screen is a genuine production-build capture at a 1440-by-1000 CSS-pixel viewport, with full-page capture extending to the content height. It is evidence of the reviewed UI, not a mockup or proof that any named physical garage has adopted Parkline.

<!-- page: c6-screen-filter | Chapter 6: SYSTEM IMPLEMENTATION -->
### 6.10.1 Floor Selection and Status Filtering

![Figure 6.2: Upper-deck map filtered to its two reserved sample bays](assets/screenshots/02-floor-filter.png)

The capture selects floor 02 and filters the map to reserved bays. Only L2-04 and L2-14 remain visible. The occupancy strip and legend still describe the full level rather than the filtered subset, which preserves the distinction between inventory statistics and search results.

Clicking L2-04 displays a reserved notice and does not open an arrival form. This behavior was exercised by supplemental check B03. Filtering and clicking do not change the reserved collection; there is no reservation creation or cancellation workflow behind the display.

A search can be combined with the filter because both predicates must pass. An unknown query produces “No bays match this search.” Search is local to the current floor and performs a case-insensitive substring match. It does not scan all garages or normalize formatted registrations the same way as arrival validation.

The map is a regular visual grid rather than a scaled drawing. Bay position in the grid is not a surveyed physical coordinate, and the lane decoration does not establish a navigable facility route. The screen is useful for operational demonstration while remaining limited as a genuine floor-planning tool.

<!-- page: c6-screen-arrival | Chapter 6: SYSTEM IMPLEMENTATION -->
### 6.10.2 Vehicle Arrival Form

![Figure 6.3: Arrival dialog with a formatted TN registration and an available bay](assets/screenshots/03-arrival-form.png)

The arrival form collects a registration, optional description and available bay. The captured input `tn 01 aa 3042` demonstrates accepted formatting before normalization. The selected bay is B1-01, which is initially available and classified as accessible in the seed data. The current MVP does not collect or enforce accessibility eligibility.

On submission, the domain helper normalizes the plate to `TN01AA3042`, checks availability and active duplication, then returns a changed bay and new session. Supplemental check B05 observed totals of 72 capacity, 35 occupied, 31 available and six reserved after success. Check B06 then observed that arrival state after a same-browser reload in that sequence.

The form does not capture driver identity, contact information, ticket number, tariff, payment method or reservation reference. It does not open a gate. The “Demo mode” note identifies the local-browser scope, and errors leave the dialog open for correction rather than committing a successful transition.

The screenshot shows the actual form, including native controls and accessible visible labels. It does not establish complete modal keyboard behavior, which remains a documented improvement area.

<!-- page: c6-screen-departure | Chapter 6: SYSTEM IMPLEMENTATION -->
### 6.10.3 Active Session and Departure Form

![Figure 6.4: Departure selector for the newly checked-in demonstration vehicle](assets/screenshots/05-departure-form.png)

The departure form lists active sessions on the selected floor. Each option combines normalized registration, bay ID and vehicle description, helping the operator distinguish sessions. The screenshot selects `TN01AA3042 · B1-01 · Green test vehicle`, created during the same supplemental demonstration.

Completing checkout releases B1-01, removes the active session and restores Riverside totals to 72 total, 34 occupied, 32 available and six reserved. Supplemental check B08 verified both the bay's accessible name and the metric values. The bay's accessible kind remains unchanged because departure clears vehicle fields, not physical classification.

The scope limitation is visible in the selection logic rather than the screenshot alone: sessions from another floor are excluded until the operator changes floors. A level with no sessions displays a hint and disables completion. Unknown IDs are rejected by the helper.

This is an occupancy departure, not a financial checkout. There is no calculation of elapsed fees, no payment approval and no receipt. The prototype also removes the active record instead of moving it into a completed-session archive. Those limitations are central to interpreting the screen accurately.

<!-- page: c6-screen-capacity | Chapter 6: SYSTEM IMPLEMENTATION -->
### 6.10.4 Floor Capacity Planning

![Figure 6.5: Capacity dialog with occupied/reserved minimums and a draft basement expansion](assets/screenshots/06-capacity-form.png)

The planning dialog exposes one numeric field per existing level. Supporting text shows occupied, reserved and minimum protected counts. In the capture, the basement is drafted from 24 to 28 bays. Saving that plan produced 76 total, 34 occupied, 36 available and six reserved, demonstrating that expansion adds availability without disturbing protected records.

Supplemental check B10 also inspected the basement input's minimum of twelve, corresponding to ten occupied plus two reserved bays. A draft of eleven had the browser's range-underflow validity flag set. The domain helper independently enforces the same protection boundary, so correctness does not depend solely on the HTML minimum.

The form edits bay counts, not the number of floors or an architectural geometry. It cannot mark new bays EV or accessible, and it cannot approve a physical facility's legal capacity. Newly allocated suffixes are standard available records, while protected existing IDs remain stable.

The confirmation notice is evidence of a valid local plan update. It is not proof of durable saving or synchronization with another operator. Persistence is a later browser effect and remains subject to the open reload finding.

<!-- page: c6-screen-location | Chapter 6: SYSTEM IMPLEMENTATION -->
### 6.10.5 New Location Creation

![Figure 6.6: Add-location form configured for Harbour Point with two floors and fifteen bays each](assets/screenshots/07-new-location-form.png)

The add-location tab collects a name, floor count and bays per floor. The preview multiplies the current numeric drafts, producing thirty bays in this example. Submission validates the counts and creates two levels with fifteen standard available bays each. The new location has no active sessions or activity.

The dashboard inserts the location into the selectable collection, creates an operations-map entry and selects its first level. Supplemental check B11 observed `[30, 0, 30, 0]` for total, occupied, available and reserved, then observed the selected name after reload in that specific sequence. A separate original reload scenario failed, so this successful capture must not be generalized into a reliability claim.

The UI rejects case-insensitive duplicate names, including surrounding whitespace after trimming. It limits the name field length, but the pure helper does not enforce list-wide uniqueness or a universal name-length rule. Floor and bay bounds are enforced by the helper independently of the form.

The new location is browser-local. It is not registered with a remote operator, verified as a physical property or made available to another device. The screen demonstrates controlled inventory construction, not enterprise site onboarding.

<!-- page: c6-screen-validation | Chapter 6: SYSTEM IMPLEMENTATION -->
### 6.10.6 Registration Validation and Error Feedback

![Figure 6.7: Actual format-validation error for a registration outside the project's TN policy](assets/screenshots/10-format-validation.png)

The screenshot submits `KA01AA1234`, which is outside the project's TN-only pattern. The form remains open and shows the required format: TN followed by two digits, two letters and four digits. This is an intentional project constraint, not a statement that the entered registration is invalid in its actual state of issue.

The supplemental script also exercised a duplicate active `TN01AA3042` registration. The helper rejected the second arrival even though the selected bay was available. The duplicate screenshot is retained among the source assets, while the report uses this format-error screen to illustrate clear recovery without changing operational state.

The message originates from the domain helper and is shown in an alert-marked paragraph. Native required fields and length/range constraints operate before or alongside domain validation. An empty description is allowed and becomes “Vehicle”; an invalid registration is not silently coerced into a different legal pattern.

Error feedback should be reviewed separately from modal accessibility. The current dialog does not implement a complete focus trap or Escape-key behavior. A future improvement should associate error text more explicitly with the affected field and verify the experience with assistive technology, while preserving the transition guards.

<!-- page: c6-screen-mobile | Chapter 6: SYSTEM IMPLEMENTATION -->
### 6.10.7 Mobile Output and an Observed Layout Defect

![Figure 6.8: Upper region of the authentic mobile capture, retaining the horizontal-overflow defect](assets/screenshots/11-mobile-upper-view.png)

At a 390-by-844 CSS-pixel viewport, the measured document width was 457 pixels. The primary heading action extended to that right boundary. Supplemental check B15 therefore failed the assertion that the document had no horizontal overflow. The printed upper-region excerpt retains the full captured width, including the overflow, rather than hiding the defect. The uncropped full-page capture is retained with the source assets.

The stylesheet does adapt: the sidebar narrows, cards form two columns, major panels stack and the bay grid uses four columns. Nevertheless, adaptive rules do not guarantee that the action row can shrink sufficiently. The location switcher is also hidden at narrow widths, limiting mobile location changes.

This observation supports a targeted improvement: allow action wrapping or a smaller-width arrangement, preserve access to location selection and test several narrow widths. It does not establish that every mobile device fails or that the entire application is unusable. A broader touch and accessibility review was not performed.

<!-- page: c6-output-reconciliation | Chapter 6: SYSTEM IMPLEMENTATION -->
## 6.11 End-to-End Demonstration Reconciliation

The implementation walkthrough concludes by reconciling visible output with domain effects. A correct demonstration should track a single operation across bay status, session membership, metric values and activity. Screens alone can look plausible even when those relationships disagree, so the capture script includes explicit assertions.

**Table 6.3: Supplemental scenario state progression**

| Scenario stage | Total | Occupied | Available | Reserved | Required interpretation |
|---|---:|---:|---:|---:|---|
| Initial Riverside | 72 | 34 | 32 | 6 | Seed baseline |
| Arrival at B1-01 | 72 | 35 | 31 | 6 | Capacity conserved; one new active session |
| Departure from B1-01 | 72 | 34 | 32 | 6 | Session removed; bay released |
| Basement expanded to 28 | 76 | 34 | 36 | 6 | Four standard available bays added |
| Harbour Point created | 30 | 0 | 30 | 0 | Independent empty two-floor inventory |
| Switch back to Riverside | 76 | 34 | 36 | 6 | Riverside's own planned state restored in view |

The scenario uses fictional vehicle input and does not perform a payment, reservation or hardware action. It demonstrates that the local operations remain scoped by location and that successful transitions conserve or alter the right quantities. Browser save/restore checks are reported separately because they involve effect timing beyond the pure transition result.

The documentation assets also include the post-arrival overview, the duplicate-validation dialog and the new-location result. These supporting captures can be used during a project demonstration even when not printed as separate full-page figures.

The chapter establishes a source-to-screen chain for the implemented MVP. The next chapter evaluates that chain, reports failures without changing application behavior and identifies which additional tests and controls are required before broader operational use.
