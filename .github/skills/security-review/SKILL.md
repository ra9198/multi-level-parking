---
name: security-review
description: 'Review parking application changes for authentication, authorization, registration-data privacy, payment security, input validation, and operational safety. Use before adding backend access or handling real customer data.'
---

# Security Review

The current MVP is an in-memory demo with no authentication, backend, or payment flow. Reassess the full request path before any production integration.

## Review checklist
- Identify the actor, resource, and permission for every read/write operation; enforce authorization on the server, not only in the UI.
- Treat registration plates and visit times as personal data: minimize collection, restrict access, set retention rules, and avoid unnecessary logs.
- Validate and normalize all input server-side. Never trust client-provided garage, bay, status, session, or operator identifiers.
- Protect session and bay transitions against races, replay, duplicate submission, and ID guessing.
- Keep secrets out of client bundles and repository files. Use environment variables and least-privilege credentials.
- If payments are added, use a compliant provider-hosted flow; do not store card data. Verify signed webhooks and make event handling idempotent.
- For hardware/sensor input, authenticate devices, validate freshness, and define a manual override and outage procedure.
- Test denied access, malformed input, duplicate requests, and failure recovery.

## Output
List findings by severity with concrete affected behavior and a fix. State what was not inspected; do not claim a formal compliance certification.

## Related skills
- `parking-backend-data` for server/data boundaries.
- `parking-domain-modeling` for state transitions.
- `verification-loop` for recording security checks.

## Inspirations
This project-specific checklist takes the security-skill approach from [ECC](https://github.com/affaan-m/ecc) and adapts it to parking workflows; it does not reproduce upstream text. [Matt Pocock's skills](https://github.com/mattpocock/skills) informed the concise, actionable workflow style.
