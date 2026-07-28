# U03 Catalog and Discovery Deployment Architecture

## Deployment Units

| Unit | Artifact | Runtime responsibility |
|---|---|---|
| Caddy | Version-pinned official image/config | TLS, discovery routing, request bounds and basic IP control |
| API | Immutable application digest | Feed/detail/search, closure checks, cursor/HMAC and query embedding |
| Worker | Same immutable application digest, different command | Incremental projection, content embedding and rebuild jobs |
| PostgreSQL | PostgreSQL 17 plus pinned vector build | Approved Catalog, FTS/vector generations, outbox and registry |
| OTel Collector | Shared pinned image/config | Privacy-aware telemetry collection |
| Prometheus/Loki/Grafana | Shared pinned images/config | Metrics, logs, dashboard and alerts |
| Backup/Restore Runner | Shared controlled tool image | Durable U03 backup and isolated restore verification |

## Network Flow

### Public Request

1. Client reaches Caddy over HTTPS on port 443.
2. Caddy routes only discovery API paths to the API service and applies request/header limits.
3. API applies subject/endpoint-cost limits and queries PostgreSQL over `private_net` with `u03_api_runtime`.
4. Semantic search may call the allowlisted embedding endpoint within the 300-millisecond connect/1.5-second total budget.
5. API rechecks approved closure in PostgreSQL and returns a normal or degraded response.

### Projection Work

1. Worker connects to PostgreSQL through `private_net` with `u03_worker_runtime`.
2. It claims U03 work from the shared job table within lane/semaphore budgets.
3. Embedding jobs call only the configured provider endpoint; incremental/rebuild jobs write candidate generations.
4. Validation succeeds before `ActiveGenerationRegistry` swaps the active pointer transactionally.

### Telemetry

API and Worker send allowed telemetry over `observability_net` to the shared collector/metrics endpoint. No discovery component writes directly to public monitoring endpoints.

## Configuration Matrix

| Configuration | Local | CI | Remote Prototype |
|---|---|---|---|
| PostgreSQL | Native or container real PostgreSQL 17 | Isolated service/native runner | Pinned Compose image/volume |
| Search extensions | Same preflight, test-compatible exact versions | Mandatory preflight/evidence | Mandatory startup/migration preflight |
| Embedding | Fake or sandbox | Deterministic fake | Configured provider secret/allowlist |
| HMAC keys | Test/local files | Ephemeral test secrets | Read-only current/previous secret files |
| Observability | Optional profile | Artifact/metric assertions | Shared stack enabled |
| Integration | Zero selected skips | Zero selected skips, blocking | Pre/post-deploy smoke and recovery evidence |

## Build and Release Artifacts

Each U03-capable release connects these immutable/versioned items:

- Git commit, application image digest and PostgreSQL/vector image digest
- Python lockfile and PostgreSQL extension manifest
- Alembic migration revision and OpenAPI artifact
- Feed/search/embedding configuration schema versions
- Golden query-set version and quality report
- PBT seed/shrink, coverage, integration and failure-injection reports
- Deployment/rollback manifest with current and candidate generation IDs

## Deployment Sequence

1. CI verifies dependencies, both images, configuration and secret-reference schema.
2. Provision real PostgreSQL 17 plus required extensions and pass clean/upgrade migrations with integration skip=0.
3. Pass US-001~US-006 examples, PBT-U03-01~16, closure branches, bilingual quality, HNSW oracle, load/query-plan and failure-injection gates.
4. Publish immutable application and PostgreSQL/vector image digests plus evidence manifest.
5. On the Remote host, verify free disk, backup health, current generation, secret files and embedding endpoint allowlist.
6. Create and verify a pre-deploy encrypted backup of durable U03 state.
7. Verify the pinned extension image/version before any migration.
8. Apply expand-compatible migrations with `u03_migration_owner`.
9. Deploy the new API/Worker image digest while retaining previous compatible image/configuration.
10. Build the candidate feed/text/vector generation under rebuild concurrency one; pause on online SLO pressure.
11. Run closure, continuity, duplicate, quality and latency smoke validation against the candidate.
12. Atomically swap the active generation pointer and verify public feed/detail/text/semantic/degraded paths.
13. Retain the previous image, compatible schema and projection generation through the rollback window.

## Rollback Sequence

Rollback does not blindly restore a database snapshot because forward-only Catalog changes and outbox state may be newer than the application image.

1. Stop new candidate/rebuild work and record the failed release/generation.
2. If the active pointer was swapped, atomically return it to the previous validated generation.
3. Redeploy the previous application image/configuration digest only if it is compatible with the expanded schema.
4. Preserve new approved Catalog/outbox truth; do not replay deletion/withdrawal or Catalog events backward.
5. Verify closure, CatalogVersion continuity, feed/detail/text fallback, rate limits, health and telemetry.
6. Use backup restore only for proven database corruption or unrecoverable migration failure under the U07 recovery runbook.

## Restore and Re-entry

1. Create an isolated PostgreSQL 17+extensions target.
2. Verify manifest, checksum, encryption key reference and server/extension compatibility.
3. Restore durable U03 Catalog/version/outbox/registry state.
4. Apply forward-compatible migrations.
5. Validate canonical IDs, current approved revisions, availability, CatalogVersion continuity and outbox receipts.
6. Rebuild feed/text/vector generations from the restored approved snapshot.
7. Run bilingual quality, exact-vector oracle and representative closure/search smoke tests.
8. Establish a validated active generation and then permit service re-entry.

## Docker-Independent Verification Gate

Docker is not a correctness prerequisite. A native PostgreSQL path is accepted only when it proves:

- PostgreSQL 17 server identity and required exact extensions
- isolated test database and clean teardown
- clean and upgrade migration paths
- real FTS, trigram, HNSW/vector, transaction and outbox semantics
- integration selection with zero skips
- PBT seed/shrink artifacts and failure injection

Mock/SQLite results cannot replace this gate.

## Failure Scenarios

| Failure | Infrastructure response |
|---|---|
| Docker unavailable locally | Use isolated native real PostgreSQL and identical preflight/tests |
| Vector extension missing/mismatched | Block migration/deployment; keep current release |
| Embedding provider unavailable | Circuit opens; safe text/filter path remains ready |
| PostgreSQL closure unavailable | API fails closed; readiness/alert reflect safety failure |
| Projection gap | Stop advancement, alert, replay/reconcile; active generation remains |
| Rebuild resource pressure | Pause rebuild, preserve online API priority |
| Candidate quality failure | Reject candidate; active pointer unchanged |
| Pointer swap failure | Transaction rolls back; prior generation remains active |
| Disk warning/critical | Stop non-essential candidate creation and initiate capacity/cleanup review |
| Observability stack unavailable | Business path continues; local bounded telemetry handling and alert on recovery |

## Shared Infrastructure and Change Control

The deployment modifies shared PostgreSQL image/extensions, database grants, worker lanes, secret mounts, Caddy routes, monitoring provisioning and CI gates. Each change uses the lightweight Git change record, consumer compatibility checks, pre-deploy backup and version-pinned rollback note inherited from U07.

## Production Readiness Boundary

This remains a single-host prototype. It cannot be represented as production-ready until multi-zone database/compute, autoscaling and quotas, managed secrets/egress, PITR, formal on-call, production search capacity and resilience/DR evaluation pass.

## Extension Compliance

- **RESILIENCY-01~15**: Critical paths, failure isolation, health/alerts, backup/restore, online rollback, testing and incident integration are mapped. Multi-zone/autoscaling remain approved prototype exceptions.
- **PBT-01~10**: Real PostgreSQL CI/Local infrastructure retains property tests, reproducible seed/shrink evidence and complementary examples.
- **Security Baseline**: Disabled; general least privilege, TLS, secret separation, egress and query privacy controls remain.

No blocking extension finding remains.
