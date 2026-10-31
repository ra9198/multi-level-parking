<!-- page: c8-conclusion | Chapter 8: CONCLUSION AND FUTURE ENHANCEMENTS -->
# CHAPTER 8 — CONCLUSION AND FUTURE ENHANCEMENTS
## 8.1 Conclusion

Parkline demonstrates a coherent browser-based model for multi-level parking operations and capacity planning. The project combines a location-scoped dashboard, floor-level bay inspection, registration normalization, controlled arrivals and departures, safe bay-count resizing and configurable new locations. Its value is the connection between understandable operator interactions and explicit, testable state-transition rules.

The implementation correctly separates several concepts that are easy to confuse. A bay's physical kind is independent of its occupancy status. A reservation is unavailable inventory but not a parked vehicle. A location total is different from the selected floor's map. Operational changes conserve capacity, while planning changes alter inventory without discarding protected records. These distinctions are visible in the data model, domain helpers and output commentary.

The project also demonstrates the importance of evidence-based evaluation. Nine existing unit tests passed, as did linting, type checking and the production build. The recorded browser results were not uniformly green: two original scenarios passed and one reload-persistence scenario failed; fifteen supplemental assertions passed and one mobile overflow assertion failed. Those outcomes support the conclusion that the MVP is functional but still needs quality hardening.

The application must not be presented as a production parking system. Browser local storage is not a shared database, the profile is not authenticated identity, reserved records do not form a reservation workflow and interface “LIVE” labels do not establish sensor connectivity. Payments, durable visit history and multi-operator transactions are absent.

Within those boundaries, the project is a useful academic software-engineering artifact. It provides a small codebase that can be explained from types through algorithms to screens, along with concrete tests and open findings. The next stage should improve reliability and clarity before expanding the domain or introducing physical integrations.

<!-- page: c8-achievements | Chapter 8: CONCLUSION AND FUTURE ENHANCEMENTS -->
## 8.2 Achievements against Project Objectives

The achievements are assessed against the objectives stated in Chapter 1. A source-backed feature and a fully accepted quality outcome are not the same thing, so the evaluation retains qualifications rather than marking every objective complete by default.

**Table 8.1: Objective-by-objective outcome assessment**

| Objective | Outcome at the reviewed revision | Qualification |
|---|---|---|
| O1 Occupancy visibility | Implemented and demonstrated | Counts describe local records, not a live facility |
| O2 Bay inspection | Implemented with floors, search and filters | Search is current-floor only |
| O3 Registration validation | Implemented and tested | TN syntax policy only; no authority verification |
| O4 Safe arrivals | Local guards and tested successful/rejection paths | No concurrent-client guarantee |
| O5 Departure release | Implemented and demonstrated | No completed-session archive or billing |
| O6 Protected resizing | Implemented and tested | Protection is by status, not minimum special-kind inventory |
| O7 New locations | Implemented and demonstrated | No edit/delete or arbitrary floor geometry |
| O8 Location isolation | Demonstrated in working state | IDs remain scoped by collection |
| O9 Local retention | Save/restore exists | Reload reliability finding remains open |
| O10 Honest verification | Tests and failures recorded | No field deployment or formal acceptance study |

The strongest achievement is the reusable domain core. It permits tests to inspect operations without depending on screen layout and gives a future backend a clear behavioral specification. The visual dashboard then demonstrates how those rules support actual operator tasks.

A second achievement is transparent documentation. The report adapts the college reference format while replacing its unrelated architecture with Parkline's actual stack and data model. Genuine captures, explicit scope exclusions and a defect register make the document useful for review rather than merely lengthy.

A third achievement is a staged development foundation. The project does not need to adopt every production feature at once. Reliability, runtime schema checking and accessible interaction can be improved within the existing MVP before the system is expanded into shared operations.

<!-- page: c8-limitations | Chapter 8: CONCLUSION AND FUTURE ENHANCEMENTS -->
## 8.3 Limitations of the Current Work

The principal limitation is authority. All working parking state resides in the browser, where it can be cleared, edited or overwritten. The application cannot safely coordinate two gate operators, arbitrate simultaneous arrivals or guarantee durable recovery. A local no-duplicate guard is valuable but cannot serve as a global allocation constraint.

Persistence has a specific observed quality issue. The original add/resize/reload browser scenario did not retain the added location as selected, even though supplemental reloads succeeded in another sequence. The exact root cause remains unconfirmed. The write/read effect ordering, transition scheduling and duplicated stored representations require investigation and repeatable regression evidence.

The model also omits historical lifecycle detail. Checkout removes an active session; it does not preserve departure time or a completed visit. Activity uses human-readable strings rather than structured event times and operator attribution. Consequently, the current records cannot support billing reconciliation, audited dispute resolution or meaningful historical analytics.

The operator interface has unfinished quality areas. Narrow-width actions overflowed in the measured mobile viewport, the garage selector is hidden in the collapsed sidebar and modal focus behavior is incomplete. A formal accessibility audit, cross-browser review and maximum-inventory performance study were not performed.

Scope limitations are equally important. There is no login, role-based authorization, reservation lifecycle, tariff engine, payment integration, sensor connection, gate protocol or number-plate recognition. EV and accessible indicators do not enforce eligibility or manage charging. Named sites and registrations are fixtures, not verified real-world operational data.

Finally, the academic evaluation is code- and execution-based. It includes no stakeholder interviews, field trial, customer survey, measured traffic reduction or financial return analysis. Those methods could be added in a future study, but the present report does not substitute invented numbers for missing evidence.

These limitations do not negate the MVP's educational value. They define where its conclusions stop and provide a concrete roadmap for the next engineering iteration.

<!-- page: c8-roadmap | Chapter 8: CONCLUSION AND FUTURE ENHANCEMENTS -->
## 8.4 Future Enhancements

Enhancements should be ordered by dependency and risk rather than visual prominence. Reliability and information clarity come first, followed by shared authority and only then external integrations. The roadmap below is proposed work; none of the listed production capabilities is claimed as already implemented.

**Table 8.2: Staged enhancement roadmap and acceptance gates**

| Stage | Proposed work | Acceptance gate |
|---|---|---|
| 1 — MVP hardening | Fix restoration/write coordination; canonical saved schema; runtime validation | Repeated reload and corrupt-storage tests pass |
| 1 — Interface quality | Wrap narrow action controls; preserve mobile location selection; complete modal focus | Geometry, keyboard and accessibility review |
| 1 — Honest presentation | Mark or remove static trends, next-arrival and live labels | Every operational claim has a data source |
| 2 — Shared data authority | Server API and durable database; atomic bay/session operations | Concurrent allocation and stale-write tests |
| 2 — Identity and privacy | Authentication, authorization, attribution and retention rules | Threat-model and access-control review |
| 2 — History and recovery | Completed sessions, structured events, backup and restore | Recovery drill and auditable visit lifecycle |
| 3 — Reservation rules | Create/cancel/expire/consume transitions and timing policy | Conflict and expiration tests |
| 3 — Commercial functions | Tariffs, grace periods and compliant payment provider | Idempotent settlement and reconciliation tests |
| 4 — Physical integration | Device identity, stale sensor data, overrides and monitoring | Hardware failure and safe fallback exercises |

A future backend should treat the browser as an untrusted client. It must repeat validation against current state and commit related records atomically. Composite identity or globally unique keys should prevent location-scoped bay IDs from colliding in a shared schema.

Sensor work should begin only after manual-state authority, stale-data handling and override ownership are agreed. Otherwise, a sensor reading and an operator action could compete without a defined resolution policy. Payment work similarly requires an explicit visit lifecycle and idempotent transaction design rather than a button added to the current checkout form.

<!-- page: c8-contribution | Chapter 8: CONCLUSION AND FUTURE ENHANCEMENTS -->
## 8.5 Academic Contribution and Closing Summary

The project contributes a practical case study in resource-state modeling. It demonstrates how a familiar physical domain can be represented with typed records, explicit guards, immutable updates and derived outputs. Its small size makes the relationship between requirements, code and behavior inspectable, which is valuable in an undergraduate project evaluation.

A second contribution is the treatment of planning as a protected transformation rather than unrestricted deletion. The capacity helper preserves occupied and reserved identities, chooses a deterministic removal order and reuses unused suffixes during expansion. This supplies a clear example of business rules that must remain stable even when the interface changes.

A third contribution is the evaluation method. The report preserves passing checks and failing checks together, distinguishes original tests from supplemental capture assertions and labels unexecuted recommendations. This avoids a common documentation weakness in which every desirable property is written as an achieved result. The evidence boundary is part of the engineering outcome.

### 8.5.1 Recommended Demonstration Narrative

A project presentation can begin with the initial Riverside counts, explain status versus kind, check in a fictional TN registration, show the changed bay and totals, check the vehicle out, expand a floor and create a new location. The presenter should then show the test summary and openly discuss the persistence and mobile findings. This narrative demonstrates both working software and the ability to evaluate it critically.

The final submission should replace candidate and signatory placeholders, confirm institutional wording with the guide and use the PDF as the pagination reference. The certificate and declaration require actual candidate review and institutional approval; a generated document does not supply either.

In conclusion, Parkline is a functional browser-local parking dashboard and a sound foundation for further software-engineering work. Its current achievement is a transparent, testable MVP—not an already deployed secure or sensor-connected parking platform. The proposed roadmap provides a disciplined way to extend that foundation while preserving its core invariants.
