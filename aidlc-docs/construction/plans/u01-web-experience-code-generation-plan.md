# U01 Web Experience Code Generation Plan

> **Single Source of Truth**: This document records the approved and completed U01 20-Step execution sequence.

## Approval Status

- **Infrastructure Design**: Approved on 2026-08-03.
- **Code Generation Part 1**: Approved on 2026-08-03.
- **Prototype Accessibility Scope Amendment**: Approved by the user on 2026-08-04.
- **Code Generation Part 2**: Completed on 2026-08-04.
- **Final Status**: **Code Generation Complete**.
- **Automatic GitHub Actions**: Paused; local and controlled manual workflow verification remain available.

## Unit Context

| Item | U01 scope |
|---|---|
| Primary story | US-007 multilingual and accessible common UI |
| Supporting stories | US-001 through US-006, US-008 through US-019, US-021 and US-027 |
| Functional rules | BR-U01-01 through BR-U01-28 |
| NFR | NFR-U01-01 through NFR-U01-30 |
| Property tests | P-U01-01 through P-U01-10 |
| Upstream contracts | U02 Identity/Profile/Consent/Feedback, U03 Feed/Detail/Search, U05 Recommendation/Conversation, U06 Notification/Admin/Incident, U07 OpenAPI/Error/Session/Runtime |
| Persistent data | None; browser cache is non-authoritative and protected state is purgeable |
| Runtime | React/TypeScript static SPA in a non-root read-only Web container behind Caddy |

## Prototype Accessibility Scope

The mandatory accessibility Gate consists of Playwright Chromium/Firefox/WebKit/mobile, axe, keyboard-only journeys, focus management, ARIA name/role/value and live-announcement assertions, and 200% zoom/320 CSS pixel reflow. Actual NVDA/Chrome or VoiceOver/Safari execution is **Out of Scope for Prototype** and retained as **Future Manual QA**. It was not executed and is not claimed as executed.

## Completed 20-Step Plan

### Step 1 - Registry, Runtime and Minimal Infrastructure Admission

- [x] Exact Node, pnpm and frontend dependencies were locked and frozen-install verified.
- [x] The minimal Web container and Compose resource/network/security contract passed.

### Step 2 - Frontend Workspace and Quality Skeleton

- [x] React/Vite/TypeScript strict workspace, formatting, lint, Vitest, axe, fast-check and Playwright were configured.
- [x] Initial production build and bundle budget passed.

### Step 3 - Generated OpenAPI Client and Typed Transport Boundary

- [x] The FastAPI OpenAPI document, generated TypeScript client and transport boundary were synchronized and drift-checked.

### Step 4 - Presentation Models and API Mappers

- [x] Typed presentation models and safe mapping/fallback rules were implemented and tested.

### Step 5 - URL Query, Filter and Pagination State

- [x] Canonical query parsing/serialization and P-U01-01 through P-U01-03 passed.

### Step 6 - Semantic UI and Accessibility Primitives

- [x] Native roles and accessible names are primary; stable `data-testid` is used only where a semantic selector is insufficient.
- [x] Field/error relationships, disclosures, live regions and remote states passed component and axe tests.

### Step 7 - Localization and Content Fallback

- [x] Korean/English resources, locale switching and fallback property P-U01-04 passed.

### Step 8 - Remote State, Cache and Failure Boundaries

- [x] Loading, ready, stale, degraded and error boundaries passed examples and P-U01-08.

### Step 9 - Protected State, Consent and Authorization

- [x] Consent purge, logout/operator denial and protected-state properties P-U01-05 and P-U01-10 passed.

### Step 10 - Feed, Detail and Back Journey

- [x] Feed filters, freshness, safe OTT navigation, detail transition and return context were implemented and tested.

### Step 11 - Search Journey

- [x] Search input, interpreted conditions, result announcement and normalized query behavior were implemented and tested.

### Step 12 - Recommendation Conversation Journey

- [x] Recommendation start/refine/reset, summary, reason and evidence disclosure were implemented; P-U01-07 passed.

### Step 13 - Account, Pending Intent and Consent Journey

- [x] Login replay/Pending Intent, account actions and consent withdrawal were implemented; P-U01-06 passed.

### Step 14 - Notifications and Admin Denial

- [x] Notification controls, operator isolation and non-disclosing Admin denial were implemented and tested.

### Step 15 - Privacy-Safe Browser Telemetry

- [x] Bounded telemetry rejects prompts, query/body data, direct identifiers and credentials; overflow/outage is non-blocking.

### Step 16 - Route Chunk, Asset and Performance Gates

- [x] Lazy route graph, asset policy, initial gzip 78,984 bytes and 4-request budget passed.

### Step 17 - Web Runtime, Caddy, Health and Network Integration

- [x] Unprivileged/read-only runtime, health endpoint, Caddy routing/security headers and Compose contracts passed.

### Step 18 - Synthetic Monitoring and Operational Evidence

- [x] Blackbox, Prometheus/Grafana mapping, Docker log rotation/Loki boundary and operator response evidence passed validation.

### Step 19 - Browser, Accessibility, Security and Supply-Chain Gates

- [x] Playwright Chromium/Firefox/WebKit/mobile passed 24 tests covering critical journeys, keyboard-only operation, focus, 200% zoom/reflow, Web Vitals and axe serious/critical violations = 0.
- [x] Testing Library semantic assertions cover role, accessible name, heading/landmark, live announcement and error relationships.
- [x] CSP, unsafe inline/eval, external URL, secret/source-map, frozen lock, dependency and license Gates passed with zero critical/high findings; three moderate findings are recorded.
- [x] Native screen-reader execution was explicitly dispositioned as Out of Scope for Prototype/Future Manual QA without claiming execution.

### Step 20 - Full Regression, Traceability and Code Summary

- [x] Frontend format/type/lint/build, 51 unit/component tests, 10 PBT tests, 8 contract tests, browser/accessibility/performance/security suites and all coverage thresholds passed.
- [x] Backend Ruff, strict MyPy, 326-test full regression, 53 PBT tests and 85.36% branch-aware coverage passed.
- [x] Real pgvector/PostgreSQL 17.10 integration passed 34 tests with zero skipped.
- [x] Compose base/local/remote, Caddy, Prometheus, frozen Web image build and OpenAPI/generated-client drift passed.
- [x] Story, BR, NFR and PBT traceability plus test evidence and code-generation summary were completed.
- [x] Steps 1 through 20, related Story checkboxes, state and audit were updated to Code Generation Complete.

## Story and Step Traceability

| Story group | Implementation steps | Verification steps |
|---|---|---|
| US-001 through US-003 | 4 through 8, 10 | 16, 19, 20 |
| US-004 through US-007 | 5 through 7, 11 | 16, 19, 20 |
| US-008 through US-013 | 4, 8, 12 | 16, 19, 20 |
| US-014 through US-018 | 8, 9, 13 | 15, 19, 20 |
| US-019, US-021, US-027 | 8, 9, 14 | 15, 18 through 20 |

## PBT Compliance

| Rule | Status | Evidence |
|---|---|---|
| PBT-01 | Compliant | P-U01-01 through P-U01-10 are explicitly identified and executed |
| PBT-02 through PBT-06 | Compliant | Round-trip, idempotence, commutativity, oracle, invariant and stateful properties passed |
| PBT-07 | Compliant | Reusable query, locale, form, remote-state and auth generators executed |
| PBT-08 | Compliant | Shrinking and fixed seed 260726 evidence recorded |
| PBT-09 | Compliant | Exact fast-check version locked and frozen-installed |
| PBT-10 | Compliant | Critical example tests passed beside every property family |

Frontend P-U01-01 through P-U01-10 passed. Backend Hypothesis PBT passed 53 tests with seed 260726.

## Release Gate Result

All prototype Code Generation Gates passed. PostgreSQL integration selection completed with skip=0; frontend success does not mask backend integration. Automatic GitHub Actions triggers remain paused under the existing repository policy and do not affect local U01 completion.

## Generated Evidence

- `aidlc-docs/construction/u01-web-experience/code/code-generation-summary.md`
- `aidlc-docs/construction/u01-web-experience/code/test-evidence.md`
- `aidlc-docs/construction/u01-web-experience/code/traceability.md`
