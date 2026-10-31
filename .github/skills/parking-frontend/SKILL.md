---
name: parking-frontend
description: 'Build or change the Parkline Next.js and React parking operations UI. Use for dashboard layout, level maps, bay controls, check-in/out forms, responsive behavior, accessibility, and visual polish.'
---

# Parking Frontend

## Workflow
1. Read the relevant route/component and domain types before editing.
2. Keep operational tasks visible in the first viewport: occupancy, level selection, bay status, and arrival/departure actions.
3. Use typed props and state; delegate transitions and validation to `src/lib/parking.ts`.
4. Every interactive control needs a real action, an accessible name, keyboard focus, and a clear disabled/empty/error/success state.
5. Keep bay status distinguishable by both label/shape and color. Preserve compact, scannable layouts on small screens.
6. Verify floor changes, search, filters, check-in, checkout, and narrow viewport behavior.

## Guardrails
- Do not imply mock records are live telemetry.
- Do not add dead navigation, fake billing, or controls that only look interactive.
- Use existing `lucide-react` icons for controls and keep touch targets usable.
- Respect reduced-motion preferences and avoid layout shifts during status updates.

## Related skills
- `parking-domain-modeling` for bay/session semantics.
- `e2e-testing` for user workflows.
- `verification-loop` for the final evidence pass.

## Inspirations
The workflow is adapted for this app from skill design patterns in [ECC](https://github.com/affaan-m/ecc) and engineering practices in [Matt Pocock's skills](https://github.com/mattpocock/skills); no upstream skill text is included.
