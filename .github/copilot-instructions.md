# Parkline project instructions

## Stack and scope
- This is a Next.js App Router application using TypeScript, React, Tailwind CSS, and npm.
- The current MVP is a client-side parking operations dashboard backed by typed sample data. Location, capacity, and session changes persist in browser local storage, not a shared database.
- Garage managers can add locations and set 1–99 bays per floor; capacity reductions must preserve occupied and reserved bays.
- Do not claim that occupancy is real-time, or that sensors, payments, reservations, authentication, or a backend are connected. Some reserved bays are sample records only.
- Preserve the parking invariants in `src/lib/parking.ts`: only an available bay can be occupied, an active registration cannot have two sessions, and checkout releases the session's bay.

## Code organization
- Route and metadata: `src/app/`.
- User-facing dashboard: `src/components/`.
- Parking rules and sample fixtures: `src/lib/`.
- Shared domain types: `src/types/`.
- Add focused tests next to the domain module. Use the `parking-domain-modeling`, `parking-frontend`, `parking-backend-data`, `tdd-workflow`, `security-review`, `e2e-testing`, and `verification-loop` skills when their descriptions match the task.

## Engineering expectations
- Validate user input at the point that owns the state transition; keep domain rules out of presentation-only code.
- Keep components accessible: labels, keyboard operation, visible focus, semantic status, and responsive layouts.
- Prefer small, testable changes and preserve existing behavior. Do not add a persistence provider or third-party integration unless asked.
- Before claiming completion, run the focused tests, `npm run lint`, `npm run typecheck`, and `npm run build` when tooling is available; report any unavailable checks honestly.
