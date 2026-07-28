# U04 Ingestion and Metadata Governance NFR Design Patterns

## Reliability and Consistency Patterns

### Durable Page Claim with Fencing

The scheduler creates bounded pages of at most 1,000 records. A worker claims a page using a lease, fencing version and expiration. Only the current fencing version may persist page progress. Cursor advancement and reconciled outcome counts commit only after every record has a durable state. Expired work can be reclaimed without trusting the former process.

### Record-Level Transaction Isolation

Raw persistence and page membership form one short transaction. Each normalization/validation decision is committed independently, so a malformed record cannot roll back siblings. Database transactions never span provider HTTP or U03 calls.

### Transactional Pending Publication

A passed decision and publication job are persisted atomically in U04. The dispatcher sends the immutable decision key to U03. A returned CatalogVersion creates a unique receipt. Timeout or restart reuses the same key; it never reruns validation merely to deliver the same decision.

### Idempotent Inbox and Replay

Provider record digest plus policy/version identifies unchanged observations. Attempt keys deduplicate normalization, revalidation and manual retry. Cursor replay, duplicate provider delivery and U03 retry converge on the same observable state. PBT-U04-02, 09, 10 and 12 verify these properties.

### Fail-Closed Validation Closure

Unknown, error or missing mandatory rule results are failures. Only a complete immutable passed decision can create a U03 command. Quarantine and raw payload types are structurally excluded from the publication mapper. PBT-U04-07 and 08 verify closure and non-leakage.

## Dependency Resilience Patterns

### Provider Bulkhead

Each provider has independent concurrency, connection pool, rate bucket, queue-age budget and circuit state. The global dispatcher applies round-robin or weighted-fair selection among eligible providers. One provider cannot consume another provider's reserved capacity.

### Timeout, Retry and Circuit Policy

Provider and U03 adapters receive explicit connect, read and total budgets from versioned configuration. Only classified transient failures retry with exponential backoff, full jitter and a bounded attempt count. Rate-limit responses honor provider retry-after. Repeated failure opens a dependency-specific circuit; half-open probes use isolated capacity.

Exact values are selected in implementation configuration within these upper bounds:

| Dependency | Connect | Total attempt | Attempts | Circuit opening signal |
|---|---:|---:|---:|---|
| Provider API | at most 3 seconds | at most 30 seconds | at most 3 | 5 consecutive transient failures or 50% failure over 20 calls |
| U03 publication | at most 1 second | at most 5 seconds | at most 5 delivery attempts before delayed recovery queue | 5 consecutive availability failures |
| PostgreSQL statement | N/A | at most 5 seconds for online claims/decisions | transaction retry at most 2 for classified serialization/deadlock | readiness failure on sustained inability |

Provider-specific policy may lower these values. Increasing them requires capacity evidence and a versioned change record.

### Last-Valid Degradation

Collection, provider or U04 worker failure never sends a withdrawal. U03 continues serving the last valid revision with freshness state. Global readiness remains healthy for isolated provider failure, while PostgreSQL or rule-store failure closes new processing.

## Scalability and Performance Patterns

### Bounded Work and Backpressure

Claim size, concurrent claims, payload bytes, decompressed bytes and pending-publication depth are bounded. When database saturation, publication age or memory crosses its guard, the scheduler stops new provider claims before accepting more work. Existing durable work drains first.

### Fair Scheduling

Provider queues are selected fairly while respecting retry-after and next-eligible times. A full synchronization cannot starve incremental freshness work. Priority is: withdrawal/tombstone reconciliation, pending publication, incremental cursor work, scheduled revalidation, then full rebuild.

### Index-First Access

Logical indexes cover eligible jobs by next time/priority, active lease, provider cursor, payload digest, validation attempt key, decision state/age, quarantine reason, publication key and retention expiry. The 1,000,000-row gate verifies bounded index scans and prohibits unbounded status-table sweeps.

### Batched Retention Sweeper

Raw payload expiry uses small restartable batches ordered by expiry and ID. It removes only payload bodies permitted to expire and preserves digest/lineage. Backup/restore cannot make expired content normally readable again.

## Security and Governance Patterns

### Allowlisted Egress Adapter

Provider base origins are configuration, not payload input. HTTPS, redirect, DNS/IP and response-size policies are enforced before parsing. Secrets are injected into the adapter and never enter domain entities, telemetry or error objects.

### Untrusted Payload Boundary

Byte and decompression limits apply before schema parsing. Pydantic boundary models enforce nesting, list, string and identifier limits. Provider-controlled values map only through declared canonical fields and parameterized persistence operations.

### Immutable Policy Activation

Provider, normalization, identity, merge and validation policies are immutable versions. An authorized activation changes the current pointer and emits an audit reference. Historical decisions always resolve their original versions; breaking U03/U05 predicates require a new contract version.

### Minimal Telemetry

Logs and traces carry provider ID, job/attempt IDs, bounded reason code and policy versions, never raw payload, token, URL query, provider response text or licensed non-display fields. Metric labels use bounded enums and provider IDs only.

## Observability and Recovery Patterns

### Layered Health

- Shallow: process/event-loop liveness.
- Readiness: PostgreSQL job/rule access and ability to persist a decision.
- Dependency status: U03 and each provider reported separately without making an isolated provider failure globally unready.
- Recovery status: oldest cursor, pending publication and unfinished restored work.

### Invariant Alarms

Quarantine leakage, duplicate publication receipt, cursor regression and count mismatch trigger immediate pipeline isolation. Lag/freshness/quarantine-rate alarms use the thresholds defined in U04-NFR-046. Alerts include job/provider/version identifiers and link to the lightweight incident record.

### Restore Re-entry Guard

After restore, schema and version references are checked, pending U03 outcomes are reconciled, cursor monotonicity and receipt uniqueness are verified, then provider claims resume. Re-entry fails closed if closure checks fail.

## Verification Handoff

| Pattern | Required evidence |
|---|---|
| Fenced page claims | concurrent PostgreSQL integration and state-machine tests |
| Transactional pending publication | failure injection before/after commit and receipt uniqueness |
| Provider bulkhead/circuit | deterministic fake-clock adapter tests and provider-isolation load test |
| Backpressure/fair scheduling | sustained/burst load and starvation assertions |
| Validation closure | 100% critical branch coverage, examples and PBT-U04-07/08 |
| Replay/idempotence | PBT-U04-02/09/10/12 and restart integration tests |
| Retention sweeper | licensed-expiry examples, batch restart and restore guard tests |
| Egress/payload boundary | SSRF, redirect, decompression, size and telemetry-redaction tests |

## Extension Compliance

- RESILIENCY-05~07: layered health, metrics, alarms and recovery status are designed.
- RESILIENCY-09: auto-scaling is N/A for the prototype; backpressure and numeric reassessment triggers are present.
- RESILIENCY-10: explicit timeout, retry, circuit, bulkhead and last-valid degradation are designed.
- RESILIENCY-11~14: durable replay, backup-aware retention, restore re-entry and failure scenarios are defined.
- PBT-01 handoff: all twelve U04 properties map to concrete patterns and evidence.

No blocking enabled-extension finding remains.
