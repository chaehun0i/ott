# U03 Catalog and Discovery NFR Requirements

## Scope and Inherited Baseline

U03 covers approved Catalog reads, feed/detail queries, title/person search, Korean/English semantic search and feed/search projection processing. It inherits the U07 Python 3.12 modular-monolith runtime, PostgreSQL persistence, Docker/GitHub Actions delivery, monthly 99.0% prototype service objective, RTO 4 hours, RPO 24 hours and Backup and Restore strategy.

The prototype runs on one server for fewer than 10 concurrent users. Multi-zone and automatic scaling remain production-transition gates rather than prototype claims.

## Requirement Summary

| Area | Target |
|---|---|
| Criticality | User APIs and approval closure High; projection refresh/rebuild Medium |
| Capacity | 100,000 approved contents, 20 providers, 10 availability records and 5 locales per content |
| Throughput | 20 query requests/second and 10 projection records/second for 10 minutes |
| Feed/detail latency | Cache-free query p95 1.5 seconds; end-to-end p95 2 seconds |
| Text search latency | U03 p95 1 second; end-to-end p95 3 seconds |
| Semantic search latency | U03 p95 2.5 seconds; semantic dependency budget 1.5 seconds |
| Projection freshness | Normal p95 within 60 seconds; alert on lag over 5 minutes sustained for 5 minutes |
| Search quality | Per-language Recall@10 at least 0.80 and NDCG@10 at least 0.75 |
| Rebuild | 100,000-content snapshot within 30 minutes while the prior valid snapshot remains available |
| Caching | No application or reverse-proxy response cache; PostgreSQL query/projection only |
| Test gate | Overall line coverage at least 80%, critical closure branches 100%, examples plus PBT-U03-01~16 |

## Workload Criticality and Capacity

- **U03-NFR-001**: Feed, detail, text/semantic search and final approval/availability closure are High because their loss removes the product's discovery value or could expose invalid metadata.
- **U03-NFR-002**: Projection refresh and rebuild are Medium because the last validated snapshot and authoritative Catalog queries can continue serving while repair occurs.
- **U03-NFR-003**: Capacity verification must include 100,000 approved contents, 20 providers, up to 10 availability records and 5 localized representations per content.
- **U03-NFR-004**: The baseline load test must sustain 20 read requests/second and 10 projection records/second for 10 minutes while measuring latency, error rate, throughput, database saturation and projection lag.
- **U03-NFR-005**: A scale review is mandatory when approved content exceeds 100,000, concurrent users reach 50, sustained query traffic exceeds 20 requests/second, projection throughput exceeds 10 records/second, rebuild exceeds 30 minutes or PostgreSQL CPU, memory, connection or index saturation persists.
- **U03-NFR-006**: Capacity test data must preserve realistic content/localization/availability cardinality and must not replace those relationships with flat synthetic rows.

## Performance

- **U03-NFR-007**: Feed and detail U03 processing must achieve p95 1.5 seconds without an application cache, leaving the U07 boundary budget within the approved end-to-end p95 2-second target.
- **U03-NFR-008**: Text search U03 processing must achieve p95 1 second and total search must remain within p95 3 seconds.
- **U03-NFR-009**: Semantic search U03 processing must achieve p95 2.5 seconds under normal embedding-provider conditions and total search must remain within p95 3 seconds.
- **U03-NFR-010**: Semantic connection establishment is limited to 300 milliseconds and the complete embedding/retrieval dependency budget to 1.5 seconds. Expiry triggers approved text/filter fallback rather than extending the request.
- **U03-NFR-011**: Every performance report must include p50, p95, p99, throughput, error rate, fallback rate, PostgreSQL connection usage, query-plan/index evidence and resource saturation.
- **U03-NFR-012**: Pagination cost must remain bounded by keyset/opaque cursor access. Page-number offset scans are prohibited for public feed and search endpoints.
- **U03-NFR-013**: Public page size is limited to 50 and database queries must request at most one lookahead row beyond the page.

## Projection Freshness and Rebuild

- **U03-NFR-014**: Approved changes must reach feed and search projections within p95 60 seconds in normal operation.
- **U03-NFR-015**: Projection lag above 5 minutes sustained for 5 minutes must alert; a CatalogVersion gap must alert immediately and stop out-of-order advancement.
- **U03-NFR-016**: A full 100,000-content projection rebuild must complete within 30 minutes on the prototype capacity profile.
- **U03-NFR-017**: The prior validated projection must continue serving during rebuild. The new snapshot can become active only after approved-closure validation completes.
- **U03-NFR-018**: Duplicate Catalog events and restart/replay must not change the projection beyond the result of one successful application.
- **U03-NFR-019**: Application and reverse-proxy response caching are not used initially. CatalogVersion cache invalidation and feed/detail TTL requirements are therefore N/A; PostgreSQL authoritative queries and versioned projections carry read performance.

## Availability, Reliability and Data Integrity

- **U03-NFR-020**: U03 participates in the monthly 99.0% prototype service objective, excluding planned maintenance, without creating a contractual SLA.
- **U03-NFR-021**: Catalog storage inability is fail-closed because current approval and regional availability cannot be proven.
- **U03-NFR-022**: Semantic provider failure, timeout or incompatible vector version must be isolated and converted to approved text/filter fallback with a stable degraded reason code.
- **U03-NFR-023**: Projection lag may degrade search quality but cannot weaken authoritative approval, withdrawal, license or regional-availability checks.
- **U03-NFR-024**: Provider ingestion failure must preserve the last valid approved revision and expose its freshness state; it cannot erase or silently refresh timestamps.
- **U03-NFR-025**: Publication, CatalogVersion advancement and outbox write must be one PostgreSQL transaction.
- **U03-NFR-026**: Projection application must be monotonic and contiguous. Gaps require replay or rebuild, never best-effort skipping.
- **U03-NFR-027**: U03 persistent data is covered by U07 encrypted daily backup, 30-day retention, RTO 4 hours, RPO 24 hours and verified restore requirements.
- **U03-NFR-028**: A restored Catalog/projection set must pass schema, CatalogVersion continuity, approved-closure and representative feed/search smoke tests before traffic resumes.

## Search Quality and Localization

- **U03-NFR-029**: Korean and English must each have a versioned golden query set representing title, person, translation, natural-language condition, typo/variant, filter and no-result cases.
- **U03-NFR-030**: Each language must achieve Recall@10 of at least 0.80 and NDCG@10 of at least 0.75 before release.
- **U03-NFR-031**: Ranking evaluation must record dataset version, CatalogVersion, text configuration, embedding model/version, scoring policy version and random seed where applicable.
- **U03-NFR-032**: Search quality gates supplement, not replace, US-004~US-006 acceptance examples and approval-closure tests.
- **U03-NFR-033**: Korean and English parsers must emit the same structured-condition schema and preserve unresolved terms rather than inventing hard filters.
- **U03-NFR-034**: Locale fallback must return the actual locale and fallback level and must remain deterministic for a fixed approved revision.
- **U03-NFR-035**: A zero-result response must distinguish legitimate no-match from degraded dependency failure without exposing internal failure text.

## Security, Privacy and Abuse Controls

The Security Baseline extension is disabled, but these are core product/data requirements.

- **U03-NFR-036**: Raw search text must never appear in application logs, metrics, traces, alert labels or error responses.
- **U03-NFR-037**: Operational telemetry may record language, query-length bucket, parsed-field count, latency, result-count bucket and a keyed non-reversible query fingerprint. Fingerprint keys are injected as secrets and are rotatable.
- **U03-NFR-038**: Query and filter parsing must be parameterized; user input cannot be interpolated into SQL, full-text expressions or vector operators.
- **U03-NFR-039**: Anonymous clients are limited to 30 U03 requests/minute and authenticated subjects to 60/minute, using the U07 rate-limit boundary.
- **U03-NFR-040**: Query text is limited to 500 Unicode characters, total filter values to 50 and page size to 50. Invalid or excessive input fails before database/embedding work.
- **U03-NFR-041**: Opaque cursors must have integrity protection, expiry, schema version and query fingerprint; altered or cross-query reuse is rejected.
- **U03-NFR-042**: Provider links must use validated HTTPS destinations and must match current verified availability, requested region and active license window.
- **U03-NFR-043**: Search/embedding adapters receive only the minimum normalized search text and required model parameters; content or user data outside the request is excluded.

## Observability and Operations

- **U03-NFR-044**: Structured logs carry correlation ID, CatalogVersion, projection version, operation, duration, result count bucket, degraded reason and error code without raw query or unapproved payload.
- **U03-NFR-045**: Metrics cover feed/detail/text/semantic latency and error, throughput, zero-result ratio, semantic fallback rate, approval-closure drop count, projection lag/gap/replay, rebuild duration, stale-content ratio and PostgreSQL saturation.
- **U03-NFR-046**: Alerts cover CatalogVersion gaps, sustained projection lag, elevated semantic fallback, non-zero approval-closure drops, stale-content ratio regression, search zero-result spike and query latency/error SLO breaches.
- **U03-NFR-047**: Approval-closure drops are both a safety metric and a data-quality signal; any non-zero production occurrence requires investigation rather than suppression.
- **U03-NFR-048**: Shallow health confirms process liveness. Deep health verifies PostgreSQL, required extensions and projection-version readability while reporting semantic dependency health separately so its failure does not mark safe text search unavailable.
- **U03-NFR-049**: U03 dashboard panels must expose service SLOs, projection freshness, search quality release version, fallback/zero-result rates, closure drops, stale ratio and database/index saturation.

## Maintainability, Testing and Consumer Usability

- **U03-NFR-050**: Overall measured source line coverage remains at least 80%; CAT, AVAIL and PROJ approval-closure branches must achieve 100% coverage.
- **U03-NFR-051**: US-001~US-006 must have explicit example tests. PBT-U03-01~16 must all have Hypothesis tests using domain-specific generators.
- **U03-NFR-052**: PBT shrinking remains enabled, CI logs a reproducible seed and discovered minimal failures become permanent example regressions.
- **U03-NFR-053**: PostgreSQL integration tests must execute against a real PostgreSQL environment with required extensions; selected integration tests may not be counted as passed when skipped.
- **U03-NFR-054**: Migration tests cover clean install, U07/U02 upgrade to U03, required extension availability, forward application and rollback compatibility policy.
- **U03-NFR-055**: OpenAPI contracts document required region, opaque cursor, actual locale, freshness, source, projection/catalog versions, degraded state and stable error codes for U01/U05 consumers.
- **U03-NFR-056**: U03 owns no UI. Keyboard, visual and screen-reader behavior remains U01 responsibility, while U03 must supply localization and degraded-state data needed for accessible presentation.
- **U03-NFR-057**: Dependency and schema changes use the inherited lightweight Git change record, compatibility evidence and version-pinned rollback note.

## Verification Matrix

| NFR set | Verification method | Evidence stage |
|---|---|---|
| 001~006 | Capacity fixture, sustained load and scale-review checklist | Code Generation, Build and Test |
| 007~013 | Query benchmark, end-to-end performance test and query-plan review | Code Generation, Build and Test |
| 014~019 | Projection lag/replay/rebuild tests and cache-absence configuration review | Code Generation, Build and Test |
| 020~028 | Failure injection, PostgreSQL transaction/integration and restore smoke tests | Code Generation, Infrastructure Design, Build and Test |
| 029~035 | Versioned golden-set evaluation and acceptance examples | Code Generation, Build and Test |
| 036~043 | Log/trace scan, injection tests, limit tests, cursor tamper and link validation | Code Generation, Build and Test |
| 044~049 | Metric/log/health contract tests, dashboards and alert-rule review | NFR Design, Code Generation |
| 050~057 | CI, coverage, PBT seed/shrink, migration and OpenAPI compatibility artifacts | Code Generation, Build and Test |

## Resiliency Compliance

| Rule | Status | U03 treatment |
|---|---|---|
| RESILIENCY-01 | Compliant | User APIs/closure are High; projection processing is Medium, with impact and dependencies documented. |
| RESILIENCY-02 | Compliant | Inherits 99.0%, RTO 4 hours and RPO 24 hours. |
| RESILIENCY-03 | Compliant | Inherits lightweight Git change records and rollback notes. |
| RESILIENCY-04 | Compliant | Inherits GitHub Actions, direct deployment and version-pinned rollback. |
| RESILIENCY-05 | Compliant | U03 metrics, structured logs, dashboard signals and alerts are specified. |
| RESILIENCY-06 | Compliant | Shallow/deep health and separate semantic dependency status are required. |
| RESILIENCY-07 | Compliant | Projection lag/gap, closure drops, stale ratio and database saturation are monitored. |
| RESILIENCY-08 | N/A | Approved single-server prototype exception; production transition must reassess multi-zone topology. |
| RESILIENCY-09 | N/A | Prototype does not auto-scale; numeric scale-review triggers are defined. |
| RESILIENCY-10 | Compliant | Semantic timeout, isolation and approved text/filter degradation are explicit. |
| RESILIENCY-11 | Compliant | Inherits Backup and Restore DR aligned to RTO/RPO. |
| RESILIENCY-12 | Compliant | U03 data is included in encrypted daily backups, 30-day retention and restore validation. |
| RESILIENCY-13 | Compliant | Restore re-entry adds CatalogVersion continuity and closure smoke checks. |
| RESILIENCY-14 | N/A at this stage | Resiliency testing approach is finalized in NFR Design per the extension question. |
| RESILIENCY-15 | Compliant | U03 alerts integrate with the inherited lightweight incident/COE process. |

## Property-Based Testing Compliance

| Rule | Status | U03 treatment |
|---|---|---|
| PBT-01 | Compliant | PBT-U03-01~16 are inherited from Functional Design. |
| PBT-09 | Compliant | pytest 9.1.1 and Hypothesis 6.161.5 are selected and locked in the current project. |
| PBT-08 | Planned | Seed logging, shrinking and replay evidence are mandatory Code Generation gates. |
| PBT-02~07, PBT-10 | N/A at this stage | Executable properties, generators and complementary examples are Code Generation concerns; requirements are handed forward. |

No blocking extension finding remains at U03 NFR Requirements.

