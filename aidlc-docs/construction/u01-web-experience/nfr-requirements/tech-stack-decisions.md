# U01 Web Experience Technology Stack Decisions

## Version Verification Basis

Verified on 2026-08-03 against official project sources:

- Node.js v24 is an LTS line; the official archive identified v24.18.0 as the latest LTS patch at verification time.
- React official documentation identifies 19.2 as the latest documented release line.
- Vite official releases identify 8.1 as the regularly patched stable line.
- fast-check official documentation supports package-manager installation and automatic shrinking; version 4 requires TypeScript 5 or newer.

Exact dependency versions will be resolved from the package registry during Code Generation and pinned in `pnpm-lock.yaml`. Pre-release versions are prohibited. A clean frozen-lockfile install is a blocking reproducibility gate.

## Core Runtime and Build

| Area | Decision | Rationale |
|---|---|---|
| Runtime | Node.js 24 LTS, pinned to an approved patch in `.node-version` and container image digest | production-supported LTS and deterministic local/container execution |
| Package manager | Corepack-managed pnpm with committed lockfile and frozen installs | strict, efficient, reproducible dependency graph |
| UI | React 19.2 release line | selected by the user; stable current React line |
| Language | TypeScript with all strict checks and `noUncheckedIndexedAccess` | protects transport mapping and state machines |
| Build | Vite 8.1 release line | current supported stable line, route chunking and manifest support |
| Delivery shape | Client-side SPA served as immutable static assets behind existing Caddy/API origin | matches application design and avoids a second business server runtime |

## Application Libraries

| Concern | Decision | Boundary |
|---|---|---|
| Routing | React Router | canonical URL and guarded route composition only |
| Server state | TanStack Query | remote cache, cancellation, stale and retry policy |
| Forms | React Hook Form + Zod | accessible field state and client schema; server remains authoritative |
| API | OpenAPI-generated TypeScript client plus thin presentation mappers | no hand-maintained duplicate transport types |
| i18n | i18next + react-i18next | Korean/English resources and explicit fallback chain |
| Styling | CSS Modules + CSS custom properties | scoped styles, design tokens, low runtime cost |
| Headless UI | minimal accessibility-reviewed primitives only where native elements are insufficient | prevents opaque theme/component coupling |

Global application state library is not selected initially. URL, TanStack Query, form and component state retain distinct ownership. A new global store requires a demonstrated cross-route client-only use case and an architecture decision update.

## Test Stack

| Layer | Tool | Gate |
|---|---|---|
| Unit/component | Vitest + Testing Library + user-event | business rules, semantic interactions and error states |
| API isolation | MSW | OpenAPI-aligned success, delay, partial failure and error scenarios |
| Accessibility | axe-core, Testing Library semantic assertions and Playwright browser matrix | axe violations, keyboard-only journeys, focus management, ARIA name/role/value, announcements and 200% zoom/reflow; native screen-reader execution is Future Manual QA outside prototype scope |
| Property based | fast-check integrated with Vitest | P-U01-01~10, shrinking enabled, replay seed logged |
| Browser E2E | Playwright | Chromium, Firefox, WebKit and mobile viewport critical journeys |
| Performance | Playwright/browser metrics plus build manifest budget script | Core Web Vitals scenarios and route bundle budget |

PBT does not replace examples. Each critical journey has explicit examples, while generated tests validate round-trip, idempotence, commutativity, oracle, invariant and stateful properties. A minimal shrunk production defect becomes a permanent example regression test.

## Static Quality and Supply Chain

- TypeScript strict compile is mandatory with no emitted build on type errors.
- ESLint uses type-aware rules; formatting is deterministic and separately checked.
- dependency versions are exact through the lockfile; CI uses frozen installs.
- generated OpenAPI client changes must be committed and drift-check clean.
- license and vulnerability audit runs against production and development dependency sets.
- build emits a manifest used for route-chunk and gzip budget checks.
- source maps are generated only for private error-analysis upload and excluded from public assets.

## Security Integration

- Authentication uses backend-managed HttpOnly cookies; UI never accepts a token prop.
- A shared API boundary obtains and attaches the server CSRF value for mutations.
- Caddy supplies CSP and other response headers; Vite output contains no inline runtime configuration requiring `unsafe-inline`.
- runtime configuration exposes only public values such as API base path and release version.
- external OTT links pass typed URL mapping, provider allowlist and safe anchor attributes.

## Deployment and Operations Integration

- production output is a static `dist` artifact copied into a pinned web-server/container stage or Caddy-served volume according to U01 Infrastructure Design.
- browser routes fall back to `index.html`; `/api`, health and metrics routes retain existing backend routing.
- hashed assets use long immutable cache; HTML and runtime config use revalidation.
- release version is injected at build time for safe telemetry correlation.
- frontend telemetry is optional centralized search/analysis data and never the source of truth for server audit or domain events.

## Deferred Exact-Version Gate

Code Generation must, before implementation:

1. query official registries for all selected packages;
2. reject deprecated, pre-release or mutually incompatible versions;
3. create `package.json`, `pnpm-lock.yaml` and `.node-version` from the same verified set;
4. execute clean `pnpm install --frozen-lockfile`, typecheck and production build;
5. document any deviation from Node 24 LTS, React 19.2 or Vite 8.1 before coding proceeds.

## Sources

- [Node.js releases](https://nodejs.org/en/about/previous-releases)
- [Node.js v24 archive](https://nodejs.org/en/download/archive/v24)
- [React versions](https://react.dev/versions)
- [Vite releases](https://vite.dev/releases)
- [fast-check getting started](https://fast-check.dev/docs/introduction/getting-started/)
- [fast-check v4 migration requirements](https://fast-check.dev/docs/migration-guide/from-3.x-to-4.x/)
