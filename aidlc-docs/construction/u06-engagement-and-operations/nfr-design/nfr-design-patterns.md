# U06 Engagement and Operations NFR Design Patterns

## Bounded Worker Lanes and Backpressure

U06 uses three independently bounded PostgreSQL-backed lanes: in-app delivery, email delivery and retention/maintenance. In-app has scheduling priority because its p95 target is one minute, but it cannot consume email or maintenance concurrency. Each lane owns its claim size, concurrency, lease, queue-age metric and saturation outcome.

| Lane | Initial concurrency | Claim maximum | Saturation behavior |
|---|---:|---:|---|
| In-app | 2 | 100 | Leave excess pending and alert at oldest age above 5 minutes |
| Email | 2 | 50 | Leave excess pending; circuit-open work is rescheduled within expiry |
| Retention/maintenance | 1 | 500 | Checkpoint, yield and resume without competing for delivery slots |

Admission uses a stable deduplication key before job allocation. Queue growth cannot allocate unbounded memory because workers stream bounded claims and persist state transitions. Core Feed, Search and Recommendation request pools do not wait for U06 delivery capacity.

## Lease, Fencing and Idempotent Completion

Workers claim ready jobs with `FOR UPDATE SKIP LOCKED`, set a unique lease owner, expiring lease time and monotonically increasing fencing token, then commit before external work. A heartbeat may extend a lease only while the owner and token still match.

Completion, retry and cancellation compare the current fencing token. A stale worker can neither overwrite a newer attempt nor mark a cancelled job delivered. Provider receipts reconcile through the same job/channel idempotency key. Expired leases return to ready state through a bounded recovery sweep; they are not treated as new user-visible jobs.

P-U06-03 and P-U06-04 verify replay and random claim, expiry, cancellation, retry and completion sequences against a reference state model.

## Email Timeout, Retry and Circuit Isolation

Each email attempt has a five-second total deadline. Retry eligibility is decided from a bounded error enum; authentication, schema, recipient and policy failures are terminal. Transient failure delays are based on 5 seconds, 30 seconds and 5 minutes with injected bounded jitter. The absolute stop is the earlier of 30 minutes and event expiry.

The email circuit observes a rolling 20-result window and does not evaluate failure ratio until 10 results exist. A failure rate of 50% opens it for 30 seconds. Half-open permits a small bounded probe set; success closes the circuit and failure reopens it. Circuit state affects only the email lane. In-app delivery and synchronous product requests continue.

All time, jitter and circuit transitions use injected Clock and Random ports so failure tests are deterministic.

## Database Connection and Transaction Budget

The shared prototype database budget reserves four API, two notification-worker and one maintenance connection for U06, with acquisition timeout and zero overflow. The exact engine pool wiring remains U07-owned, while U06 exposes pool-wait and timeout signals.

Transactions are deliberately short:

1. Validate and persist command/job intent plus idempotency state.
2. Commit before channel or cross-unit calls.
3. Perform bounded external work.
4. Reopen a transaction and close using expected version/fencing token.

Privileged admin completion is not reported until its cross-unit receipt and append-only audit event close atomically in U06. If audit closure fails, the command remains non-successful and is reconciled rather than guessed successful.

## Index and Query Patterns

| Access path | Initial index pattern |
|---|---|
| Notification deduplication | Unique member-reference, content, event type, effective time and channel key |
| Ready job claim | Partial/composite lane, status, available-at, expiry, priority and job ID |
| Lease recovery | Status, lease-expiry and fencing token |
| Member notification list | Member reference, created-at descending and notification ID keyset |
| Active override lookup | Content ID, status, start/expiry and override ID |
| Override expiry | Active status, expiry and override ID |
| Audit investigation | Occurred-at descending plus audit ID keyset; target/type and correlation lookup indexes |
| Open incident correlation | Unique active correlation key; status, severity and updated-at query index |
| Retention | Expiry/retention class and primary ID keyset |

Initial tables are not partitioned. Query-plan evidence at 10,000 pending jobs and 100,000 audit/incident rows is required. Partitioning is reconsidered only after measured table/index maintenance or retention cost crosses the scale trigger.

## Audit HMAC Integrity and Key Rotation

Audit fields are projected into one versioned canonical representation with deterministic ordering, explicit type encoding and domain separation. HMAC-SHA-256 uses a file-injected audit key ring containing one current signing key and bounded previous verification keys. Records store algorithm, canonical schema version and key ID, never key material.

Rotation switches new events to the new key. Historical events remain verifiable with the previous key during a defined overlap. A bounded maintenance command may re-sign canonical historical events as a new verification record; it never updates or deletes the original event. Digest mismatch raises an immediate audit-integrity alert and excludes the record from trusted evidence.

This pattern detects unintended alteration but does not claim external non-repudiation. Encrypted backup and separately authorized maintenance remain U07 responsibilities.

## Authorization, Recent Authentication and Request Integrity

The API resolves roles and recent-authentication state through U02 for every privileged request. Content Operator can read and submit allowlisted content operations; System Administrator can read trace, audit and incident data. A client role string is never authoritative.

High-impact exposure operations require:

- a U02 session authenticated within 15 minutes;
- expected catalog version and typed allowlisted patch;
- bounded explicit reason and correlation ID;
- idempotency key;
- valid Origin/CSRF controls inherited from U02/U07;
- an actor-and-operation rate bucket.

Forbidden and unknown targets return a common non-enumerating response. Authorization and audit failure paths are targeted for 100% branch coverage.

## Rate Limiting and Cache Safety

The prototype uses separate process-local fixed-window buckets for admin mutation and trace/investigation reads, keyed by pseudonymous actor and operation. Buckets have fixed capacities, bounded key retention and no direct identifiers. Multi-process or multi-instance deployment is a mandatory trigger to replace this with a shared limiter adapter.

Correctness data is not cached: roles, recent authentication, notification preferences, approval state, active overrides, trace views and health truth are read from authoritative versioned ports. Process cache is limited to immutable version-keyed policy definitions and localized templates. An unknown version misses closed rather than using an arbitrary current value.

## Deterministic Health Aggregation

Deep health fans out to contributors in bounded parallel calls. Each contributor has its own deadline and returns a typed immutable result containing required/optional class, state, reason, observation time and freshness limit. The aggregator is a pure truth table:

- process failure makes liveness false;
- missing, stale, unknown or unhealthy required evidence makes readiness false;
- optional failure adds degraded status but does not make liveness false;
- all externally visible names/reasons come from bounded vocabularies.

Results are assembled only after every contributor reaches a result or timeout. No last-success value survives beyond its explicit freshness. P-U06-11 compares aggregation to a reference oracle and permutes contributor arrival order.

## Alert Correlation and Incident Concurrency

Alert normalization produces a versioned correlation key from service, symptom and impact scope. A partial unique constraint permits one open incident per key. Creation and update use optimistic compare-and-set; racing signals reload and merge as occurrences rather than generating duplicate incidents.

Rate, duration and critical-immediate policies are immutable versions. A recovery signal moves an incident to monitoring. Recurrence under the same key returns monitoring to mitigating. Resolution requires owner and recovery evidence, then creates a COE/follow-up linkage. P-U06-12 exercises random alert and transition sequences against a reference state machine.

## Retention, Legal Hold and Restore Closure

Retention workers use class-specific expiry, bounded keyset claims and monotonic checkpoints. Legal hold is evaluated before deletion and wins over normal expiry. User deletion removes or irreversibly de-links destination/body data while preserving only authorized pseudonymous audit facts.

Restore verification checks schema head, job deduplication uniqueness, lease/fencing consistency, override version/state, audit sequence/HMAC verification, trace prohibited-field absence, open incident correlation uniqueness and U02~U05/U07 contract compatibility. Delivery remains paused until closure passes; in-app then email lanes resume in order.

## Scale Evolution

Scaling is evidence-driven:

1. Tune lane concurrency, claim sizes and PostgreSQL indexes within the shared connection budget.
2. Split API and U06 worker processes while retaining the same outbox and fencing contracts.
3. Review table partitioning and connection capacity when data/query evidence requires it.
4. Add a Broker Adapter only if queue SLO remains unmet after the previous steps.
5. Reassess multi-zone production topology before commercial launch.

The domain event and job contracts remain broker-neutral so evolution does not change business semantics.

## Verification Pattern Matrix

| Pattern | Required evidence |
|---|---|
| Lane isolation/backpressure | saturation and cross-lane failure injection; core-request non-impact |
| Lease/fencing/idempotency | concurrent real PostgreSQL claim, expiry, stale completion and replay tests |
| Retry/circuit | fake clock/random/channel adapter tests for every terminal/transient branch |
| Index/query | `EXPLAIN` evidence at 10,000 jobs and 100,000 audit/incident records |
| Audit HMAC | canonicalization round-trip, key rotation, mismatch and prohibited-field tests |
| Authorization/rate | role/recent-auth/CSRF/idempotency/non-enumeration and bucket boundary tests |
| Health | P-U06-11 oracle/permutation, timeout and stale contributor tests |
| Incident | P-U06-12 state machine plus alert race/correlation PostgreSQL tests |
| Retention/recovery | legal hold, deletion de-link, checkpoint replay and isolated restore drill |
| Scale/capacity | 5 sustained/15 burst RPS and documented transition-trigger evidence |

Monthly tests inject email and U02~U05 dependency failure, stale health and alert storms. Quarterly restore drills include U06 closure and retain machine-readable evidence. Overall coverage remains at least 80%, with named safety branches targeted at 100% and selected PostgreSQL integration reporting zero skips.

## Extension Compliance

RESILIENCY-01~02 are represented by criticality, SLO and inherited recovery goals. RESILIENCY-03~04 use versioned policy and reversible migration/adapter contracts. RESILIENCY-05~07 use bounded telemetry, layered health, queue/capacity and integrity alerts. RESILIENCY-08~09 retain the approved prototype exception with explicit scale gates. RESILIENCY-10 is satisfied by lanes, deadlines, retry/circuit/fencing and degradation. RESILIENCY-11~13 are covered by backup scope and restore closure. RESILIENCY-14 uses monthly failure tests and quarterly restore drills. RESILIENCY-15 uses deterministic incident/COE workflows.

P-U06-01~12 are assigned to codec, admission, deduplication, delivery/incident state machines, override oracle, audit induction, privacy and health patterns. PBT-02~08 and PBT-10 remain mandatory Code Generation evidence; PBT-09 remains compliant through locked Hypothesis. Security Baseline is disabled, while authorization, HMAC audit, trace allowlists, secret isolation and privacy checks remain blocking core design controls.

No blocking enabled-extension finding remains at U06 NFR Design.
