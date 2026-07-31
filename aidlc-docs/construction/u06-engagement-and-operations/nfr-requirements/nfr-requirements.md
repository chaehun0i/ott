# U06 Engagement and Operations NFR Requirements

## Scope and Measurement Baseline

These requirements apply to notification admission/delivery, content-operation coordination, audit, recommendation trace investigation, health aggregation, alert correlation and incident management. Unless stated otherwise, latency is measured at the U06 API or worker boundary under the approved single-server prototype profile: fewer than 10 concurrent users, 5 sustained and 15 burst requests per second.

## Criticality and Capacity

- **U06-NFR-001**: Privileged content mutation, audit closure and incident state are high-criticality control paths because incorrect or unavailable behavior can expose invalid content or prevent accountable recovery.
- **U06-NFR-002**: Notification delivery is medium criticality and must remain isolated from Feed, Search, Recommendation and account request availability.
- **U06-NFR-003**: Trace investigation is high criticality for diagnosis but is never an authorization source for recommendation exposure.
- **U06-NFR-004**: The prototype must sustain 5 U06 API/worker operations per second and a 15-operation burst without violating correctness, privacy or retry bounds.
- **U06-NFR-005**: Capacity evidence must cover 10,000 pending notification jobs and indexed queries over 100,000 audit/incident records.
- **U06-NFR-006**: Every API list query must use bounded pagination; default 20 and maximum 100 records. Worker claims must be bounded at 500 jobs per transaction.
- **U06-NFR-007**: Queue depth, oldest-job age, database connections, worker utilization and storage growth must be observable.
- **U06-NFR-008**: Capacity and architecture must be reassessed when sustained CPU, memory, connection or worker utilization exceeds 70%, workload doubles, or an SLO is missed for two consecutive measurement windows.
- **U06-NFR-009**: Automatic horizontal scaling is excluded for the approved prototype; the exclusion expires before commercial production.

## API and Processing Performance

- **U06-NFR-010**: Normal admin list/detail and privacy-safe trace queries must complete within p95 2 seconds and p99 4 seconds.
- **U06-NFR-011**: A version-conditional admin command must be validated, durably accepted or rejected and return within p95 2 seconds; asynchronous cross-unit completion may be queried separately.
- **U06-NFR-012**: Shallow liveness must complete within p95 250 milliseconds without external calls.
- **U06-NFR-013**: Deep health must complete within p95 1 second using per-contributor timeouts and must not serialize unbounded dependency detail.
- **U06-NFR-014**: Approved event admission and deduplication must complete within p95 500 milliseconds excluding scheduled delivery delay.
- **U06-NFR-015**: In-app notification delivery or terminal classification must occur within p95 1 minute of an admitted event.
- **U06-NFR-016**: Email delivery or terminal classification must occur within p95 5 minutes of an admitted event.
- **U06-NFR-017**: Performance tests must report sample size, warm-up, data volume, percentile method, machine/runtime profile and PostgreSQL version.

## Timeout, Retry and Isolation

- **U06-NFR-018**: Each email adapter attempt has a 5-second total timeout and no unbounded connect/read/write/pool wait.
- **U06-NFR-019**: Email delivery permits at most three attempts with exponential backoff and injected jitter, ending at 30 minutes or event expiry, whichever occurs first.
- **U06-NFR-020**: Only transient network, timeout, throttling and designated server failures are retryable; schema, authorization, recipient and policy failures are terminal.
- **U06-NFR-021**: The same idempotency/deduplication key must protect enqueue, claim, retry and provider receipt reconciliation.
- **U06-NFR-022**: In-app and email delivery use separate attempt state and concurrency budgets; one channel cannot exhaust the other.
- **U06-NFR-023**: Notification failure cannot roll back or fail a U03 publication, U05 recommendation or synchronous user query.
- **U06-NFR-024**: U03/U04/U05/U07 port calls use explicit bounded deadlines and execute outside long U06 database write transactions.
- **U06-NFR-025**: A failed audit write blocks the associated privileged mutation or trace response rather than producing an unaudited success.

## Availability, Consistency and Recovery

- **U06-NFR-026**: U06 inherits the prototype monthly availability objective of 99.0%, excluding planned maintenance, with no contractual SLA.
- **U06-NFR-027**: Durable U06 state inherits RTO 4 hours, RPO 24 hours and the U07 Backup and Restore strategy.
- **U06-NFR-028**: Notification and admin commands must be idempotent under at-least-once worker execution, duplicate HTTP submission and process restart.
- **U06-NFR-029**: Admin override application uses optimistic version comparison; stale commands never silently overwrite newer catalog state.
- **U06-NFR-030**: Audit events, delivery attempts and incident transitions are append-only facts with monotonic sequence/order guarantees per aggregate.
- **U06-NFR-031**: Liveness remains available during dependency failure; readiness fails only for unavailable/stale required contributors, while optional failures report degraded state.
- **U06-NFR-032**: Alert storms are bounded through correlation, occurrence aggregation and update rate limits; they cannot create an unbounded number of incidents.
- **U06-NFR-033**: Restore verification must prove notification deduplication keys, active override versions, audit continuity, trace privacy, open incident state and U02~U05/U07 contract compatibility.
- **U06-NFR-034**: U06 must not mark backup, restore, deploy or rollback successful without a verified U07 source receipt.

## Authorization, Privacy and Audit Integrity

- **U06-NFR-035**: U02 server-side authorization is mandatory for every privileged operation; client-supplied role claims alone are invalid.
- **U06-NFR-036**: Content Operators may inspect content and submit allowlisted version-conditional content changes. System Administrators may investigate recommendation traces, incidents and audit records.
- **U06-NFR-037**: High-impact exposure changes require a recently validated session, explicit bounded reason, expected version, correlation ID and idempotency key.
- **U06-NFR-038**: Unauthorized, forbidden and non-existent privileged resources must use non-enumerating response behavior.
- **U06-NFR-039**: U06 persistence uses its own schema and runtime roles; no U06 runtime role may directly write U02~U05 or U07-owned business tables.
- **U06-NFR-040**: Audit records use an append-only application contract, ordered event identity and a digest over canonical allowed fields to detect accidental alteration.
- **U06-NFR-041**: Audit and incident data must be encrypted in transit and included in encrypted U07 backups.
- **U06-NFR-042**: Direct user identifiers, credentials, session tokens, notification body content, provider error bodies, raw prompts/responses and chain-of-thought are prohibited in audit, trace, metric labels and structured operational events.
- **U06-NFR-043**: Member and actor references are pseudonymous and purpose-limited; notification destination lookup occurs only at the channel adapter boundary.
- **U06-NFR-044**: Trace views expose only allowlisted U05 versions, counts, bounded scores, decision/validation codes and fallback status.
- **U06-NFR-045**: Secret values are file/secret-store injected and never committed, returned, logged, added to metrics or persisted in U06 tables.
- **U06-NFR-046**: Legal and privacy review remains a production-readiness gate; the disabled Security Baseline does not waive these core requirements.

## Retention and Data Lifecycle

- **U06-NFR-047**: Rendered notification body and provider delivery detail expire after 30 days unless an earlier event/privacy expiry applies.
- **U06-NFR-048**: Notification job state and bounded delivery outcome metadata expire after 90 days.
- **U06-NFR-049**: Audit events, incident records and COE/corrective-action records are retained for 365 days by default.
- **U06-NFR-050**: Legal hold suspends normal deletion for the scoped record while preserving access controls and auditability.
- **U06-NFR-051**: User deletion removes or irreversibly de-links user-related notification destinations/body content while retaining only legally required pseudonymous audit facts.
- **U06-NFR-052**: Retention commands claim at most 500 records, commit monotonic checkpoints and are safely repeatable.

## Observability, Health and Incident Response

- **U06-NFR-053**: Metrics must cover request latency/error/throughput, job queue depth/age, channel attempts/outcomes, retry/expiry, override conflicts, audit failures, trace outcomes, health state and incident transitions.
- **U06-NFR-054**: Metric labels are limited to fixed service, component, operation, channel, outcome, reason and severity vocabularies.
- **U06-NFR-055**: User/content/trace/incident IDs, message text and free-form reasons are prohibited metric labels.
- **U06-NFR-056**: Structured logs/events contain timestamp, service, operation, bounded outcome/reason, correlation ID and pseudonymous or digested references only when required for investigation.
- **U06-NFR-057**: Single-process prototype tracing uses correlation IDs and bounded stage events; distributed tracing is deferred until service separation.
- **U06-NFR-058**: Required readiness failure alerts immediately; audit failure alerts on one event; notification terminal failure rate above 10% for 10 minutes alerts; oldest pending job above 5 minutes alerts.
- **U06-NFR-059**: A correlated alert persisting five minutes or satisfying a critical immediate condition creates or updates an incident according to versioned policy.
- **U06-NFR-060**: Dashboards must display SLO percentiles, error/terminal rates, queue age/depth, retry saturation, override conflict/audit failures, contributor freshness and incident status.
- **U06-NFR-061**: The lightweight incident process includes detection, acknowledgement, mitigation, monitoring, resolution, owner, impact, evidence, COE and corrective-action tracking.

## Maintainability, Compatibility and Usability

- **U06-NFR-062**: Domain/application code remains framework-independent and cannot import FastAPI, SQLAlchemy or concrete channel/observability adapters.
- **U06-NFR-063**: Notification, override, audit, trace, health, alert and incident contracts are independently versioned and retain the previous supported consumer shape during migration.
- **U06-NFR-064**: Every externally visible state/reason has stable Korean and English presentation keys; internal provider details never become user-facing text.
- **U06-NFR-065**: U01 receives bounded pagination, processing/terminal state, retry-safe idempotency and non-enumerating error contracts.
- **U06-NFR-066**: No new broker, cache or external audit product is introduced without measured capacity need, license/security review, migration and rollback plan.
- **U06-NFR-067**: Ruff, strict MyPy, contract tests and PostgreSQL integration tests are required for implementation changes.

## Test and Release Gates

- **U06-NFR-068**: pytest/Hypothesis must execute P-U06-01~12 with reusable domain strategies, shrinking and a logged/replayable seed.
- **U06-NFR-069**: US-019, US-021, US-023 and US-025 retain explicit example tests; PBT cannot be the sole critical-path evidence.
- **U06-NFR-070**: Real PostgreSQL integration tests cover migration, deduplication/idempotency, optimistic conflict, append-only audit, worker claim concurrency, retention and restore constraints with selected skip count zero.
- **U06-NFR-071**: Failure injection covers email timeout/throttling/schema error, U02 preference/role outage, U03/U04 command failure, U05 trace outage, stale health and alert storm.
- **U06-NFR-072**: Privacy scans verify prohibited fields are absent from schemas, persistence, telemetry, metrics, fixtures and API responses.
- **U06-NFR-073**: Capacity tests exercise the approved RPS, 10,000 pending jobs and 100,000 audit/incident query profile.
- **U06-NFR-074**: Overall measured source coverage remains at least 80%; authorization, notification eligibility/deduplication, override scope/version, audit append/privacy, trace allowlist and health/incident transition safety branches require 100% targeted coverage.
- **U06-NFR-075**: Alembic clean install and upgrade from the current U05 head, Compose validation and U07 restore compatibility are blocking release gates.

## Requirement Traceability

| NFR range | Functional scope |
|---|---|
| 001~009 | criticality, capacity and prototype scale |
| 010~017 | API, health and notification performance |
| 018~025 | timeout, retry, idempotency and dependency isolation |
| 026~034 | availability, consistency and recovery |
| 035~046 | authorization, audit, trace privacy and secrets |
| 047~052 | retention and deletion lifecycle |
| 053~061 | observability, alerts and incident response |
| 062~067 | architecture, compatibility and usability |
| 068~075 | PBT, examples, PostgreSQL, privacy, capacity and release gates |

## Extension Compliance

- **Resiliency Baseline**: RESILIENCY-01~07, 10~15 are covered by criticality, availability, health, alerts, isolation, recovery evidence and incident requirements. RESILIENCY-08~09 retain the approved prototype exception with explicit reassessment triggers.
- **PBT-09**: Hypothesis 6.161.5 is selected with pytest 9.1.1 and is already present in `pyproject.toml` and `uv.lock`.
- **Security Baseline**: disabled and N/A as an extension. U06-NFR-035~052 preserve mandatory core authorization, privacy, audit, encryption and retention controls.

No blocking enabled-extension finding remains at U06 NFR Requirements.
