# U01 Web Experience Logical Components

## Runtime Topology

| Boundary | Logical component | Responsibility | Must not own |
|---|---|---|---|
| Browser boot | `RuntimeConfigLoader` | same-origin public config validation | secret or credential |
| Browser shell | `AppShell` | routing, locale, navigation, fatal boundary | domain decisions |
| Transport | `ApiClientBoundary` | generated client, CSRF, cookie request, abort, typed HTTP outcome | UI rendering or token exposure |
| Mapping | `PresentationMapperRegistry` | transport-to-view mapping, URL validation, fallback labeling | backend entity mutation |
| Remote state | `QueryCoordinator` | namespace keys, coalescing, retry, stale projection | persistent business state |
| Protected cleanup | `ProtectedStatePurgeCoordinator` | cancel/remove protected state atomically | server consent decision |
| Authentication | `AuthenticationRecoveryCoordinator` | single-flight 401 recovery and one-time Pending Intent | credentials or authorization decision |
| Accessibility | `SemanticPrimitiveLayer` | native-first widgets and interaction contracts | page business flow |
| Navigation | `FocusAndRouteCoordinator` | route announcement and focus restoration | query data |
| Observability | `BrowserTelemetryAdapter` | allowlist, sanitize, bounded batch and send | audit record or raw user input |
| Build quality | `FrontendQualityGate` | type, lint, tests, a11y, browser, bundle, audit gates | runtime behavior |

## API Client Boundary

### Input

- generated OpenAPI operation and typed request;
- `AbortSignal` for reads;
- mutation metadata containing CSRF intent and optional idempotency key.

### Output

A discriminated transport outcome: `success`, `validation`, `unauthenticated`, `forbidden`, `conflict`, `rateLimited`, `serverFailure`, `networkFailure`, or `aborted`. Raw exceptions do not cross this boundary.

### Constraints

- credential mode and CSRF attachment are centralized;
- at most one authentication recovery is active;
- 401 replay is restricted to safe read or explicitly replayable command;
- response body is never logged by the browser telemetry adapter.

## Query Coordinator

The coordinator owns query key factories for public, member, recommendation and admin scopes. Each policy declares stale time, garbage collection time, retry class and cancellation support. Components receive hooks/adapters, not raw query client mutation access.

| Event | Cancel | Remove | Follow-up |
|---|---|---|---|
| logout | member, recommendation, admin | protected caches and drafts | public route |
| consent withdrawal | personalization and feedback | conversation, personalized projections | non-personalized refresh |
| recommendation reset | current recommendation session | turns, conditions, results | empty recommendation form |
| admin 403 | admin | admin cache and drafts | access-denied route |

## Page and Region Composition

Each route owns a `RouteBoundary`, page heading and route-level data orchestration. Each independently recoverable data panel uses `RemoteRegion` with typed state, error message, timestamp and scoped retry. Content cards and semantic primitives remain pure presentation components.

Page modules cannot directly access cookie, CSRF token, global query client, telemetry transport or raw OpenAPI response. They use narrow adapters from the logical component layer.

## Semantic Primitive Layer

| Primitive | Contract |
|---|---|
| `Button`/`Link` | native semantics, visible focus, disabled vs unavailable distinction |
| `Field` | stable label, hint/error IDs, described-by composition |
| `ErrorSummary` | submit-only focus, links to invalid fields |
| `Disclosure` | button ownership, expanded state, controlled panel ID |
| `Dialog` | focus entry/trap/return, escape and labelled title |
| `LiveRegion` | deduplicated status/error announcements |
| `RemoteRegion` | busy, empty, stale, degraded and error semantics |

Every primitive has example-based interaction and axe tests. Error ID generation additionally uses P-U01-09.

## Route and Chunk Graph

- `shell`: AppShell, locale bootstrap, base primitives and Feed route.
- `search`: Search page, condition editor.
- `detail`: Content detail, availability and external link mapper.
- `recommendation`: conversation state and recommendation panels.
- `account`: profile, consent, library and data-rights screens.
- `admin`: separate shell, override, trace and incident screens.

Imports flow from route chunks toward shared primitives and adapters. Shared code cannot import route modules. A build graph check prevents protected route code from entering the initial shell.

## Browser Telemetry Adapter

The adapter accepts only typed allowlisted events. Sanitization occurs before enqueue. The memory buffer has fixed event and byte limits; overflow drops the oldest low-priority performance event and increments one bounded drop counter. Security, audit and domain events are never synthesized from browser telemetry.

## Quality Gate Components

| Gate | Evidence |
|---|---|
| `TypeGate` | strict TypeScript and generated client compile |
| `StaticGate` | ESLint, format and forbidden import rules |
| `ExampleGate` | Vitest/Testing Library critical scenarios |
| `PropertyGate` | P-U01-01~10 fast-check with seed and shrinking |
| `AccessibilityGate` | axe, keyboard E2E and manual screen-reader checklist |
| `ContractGate` | generated OpenAPI drift and MSW schema fixtures |
| `BrowserGate` | Chromium, Firefox, WebKit and mobile viewport smoke |
| `PerformanceGate` | route gzip 200KB, LCP/INP/CLS scenario evidence |
| `SupplyChainGate` | frozen lock install and no unapproved critical/high finding |

All automated gates are blocking. The manual screen-reader evidence is blocking before release approval, not before every local development iteration.

## Dependency and Failure Matrix

| Dependency | Failure containment | User-visible response |
|---|---|---|
| U03 Feed/Search | route or region boundary | stale data with timestamp or local retry |
| U05 Recommendation | recommendation region | preserved draft, retry/new session, safe fallback response if server provides it |
| U02 Identity/Consent | protected region and auth coordinator | reauthentication, field conflict or non-personalized transition |
| U06 Notification/Admin | member/admin region | local failure; public content remains available |
| Runtime config/chunk | fatal or route boundary | boot recovery or route reload without exposing internals |
| Telemetry endpoint | telemetry adapter | silent bounded drop; no user journey failure |

## Extension Compliance

### Resiliency Baseline

| Rule | Status | Design evidence |
|---|---|---|
| RESILIENCY-01~04 | Compliant by inheritance | U01 criticality and U07 availability/deployment decisions are unchanged. |
| RESILIENCY-05~07 | Compliant | typed browser telemetry, Web Vitals, error outcome and dashboard evidence are defined. |
| RESILIENCY-08~09 | N/A | no independent server topology; measured CDN/image evolution path is documented. |
| RESILIENCY-10 | Compliant | failure boundaries, cancellation, bounded retry and protected cache isolation are explicit. |
| RESILIENCY-11~14 | N/A | U01 owns no persistent business data or DR execution. |
| RESILIENCY-15 | Supporting | safe correlation evidence integrates with U06 incident flow. |

No blocking resiliency finding remains.

### Property-Based Testing

PBT-01 remains traceable through P-U01-01~10. The logical components expose pure codecs, state models and validators suitable for PBT-02~08; shrinking, deterministic replay and example regression promotion support PBT-08 and PBT-10. No blocking PBT finding remains.

### Security Baseline

Disabled and N/A as an extension. CSP, cookie/CSRF, protected cache purge, safe URL mapping, dependency audit and telemetry minimization remain core design constraints.
