---
name: tdd-workflow
description: 'Implement parking features or fixes with a focused red-green-refactor loop. Use when changing occupancy rules, sessions, bay assignment, validation, or user-facing workflows.'
---

# TDD Workflow

## Loop
1. Pick one vertical behavior and name its observable contract.
2. Add the smallest failing test at the highest useful seam. For parking rules, prefer `src/lib/parking.test.ts` and the pure functions in `src/lib/parking.ts`.
3. Run only that test and confirm it fails for the intended reason.
4. Implement the smallest change that makes it pass; do not weaken the assertion to fit the implementation.
5. Refactor while keeping the test green.
6. Add boundary cases: missing bay/session, duplicate registration, reserved bay, malformed input, and repeated checkout where relevant.
7. Run the broader tests, lint, typecheck, and build before finishing.

## Parking-specific cases
- Check-in only claims available bays and normalizes registration input.
- Duplicate active registrations are rejected.
- Reserved bays are not walk-in choices.
- Checkout releases the bay and removes its active session together.
- Occupancy counts exclude reservations from the occupied count.

## Reporting
Report the exact commands run and distinguish passing tests from checks blocked by missing tooling or external services.

## Related skills
- `parking-domain-modeling` defines the invariants.
- `e2e-testing` covers multi-step operator flows.
- `verification-loop` closes out the change.

## Inspirations
This original workflow is informed by the red-green-refactor emphasis in [ECC](https://github.com/affaan-m/ecc) and the vertical-slice testing approach in [Matt Pocock's skills](https://github.com/mattpocock/skills).
