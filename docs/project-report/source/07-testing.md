<!-- page: c7-strategy | Chapter 7: TESTING AND EVALUATION -->
# CHAPTER 7 — TESTING AND EVALUATION
## 7.1 Testing Strategy and Evidence Baseline

Testing combines source review, static verification, domain tests, browser workflows and screen/geometry checks. The aim is to establish what was observed at the reviewed revision, not to manufacture an all-green project narrative. The application behavior was not changed to repair findings during this documentation task.

The review baseline is commit `aa4b73016f271a7e0778c6c8bbd6c17346f52346`, with checks recorded on 31 October 2026. Dependencies were installed with `npm ci`. The application was built successfully and served locally in production mode for browser evidence. Chromium 153.0.8010.0 was supplied through an environment-specific launcher because a default browser was not preinstalled. The existing scenario source was unchanged.

**Table 7.1: Recorded verification summary**

| Verification | Result | Evidence boundary |
|---|---|---|
| Existing Vitest suite | 9 passed, 0 failed | Selected domain and fixture cases |
| ESLint | Passed | Configured static checks only |
| TypeScript no-emit check | Passed | Compile-time source consistency |
| Next.js production build | Passed | Compilation and route generation |
| Existing Playwright scenarios | 2 passed, 1 failed | Complete recorded run of three scenarios |
| Supplemental report browser checks | 15 passed, 1 failed | Sixteen separate documentation assertions |
| Uncaught page errors in supplemental sequence | None observed | Not a universal runtime-error guarantee |

The original browser failure occurred in the add-location, resize-capacity and reload scenario. After reload, the garage selector returned `riverside` rather than the expected generated location ID. The supplemental failure was the 390-pixel overflow assertion, with a measured document width of 457 pixels.

A unit-test pass does not override either browser failure. Likewise, a successful local reload in another sequence does not prove restoration reliability. The sections below retain these distinctions and identify untested boundaries, observed issues and proposed acceptance checks.

<!-- page: c7-unit | Chapter 7: TESTING AND EVALUATION -->
## 7.2 Existing Unit and Fixture Test Cases

The existing `src/lib/parking.test.ts` file contains seven parking-operation tests and two location tests. It uses small explicit fixtures for transition checks and loops through seeded locations for consistency assertions. All nine cases passed in the recorded unit run [6].

**Table 7.2: Existing Vitest cases and observed results**

| ID | Existing scenario | Main expected condition | Result |
|---|---|---|---|
| UT-01 | Count occupancy without treating reservations as vehicles | 3 total, 1 occupied, 1 reserved, 1 available; unknown-level percent 0 | Pass |
| UT-02 | Check in and normalize registration | TN01AA9876; occupied result; original bay unchanged | Pass |
| UT-03 | Reject duplicate and unavailable bay | Duplicate and availability exceptions | Pass |
| UT-04 | Reject registrations outside TN format | Format error for invalid input | Pass |
| UT-05 | Check out and release the bay | Available status, cleared plate, no active session; missing ID rejected | Pass |
| UT-06 | Expand/reduce capacity safely | Protected occupied/reserved IDs survive | Pass |
| UT-07 | Reject capacity below protection or above limit | Protected minimum and 100-bay errors | Pass |
| UT-08 | Validate configured locations and sample inventory | Names, session/occupied consistency, TN plate shape, independent arrays | Pass |
| UT-09 | Create requested floor/bay counts | Trimmed name, 2 floors, 24 available bays and capacity 12 | Pass |

UT-03 and UT-05 include more than one assertion path, but each remains one test case in the reported count. The report does not inflate the suite by counting every expectation as a separate test.

The unit suite gives useful confidence in the normal local transitions and selected rejection paths. It does not test every integer boundary, malformed timestamp, unknown resize level, special-kind removal policy, corrupted saved value or cross-tab conflict. It also cannot detect a dialog selector problem or a persistence effect race because it does not mount the dashboard in a browser.

The recommended next step is to add focused cases for the open boundaries while retaining the current small fixtures. Property-style assertions, such as capacity conservation after any valid arrival/departure pair, would complement example-based tests without changing the scope of the existing results.

<!-- page: c7-e2e | Chapter 7: TESTING AND EVALUATION -->
## 7.3 Existing Browser Workflow Results

The existing Playwright file defines three scenarios. The documentation runner pointed them at the built local application and used isolated browser contexts. A complete recorded run executed all three, with two passes and one failure. An earlier launcher setup timeout was treated as environment troubleshooting rather than evidence of a parking-rule defect; the results below refer to the subsequent complete run.

**Table 7.3: Existing Playwright scenarios and final recorded outcomes**

| ID | Scenario and steps | Expected result | Recorded outcome |
|---|---|---|---|
| E2E-01 | Select Marina, VR and Phoenix locations | Selector reflects each requested ID | Pass |
| E2E-02 | Add Harbour Point with 2×15 bays; resize Ground floor to 18; reload | Added location remains selected and Ground floor remains 18 | Fail after reload: selector value `riverside` |
| E2E-03 | Check TN01AA3042 into B1-01 and back out | Confirmation, occupied bay, then released bay | Pass |

E2E-02 reached the creation and capacity-update stages before failing its post-reload selected-location assertion. The recorded expected pattern was a generated `location-` ID. The received value was the seed location ID. This is stronger evidence than a generic statement that “persistence has an issue”, because it identifies the exact user journey and assertion boundary.

The current evidence does not prove a single root cause. Source review suggests that restoration scheduling and the readiness-gated write effect need coordination, and the duplicated saved representations complicate recovery. These are investigation hypotheses, not confirmed fixes. No application code was modified as part of the report.

The supplemental capture sequence successfully reloaded a new location in a different flow, showing that restoration can work in some circumstances. The appropriate conclusion is a reliability concern requiring repeated regression tests, not that persistence always fails or always succeeds.

Future acceptance should repeat fresh-load and saved-load scenarios under varied timing, verify both the selected location and its full operational inventory, and inspect the stored value before and after hydration. Merely increasing a test timeout would not address an incorrect saved or restored state.

<!-- page: c7-supplemental | Chapter 7: TESTING AND EVALUATION -->
## 7.4 Supplemental Documentation Browser Checks

The capture utility exercises additional interactions and records each assertion independently. It continues after an assertion failure so that remaining evidence and screenshots can still be collected. Its zero process exit on completed collection must not be mistaken for all assertions passing.

**Table 7.4: Supplemental browser assertions B01 to B16**

| ID | Assertion | Result |
|---|---|---|
| B01 | Riverside cards equal 72 / 34 / 32 / 6; 24 basement bays | Pass |
| B02 | Upper-deck reserved filter returns two bays | Pass |
| B03 | Reserved-bay click gives a notice, not a session dialog | Pass |
| B04 | Unknown search displays the empty-map message | Pass |
| B05 | Formatted arrival normalizes and changes counts correctly | Pass |
| B06 | Arrived vehicle remains visible after reload in this sequence | Pass |
| B07 | Duplicate active registration is rejected | Pass |
| B08 | Checkout releases B1-01 and restores seed counts | Pass |
| B09 | Capacity expansion adds availability only | Pass |
| B10 | Basement input minimum is 12 and rejects 11 natively | Pass |
| B11 | New Harbour Point has 30 empty bays and reloads in this sequence | Pass |
| B12 | Switching back restores Riverside's own expanded inventory | Pass |
| B13 | Non-TN format displays the domain error | Pass |
| B14 | Trimmed case-insensitive duplicate location name is rejected | Pass |
| B15 | No document-level overflow at a 390-pixel viewport | Fail |
| B16 | No uncaught page errors during the exercised sequence | Pass |

The results establish specific browser observations, not a cross-browser or assistive-technology audit. B15 measured `innerWidth=390` and `documentElement.scrollWidth=457`. The overflowing element identified by the diagnostic was a primary action button in the heading row. The associated full-page mobile screenshot is printed in Chapter 6.

The evidence file also records Chromium version, desktop and mobile viewports, source commit and assertion details. It is retained separately from the existing Playwright result so that original tests and documentation-added checks remain distinguishable.

<!-- page: c7-boundaries | Chapter 7: TESTING AND EVALUATION -->
## 7.5 Boundary, Negative and Recovery Test Design

The following cases are recommended additions. Unless explicitly linked to the executed suite, they were not run as separate acceptance tests in this documentation task. Static inspection can predict a code path, but it is not a substitute for an executed result.

**Table 7.5: Proposed additional boundary and recovery cases — not executed as a new suite**

| Proposed ID | Input / situation | Expected criterion |
|---|---|---|
| PT-01 | Capacity 0, negative, fractional or NaN | Reject without mutating input arrays |
| PT-02 | Capacity exactly protected count | Remove available records only; retain all protected IDs |
| PT-03 | Expand to 99 with gaps in suffixes | Fill unused numbers; produce no duplicate IDs |
| PT-04 | Resize an unknown level | Reject “Parking level not found” |
| PT-05 | Create 1×1 and 10×99 locations | Correct bounds, counts and all-available standard records |
| PT-06 | Create 0/11 floors or 0/100 bays | Reject invalid creation bounds |
| PT-07 | Check in with a malformed timestamp | Define and test a future timestamp-validation policy |
| PT-08 | Checkout session references a missing bay | Reject inconsistent state rather than silently remove session |
| PT-09 | Invalid JSON or incompatible saved schema | Safe recovery without uncaught error or overwrite |
| PT-10 | Repeated saved-plan loads under varied timing | Preserve selected site and canonical operations |
| PT-11 | Two tabs modify the same bay | Document current conflict; later reject stale revisions |
| PT-12 | Storage quota or access denial | Preserve usable UI and expose an unsaved-state warning |

Some rejection branches already exist for PT-01, PT-04 and PT-06, but the current suite does not exercise all values. PT-07, PT-08 and PT-12 include proposed behavior that would need implementation decisions before a passing expectation can be adopted.

A useful testing principle is to preserve the original collection after every rejected operation. Another is to compare identity sets, not just counts, when shrinking capacity. Losing one occupied bay while creating another could preserve a total yet violate operational safety. Boundary tests should therefore inspect protected IDs, session relationships and mutation behavior together.

<!-- page: c7-static | Chapter 7: TESTING AND EVALUATION -->
## 7.6 Static Checks, Build Verification and Evidence Handling

The documentation run executed linting, type checking and a production build after dependency installation. All completed successfully. The build generated the home route and framework not-found route. These results confirm that the reviewed application can be compiled with the resolved toolchain in the tested environment.

```text
npm test             9 tests passed
npm run lint         completed successfully
npm run typecheck    completed successfully
npm run build        production compilation completed successfully
Playwright           2 passed, 1 failed
Report browser checks 15 passed, 1 failed
```

The static checks have defined limits. ESLint evaluates configured rules; it does not validate the truth of “LIVE” labels or prove a persistence effect is race-free. TypeScript checks source types, but the saved JSON is asserted into a shape without a full runtime validator. A successful production build does not guarantee correct browser state after reload or eliminate responsive-layout defects.

### 7.6.1 Evidence Preservation

The report source includes machine-readable unit results, existing browser results, supplemental browser results and dependency versions. Screenshots are tied to the same reviewed baseline. The generated report's validation summary records page count, content inventory and layout checks. These artifacts allow a reviewer to inspect how the report's claims were formed.

Generated caches, dependencies and browser binaries are not treated as project deliverables. The report assets contain only the material needed to reproduce or review the document. The source commit identifies the application baseline; documentation files added later do not imply a changed parking implementation.

No test coverage percentage, security score, endpoint latency or field-availability figure is reported because those measurements were not collected. The absence of such numbers is deliberate. A precise statement of executed checks is stronger academic evidence than a fabricated completeness metric.

<!-- page: c7-security | Chapter 7: TESTING AND EVALUATION -->
## 7.7 Security and Privacy Review

The current browser-local design has no authentication, authorization or trusted audit identity. The manager profile is static presentation. Anyone with access to the running page and its browser context can operate the UI or inspect local data. This is a documented MVP boundary, not a vulnerability assessment claiming that all production controls should already exist.

**Table 7.6: Source-level security/privacy assessment and future controls**

| Concern | Current observation | Recommended production control |
|---|---|---|
| Operator identity | No sign-in or role checks | Authenticate users and authorize each operation |
| Registration data | Stored in plain JSON in the browser | Minimize collection, restrict access and define retention |
| Data integrity | Client can edit collections and storage | Server-side validation and transactional constraints |
| Concurrent allocation | No shared authority | Atomic bay/session updates and conflict responses |
| Auditability | Activity lacks actor and structured event time | Append-only, attributed audit events |
| Storage corruption | Shallow restoration checks | Versioned runtime schema and recovery path |
| Credentials/payments | Not collected or integrated | Use compliant providers; never add secrets to local storage |
| Connected devices | No device protocol or identity | Device authentication, stale-data handling and manual override |

The TN regular expression is input validation, not identity verification. It cannot prove that a registration exists, belongs to the arriving vehicle or has authorization to use an accessible space. Likewise, preventing a duplicate in one session array is not a security guarantee against malicious edits or concurrent clients.

No penetration test, dependency vulnerability audit or OWASP certification was performed. The review is based on source structure and exercised behavior. The existing architecture should use fictional data during demonstrations, especially on shared computers. Clearing site data removes local records but is not a centrally governed deletion or audit process.

Production security work should begin with a threat model and data policy, then implement server authority and access controls. Adding a login screen alone would not repair client-side trust or concurrency limitations.

<!-- page: c7-accessibility | Chapter 7: TESTING AND EVALUATION -->
## 7.8 Accessibility and Responsive Evaluation

The source review found labels, native controls, semantic buttons, visible focus styles, bay accessible names and status/error roles. These features provide a useful foundation. The browser capture utility used accessible names for most interactions, which also confirms that key controls can be located semantically in the tested DOM.

The evaluation did not include screen-reader testing, a complete keyboard-only session, contrast measurements or a formal WCAG audit. Therefore, the report does not label the application fully accessible. ARIA roles alone cannot supply missing keyboard behavior or guarantee that focus remains within a modal dialog.

**Table 7.7: Accessibility/responsive evidence and open review items**

| Item | Evidence type | Outcome / next action |
|---|---|---|
| Form labels and bay names | Source and browser selectors | Present in exercised controls |
| Success and error feedback | Source and browser assertions | Status/alert text observed |
| Dialog focus trap and return | Source review | Not implemented; add tested behavior |
| Escape-key dismissal | Source review | Not implemented |
| Tab keyboard pattern | Source review | Add arrow-key and roving-focus behavior |
| Reduced motion | Stylesheet review | Media query exists; no user study |
| 390-pixel overflow | Executed geometry assertion | Failed: document width 457 pixels |
| Narrow-screen garage selection | Stylesheet review | Selector hidden below sidebar breakpoint |
| Contrast and assistive technology | Not executed | Requires separate evaluation |

The overflow defect is localized evidence, not a general statement about all viewports. The desktop layout rendered coherently in the tested capture, while narrow-width heading actions exceeded the viewport. A corrective test should assert both document width and visibility/reachability of primary actions at several widths.

Accessibility acceptance should also verify that opening a dialog moves focus predictably, Tab remains within it, Escape closes it, and focus returns to the invoking control. These behaviors should be tested with native keyboard input rather than inferred from `aria-modal=true`.

<!-- page: c7-performance | Chapter 7: TESTING AND EVALUATION -->
## 7.9 Performance and Scalability Reasoning

No response-time benchmark, network load test or large-data experiment was performed. The analysis below is algorithmic reasoning from the implementation, not a measured performance result. No parking API exists to benchmark.

Let B be the selected location's bay count, S its active-session count and L its floor count. Occupancy calculation scans bays to obtain a level and then counts statuses, so its work is linear in B. The dashboard calls that helper repeatedly for totals, tabs and floor cards, producing work that grows roughly with L×B during a render, in addition to map filtering and session selectors.

**Table 7.8: Dominant operation costs inferred from source**

| Operation | Approximate work | Interpretation |
|---|---|---|
| One level occupancy | O(B) | Filters selected-level records and counts states |
| Arrival | O(B + S) | Bay lookup, duplicate scan and immutable updates |
| Departure | O(B + S) | Session lookup, bay mapping and session filtering |
| Capacity shrink | O(B + A log A) | A available target-level bays sorted by suffix |
| Capacity expansion | O(B + 99) | Used-number set and bounded suffix scan |
| Search/filter | O(B_level) | Current-floor substring and status checks |
| Save snapshot | O(serialized state size) | Entire saved object is serialized on relevant changes |

New-location creation is bounded at 990 bays. That limit makes array-based logic plausible for a prototype, but it does not establish acceptable rendering on every device. Local saving is synchronous browser work and stores duplicated structures; larger activity collections can increase serialization cost because the array is not pruned even though only five items are shown.

Future optimization should follow measurement. Possible directions include one-pass aggregate statistics, stable derived collections, bounded activity retention and a canonical persistence representation. Once a server is introduced, pagination, indexing, transaction contention and network behavior become separate evaluation topics.

The current conclusion is modest: the algorithms are understandable and bounded for the intended demonstration, while scalability and responsiveness at maximum inventory remain unmeasured.

<!-- page: c7-findings | Chapter 7: TESTING AND EVALUATION -->
## 7.10 Defect Register, Acceptance Review and Evaluation Summary

The defect register separates observed failures from source-level risks. A proposed fix is not described as completed. The report preserves the current application's behavior so that the project team can reproduce the findings and decide on follow-up work.

**Table 7.9: Open findings and suggested acceptance evidence**

| ID | Classification | Finding | Suggested closure evidence |
|---|---|---|---|
| D-01 | Observed browser failure | Added/expanded location not retained as selected after reload | Repeated existing scenario passes with verified stored content |
| D-02 | Observed layout failure | 390-pixel viewport has 457-pixel document width | Width assertions and reachable actions across narrow widths |
| D-03 | Source-level quality gap | Dialog focus lifecycle incomplete | Keyboard and assistive-technology tests |
| D-04 | Source-level integrity gap | Saved JSON lacks complete runtime validation | Versioned schema and corruption/recovery tests |
| D-05 | Architectural limitation | Browser snapshots cannot coordinate operators | Transactional server and stale-write conflict tests |
| D-06 | Presentation limitation | Static values and live labels can imply telemetry | Clear sample labels or removal of unsupported claims |

No formal user acceptance study or college approval was conducted. The acceptance criteria in this report are proposed review criteria derived from the implemented workflows. A supervisor or project evaluator can use the appendices to reproduce the demonstration and inspect the evidence.

The evaluation supports three conclusions. First, core local domain behavior is supported by a passing nine-case suite and successful arrival/departure browser evidence. Second, static verification and compilation are healthy in the tested environment. Third, persistence and mobile quality are not fully accepted because concrete browser checks failed, while production identity, history and concurrency remain outside scope.

This mixed outcome is useful rather than contradictory. It identifies a working educational foundation and a prioritized improvement list. The final chapter uses those findings to conclude the project without overstating readiness or hiding open engineering work.
