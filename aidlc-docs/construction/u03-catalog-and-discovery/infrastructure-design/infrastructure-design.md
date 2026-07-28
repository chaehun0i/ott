# U03 Catalog and Discovery Infrastructure Design

## Infrastructure Decision Summary

| Category | Selected infrastructure |
|---|---|
| Environments | Docker-optional Local/CI real PostgreSQL; Remote Linux Docker Compose |
| Compute | Shared immutable API/worker image, separate services and bounded U03 concurrency |
| Database | Shared PostgreSQL 17 cluster, isolated `u03_catalog` schema and roles |
| Search extensions | Version-pinned `vector`; built-in `pg_trgm` and `unaccent`; startup/migration preflight |
| Storage | 15 GB U03 soft budget inside PostgreSQL 40 GB allocation; warning 70%, critical 80% |
| Messaging | Shared PostgreSQL outbox with U03 indexed lanes and semaphore budgets |
| Network | Caddy public discovery routes; private database/worker; allowlisted embedding egress |
| Secrets | Purpose-separated read-only secret files for embedding and HMAC current/previous keys |
| Monitoring | Shared Prometheus/Loki/Grafana/OTel with U03 dashboard and alerts |
| Delivery | GitHub Actions, GHCR digest, extension/migration/quality preflight and online generation swap |
| Backup | Durable Catalog/version/outbox/registry included; rebuildable indexes/candidates excluded |

## Environment Architecture

### Local

- The preferred full-stack path remains Docker Compose when Docker is healthy.
- A native real PostgreSQL 17 instance is equally valid for schema, integration, PBT and migration verification when it provides the required extensions.
- Native and container paths use the same application configuration schema, migration chain, extension preflight and test markers.
- `pytest -m integration` must select actual integration tests and report zero skips; absence of Docker is not a waiver.
- Embedding uses a fake or explicitly configured sandbox adapter by default. Production credentials are never copied into Local.

### CI Test

- GitHub Actions provisions a version-pinned PostgreSQL 17 plus vector environment or connects to an equivalent isolated native PostgreSQL runner.
- Preflight records server version and exact `vector`, `pg_trgm` and `unaccent` versions/capabilities before migrations.
- CI runs clean migration, U07/U02-to-U03 upgrade, FTS/HNSW, outbox/replay/rebuild/failure injection, PBT and `pytest -m integration` with zero selected skips.
- Search golden-set, exact-vector oracle, query-plan, PBT seed/shrink and migration evidence are retained as artifacts.
- No live embedding or production HMAC secret is required; deterministic test adapters and test-only keys are injected.

### Remote Prototype

- One cloud-neutral Linux host runs the existing Docker Compose project.
- Caddy, Web, API, Worker, PostgreSQL and observability services remain separate containers/services even when API and Worker share an immutable application image.
- Public exposure remains limited to Caddy ports 80/443. Database, workers, metrics and deep health have no host-published ports.
- Extension versions, image digests, schema revision, active projection generation and embedding contract version are recorded in the release manifest.

## Compute Infrastructure

### Shared Host Budget

The U03 limits operate inside the inherited 4 vCPU, 8 GiB and 100 GB host, not as additional reserved capacity.

| Workload | Initial U03 limit | Isolation behavior |
|---|---:|---|
| Online database concurrency | 4 | Uses API pool; closure capacity is reserved |
| Embedding outbound concurrency | 4 | Separate semaphore and circuit breaker |
| Incremental projection workers | 2 | Worker pool and U03 lane budget |
| Full rebuild workers | 1 | Low-priority, pausable workload |

The rebuild coordinator pauses or reduces rebuild work when online latency, API pool wait, CPU, memory or disk I/O breaches the U03 online thresholds. Restart policies recover process failure but do not loop indefinitely on configuration or extension errors.

### Scale Review

Review compute/database separation when content exceeds 100,000, concurrent users reach 50, query traffic exceeds 20 requests/second, projection traffic exceeds 10 records/second, rebuild exceeds 30 minutes, U03 disk crosses the soft budget, or PostgreSQL/index saturation persists.

## Storage Infrastructure

### PostgreSQL Schema and Roles

U03 uses the shared PostgreSQL database and an isolated `u03_catalog` schema.

| Role | Grants |
|---|---|
| `u03_migration_owner` | U03 DDL, extension-dependent migration objects; no application runtime |
| `u03_api_runtime` | Read approved Catalog/projections, execute approved U03 routines; no projection mutation |
| `u03_worker_runtime` | Catalog publication port, outbox claim/receipt, projection/generation mutation; no other Unit writes |
| `backup_reader` | Durable U03 backup set only; no application writes |
| `monitor_reader` | Bounded health/version/system views; no content payload read |

U04 invokes U03 publication through an application port executed with the permitted U03 boundary. U01, U05 and U06 consume U03 APIs/ports and do not receive table-write grants.

### Search Extension Supply

- The Remote PostgreSQL image/build manifest is based on PostgreSQL 17 and pins the vector extension source/package version.
- `pg_trgm` and `unaccent` are enabled from the compatible PostgreSQL distribution and recorded.
- Container start checks binary/control-file availability; migration preflight checks database extension version and privileges.
- CI and Local native paths run the same SQL preflight.
- A missing or mismatched extension is a blocking deployment/integration failure; vector behavior is not replaced with an in-memory mock outside unit tests.

The exact vector image/package version is resolved and locked during U03 Code Generation against the real PostgreSQL 17 environment.

### Disk and Index Budget

U03 has a 15 GB soft allocation inside the inherited 40 GB PostgreSQL allocation. It covers durable Catalog tables, localizations, availability, outbox/receipts, active and rollback-window projection generations and indexes.

- U03 usage at 70% of the 15 GB soft allocation creates a warning.
- U03 usage at 80% creates a critical alert and blocks non-essential generation creation until reviewed.
- Host/PostgreSQL global disk limits remain stronger than U03 limits.
- Candidate generations have expiry/cleanup; the active and rollback generation cannot be removed by automated cleanup.
- Actual 100,000-content fixtures determine the final table/index split before production classification.

### Backup and Restore Scope

Daily encrypted off-host backup includes approved content/revisions, localizations, availability, source provenance, CatalogVersion, outbox durable state/receipts, policy/version metadata and active-generation registry.

FTS/vector indexes and incomplete candidate generations are treated as rebuildable artifacts rather than recovery truth. Restore recreates required extensions, applies schema, restores durable state, rebuilds candidate projections, validates closure/quality and only then establishes a new active generation. The existing RTO 4 hours and RPO 24 hours remain the gate.

## Messaging Infrastructure

U03 reuses the shared PostgreSQL outbox/job tables with columns and partial indexes for `unit`, `job_type`, `priority`, `available_at`, claim lease and terminal state.

| Lane | Initial concurrency | Purpose |
|---|---:|---|
| Incremental projection | 2 | Feed/text changes and contiguous version processing |
| Embedding | 4 outbound, bounded worker claims | Provider calls and vector validation |
| Rebuild | 1 | Immutable generation construction and evaluation |

Claim queries use `FOR UPDATE SKIP LOCKED`. Unit/job-type budgets stop rebuild backlog from exhausting U02 privacy jobs or U04 ingestion. Retry, dead-letter, CatalogVersion gap and manual reconciliation remain durable PostgreSQL states.

## Network Infrastructure

### Public Routes

Caddy exposes only approved discovery API prefixes such as `/api/v1/feed`, `/api/v1/contents` and `/api/v1/search` through the shared API service. Request size, trusted proxy headers, TLS, endpoint timeout and basic IP controls use the U07 edge policy.

### Private and Observability Networks

- API, Worker and PostgreSQL connect through `private_net`; PostgreSQL and Worker are not attached to public routes.
- API/Worker telemetry connects to `observability_net`; Prometheus, Loki, OTel Collector and deep health are not directly public.
- Grafana remains behind the protected Caddy operations route.

### Embedding Egress

API and Worker may resolve and connect only to the configured embedding endpoint plus required DNS/TLS services. Provider host, scheme and port are configuration allowlists. Redirects to unapproved hosts are rejected. Separate API and Worker credentials may be used when the provider supports scope separation.

## Secret and Key Infrastructure

| Secret file | Services | Purpose |
|---|---|---|
| `u03_embedding_credential` | API, Worker | Provider authentication with minimum scope |
| `u03_cursor_hmac_current` | API | New cursor signing/current verification |
| `u03_cursor_hmac_previous` | API during rotation | Bounded old-cursor verification |
| `u03_query_hmac_current` | API | New non-reversible query fingerprints |
| `u03_query_hmac_previous` | API during rotation | Bounded correlation during rotation |
| `database_u03_api` | API | `u03_api_runtime` connection |
| `database_u03_worker` | Worker | `u03_worker_runtime` connection |

Secrets are read-only service mounts, excluded from image layers, database, backup, logs and CI artifacts. Previous keys are removed after cursor/fingerprint rotation windows and verification evidence.

## Monitoring Infrastructure

U03 extends the shared Prometheus/Loki/Grafana/OTel stack rather than deploying a separate stack.

### Dashboard

- Feed/detail/text/semantic latency, errors, throughput and PostgreSQL pool wait
- Projection version, lag, gap, retry, dead-letter and rebuild duration/progress
- Embedding timeout, circuit state, concurrency and fallback rate
- Approval-closure drop, stale ratio, zero-result ratio and active generation
- U03 schema/table/index disk usage and HNSW/golden-set release evidence

### Alerts

- CatalogVersion gap: immediate
- Projection lag over 5 minutes for 5 minutes
- Approval-closure drop count at least one: immediate
- Semantic fallback over 20% for 15 minutes
- Zero-result or stale ratio above twice the versioned baseline
- U03 disk warning/critical at 70%/80% of soft budget
- Rebuild over 30 minutes, quality failure or active-pointer swap failure

Telemetry label allowlists prohibit raw/normalized query, vector, provider payload, content synopsis, unapproved record and secret/key identifiers beyond non-secret key ID.

## CI and Verification Infrastructure

Required CI jobs include format/lint/type, unit/contract, real-PostgreSQL integration, PBT, bilingual quality evaluation, coverage, migrations, extension preflight, failure injection, OpenAPI compatibility and dependency/image scanning.

The PostgreSQL gate fails when selected integration tests are skipped, required extensions are absent/mismatched, migration paths fail, HNSW cannot meet the exact-oracle threshold, or CAT/AVAIL/PROJ closure branches are not fully covered.

## Logical Component Mapping

| Logical components | Infrastructure resources |
|---|---|
| LC-U03-01~14 | API service, Caddy routes, API pool, HMAC secret mounts |
| LC-U03-15~17 | `u03_catalog` schema, PostgreSQL tables/FTS/HNSW indexes and generations |
| LC-U03-18~19 | API/Worker embedding egress, provider secret, concurrency/circuit configuration |
| LC-U03-20~24 | Shared outbox/job tables, U03 lanes, Worker service and generation registry |
| LC-U03-25 | CI golden fixtures, evaluation runner and evidence artifacts |
| LC-U03-26 | Caddy/IP controls plus application rate-limit store/configuration |
| LC-U03-27~28 | OTel SDK/Collector, Prometheus, Loki, Grafana and health endpoints |
| LC-U03-29 | Separate API/Worker PostgreSQL pools and connection secrets |
| LC-U03-30 | CI PostgreSQL 17+extensions service/native runner and artifact store |

## Shared Infrastructure Changes

The U07 host, edge, database, outbox, observability and CI remain shared. U03 adds pinned search extensions, `u03_catalog` roles, a 15 GB soft disk budget, purpose-separated secrets, U03 job lanes, dashboard/alerts and an extension-aware deployment gate. These additions are recorded in `aidlc-docs/construction/shared-infrastructure.md`.

## Production Transition Gates

- Multi-zone compute/database and load balancing
- Auto-scaling and central distributed rate-limit/circuit state
- Managed PostgreSQL/vector compatibility, PITR and measured index capacity
- Production egress control and managed secret/KMS integration
- Formal on-call, search-quality ownership and multi-region/DR reassessment
- Capacity test beyond 100,000 contents and security/privacy review

## Extension Compliance

- **Resiliency**: Compute/pool/job isolation, extension preflight, online rollback, backup/rebuild, health/alerts and failure-injection environments are mapped. RESILIENCY-08~09 remain prototype N/A exceptions with transition gates.
- **PBT**: CI/native/container real PostgreSQL paths support Hypothesis seed/shrink artifacts and selected integration skip=0.
- **Security Baseline**: Disabled and therefore N/A. Core network, TLS, secret, role, query privacy and integrity controls remain required.

No blocking extension finding remains.

