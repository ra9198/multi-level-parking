---
name: parking-backend-data
description: 'Design future parking APIs, database persistence, validation, and concurrency controls. Use when replacing the in-memory demo store or adding server actions, routes, or a database.'
---

# Parking Backend and Data

The current app has no backend. Apply this skill only when a real persistence/API slice is requested.

## Design sequence
1. Keep the domain contract in `src/types/parking.ts` and transition rules in `src/lib/parking.ts` as the starting interface.
2. Define ownership and authorization before exposing garage data or mutations.
3. Choose durable records for garages, levels, bays, reservations, and parking sessions. Give each record stable IDs and timestamps.
4. Enforce check-in atomically: lock/claim an available bay, reject a duplicate active registration, create the session, and mark the bay occupied in one transaction.
5. Enforce checkout atomically: close the active session and release its bay together. Make retries idempotent.
6. Validate request shape and business rules at the server boundary; return typed success/error results without leaking internal details.
7. Add migration, rollback, concurrency, and permission tests before connecting the UI.

## Boundary rules
- Separate a repository interface from its database adapter so domain tests do not require a live database.
- Do not trust client-supplied bay status, session duration, prices, or operator identity.
- Model reservations with time windows and explicit lifecycle rules; do not treat them as occupied sessions.
- Keep payment processing, access control, and sensor ingestion as separate integrations with explicit failure behavior.

## Related skills
- `parking-domain-modeling` for invariants.
- `security-review` for identity and data handling.
- `tdd-workflow` for transaction and retry behavior.

## Inspirations
This original, project-specific workflow references [ECC](https://github.com/affaan-m/ecc) for backend/API skill structure and [Matt Pocock's skills](https://github.com/mattpocock/skills) for interface-first design and explicit behavior.
