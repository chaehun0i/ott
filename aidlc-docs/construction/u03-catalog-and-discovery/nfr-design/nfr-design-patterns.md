# U03 Catalog and Discovery NFR Design Patterns

## Design Intent

U03 keeps PostgreSQL as the authoritative approved Catalog and the prototype search engine. The design separates synchronous query safety from asynchronous projection work, protects the 2/3-second API targets with nested deadlines, and treats every search projection as an optimization that must pass current approval and regional-availability closure before exposure.

## Pattern Summary

| Pattern | Purpose | Primary NFRs |
|---|---|---|
| PAT-U03-01 Separate connection bulkheads | Prevent projection work from exhausting online queries | 004, 007~010, 045 |
| PAT-U03-02 Nested query deadlines | Keep work inside endpoint budgets | 007~013 |
| PAT-U03-03 Locale-specific FTS and trigram | Deterministic Korean/English text retrieval | 029~034 |
| PAT-U03-04 HNSW with exact oracle | Scalable semantic retrieval with measurable recall | 003, 009, 029~031 |
| PAT-U03-05 Reciprocal Rank Fusion | Combine heterogeneous rankers without unstable score scaling | 029~035 |
| PAT-U03-06 Async versioned embedding | Isolate provider latency from Catalog publication | 014~018, 022 |
| PAT-U03-07 Circuit breaker and bulkhead | Contain embedding dependency failure | 010, 022, 045~048 |
| PAT-U03-08 Path-specific retry | Protect user latency while allowing durable job recovery | 010, 018, 022 |
| PAT-U03-09 Approved text fallback | Preserve safe discovery during semantic failure | 021~023, 035 |
| PAT-U03-10 Ordered outbox claims | Parallelize safely without losing content order | 014~018, 025~026 |
| PAT-U03-11 CatalogVersion gap barrier | Stop unsafe out-of-order projection advancement | 015, 026, 046 |
| PAT-U03-12 Idempotent receipt and replay | Make restart and duplicate delivery safe | 018, 025~026 |
| PAT-U03-13 Immutable generation and atomic swap | Rebuild online with rollback | 016~017, 028 |
| PAT-U03-14 Stateless scale-out | Expand API/worker capacity without premature service split | 004~005 |
| PAT-U03-15 Purpose-separated HMAC rotation | Protect cursor integrity and query privacy | 036~041 |
| PAT-U03-16 Layered cost-aware rate limiting | Bound anonymous, subject and semantic cost | 039~040 |
| PAT-U03-17 Privacy-minimized telemetry | Observe behavior without raw query retention | 036~037, 044~049 |
| PAT-U03-18 Split health and degraded readiness | Keep text search available during semantic outage | 021~023, 048 |
| PAT-U03-19 Quality and property gates | Prove ranking, closure and transformations | 029~034, 050~054 |
| PAT-U03-20 Automated failure injection | Verify recovery paths continuously | 014~018, 021~028, 053 |

## Performance and Scalability Patterns

### PAT-U03-01 — Separate Connection and Concurrency Bulkheads

API and projection worker use separate bounded PostgreSQL pools within the U07 global connection budget. The API pool prioritizes short read transactions. The worker pool handles claims, embedding persistence and generation builds. Neither pool can borrow without a configured global capacity review.

Pool acquisition has a bounded wait and emits saturation metrics. Worker concurrency reduces before API capacity is consumed. Scale-out adds replicas only after recalculating the total possible connection count against PostgreSQL limits.

### PAT-U03-02 — Deadline Propagation and Statement Budgets

The request context owns an absolute deadline. Child components receive the remaining budget, not independent full timeouts.

| Operation | Initial budget | Timeout result |
|---|---:|---|
| Online PostgreSQL statement | 1.2 seconds maximum | Cancel statement and map safely |
| Text retrieval | 800 milliseconds | Return timeout or semantic fallback path as applicable |
| Approval/availability closure | 300 milliseconds reserved | Fail closed if current truth cannot be proven |
| Embedding connect | 300 milliseconds | Open failure accounting and use text fallback |
| Embedding plus semantic retrieval | 1.5 seconds total | Cancel and use remaining budget for text fallback |

The closure reserve cannot be spent on semantic retrieval. Background rebuild and migration use separate profiles and never inherit online limits.

### PAT-U03-03 — Locale-Specific Text Documents

Each content revision produces one normalized search document per locale. Weighted fields preserve exact title, alternate titles, title text, people and description boundaries. A locale-specific `tsvector` uses a GIN index. Exact/prefix/variant title and person search uses `pg_trgm` GIN indexes. `unaccent` is applied only through versioned normalization where it does not damage the language contract.

Search configuration version, normalization version and weights are stored with the projection generation. Query construction is fully parameterized.

### PAT-U03-04 — HNSW with Exact-Scan Oracle

One HNSW index exists per compatible embedding model/dimension generation. Build-time and query-time parameters are configuration, not constants in domain code. Release evaluation compares approximate top results to an exact-vector reference over the same approved snapshot. HNSW tuning must preserve the per-language Recall@10 threshold while meeting the 2.5-second semantic budget.

Incompatible model versions are never queried together. A missing compatible generation produces text fallback, not coercion or vector padding.

### PAT-U03-05 — Reciprocal Rank Fusion

Text and vector retrievers return ranked content IDs with evidence. The HybridRanker combines ranks with versioned Reciprocal Rank Fusion. Exact-title tier and hard filters remain outside fusion: exact-title precedence is preserved and no fusion score can reintroduce a filtered item.

For a fixed CatalogVersion, projection generation, query normalization version and RRF configuration, ranking is deterministic. Content ID is the final tie-breaker.

### PAT-U03-14 — Evolutionary Scale-Out

API instances remain stateless. Projection workers can scale by job type and content partition while preserving per-content order and CatalogVersion gap barriers. PostgreSQL is the shared consistency boundary and connection budgets remain centrally calculated.

Separate search infrastructure requires a new architecture gate based on measured saturation, quality, rebuild or independent-scaling need. Scale pressure alone does not bypass approved closure.

## Resilience Patterns

### PAT-U03-06 — Asynchronous Versioned Embedding

Catalog publication commits without calling the embedding provider. A versioned outbox event schedules embedding generation. The event contains approved revision reference and model contract, never raw/quarantined payload. Until the new vector is generated and validated, the previous compatible projection remains active and current approval is still rechecked.

Successful embedding creates a candidate generation record. Publication occurs only after model/dimension, finite values, content ownership and approved-revision checks pass.

### PAT-U03-07 — Circuit Breaker and Dependency Bulkhead

The embedding adapter has a maximum request concurrency of four per process. The circuit evaluates the latest 20 eligible calls and opens for 30 seconds when failures reach 50 percent. Half-open allows two probes; both must succeed before closing. Timeout, connection failure, eligible 5xx and contract-invalid responses count toward the circuit. User cancellation and local validation errors do not.

Circuit state is observable but contains no raw query. When open, callers fail fast into approved text fallback.

### PAT-U03-08 — Retry by Execution Path

User search never automatically retries embedding calls because the 3-second response budget and fallback are more valuable than a repeated dependency call. Background embedding jobs retry only explicitly retry-safe failures, at most twice, using exponential backoff with jitter and a durable attempt record. Contract errors, invalid vectors and authorization failures are not retried.

### PAT-U03-09 — Approved Text/Filter Degradation

Semantic timeout, open circuit, model incompatibility or vector-generation absence routes to text/filter search. The fallback applies the same filters, authoritative approval, withdrawal, license and regional availability closure. Response includes a stable degraded reason and versions but never internal provider text.

If PostgreSQL authoritative closure is unavailable, the fallback also fails closed. Semantic failure cannot turn a safety failure into a stale response.

### PAT-U03-10 — Ordered Parallel Projection Claims

Workers claim durable events with `FOR UPDATE SKIP LOCKED`. Work may run in parallel across content partitions, but one content ID is processed in source order. Completion records include event ID, content ID and CatalogVersion. A worker cannot advance the active applied version past an unresolved lower CatalogVersion.

### PAT-U03-11 — Gap Barrier

The ProjectionCoordinator maintains the highest contiguous applied CatalogVersion. Receiving a higher non-contiguous version records a gap, stops global advancement and schedules replay/reconciliation. The currently active validated generation remains readable. Gap detection alerts immediately.

### PAT-U03-12 — Idempotent Receipt and Replay

A unique receipt per consumer/event makes duplicate delivery a no-op. Handlers use compare-and-set against content revision/model version so older work cannot replace newer output. Restart resumes uncompleted claims after lease expiry. Replay produces observable state equivalent to one ordered application.

### PAT-U03-13 — Immutable Generation Build and Swap

Rebuild creates a new immutable generation beside the active one. It captures source CatalogVersion, FeedPolicyVersion, search configuration and embedding versions. Validation checks completeness, approved closure, no duplicates, version continuity and quality/latency smoke tests.

One PostgreSQL transaction changes the active-generation pointer. The previous generation remains immutable through the rollback window. A failed build or pointer swap leaves the current active generation unchanged.

### PAT-U03-18 — Split Health and Readiness

Liveness checks process progress only. Readiness checks PostgreSQL, required extensions, current generation readability and closure query capability. Embedding provider health is reported separately: its failure marks semantic mode degraded but does not remove safe text/feed readiness. Deep health is protected as required by U07.

### PAT-U03-20 — Failure Injection

Automated component/integration tests inject embedding timeout/open/half-open behavior, PostgreSQL closure-read failure, duplicate/out-of-order/gap events, worker restart after claim, rebuild validation failure and active-pointer swap failure. Tests assert safe fallback or fail-closed behavior, state equivalence after retry/replay, observability signals and absence of unapproved leakage.

This extends the inherited lightweight dependency-failure practice. Quarterly restore drills remain U07-owned and include U03 CatalogVersion continuity and projection rebuild validation.

## Security and Privacy Patterns

### PAT-U03-15 — Purpose-Separated HMAC Keys

Query fingerprints and cursor signatures use different injected HMAC keys. Each signed payload carries a non-secret key ID. Verification accepts the current and immediately previous key during rotation, while all new signatures use the current key. A bounded cursor expiry limits the dual-verify window.

An unkeyed query hash is forbidden. Rotation emits counts by key ID but never raw payload. Key material is not stored with Catalog or projection data.

### PAT-U03-16 — Layered Rate Limits

The reverse proxy enforces a basic IP bucket. The application enforces subject/IP and endpoint-cost buckets: anonymous 30 and authenticated 60 U03 requests/minute. Semantic search uses a distinct high-cost bucket/concurrency bulkhead, so exhaustion cannot block feed/detail/text requests. Rejection occurs before database or embedding work and uses a stable retry response contract.

### PAT-U03-17 — Privacy-Minimized Observability

Request telemetry records correlation ID, locale, query-length bucket, parsed-field count, result-count bucket, versions, latency and degraded reason. It never records raw query, normalized query, vector, unapproved payload or provider error body. Fingerprints are keyed and rotate with PAT-U03-15.

All SQL/FTS/vector expressions use typed parameters. Cursor decoding validates integrity and bounds before query construction.

## Observability and Quality Patterns

### Alert Thresholds

| Signal | Initial threshold | Response |
|---|---|---|
| CatalogVersion gap | Any gap | Immediate alert and replay/reconciliation |
| Projection lag | Over 5 minutes for 5 minutes | Alert; keep validated generation active |
| Approval-closure drop | At least one | Immediate safety/data-quality investigation |
| Semantic fallback rate | Over 20% for 15 minutes | Alert dependency/compatibility owner |
| Zero-result ratio | More than 2 times versioned baseline | Investigate index, parser and data freshness |
| Stale-content ratio | More than 2 times versioned baseline | Investigate ingestion/projection health |

Threshold changes are versioned and must retain rationale. Low-volume ratio alerts require a minimum sample count to avoid noise; the exact sample floor is tuned in Code Generation configuration.

### PAT-U03-19 — Quality and PBT Gates

The release gate combines US-001~US-006 examples, per-language Recall@10/NDCG@10, real-PostgreSQL integration tests with zero selected skips, closure branch coverage and PBT-U03-01~16. HNSW is compared with an exact-vector oracle. Cursor pagination is compared with a fully sorted reference. Projection command sequences use a stateful reference model.

## Traceability

| Pattern group | U03 NFRs |
|---|---|
| PAT-U03-01~05 | 003~013, 029~035, 045 |
| PAT-U03-06~13 | 014~028, 045~048 |
| PAT-U03-14 | 004~005 |
| PAT-U03-15~17 | 036~044 |
| PAT-U03-18 | 020~023, 048 |
| PAT-U03-19 | 029~034, 050~054 |
| PAT-U03-20 | 014~018, 021~028, 053 |

## Extension Compliance

### Resiliency

- **RESILIENCY-01~02 — Compliant**: High/Medium workloads and inherited availability/recovery targets drive the patterns.
- **RESILIENCY-03~04 — Compliant by inheritance**: Versioned configuration, immutable generations and rollback evidence fit the GitHub Actions/direct-deploy process.
- **RESILIENCY-05~07 — Compliant**: Metrics, structured logs, split health, projection/fallback/closure alerts and dashboard inputs are explicit.
- **RESILIENCY-08~09 — N/A for the prototype**: Single-server/no-auto-scaling exceptions remain; stateless/partitionable evolution and triggers are preserved.
- **RESILIENCY-10 — Compliant**: Deadline, path-specific retry, circuit, bulkhead and approved fallback are fully designed.
- **RESILIENCY-11~13 — Compliant by U07 ownership**: Backup/restore remains U07-owned; U03 adds continuity and projection validation to re-entry.
- **RESILIENCY-14 — Compliant**: The selected lightweight automated failure tests plus quarterly restore drill are incorporated.
- **RESILIENCY-15 — Compliant**: Alerts route into the inherited lightweight incident/COE flow.

### Property-Based Testing

- **PBT-01 — Compliant**: All PBT-U03-01~16 design boundaries remain identifiable.
- **PBT-02~PBT-07 — Planned for Code Generation**: Round-trip, invariant, idempotence, oracle and stateful properties have concrete component boundaries.
- **PBT-08~PBT-10 — Planned/Compliant handoff**: Hypothesis, seed/shrink evidence and complementary examples remain mandatory implementation gates.

Security Baseline is disabled; core security/privacy patterns remain enforced. No blocking extension finding remains.

