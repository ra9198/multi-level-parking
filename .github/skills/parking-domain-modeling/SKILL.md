---
name: parking-domain-modeling
description: 'Model multi-level parking operations: levels, bays, occupancy, vehicle sessions, reservations, and capacity invariants. Use when changing parking rules, workflows, data shapes, or requirements.'
---

# Parking Domain Modeling

Use this skill before changing terminology, state transitions, or data structures for garage operations.

## Workflow
1. Identify the actor and event: arrival, departure, reservation, cancellation, or bay maintenance.
2. State the invariant before choosing a UI or storage shape.
3. Keep the concepts distinct:
   - A **level** contains a fixed set of bays.
   - A **bay** has a type and one operational status: available, occupied, or reserved.
   - A **parking session** binds one vehicle registration to one occupied bay from entry until checkout.
   - A **reservation** is a time-bound claim, not an occupied vehicle session.
4. Model state transitions in `src/lib/parking.ts`; keep UI rendering and persistence adapters outside those rules.
5. Add tests for the happy path, invalid transitions, duplicate active registrations, and empty/missing records.

## Invariants
- A bay belongs to exactly one level.
- A bay can have at most one active session; an active session refers to exactly one occupied bay.
- A reserved bay is not available for walk-in assignment and is not counted as occupied.
- Checkout removes the active session and makes its bay available.
- Capacity is the sum of bays across levels; available + occupied + reserved equals capacity.

## Current implementation boundary
The MVP stores sample bays and sessions in client memory. Do not describe this as durable or live sensor data. A future database/API must enforce the same invariants transactionally and handle concurrent arrivals.

## Related skills
- `parking-backend-data` for persistence and API seams.
- `tdd-workflow` for testing transitions.
- `security-review` when registration data or operator permissions change.

## Inspirations
This project-specific skill uses the concise, task-oriented skill structure seen in [ECC](https://github.com/affaan-m/ecc) and adapts domain-modeling practices from [Matt Pocock's skills](https://github.com/mattpocock/skills). It is original guidance, not copied skill content.
