<!-- page: c5-software | Chapter 5: TECHNOLOGIES AND TOOLS USED -->
# CHAPTER 5 — TECHNOLOGIES AND TOOLS USED
## 5.1 Software Requirements and Dependency Baseline

Parkline is built with Next.js, React, TypeScript and a CSS/PostCSS toolchain. The package manifest declares the application scripts, while `package-lock.json` records resolved dependencies. The report distinguishes exact manifest pins from version ranges: an entry such as `^5.7.2` is an allowed range, not a claim that every installation uses precisely 5.7.2 [7].

**Table 5.1: Technology baseline declared by the repository**

| Category | Package / tool | Manifest declaration | Role |
|---|---|---|---|
| Application framework | next | 16.4.3 | App Router, development server and production build |
| UI runtime | react / react-dom | 19.0.0 / 19.0.0 | Components, hooks and DOM rendering |
| Language tooling | typescript | ^5.7.2 | Static type checking and build integration |
| Styling | tailwindcss | ^3.4.17 | CSS utility framework and directives |
| CSS processing | postcss / autoprefixer | ^8.5.32 / ^10.4.20 | Stylesheet processing and prefix handling |
| Icons | lucide-react | ^0.468.0 | Consistent interface icons |
| Linting | eslint / eslint-config-next | ^9.39.5 / 16.4.3 | Configured source checks |
| Unit testing | vitest / vite | ^5.0.5 / ^7.3.7 | Node-based tests and transform toolchain |
| Browser testing | @playwright/test | ^1.64.1 | End-to-end operator scenarios |

The documentation environment used Node.js 22.22.3 and npm 10.9.8. A machine-readable resolved-version inventory is included with the report source. These environment facts support reproducibility but do not imply that another lockfile or future dependency update will produce identical results.

No database driver, authentication library, payment SDK or sensor integration package is declared for the current application. A framework dependency alone does not establish such capabilities. The technology chapter therefore explains the actual frontend and verification stack instead of substituting the reference report's unrelated Java and database technologies.

<!-- page: c5-hardware | Chapter 5: TECHNOLOGIES AND TOOLS USED -->
## 5.2 Hardware and Execution Environment

The application is a browser-based MVP rather than hardware-dependent parking equipment. It does not require a gate controller, occupancy sensor, camera, RFID reader or charging-station controller. The documentation was prepared by running a local production build and opening it with headless Chromium for repeatable screen capture.

The repository specifies Node.js 20.9 or newer. It does not publish measured minimum RAM, CPU, disk or browser-version requirements. Consequently, the hardware guidance below is a practical planning recommendation, not an experimentally established minimum.

**Table 5.2: Execution needs and unmeasured planning guidance**

| Environment | Required capability | Qualification |
|---|---|---|
| Development workstation | Supported Node.js, npm, editor and modern browser | Repository states the Node baseline; no hardware benchmark provided |
| Dependency installation | Network access to the npm registry and adequate disk | Lockfile dependencies must be downloadable |
| Unit/static verification | Ability to run Node processes | Browser installation not required for Vitest, lint or type checks |
| Browser verification | Compatible Chromium or another configured Playwright browser | Browser binaries and platform libraries are separate prerequisites |
| Demonstration server | Ability to bind and serve the Next.js application | A local server is not a shared parking backend |
| End-user browser | JavaScript and usable local storage | Data belongs to that browser profile and origin |

For a remote preview, the server should bind to an externally reachable interface and accept the deployment host. Browser-facing requests must use the served application origin, not a developer's localhost address. The current dashboard does not call a separate backend, which simplifies preview networking.

A future field installation would need an independent infrastructure specification: terminal hardware, network connectivity, power recovery, shared database capacity, backup media, physical integrations and monitoring. None of those requirements can be validated from the present UI alone.

The report's screenshots are evidence of software rendering in the tested Chromium environment. They do not certify kiosk suitability, low-end-device performance, touch ergonomics or behavior during power and network failures.

<!-- page: c5-typescript | Chapter 5: TECHNOLOGIES AND TOOLS USED -->
## 5.3 Programming Languages Used
### 5.3.1 TypeScript for Domain and Application Logic

TypeScript is used for the domain records, pure transition helpers, fixture generation, dashboard state and test code. The compiler configuration enables strict checking and no-emit type verification. The `@/*` path alias resolves to the source directory, reducing fragile relative imports and keeping UI-to-domain dependencies readable.

The domain's union types constrain status and kind vocabularies, while interfaces make relationships explicit. Function signatures document the inputs required for a transition and the paired collections returned afterward. For example, a check-in cannot be called without a bay ID, registration, vehicle string and start timestamp according to its source type. That compile-time contract still permits invalid string content, so runtime guards remain necessary.

### 5.3.2 TSX and Declarative Markup

The dashboard uses TSX to express the visual hierarchy and attach typed event handlers. A form submission prevents the default browser action, calls a transition or planning helper and updates React state. Rendering is conditional: a dialog appears only when its mode is active, a notice appears when text is present and an empty-map message appears when filtering produces no bays.

### 5.3.3 CSS and Configuration Data

CSS defines the visual tokens, component layouts, responsive breakpoints, focus styles and reduced-motion behavior. JSON is used in package manifests, TypeScript configuration and browser persistence. The saved JSON is a serialization format, not a database schema and not a runtime type validator.

The report-generation utilities use Python and a small Node-based capture script as documentation tooling. They are not part of the parking application's runtime stack. This distinction matters because producing a PDF should not imply that the application itself has a Python backend.

The language choices support a single main frontend toolchain with focused verification. Future server code could reuse domain concepts, but security and concurrency requirements would still need to be enforced at the new trusted boundary rather than inherited automatically from TypeScript declarations.

<!-- page: c5-react | Chapter 5: TECHNOLOGIES AND TOOLS USED -->
## 5.4 React State, Derived Values and Effects

React supplies `useState`, `useMemo`, `useEffect` and `useTransition` in the dashboard. State hooks hold the selected location and level, the operation collections, search/filter values, dialog inputs, notices and planning drafts. A state update causes the visible interface to be recalculated from the current snapshot [5, 9].

Derived values include the selected location, its current operation collections, the selected level's bays, floor statistics and total statistics. `filteredBays` is calculated with `useMemo`, combining the status condition with an ID/registration substring check. The memo does not make the whole dashboard constant-time: `levelBays` is constructed during render, and many counts still scan arrays. This is a reasonable small-data design, not a demonstrated optimization guarantee.

Effects manage the browser storage boundary. The first effect reads and parses a saved value, then schedules restored state through a transition. A second effect writes serialized state once the readiness flag is enabled. This keeps side effects out of the pure domain helpers but creates a responsibility to coordinate initialization and saving correctly. The recorded reload failure shows why effect presence alone is insufficient evidence of reliable restoration.

`useTransition` marks restoration-related state updates as transition work. It is a rendering-scheduling mechanism, not a data transaction, lock or durability guarantee. The flag named `storageReady` prevents unconditional writes before the read path completes, but the interaction between deferred restoration and later writes needs a regression-focused review.

A maintainability improvement would be to isolate persistence into a dedicated hook with an explicit loading state, schema validation and a canonical stored representation. Session and capacity UI could then become smaller components. Such a refactor should preserve the existing domain helper tests and add repeated-load tests before changing behavior.

React's role in this project is therefore state-driven presentation. Authority over physical inventory, authenticated identity and multi-user conflict resolution remain outside the current browser architecture.

<!-- page: c5-next | Chapter 5: TECHNOLOGIES AND TOOLS USED -->
## 5.5 Next.js Routing, Layout and Build

Next.js provides the application entry point, build pipeline and serving commands. The App Router files in `src/app` contain a root layout and a home page. The page imports and returns `ParkingDashboard`; the layout imports global CSS, sets metadata and wraps children in an English-language HTML document. The production build classified `/` as a prerendered route in the recorded run [8].

There are no parking API route handlers, server actions or database repositories in this source tree. The root page can be server-composed while the dashboard hydrates into an interactive client component. That combination should not be described as a full client-server parking operations backend.

**Table 5.3: Application entry files and relevant configuration**

| File | Responsibility | Important interpretation |
|---|---|---|
| `src/app/page.tsx` | Render the dashboard route | No parking business logic in the route |
| `src/app/layout.tsx` | Metadata, global CSS and root document | Description includes “Live”; not proof of telemetry |
| `src/app/globals.css` | Global and component styling | Responsive presentation, not physical floor geometry |
| `next.config.ts` | Next.js configuration | Development origin setting is not authentication |
| `next-env.d.ts` | Generated framework type declarations | Tooling support, not domain data |
| `tsconfig.json` | Compiler settings and source alias | Static checking only |

The scripts separate development, production compilation and production serving. `npm run dev` starts the development server. `npm run build` creates production output. `npm run start` serves that output. Production screenshots in this report were captured after a successful build, avoiding development overlays as a source of visual evidence.

The repository's agent guidance explicitly warns that installed Next.js documentation should be consulted before changing framework code. This documentation task did not need to alter route behavior or framework configuration. The report uses the installed documentation to explain the current boundary rather than assuming an older Next.js convention.

<!-- page: c5-styling | Chapter 5: TECHNOLOGIES AND TOOLS USED -->
## 5.6 Styling, PostCSS and Iconography

Tailwind CSS is configured through `tailwind.config.ts` and included with base, component and utility directives at the beginning of the global stylesheet. PostCSS and Autoprefixer form part of the stylesheet build pipeline. The dashboard's main visual language, however, is expressed in named CSS classes such as `metric-grid`, `parking-panel`, `bay-occupied`, `management-modal` and `form-error` [16].

This arrangement combines a framework foundation with application-specific component styling. CSS custom properties define the colors, radius and shadow so that repeated panels and controls remain visually coherent. The desktop layout separates a fixed-width sidebar, a main content region and a right-hand information column. Smaller breakpoints reduce the sidebar, stack the content and change the bay grid from six columns to four.

Lucide React supplies SVG icons for locations, layers, vehicles, arrivals, departures, settings, search, accessibility and EV indicators [17]. Icons are embedded within buttons or paired with visible text. A visual icon is not an operational integration: a lightning symbol does not imply charging-station communication, and a bell does not imply a notification service.

**Table 5.4: Styling mechanisms and their practical role**

| Mechanism | Example | Role in the MVP |
|---|---|---|
| CSS variables | `--green`, `--canvas`, `--radius` | Shared visual tokens |
| State classes | `bay-available`, `bay-occupied`, `bay-reserved` | Visual occupancy categories |
| Grid and flex layout | Metrics, bay map, heading actions | Adaptive arrangement of panels and controls |
| Media queries | 1150 / 900 / 620 pixels | Breakpoint-specific presentation |
| Focus-visible outline | Buttons, links, inputs and selects | Keyboard focus indication |
| Reduced-motion query | Animation/transition overrides | Reduced visual motion preference |
| SVG components | `CarFront`, `Zap`, `Accessibility` | Consistent pictorial cues |

The observed mobile overflow illustrates a limitation of breakpoint-based styling: changing grid structure does not automatically guarantee that every child can shrink or wrap. Verification must inspect the rendered geometry and real action controls, not simply count media queries.

<!-- page: c5-testing-tools | Chapter 5: TECHNOLOGIES AND TOOLS USED -->
## 5.7 Unit, Browser and Static Verification Tools

Vitest is configured to run `src/**/*.test.ts` in a Node environment. The suite imports the pure domain helpers and managed-location data directly. This keeps tests fast and independent of browser layout. The existing file contains nine test cases covering occupancy, normalization through check-in, rejection paths, checkout, resizing, fixture consistency and new-location construction [6, 14].

Playwright is configured with the `e2e` test directory, a Chromium desktop project, a base URL and a web-server command for local development. It exercises three operator workflows. During documentation, an environment-specific runner used an available Chromium binary and the already running production server; the test scenario source itself was not changed. The recorded final run had two passing scenarios and one failed reload assertion [15].

ESLint uses the Next.js core-web-vitals and TypeScript configurations. TypeScript's `--noEmit` mode checks source without producing application JavaScript. The production build adds another compilation and route-generation gate. These tools answer different questions and are reported separately.

**Table 5.5: Verification commands and evidence categories**

| Command / script | Evidence category | Documentation-run result |
|---|---|---|
| `npm test` | Existing unit tests | Nine passed |
| `npm run lint` | Configured static lint | Passed |
| `npm run typecheck` | Source type consistency | Passed |
| `npm run build` | Production compilation | Passed |
| Playwright existing scenarios | Browser integration | Two passed; one failed after reload |
| `capture-report-evidence.mjs` | Supplemental report checks/screens | Fifteen passed; one mobile overflow check failed |

The supplemental script is documentation tooling. It is retained for reproducible screen capture and does not replace or inflate the original unit-test count. A successful script process exit means the evidence was collected; individual assertion statuses must be read from its JSON output. This distinction is especially important because the script intentionally records failures and continues to capture the remaining screens.

<!-- page: c5-workflow | Chapter 5: TECHNOLOGIES AND TOOLS USED -->
## 5.8 Development Workflow and Reproducibility

The repository uses npm scripts as the common interface for installation, verification and serving. A reproducible review starts from the checked-out revision and lockfile, installs dependencies, runs the static and unit checks, builds the application and only then captures browser behavior. The report source records the review date and source commit so that later changes are not confused with the documented baseline.

```bash
npm ci
npm test
npm run lint
npm run typecheck
npm run build
npm run start -- --hostname 0.0.0.0 --port 3000
```

Browser tests additionally need a browser installation and platform libraries. On a normally configured workstation, `npx playwright install chromium` provides the default browser binary. Restricted environments may require an explicitly supplied compatible binary. That environment accommodation is not a parking feature and should not be copied into production configuration without review.

The report-generation workflow reads editable metadata and Markdown chapter sources, then produces a PDF and Word document from the same content. Genuine application screenshots and deterministic diagrams are retained as assets. The generated PDF has a fixed page count verified by a PDF parser. Word pagination can vary with installed fonts and layout engine, so the PDF is the submission pagination reference.

Documentation output is kept separate from runtime application code. The report does not introduce a database dependency, alter parking rules or repair defects discovered during evaluation. This preserves the meaning of the test baseline and lets the project team decide how to prioritize the findings.

A final reproducibility caution concerns time-based fixtures. Some seed timestamps are generated at module evaluation, and the UI contains static date text. Counts and identities are suitable for deterministic checks, but relative ages and generated timestamp-based IDs may differ between runs. The documentation therefore records expected invariants rather than pretending every serialized byte is stable.
