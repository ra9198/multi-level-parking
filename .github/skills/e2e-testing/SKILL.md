---
name: e2e-testing
description: 'Plan and run browser-level tests for parking dashboard workflows with Playwright. Use for check-in/out, level switching, filters, responsive layout, and regression coverage.'
---

# End-to-End Testing

## Workflow
1. Start the app using its documented dev command and confirm the dashboard renders.
2. Use role- and label-based locators; avoid CSS selectors tied to decorative markup.
3. Cover one complete arrival: open the form, enter a registration, choose a bay, submit, and verify occupancy plus activity.
4. Cover checkout: choose an active vehicle, submit, and verify the bay becomes available and the activity updates.
5. Cover level tabs, bay search, status filtering, reserved-bay behavior, validation errors, and empty results.
6. Run key flows at desktop and mobile viewport sizes. Check keyboard operation and dialog dismissal.
7. Keep fixture data deterministic and reset state between tests. Do not assert live sensor or backend behavior in this demo.

## Assertions
- Prefer visible user outcomes: bay status, registration, counts, and accessible feedback.
- Wait for a state change rather than fixed delays.
- Capture screenshots only for meaningful layout regressions; avoid brittle pixel assertions for dynamic text.

## Related skills
- `parking-frontend` for accessibility and responsive behavior.
- `parking-domain-modeling` for expected state changes.
- `verification-loop` for test evidence.

## Inspirations
This original workflow adapts the E2E skill category in [ECC](https://github.com/affaan-m/ecc) and interface-first test thinking from [Matt Pocock's skills](https://github.com/mattpocock/skills).
