# U04 Ingestion and Metadata Governance NFR Requirements

## Scope and Inherited Baseline

U04 covers provider synchronization, raw retention, normalization, deterministic identity/merge, validation, quarantine, revalidation and durable U03 publication dispatch. It inherits the Python 3.12 modular monolith, PostgreSQL 17 runtime, Docker delivery, monthly 99.0% prototype service objective, RTO 4 hours, RPO 24 hours and Backup and Restore strategy.

The prototype runs on one server for fewer than 10 concurrent users. Production multi-zone and auto-scaling remain transition gates rather than current claims.

## Requirement Summary

| Area | Target |
|---|---|
| Criticality | Publication safety and quarantine boundary High; provider collection Medium |
| Capacity | 20 providers, 100,000 canonical contents, 1,000,000 retained lineage/decision rows in verification data |
| Throughput | Sustained 10 records/second and burst 25 records/second for 10 minutes |
| Full synchronization | 100,000 provider records within 4 hours, excluding provider-enforced pauses |
| Pipeline latency | Durable raw record p95 2 seconds; validation decision p95 5 seconds; passed decision delivered to U03 p95 60 seconds |
| Freshness | At least 95% of eligible provider records processed within the provider-specific refresh window |
| Availability | Monthly 99.0% internal worker objective, excluding provider outage and planned maintenance |
| Recovery | RTO 4 hours, RPO 24 hours, deterministic cursor replay and pending-publication reconciliation |
| Testing | Overall line coverage at least 80%; validation, quarantine and publication safety branches 100% |

## Workload Criticality and Capacity

- **U04-NFR-001**: Validation closure, quarantine non-leakage and U03 publication idempotence are High because failure can expose unlicensed, stale or incorrect metadata.
- **U04-NFR-002**: Provider collection scheduling is Medium because U03 continues serving the last valid approved catalog during an outage.
- **U04-NFR-003**: Capacity verification must cover 20 configured providers, 100,000 canonical contents, at least 5 localized field candidates and 10 regional availability candidates per representative content.
- **U04-NFR-004**: Persistence verification must include 1,000,000 raw/normalized/validation lineage rows so retention, index and replay behavior are measured beyond the current catalog cardinality.
- **U04-NFR-005**: A baseline worker test must sustain 10 records/second for 30 minutes and a 25-records/second burst for 10 minutes while measuring queue age, database saturation, provider fairness and publication lag.
- **U04-NFR-006**: A 100,000-record full provider synchronization must complete within 4 hours, excluding documented provider rate-limit or retry-after pauses.
- **U04-NFR-007**: Scale review is mandatory when provider count exceeds 20, a provider page exceeds 100,000 records, retained lineage exceeds 1,000,000 rows, sustained demand exceeds 10 records/second, burst demand exceeds 25 records/second or resource saturation persists.
- **U04-NFR-008**: One provider cannot consume more than its configured worker and connection budget or starve other providers.

## Performance and Freshness

- **U04-NFR-009**: Persisting a received raw record and durable page membership must achieve p95 2 seconds under baseline load, excluding upstream download time.
- **U04-NFR-010**: Normalization, identity resolution, merge and validation must produce a durable decision within p95 5 seconds per record under baseline load.
- **U04-NFR-011**: A passed decision must receive a U03 CatalogVersion within p95 60 seconds in normal operation.
- **U04-NFR-012**: At least 95% of eligible records must reach a durable published, unchanged, quarantined or retryable state within the provider-specific refresh window.
- **U04-NFR-013**: Performance reports must include p50, p95, p99, records/second, error/quarantine/retry rates, oldest cursor age, oldest pending publication, database connections and CPU/memory/storage saturation.
- **U04-NFR-014**: Provider fetch time, provider-enforced delay, internal transformation time and U03 publication time must be measured separately.
- **U04-NFR-015**: Raw payload size defaults to a 2 MiB per-record limit and decompressed page size defaults to 32 MiB; provider-specific increases require a versioned policy, capacity evidence and security review.
- **U04-NFR-016**: Internal collection pages are bounded to at most 1,000 records per claim so one transaction cannot monopolize the worker or database.

## Availability, Reliability and Consistency

- **U04-NFR-017**: U04 participates in the monthly 99.0% prototype objective for scheduler, worker and internal validation availability, excluding planned maintenance and the external provider's own availability.
- **U04-NFR-018**: Provider failure cannot remove or silently refresh the last valid U03 revision.
- **U04-NFR-019**: A record-level failure is isolated; valid sibling records progress and the job reports partial success.
- **U04-NFR-020**: Raw persistence, page membership and payload digest are one U04 transaction. Validation run, rule results and decision are another atomic U04 transaction.
- **U04-NFR-021**: U03 publication is not a distributed transaction. A durable `passed_pending_publication` decision and stable idempotency key bridge the boundary.
- **U04-NFR-022**: An unknown U03 outcome is retried or reconciled with the same key. It cannot create a second validation decision or observable catalog transition.
- **U04-NFR-023**: Cursor advancement requires every claimed record to have a durable outcome. Restart and replay cannot omit records or duplicate observable publication.
- **U04-NFR-024**: Retryable provider/U03 calls use explicit connection and total timeouts, limited attempts, exponential backoff with jitter and dependency-specific circuit state; exact budgets are defined in NFR Design.
- **U04-NFR-025**: Retry exhaustion leaves durable recoverable state and never converts technical failure into validation quarantine unless a stable non-transient contract conflict exists.
- **U04-NFR-026**: PostgreSQL inability is fail-closed for new decisions and cursor advancement. Existing U03 reads remain independent.
- **U04-NFR-027**: Provider-specific concurrency, connection pools and rate-limit buckets form bulkheads so one dependency cannot exhaust shared capacity.

## Recovery and Data Protection

- **U04-NFR-028**: U04 durable job, cursor, provenance, normalization, merge, rule, validation, quarantine and publication-receipt state is included in encrypted daily backups with 30-day retention.
- **U04-NFR-029**: Recovery must meet RTO 4 hours and RPO 24 hours under the inherited Backup and Restore strategy.
- **U04-NFR-030**: Raw payload bodies follow provider-specific licensed retention and may expire earlier than backup retention; expired bodies cannot be resurrected through normal restore without a documented legal basis.
- **U04-NFR-031**: Post-restore validation verifies schema, policy/rule version references, cursor monotonicity, decision/result closure, quarantine non-leakage and publication-receipt uniqueness.
- **U04-NFR-032**: Service re-entry first reconciles pending publication outcomes, then resumes provider cursors; it does not rerun already acknowledged publication with a new key.
- **U04-NFR-033**: Recovery tests include interrupted page claims, duplicate delivery, U03 timeout after commit, raw-body expiry and validation-rule change during backlog.

## Security, Licensed Data and Abuse Controls

The Security Baseline extension is disabled, but these core controls are mandatory.

- **U04-NFR-034**: Provider credentials, signing keys and tokens are injected as secrets and never stored in provider policy rows, source code, images, raw payload history, logs or test fixtures.
- **U04-NFR-035**: Provider endpoints must use configured HTTPS origins. Redirects, DNS resolution and outbound destinations are restricted to the provider allowlist to prevent server-side request forgery.
- **U04-NFR-036**: Provider payloads are untrusted input. Parsing enforces byte, nesting, collection-cardinality, string-length and decompression limits before domain processing.
- **U04-NFR-037**: SQL and filter expressions are parameterized. Provider-controlled identifiers and JSON paths cannot become SQL identifiers without an explicit mapping.
- **U04-NFR-038**: Raw payload bodies, provider credentials and licensed non-display fields are excluded from logs, metrics, traces, errors, U03 commands and U05 contracts.
- **U04-NFR-039**: Raw payload access, manual revalidation and provider policy activation require server-side operator authorization and produce actor, reason, time and target-version audit references.
- **U04-NFR-040**: Raw retention and deletion follow the immutable ProviderPolicy version recorded at collection time. Digest and minimum provenance remain only when permitted.
- **U04-NFR-041**: Payload digests use SHA-256 or a stronger approved standard. Digests support equality/integrity and are not treated as authentication signatures.
- **U04-NFR-042**: Stable public/operator error codes cannot contain raw provider text, secrets, internal paths or stack traces.
- **U04-NFR-043**: Dependency and container vulnerability scans remain mandatory CI gates under U07 policy.

## Observability and Operations

- **U04-NFR-044**: Structured logs include correlation/job/attempt IDs, provider ID, page fingerprint, policy/rule/normalization versions, state transition, duration and stable result code without raw payload.
- **U04-NFR-045**: Metrics cover records by state, throughput, job outcomes, quarantine reason family, retry/rate-limit count, cursor age, pending-publication age, provider fairness, raw expiry, tombstones and U03 receipt outcomes.
- **U04-NFR-046**: Alerts fire when the oldest pending publication exceeds 5 minutes, cursor age exceeds twice its provider refresh window, no successful provider sync occurs within two expected windows, a job remains running beyond 4 hours, or quarantine rate exceeds 20% for 15 minutes with at least 100 records.
- **U04-NFR-047**: Any quarantine non-leakage violation, duplicate publication receipt, cursor regression or count-reconciliation failure is a page immediately and blocks the affected pipeline.
- **U04-NFR-048**: Shallow health confirms worker process liveness. Deep health reports PostgreSQL/job-store access, policy/rule readability and U03 publication connectivity separately from provider-specific degradation.
- **U04-NFR-049**: A failing provider does not make global readiness fail while other providers and durable recovery remain safe; PostgreSQL or rule-store failure does fail readiness.
- **U04-NFR-050**: Dashboard panels expose the 99.0% objective, throughput, saturation, freshness compliance, cursor/publish lag, quarantine distribution, retry/circuit state and recovery backlog.
- **U04-NFR-051**: Alerts integrate with the inherited lightweight incident process and retain incident references for rule, provider and code-version changes.

## Maintainability, Testing and Consumer Usability

- **U04-NFR-052**: Provider adapters implement one typed ProviderPort and cannot contain validation, merge or U03 persistence rules.
- **U04-NFR-053**: ProviderPolicy, normalization, identity, merge and ValidationRuleContract changes are immutable versions with compatibility evidence and rollback notes.
- **U04-NFR-054**: Overall measured source line coverage remains at least 80%; validation closure, quarantine non-leakage and publication idempotency branches require 100% coverage.
- **U04-NFR-055**: US-020 and each critical failure family require explicit example tests in addition to PBT-U04-01~12.
- **U04-NFR-056**: Hypothesis tests use reusable domain strategies, retain shrinking, log a reproducible seed and promote shrunk failures to permanent examples.
- **U04-NFR-057**: PostgreSQL integration tests execute on real PostgreSQL 17 with zero skips; a skipped selected integration test cannot satisfy the gate.
- **U04-NFR-058**: Contract tests verify U03 PassedValidation/withdrawal compatibility and U05 ValidationRuleContract compatibility for current and previous supported versions.
- **U04-NFR-059**: Migration tests cover clean installation, upgrade from U03 head, rollback compatibility policy and 1,000,000-row index/query plans.
- **U04-NFR-060**: U04 owns no end-user UI. Operator consumers receive stable reason codes, counts, timestamps and status transitions suitable for accessible U06 presentation.

## Verification Matrix

| NFR set | Verification method | Evidence stage |
|---|---|---|
| 001~008 | Capacity fixtures, sustained/burst tests and provider fairness review | Code Generation, Build and Test |
| 009~016 | Pipeline benchmarks, payload-limit tests and PostgreSQL saturation evidence | Code Generation, Build and Test |
| 017~027 | Failure injection, transaction, replay, retry and circuit tests | NFR Design, Code Generation |
| 028~033 | Backup manifest, restore/re-entry and expiry/replay drills | Infrastructure Design, Build and Test |
| 034~043 | Secret scan, SSRF/parser/input tests, authorization and telemetry redaction scans | Code Generation, Build and Test |
| 044~051 | Log/metric/health contracts, dashboards and alert-rule tests | NFR Design, Code Generation |
| 052~060 | Static checks, coverage, PBT, real PostgreSQL, migration and consumer contracts | Code Generation, Build and Test |

## Resiliency Compliance

| Rule | Status | U04 treatment |
|---|---|---|
| RESILIENCY-01 | Compliant | Publication safety is High, collection is Medium, impacts and U03/U07/provider dependencies are documented |
| RESILIENCY-02 | Compliant | Inherits 99.0%, RTO 4 hours and RPO 24 hours |
| RESILIENCY-03 | Compliant | Inherits prototype change exemption while requiring version history and rollback notes |
| RESILIENCY-04 | Compliant | Inherits GitHub Actions, direct deployment and version-pinned rollback; migrations remain compatible |
| RESILIENCY-05 | Compliant | Metrics, structured logs, dashboard dimensions and alert thresholds are specified |
| RESILIENCY-06 | Compliant | Shallow/deep health and provider-specific degradation are required |
| RESILIENCY-07 | Compliant | Cursor, publication, freshness, saturation, backup and invariant signals are monitored |
| RESILIENCY-08 | N/A | Approved single-server prototype exception; production transition must reassess multi-zone topology |
| RESILIENCY-09 | N/A | Prototype does not auto-scale; numeric capacity and review triggers are defined |
| RESILIENCY-10 | Compliant | Timeout, bounded retry, circuit, provider bulkhead and last-valid degradation are mandatory |
| RESILIENCY-11 | Compliant | Backup and Restore matches inherited RTO/RPO |
| RESILIENCY-12 | Compliant | Durable U04 state is backed up while licensed raw retention remains authoritative |
| RESILIENCY-13 | Compliant | Restore validation, pending-publication reconciliation and cursor resume define re-entry |
| RESILIENCY-14 | Compliant handoff | Required failure/recovery scenarios are identified; schedule/mechanics are finalized in NFR Design |
| RESILIENCY-15 | Compliant | Alerts, immutable versions and incident references support correction and learning |

No blocking Resiliency finding remains at U04 NFR Requirements.

## Property-Based Testing Compliance

| Rule | Status | U04 treatment |
|---|---|---|
| PBT-01 | Compliant | PBT-U04-01~12 from Functional Design are mandatory handoff inputs |
| PBT-09 | Compliant | pytest 9.1.1 and Hypothesis 6.161.5 are selected and locked |
| PBT-08 | Planned | Shrinking, seed logging, replay and regression promotion are explicit requirements |
| PBT-02~07, PBT-10 | N/A at this stage | Executable generators/tests and complementary examples are Code Generation responsibilities |

No blocking PBT finding remains at U04 NFR Requirements.

## Security Baseline

Disabled by the approved Extension Configuration. U04-NFR-034~043 remain mandatory core security and licensed-data controls.
