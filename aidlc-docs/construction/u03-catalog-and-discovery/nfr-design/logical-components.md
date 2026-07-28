# U03 Catalog and Discovery Logical Components

## Component Topology

| ID | Logical component | Responsibility | Owned state |
|---|---|---|---|
| LC-U03-01 | Discovery API Adapter | Validate request envelopes and map stable responses/errors | None |
| LC-U03-02 | FeedQueryService | Orchestrate feed sections, filters, pagination and closure | None |
| LC-U03-03 | ContentDetailService | Orchestrate localized detail and verified provider links | None |
| LC-U03-04 | SearchService | Orchestrate text/semantic plan, fallback and response | None |
| LC-U03-05 | RequestBudget | Propagate absolute deadline and child budgets | Request-local only |
| LC-U03-06 | QueryNormalizer | Canonicalize locale, text, filters and query fingerprint input | None |
| LC-U03-07 | SearchPlanner | Choose text, semantic or degraded plan from capabilities/deadline | None |
| LC-U03-08 | TextRetriever | Execute locale FTS, exact/prefix and person retrieval | Search projection read only |
| LC-U03-09 | VectorRetriever | Execute compatible HNSW query and return ranked IDs | Vector projection read only |
| LC-U03-10 | HybridRanker | Apply exact-title precedence, hard filters and RRF | None |
| LC-U03-11 | ApprovedClosureGuard | Recheck approval, withdrawal, license and regional availability | Approved Catalog read only |
| LC-U03-12 | LocalizationResolver | Apply deterministic locale fallback with actual locale | None |
| LC-U03-13 | CursorService | Sign, verify, decode and rotate snapshot cursors | Key references only |
| LC-U03-14 | QueryFingerprintService | Produce keyed non-reversible query fingerprints | Key references only |
| LC-U03-15 | CatalogRepository | Read/write U03 approved aggregates and revisions | Approved Catalog tables |
| LC-U03-16 | FeedProjectionRepository | Query and build immutable feed generations | Feed projection tables |
| LC-U03-17 | SearchProjectionRepository | Query and build text/vector generations | Search projection tables |
| LC-U03-18 | EmbeddingAdapter | Invoke provider-neutral embedding contract | Circuit/bulkhead runtime state |
| LC-U03-19 | EmbeddingJobHandler | Generate/version/validate embeddings asynchronously | Job attempt/result records |
| LC-U03-20 | ProjectionEventClaimer | Claim outbox work and manage leases/receipts | Claim and receipt tables |
| LC-U03-21 | CatalogVersionBarrier | Track contiguous version and detect gaps | Applied/gap state |
| LC-U03-22 | ProjectionCoordinator | Apply content changes idempotently | Projection state transitions |
| LC-U03-23 | RebuildCoordinator | Build, validate, swap and retire generations | Generation registry |
| LC-U03-24 | ActiveGenerationRegistry | Resolve and atomically swap active projection pointers | Active pointer and history |
| LC-U03-25 | SearchQualityEvaluator | Evaluate golden sets and exact-vector oracle | Versioned evaluation artifact |
| LC-U03-26 | U03RateLimiter | Enforce subject/IP and semantic cost buckets | Bounded counters |
| LC-U03-27 | DiscoveryTelemetry | Emit minimized logs, metrics and trace attributes | Telemetry only |
| LC-U03-28 | DiscoveryHealthContributor | Report DB/extensions/generation/semantic capability | Health snapshot only |
| LC-U03-29 | PostgreSQLPoolPartition | Enforce API/worker connection budgets | Pool runtime state |
| LC-U03-30 | U03IntegrationGate | Verify extensions, migrations, PostgreSQL and zero skips | Test artifacts only |

## Synchronous Query Collaborations

### Feed and Detail

1. `Discovery API Adapter` validates required region, locale, limits and cursor envelope.
2. `RequestBudget` establishes the endpoint deadline.
3. `FeedQueryService` or `ContentDetailService` calls `CatalogRepository` or `FeedProjectionRepository` through the API pool.
4. `CursorService` verifies schema, key ID, integrity, expiry, query fingerprint and snapshot version before pagination.
5. `ApprovedClosureGuard` rechecks every candidate against current approved Catalog and exact regional availability using its reserved budget.
6. `LocalizationResolver` resolves each field and reports actual locale/fallback level.
7. `DiscoveryTelemetry` emits bounded dimensions without content payload or raw query.

### Text and Semantic Search

1. `SearchService` receives a canonical request and remaining deadline.
2. `QueryNormalizer` produces structured conditions and input for `QueryFingerprintService`.
3. `SearchPlanner` checks compatible active generations, semantic circuit/capacity and remaining budget.
4. `TextRetriever` always remains available when PostgreSQL closure is healthy. `VectorRetriever` is invoked only when compatible vectors and dependency conditions allow.
5. `EmbeddingAdapter` enforces the 300-millisecond connect and 1.5-second total budget, concurrency four and circuit policy.
6. `HybridRanker` applies exact-title precedence, hard filters and RRF.
7. `ApprovedClosureGuard` performs the final authoritative recheck.
8. On semantic failure, `SearchPlanner` returns the approved text/filter result with a stable degraded code. PostgreSQL closure failure returns a safe service error.

## Asynchronous Projection Collaborations

### Incremental Change

1. U04 calls U03 `ApprovedCatalogWritePort`; `CatalogRepository` atomically records the approved revision, CatalogVersion and outbox event.
2. `ProjectionEventClaimer` uses `FOR UPDATE SKIP LOCKED` and records a bounded lease.
3. `CatalogVersionBarrier` checks per-content order and global contiguous advancement.
4. Feed changes can be built directly by `ProjectionCoordinator`; semantic changes schedule `EmbeddingJobHandler`.
5. `EmbeddingJobHandler` invokes `EmbeddingAdapter` with background retry policy, validates model/dimension/vector and persists to a candidate generation.
6. `ProjectionCoordinator` compares revision/version before applying and writes an idempotent receipt.
7. `CatalogVersionBarrier` advances only when all lower versions are resolved. Gap state triggers replay/reconciliation and an alert.

### Full Rebuild

1. `RebuildCoordinator` captures an authoritative CatalogVersion and creates a new immutable generation ID.
2. Repository builders populate feed, locale FTS, trigram and compatible vector data with worker pool limits.
3. `SearchQualityEvaluator` checks closure, duplicates, continuity, Recall@10, NDCG@10, exact-vector recall and performance smoke tests.
4. `ActiveGenerationRegistry` swaps both active pointers in one transaction only after validation.
5. The prior generation remains readable for the rollback window. Cleanup occurs only after the window and backup/rollback evidence.

## State and Ownership Boundaries

| State | Write owner | Read consumers | Prohibited access |
|---|---|---|---|
| Approved content/revisions/localizations/availability | U03 CatalogRepository | U01, U05 and U06 through U03 ports | U04/U05/U06 direct writes |
| Feed/search/vector generations | U03 projection components | U03 query services | External units direct mutation |
| Raw/normalized/quarantined metadata | U04 | U03 only through passed decision contract | U03 direct raw/quarantine reads |
| User preferences/features | U02 | U05 through feature port | U03 search/persistence writes |
| Recommendation rank/explanations | U05 | U01/U06 through defined contracts | U03 generation or mutation |
| Outbox claim/receipt/gap state | U03 projection components on U07 job substrate | U03 operations/health | Query services mutation |

## Error and Degradation Propagation

| Source | Internal classification | Public behavior | Operational signal |
|---|---|---|---|
| Invalid input/cursor | Validation error | Stable 4xx error | Bounded rejection counter |
| Content not approved/available | Not found/ineligible | Omit or stable not-found | Closure drop only if projection had included it |
| PostgreSQL closure timeout/failure | Safety dependency failure | Fail closed, retryable service error | Immediate error/health signal |
| Embedding timeout/open circuit | Degradable dependency failure | Approved text/filter result, degraded code | Fallback/circuit metrics |
| Vector model mismatch | Compatibility degradation | Approved text/filter result, degraded code | Compatibility alert/event |
| Projection gap | Recoverable async inconsistency | Keep active validated generation | Immediate gap alert |
| Rebuild validation failure | Candidate-generation failure | Keep prior generation | Rebuild failure metric/log |
| Active pointer swap failure | Atomic transition failure | Prior pointer remains active | Immediate job failure alert |

## Security and Privacy Component Rules

- `Discovery API Adapter` rejects over-limit input before database or embedding work.
- `U03RateLimiter` combines reverse-proxy IP limits with application subject/endpoint-cost limits; semantic capacity has a separate bucket.
- `QueryNormalizer`, repositories and retrievers use typed parameters only.
- `QueryFingerprintService` and `CursorService` use separate HMAC purposes and current/previous-key verification.
- `DiscoveryTelemetry` owns the allowlist of log/metric/trace attributes. Other components must not serialize query or provider payloads directly.
- `EmbeddingAdapter` sends only normalized search text or approved embedding document fields required by the configured contract.

## Observability Topology

`DiscoveryTelemetry` emits structured JSON logs to the U07 collector, Prometheus-compatible metrics to the common endpoint and trace context through all synchronous/worker calls. `DiscoveryHealthContributor` contributes liveness/readiness/dependency capability without exposing provider or database detail publicly.

Alert routing uses the inherited U07 alert router and lightweight incident/COE process. Dashboard signals include latency/error/throughput/saturation, projection lag/gaps, fallback, closure drops, zero results, stale ratio, generation versions, rebuild duration and golden-set release status.

## Consumer Contracts

| Consumer/provider | Contract |
|---|---|
| U01 Web Experience | Feed/detail/search DTOs with region, locale, actual locale, source/freshness, cursor, versions and degraded reason |
| U04 Metadata Governance | PassedValidation and withdrawal commands through ApprovedCatalogWritePort |
| U05 Recommendation | ApprovedCatalogReadPort and AvailabilityPort returning only current regional approved candidates |
| U06 Operations | Authorized catalog override/read operations and U03 alert/audit references |
| U07 Platform | Request context, rate-limit edge, PostgreSQL/outbox runtime, telemetry, health, backup/restore and delivery contracts |
| Embedding provider | Provider-neutral versioned embedding request/response with timeout and privacy allowlist |

## Test Component Handoff

- `U03IntegrationGate` provisions real PostgreSQL with `pg_trgm`, `unaccent` and `vector`, applies clean/upgrade migrations and rejects selected integration skips.
- `SearchQualityEvaluator` doubles as the HNSW exact oracle and bilingual golden-set release gate.
- Hypothesis strategies generate approved revisions, locale maps, regional availability, filters, cursor snapshots, rank lists and event sequences.
- Stateful tests drive `ProjectionEventClaimer`, `CatalogVersionBarrier`, `ProjectionCoordinator` and `ActiveGenerationRegistry` against a simplified reference model.
- Failure injection replaces adapter/repository boundaries, not domain invariants, and verifies telemetry privacy as well as output behavior.

## NFR Traceability

| Components | U03 NFRs |
|---|---|
| LC-U03-01~14 | 007~013, 020~023, 029~043, 055~056 |
| LC-U03-15~17 | 003~019, 024~028, 033~035 |
| LC-U03-18~19 | 009~010, 022, 036~037, 043~048 |
| LC-U03-20~24 | 014~018, 025~028, 045~049 |
| LC-U03-25 | 029~034, 050~053 |
| LC-U03-26~29 | 004~013, 036~049 |
| LC-U03-30 | 050~057 |

## Extension Compliance

- **RESILIENCY-01~15 — Compliant/N/A as designed**: Criticality, deadline/circuit/bulkhead, health/alerts, gap/replay, online rollback and automated failure tests have explicit owners. Prototype multi-zone/auto-scaling remain approved N/A exceptions with evolution components.
- **PBT-01~10 — Compliant handoff**: Component boundaries support round-trip, invariant, idempotence, oracle and stateful tests with Hypothesis, shrinking, seeds and complementary examples.
- **Security Baseline — N/A**: Extension is disabled; core privacy, integrity, parameterization and resource protection remain explicit.

No blocking extension finding remains for U03 NFR Design.
