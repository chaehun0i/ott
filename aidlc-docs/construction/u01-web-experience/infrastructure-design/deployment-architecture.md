# U01 Web Experience Deployment Architecture

## Deployment Inventory

| Component | Exposure | Networks | Persistent state | Resource limit |
|---|---|---|---|---|
| Caddy | host 80/443 | public edge, existing backend/observability routes | existing Caddy data | existing platform decision |
| Web | internal only | public edge only | none | 0.5 CPU, 256MB |
| API | internal via Caddy | existing public/private/observability/AI networks | PostgreSQL/existing volumes | existing platform decision |
| Blackbox exporter | internal | observability plus public edge reachability | none | existing platform decision |
| Prometheus/Grafana/OTel/Loki | internal or existing operator exposure | observability | existing volumes/config | existing platform decision |

## Request Sequence

### Static or Browser Route

1. Browser connects to Caddy on HTTPS.
2. Caddy applies compression and response security headers.
3. Non-API path is proxied to `web`.
4. A known asset is returned with immutable cache; a browser route receives no-cache `index.html`; a missing asset receives 404.
5. React boots, validates public runtime configuration and requests route chunks as needed.

### API Request

1. Browser sends a same-origin `/api/*` request with backend-managed session cookie.
2. Caddy routes it to API before evaluating the web catch-all.
3. API applies CSRF, authentication, authorization and domain validation.
4. The browser maps typed outcome to the appropriate route/region state.

### Browser Telemetry

1. BrowserTelemetryAdapter sanitizes an allowlisted event before queueing.
2. A bounded batch is sent to the same-origin ingestion endpoint.
3. API rejects forbidden fields and high-cardinality labels.
4. Accepted data is forwarded to existing observability adapters.
5. Failure is dropped within the client bound and never blocks the user journey.

## Network Policy

| Source | Destination | Allowed purpose |
|---|---|---|
| Internet | Caddy 80/443 | redirect/TLS and public application |
| Caddy | Web internal port | static/browser route serving |
| Caddy | API 8000 | `/api/*` only |
| Blackbox | Caddy public route | synthetic availability |
| Web | Database/worker/providers | denied; no runtime need |
| Internet | Web internal port | denied; no host publication |

## Startup and Health Order

The Web service has no Backend or database startup dependency. It becomes healthy when its process and required static artifact are available. Caddy may start independently and reports upstream failure until Web/API are available. Compose health dependencies must not imply that static Web requires PostgreSQL.

Operational interpretation:

- Web live fails: static service/process problem; alert and operator restart/rollback.
- Public Blackbox fails while Web live succeeds: Caddy, TLS, DNS or routing problem.
- API readiness fails while public Web succeeds: shell may load, protected data regions degrade; API alert handles traffic readiness.
- API deep health degrades: dependent feature regions display scoped degraded state; Web liveness remains healthy.

## Deployment and Rollback

### Controlled Deployment

1. verify exact package/image versions and frozen lock install;
2. run type, lint, test, PBT, accessibility, browser, contract, security and performance gates;
3. build immutable Web image and verify its contents;
4. validate base and remote Compose rendering;
5. validate Caddy config and security headers in an isolated environment;
6. start Web, confirm live health, then update Caddy routing/config;
7. run public Blackbox, core browser journeys and API routing negative tests;
8. record image digest, release version and verification evidence.

Automatic GitHub Actions triggers remain paused until the existing controlled workflow reactivation gate is satisfied.

### Rollback

Rollback redeploys the previous pinned Web image and compatible Caddy configuration. HTML must reference an asset set still present in that image. U01 has no database migration or persistent-data rollback. API compatibility is checked through the OpenAPI contract Gate before either release or rollback.

## Failure and Recovery Scenarios

| Scenario | Detection | Recovery | Evidence |
|---|---|---|---|
| Web process exit | Compose and Blackbox | restart policy; investigate repeated exit | container status and rotated JSON log |
| Web unhealthy but running | health/Blackbox alert | operator restart or image rollback | alert, runbook action, image digest |
| Bad SPA fallback | route/asset synthetic test | restore prior web config/image | 404/content-type assertions |
| CSP regression | browser console/header test | restore prior Caddy config/image | CSP parser and E2E report |
| API outage | API readiness and UI region test | existing API recovery; Web stays live | API alert and degraded UI evidence |
| Telemetry outage | ingestion error/drop metric | restore collector path; no user retry | bounded drop counter |

## Scale Evolution

Scale changes are permitted only after sustained evidence:

1. high asset origin bandwidth or geographical LCP regression → CDN for immutable assets;
2. image transfer dominates LCP/bandwidth → image resizing/optimization service;
3. telemetry volume or cardinality approaches capacity → sampling and collector isolation;
4. SSR/BFF remains outside this path and requires its own measured business need and ADR.

## Text Alternative

Internet traffic reaches only Caddy. Caddy sends API paths to the existing API container and all browser/static paths to an internal, non-root, read-only Web container. Web has no database, queue, secret, private network or host port. Blackbox checks the public path through Caddy, while API readiness and deep health remain separate. Browser telemetry uses a privacy-filtered same-origin API path into existing observability infrastructure.
