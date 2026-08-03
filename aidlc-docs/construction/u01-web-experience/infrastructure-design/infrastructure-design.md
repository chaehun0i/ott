# U01 Web Experience Infrastructure Design

## Deployment Scope

U01은 기존 단일 서버 Docker Compose에 `web` 정적 자산 service를 추가한다. Node.js는 multi-stage build에서만 사용하며 production에는 application JavaScript server를 두지 않는다. 기존 Caddy가 유일한 public edge이고 `/api/*`는 API, 그 밖의 browser route는 `web`으로 전달한다.

## Infrastructure Mapping

| Logical component | Infrastructure mapping | Isolation |
|---|---|---|
| React/Vite application | immutable files in unprivileged `web` container | read-only filesystem, no secret, no DB network |
| RuntimeConfigLoader | `/config/runtime.json` static/public contract | public allowlist fields only, no secret |
| ApiClientBoundary | same-origin browser `/api/*` through Caddy | API owns cookie, CSRF and authorization |
| Route/Error boundaries | browser bundle | no separate server process |
| BrowserTelemetryAdapter | same-origin bounded `/api/v1/client-telemetry` ingestion | allowlisted schema, no raw input or direct identifiers |
| Quality gates | Node 24 builder/test environment | absent from runtime image |
| Static access logs | web JSON stdout plus Docker rotation | Loki is optional central search replica |

## Build Infrastructure

### Multi-Stage Contract

1. A Node.js 24 LTS builder uses Corepack and the committed `pnpm-lock.yaml`.
2. Dependency installation uses `pnpm install --frozen-lockfile`.
3. Generated OpenAPI client drift, typecheck, lint, unit/component/PBT, accessibility and production build gates run before artifact packaging.
4. The `dist` output and minimal web-server configuration are copied into a pinned unprivileged runtime image.
5. Node, pnpm store, source code, tests, source maps and build credentials are absent from the production layer.

The final image and all base images are pinned by immutable digest in the remote Compose overlay. Pre-release dependencies and mutable production tags are forbidden.

## Compute Contract

| Setting | `web` value | Rationale |
|---|---|---|
| CPU | `0.5` | bounded static serving on prototype host |
| Memory | `256m` | static web-server and access-log headroom |
| User | non-root | no privileged runtime required |
| Root filesystem | read-only | immutable artifact contract |
| Writable space | bounded `tmpfs` only if server requires runtime temp | prevents persistent mutation |
| Restart | `unless-stopped` for process exit only | does not claim health-based restart |
| Replicas | one | approved single-server prototype |

An unhealthy-but-running container is not automatically restarted by Docker Compose. Blackbox/health failure raises an alert and an operator follows the runbook. A health restart controller is not introduced.

## Storage and Messaging

### Storage: N/A

U01 owns no persistent business data, database schema, volume or backup. Browser cache and storage are non-authoritative; credentials and protected state are not persisted. Hashed static assets are reproducible build artifacts and are restored by redeploying the pinned image, not by database backup.

### Messaging: N/A

U01 owns no queue or broker. Feedback, recommendation, notification and operator commands use existing synchronous U02/U05/U06 API contracts. Browser telemetry is best-effort bounded delivery and is not a durable domain event or audit channel.

## Network Topology

- only Caddy publishes host ports 80 and 443;
- `web` joins a narrow edge network shared with Caddy and exposes no host port;
- `web` does not join database, private backend, observability-write or provider-egress networks;
- Caddy proxies `/api/*` to `api:8000` before the catch-all web route;
- Caddy proxies all other requests to `web`, which serves files and falls back to `index.html` only for browser routes;
- asset paths that do not exist return 404 and never fall back to HTML;
- the browser uses same-origin API and telemetry paths, so no broad CORS policy is needed.

## Routing and Cache Contract

| Path class | Target | Cache policy |
|---|---|---|
| `/api/*` | API container | backend-defined; never SPA fallback |
| `/assets/<hash>.*` | web static asset | `public, max-age=31536000, immutable` |
| `/config/runtime.json` | web public config | `no-cache`, schema validated at boot |
| known static files | web | type-appropriate revalidation |
| browser routes | web `index.html` | `no-cache` |
| missing asset-like path | web 404 | no HTML fallback |

Caddy retains zstd/gzip. Compression is disabled for already compressed formats when the server handles content types. HTML is revalidated so a deployment does not strand clients on a removed asset graph; at least one prior asset set remains available during controlled rollout or rollback.

## Security Headers and Runtime Configuration

Caddy is the central header enforcement point:

- `Content-Security-Policy` defaults to `default-src 'self'`, blocks object/embed, restricts base/form/frame ancestors, and defines explicit connect/image/font/style sources;
- executable inline script and `unsafe-eval` are forbidden; a build-generated hash is used only if an unavoidable static bootstrap exists;
- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy: strict-origin-when-cross-origin`;
- restrictive `Permissions-Policy` for unused browser capabilities;
- HSTS is enabled only on real HTTPS remote domains, not local HTTP.

`runtime.json` may contain only API base path, supported locales, default locale and release version. A schema failure blocks application boot with a safe static error. No secret, credential, provider token, internal hostname or private network address may be present in build args, labels, environment exposed to the browser or generated JavaScript.

## Health and Synthetic Monitoring

| Consumer | Endpoint/check | Meaning |
|---|---|---|
| Compose `web` healthcheck | `http://127.0.0.1:<internal>/health/live` | web process responds and required `index.html` exists |
| Caddy upstream | web service connectivity | static origin can accept requests |
| Blackbox exporter | public `/` and a known hashed/health asset through Caddy | TLS/edge/routing/web path works from user perspective |
| Prometheus | blackbox metrics plus API telemetry metrics | availability, latency and failure alert input |

The frontend health endpoint does not call Backend, PostgreSQL or external providers. API readiness/deep health remain separate endpoints and failures appear as degraded UI rather than falsifying static web liveness.

## Browser Telemetry Infrastructure

The browser sends a typed, bounded event to a same-origin API ingestion endpoint. The endpoint:

1. enforces request size, rate limit and an allowlisted schema;
2. rejects prompt, query text, body, user/content/session/trace identifiers and credentials;
3. maps route template, Web Vitals, release, API operation/outcome and safe correlation reference to bounded metrics/events;
4. forwards permitted telemetry through existing OTel/Prometheus-compatible observability paths;
5. does not write U06 audit tables or create durable business events.

Telemetry loss never fails the user request. Metric labels remain bounded; correlation references belong in structured event fields, not metric labels.

## Logging

`web` emits structured access/error logs to stdout. Docker `json-file` with `max-size: 10m` and `max-file: 5` is the recoverable host-level original with bounded retention. Loki receives an optional search copy and is not the sole source of truth.

Logs exclude query strings, cookies, authorization/CSRF headers, request bodies, referrers containing sensitive values and direct identifiers. Labels are limited to service, route class, method class, status class and release.

## Shared Infrastructure Decision

Existing Caddy, public edge network, Blackbox exporter, Prometheus/Grafana, OTel and optional Loki are reused. No new shared database, queue, object storage or secret service is required. Therefore `aidlc-docs/construction/shared-infrastructure.md` does not require a separate update; U01-specific additions stay in this unit and are implemented in existing configuration files during Code Generation.

## Code Generation Blocking Gates

Before application feature implementation begins:

1. exact Node/package/runtime image versions must be registry-verified and locked;
2. `web` service skeleton must render through `docker compose config` with CPU `0.5`, memory `256m`, read-only root, non-root runtime, edge network only, healthcheck and Docker log rotation;
3. Caddy route ordering must prove `/api/*` cannot fall through to the SPA;
4. the runtime image must contain no source map, Node runtime, secret or writable application directory;
5. production CSP must parse without `unsafe-inline` executable script or `unsafe-eval`;
6. a public Blackbox check must distinguish web availability from API deep health.

Failure of any gate blocks feature code generation.

## Extension Compliance

### Resiliency Baseline

| Rule | Status | Evidence |
|---|---|---|
| RESILIENCY-01~04 | Compliant by inheritance | U01 criticality and U07 availability/deployment/rollback remain approved. |
| RESILIENCY-05~07 | Compliant | health, Blackbox, Web Vitals, logs and dashboard paths are mapped. |
| RESILIENCY-08~09 | N/A with evolution gate | approved single-server prototype; CDN/image/telemetry expansion is measurement-driven. |
| RESILIENCY-10 | Compliant | network isolation, same-origin routing and failure separation are explicit. |
| RESILIENCY-11~14 | N/A | no U01 persistent business data; static artifact recovery is redeployment. |
| RESILIENCY-15 | Supporting | safe correlation evidence feeds established U06 incident flow. |

No blocking resiliency finding remains.

### Property-Based Testing

Infrastructure Design has no new runtime PBT property. The builder and test environment preserve fast-check shrinking, fixed/reported seed replay and P-U01-01~10 execution. PBT infrastructure is compliant for this stage.

### Security Baseline

Disabled and N/A as an extension. Non-root/read-only execution, CSP, secret exclusion, same-origin isolation, safe telemetry and dependency locking remain mandatory core controls.
