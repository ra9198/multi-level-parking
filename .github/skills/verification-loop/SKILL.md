---
name: verification-loop
description: 'Verify a parking application change before reporting it complete. Use after implementation to run focused tests, lint, typecheck, build, and check the changed behavior.'
---

# Verification Loop

## Procedure
1. Identify the changed behavior and the cheapest test that could falsify the implementation.
2. Run the focused unit/component test first; repair and rerun failures in the same slice.
3. Run `npm test`, `npm run lint`, `npm run typecheck`, and `npm run build` when available and relevant.
4. For UI changes, run the affected Playwright workflow and inspect desktop/mobile output when browser tooling is available.
5. Inspect the final diff for unrelated changes and verify docs/config match actual behavior.
6. Report commands and outcomes exactly. Explicitly mark checks not run because of missing runtimes, dependencies, credentials, or integrations.

## Parking-specific assertions
- Capacity is partitioned into available, occupied, and reserved bays.
- Active sessions and occupied bays remain consistent after each transition.
- Search/filter/floor selection do not mutate inventory.
- Demo mode and absent external integrations are clearly documented.

## Related skills
- `tdd-workflow` for the implementation loop.
- `e2e-testing` for browser workflows.
- `security-review` when identity or real customer data is involved.

## Inspirations
The evidence-based closeout pattern is adapted for this app from [ECC](https://github.com/affaan-m/ecc) and [Matt Pocock's engineering skills](https://github.com/mattpocock/skills). This is an original workflow, not an upstream copy.
