<!-- page: references-local | REFERENCES -->
# REFERENCES
## Repository and Directly Inspected Sources

[1] Parkline project. **README.md — Parkline: Multi-Level Parking Operations.** Repository `ra9198/multi-level-parking`, reviewed revision `aa4b73016f271a7e0778c6c8bbd6c17346f52346`, 31 October 2026. Describes MVP scope, local persistence, commands and production next steps.

[2] Parkline project. **src/types/parking.ts.** Same reviewed revision. Authoritative declarations for BayStatus, BayKind, ParkingLevel, ParkingBay, ParkingSession, ParkingActivity and ParkingLocation.

[3] Parkline project. **src/lib/parking.ts.** Same reviewed revision. Authoritative implementation of occupancyForLevel, resizeLevelBays, normalizeTamilNaduPlate, checkIn and checkOut.

[4] Parkline project. **src/lib/parking-data.ts.** Same reviewed revision. Initial levels, bay statuses, registrations, sample activity, additional fixture locations and createManagedLocation.

[5] Parkline project. **src/components/parking-dashboard.tsx; src/app/page.tsx; src/app/layout.tsx; src/app/globals.css.** Same reviewed revision. UI behavior, state ownership, local persistence, routes, metadata and presentation.

[6] Parkline project. **src/lib/parking.test.ts; e2e/parking-workflows.spec.ts.** Same reviewed revision. Existing unit/fixture tests and three operator browser scenarios.

[7] Parkline project. **package.json; package-lock.json; tsconfig.json; next.config.ts; vitest.config.ts; playwright.config.ts; eslint.config.mjs.** Same reviewed revision. Dependency declarations, resolved toolchain, compiler and verification configuration.

[8] Next.js project. **Installed Next.js 16.4.3 documentation**, especially App Router server/client component and deployment guidance under `node_modules/next/dist/docs/01-app/`. Official documentation entry point: https://nextjs.org/docs. Installed package materials were inspected directly for this report.

[9] React project. **Managing State; Synchronizing with Effects.** Official learning documentation. https://react.dev/learn/managing-state and https://react.dev/learn/synchronizing-with-effects. Reader resources for state-driven rendering and effects; not a claim of a live documentation retrieval during this task.

[10] Microsoft. **The TypeScript Handbook.** https://www.typescriptlang.org/docs/handbook/intro.html. Reader resource for interfaces, union types and compile-time checking. Runtime storage-validation limitations were established from the project code, not inferred as solved by static types.

<!-- page: references-external | REFERENCES -->
## Standards, Official Tool Guidance and Books

[11] WHATWG. **HTML Living Standard — Web Storage.** https://html.spec.whatwg.org/multipage/webstorage.html. Normative reader resource for browser key/value storage and its scope.

[12] World Wide Web Consortium. **Web Content Accessibility Guidelines (WCAG) 2.2.** W3C Recommendation. https://www.w3.org/TR/WCAG22/. Evaluation framework only; this report does not certify conformance.

[13] OWASP Foundation. **HTML5 Security Cheat Sheet — Local Storage.** https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html. Reader resource for browser-storage trust and sensitive-data considerations.

[14] Vitest project. **Vitest Guide and Configuration Reference.** https://vitest.dev/guide/ and https://vitest.dev/config/. Tool documentation; executed unit outcomes are preserved in the accompanying result file.

[15] Microsoft. **Playwright Test Documentation.** https://playwright.dev/docs/intro. Tool guidance for browser scenarios, assertions and isolation. The environment-specific launcher used for this review is described in the evidence notes.

[16] Tailwind Labs. **Tailwind CSS v3 Documentation.** https://v3.tailwindcss.com/docs/installation. Version-family reader resource corresponding to the project's v3 dependency.

[17] Lucide project. **Lucide React Guide.** https://lucide.dev/guide/packages/lucide-react. Reader resource for the SVG icon component library.

[18] Sommerville, Ian. **Software Engineering.** 10th edition. Pearson, 2016. General reference for requirements, architecture, verification and project feasibility.

[19] Fowler, Martin. **Refactoring: Improving the Design of Existing Code.** 2nd edition. Addison-Wesley, 2018. General reference for maintainable decomposition and behavior-preserving change.

[20] OpenJS Foundation / Node.js project. **Node.js Documentation.** https://nodejs.org/docs/latest-v22.x/api/. Runtime reader resource. The observed review environment was Node.js 22.22.3; the repository's stated minimum remains 20.9.

[21] User-supplied college reference. **IMS_BCA_Project_Report.pdf**, `Example Docs/`, 115 pages. Used only as a formatting and report-organization reference. Its healthcare architecture, author identity, signatory names and implementation claims are not evidence about Parkline.

External links above are bibliographic reader resources. No external paper experiment, vendor benchmark or field survey is claimed. Source-level implementation claims in this report are grounded in items [1]–[8] and the accompanying executed evidence.
