# Parkline: Multi-Level Parking Operations

A web-based garage operations dashboard starter built with Next.js, TypeScript, React, Tailwind CSS, and npm.

## Current MVP

- Overview of total, occupied, available, and reserved bays across three levels.
- Four garage locations with independent sample inventory: Riverside Centre, Marina Mall (Velachery), VR Mall (Anna Nagar), and Phoenix Mall (OMR).
- Add locations with a configurable number of floors and bays per floor; edit each floor's capacity from the planning dialog.
- Capacity planning supports 1–10 floors and 1–99 bays per floor; reducing capacity cannot remove occupied or reserved bays.
- Floor selector with a visual 24-bay map for each level.
- Search bays by bay ID or vehicle registration and filter by status.
- Check vehicles in to an available bay and check active sessions out.
- Validate Tamil Nadu vehicle registrations in the `TN01AA1234` format (two RTO digits, two series letters, four digits).
- Recent activity list and floor-level capacity summaries.
- Responsive dashboard with keyboard-accessible controls and status feedback.

Location capacity, new locations, and session changes are saved in this browser's local storage. This is device-local demo persistence, not a shared database. There is no authentication, payment processing, reservation workflow, sensor connection, or live occupancy feed. This is a functional UI/domain-logic MVP, not a production parking system.

## Run locally

Requires Node.js 20.9 or newer and npm.

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Checks

```bash
npm test
npm run lint
npm run typecheck
npm run build
```

The parking transition tests are in `src/lib/parking.test.ts`.

Browser tests use Playwright. After installing dependencies, install a browser once with `npx playwright install chromium`, then run `npm run test:e2e`.

## Project skills

Workspace-specific GitHub Copilot skills live under `.github/skills/`:

- `parking-domain-modeling`: parking terms, state transitions, and invariants.
- `parking-frontend`: dashboard interaction, accessibility, and responsive UI.
- `parking-backend-data`: future API/persistence and concurrency design.
- `tdd-workflow`: focused red-green-refactor workflow.
- `security-review`: identity, registration privacy, and operational safety.
- `e2e-testing`: browser workflows for check-in/out and occupancy.
- `verification-loop`: evidence-based test and build closeout.

`.github/copilot-instructions.md` describes the project-wide conventions. These skills are original, project-specific adaptations, not copies or installations of the referenced repositories:

- [Everything Claude Code (ECC)](https://github.com/affaan-m/ecc)
- [Matt Pocock's Skills](https://github.com/mattpocock/skills)

## Next steps for production

1. Confirm operational rules for reservations, pricing, grace periods, and accessible/EV bay assignment.
2. Add a server-side data store and transactional check-in/check-out operations.
3. Add operator authentication, role-based authorization, audit history, and registration-data retention rules.
4. Integrate and monitor sensors only after defining device identity, stale-data handling, and manual override behavior.
5. Add payment processing through a compliant provider if payment collection is in scope.
