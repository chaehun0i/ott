# U06 Engagement and Operations Logical Components

## Component Inventory

| Component | Responsibility | Must not do |
|---|---|---|
| `NotificationEventAdmission` | Validate U03 approved-event version/type and create stable event identity | Admit raw, quarantined or withdrawn content |
| `AudiencePreferenceReader` | Read U02 interest, channel preference and destination reference | Read direct identity tables or cache correctness state |
| `NotificationJobCoordinator` | Deduplicate, schedule, cancel and expose job state | Deliver channels inside admission transaction |
| `LaneScheduler` | Select bounded in-app, email and maintenance claims by priority | Share unbounded concurrency across lanes |
| `LeaseFencingCoordinator` | Claim, heartbeat, expire and fence worker completion | Accept stale-token completion |
| `InAppDeliveryAdapter` | Persist/display in-app notification projection | Call email provider |
| `EmailDeliveryAdapter` | Resolve destination and perform bounded provider call | Expose provider errors or credentials |
| `EmailCircuitBreaker` | Track bounded results and govern open/half-open/closed state | Affect in-app or core request availability |
| `AdminOperationFacade` | Enforce admission, recent auth, idempotency, U03/U04 command and audit closure | Write cross-unit tables or report unverified success |
| `OverridePolicyEngine` | Validate allowlisted field scope, expected version and active-time precedence | Change approval or validation rules |
| `AuditRecorder` | Canonicalize, HMAC-sign and append privileged outcomes | Update/delete historical audit events |
| `AuditIntegrityVerifier` | Verify canonical schema/key ID/HMAC and produce integrity signals | Repair mismatches silently |
| `TraceInvestigationFacade` | Authorize, fetch bounded U05 trace view and audit query outcome | Read U05 tables/logs or return prohibited content |
| `HealthContributionCollector` | Fan out bounded checks and create immutable contribution snapshot | Reuse stale success beyond freshness |
| `HealthTruthTable` | Derive liveness, readiness, deep and degraded states purely | Perform I/O or mutate contributor state |
| `AlertNormalizer` | Map U07/U06 signals to bounded severity/reason/correlation key | Include free-form or identity metric labels |
| `IncidentCoordinator` | Correlate signals, CAS transitions, recovery evidence and COE linkage | Override U07 recovery/deploy result |
| `RetentionCoordinator` | Execute class expiry, legal hold, de-link and checkpoints | Delete held records or run unbounded batch |
| `U06Telemetry` | Emit bounded metrics/events/dashboard/alert inputs | Emit IDs, bodies, reasons, secrets or provider payloads |
| `U06RecoveryVerifier` | Validate restore closure and ordered lane re-entry | Resume delivery before closure |

## Port Boundaries

| Port | Provider | Contract requirements |
|---|---|---|
| `AuthorizationDecisionPort` | U02 | Roles, permissions, recent-auth evidence and pseudonymous actor reference |
| `NotificationPreferencePort` | U02 | Versioned interests, type/channel switches and purpose-limited destination reference |
| `ApprovedNotificationEventPort` | U03 | Approved event/content version, locale/region and no raw/quarantine record |
| `AdminCatalogCommandPort` | U03/U04 | Expected version, allowlisted typed patch and immutable receipt |
| `RecommendationTracePort` | U05 | Bounded privacy-safe trace view only |
| `HealthContributionPort` | U02~U05/U07 | Typed state, required flag, reason, observation/freshness and bounded evidence |
| `AlertPort` | U07 and unit telemetry | Bounded signal/threshold/status contract |
| `ChannelDeliveryPort` | Email/in-app adapters | Idempotency key, typed result, timeout and receipt digest |
| `Clock`, `Random`, `IdGenerator` | U07 | Deterministic time/jitter/identity support |
| U06 repositories/unit of work | U06 persistence adapter | Jobs, delivery, overrides, audit, incidents and retention ownership |

Detached port values prevent U06 from importing another unit's ORM models. Domain/application packages import no FastAPI, SQLAlchemy, HTTPX or concrete observability/channel adapters.

## Notification Interaction

1. `NotificationEventAdmission` validates an approved U03 event and canonical event identity.
2. `AudiencePreferenceReader` streams bounded eligible member/channel projections from U02.
3. `NotificationJobCoordinator` inserts idempotent per-channel jobs and returns existing state on replay.
4. `LaneScheduler` claims ready jobs using `LeaseFencingCoordinator` and commits the lease.
5. The channel adapter runs outside the claim transaction under its deadline/circuit.
6. Completion compares fencing token and writes one attempt/result. A stale token is ignored and signaled.
7. Preference/interest/approval changes cancel pending jobs through the same idempotent coordinator.

## Privileged Operation Interaction

1. `AdminOperationFacade` resolves U02 permission and recent authentication, then applies actor/operation rate limit, CSRF/origin, schema, expected version and idempotency checks.
2. `OverridePolicyEngine` proves field scope and produces a versioned U03/U04 command.
3. U06 persists pending operation intent and commits.
4. The external command port returns an immutable applied/conflicted/rejected receipt.
5. `AuditRecorder` canonicalizes and HMAC-signs the outcome in the final U06 transaction.
6. Only a closed receipt plus audit event can produce a successful API response.

If cross-unit execution outcome is unknown, reconciliation queries the immutable operation key; it never replays a non-idempotent mutation blindly.

## Trace Investigation Interaction

1. `TraceInvestigationFacade` requires System Administrator permission and bounded trace ID/request shape.
2. `RecommendationTracePort` returns the allowlisted U05 view or a typed unavailable/not-found result.
3. U06 applies field/size/pagination limits and creates one audit outcome.
4. The API returns only after audit closure. Forbidden and missing use the same externally observable status where enumeration is possible.

## Health, Alert and Incident Interaction

1. `HealthContributionCollector` runs contributors in bounded parallel with independent timeouts.
2. `HealthTruthTable` computes the immutable snapshot independent of arrival order.
3. `U06Telemetry` emits bounded metrics/events; `AlertNormalizer` maps threshold or integrity signals to a correlation key.
4. `IncidentCoordinator` inserts or CAS-updates the one open incident for that key and appends transition evidence.
5. Recovery moves the incident to monitoring; recurrence returns it to mitigating; resolution requires owner/evidence and links COE actions.

## Persistence Components and Constraints

| Repository | Owned records | Key constraints |
|---|---|---|
| `NotificationJobRepository` | events, jobs and channel state | stable dedup unique key; terminal immutable state |
| `DeliveryAttemptRepository` | attempts and receipt digests | job/channel/attempt uniqueness; fencing-token completion |
| `OverrideRepository` | operation intent, override revisions and receipts | expected catalog version; allowlisted typed fields; one active revision rule |
| `AuditRepository` | canonical append-only events and key metadata | monotonic identity; no update/delete application API; HMAC required |
| `IncidentRepository` | alerts, occurrences, incidents, transitions and COE actions | one open correlation key; optimistic version; valid transition |
| `RetentionRepository` | class checkpoints, legal holds and de-link status | bounded claim; monotonic checkpoint; hold precedence |

Each repository resides in a U06-owned PostgreSQL schema. Migration owner manages DDL; API and worker roles have least-privilege table/function grants; maintenance has bounded retention/recovery grants. No U06 runtime role writes U02~U05/U07 business tables.

## Concurrency and Resource Budgets

| Resource | Initial budget | Failure/saturation outcome |
|---|---:|---|
| U06 API database connections | 4 | Bounded acquisition failure; no overflow |
| Notification worker connections | 2 | Claims wait/yield; queue age metric rises |
| Maintenance connections | 1 | Checkpoint/yield and retry later |
| In-app lane concurrency | 2 | Jobs remain pending within expiry |
| Email lane concurrency | 2 | Jobs remain pending or circuit-rescheduled |
| Maintenance concurrency | 1 | No delivery-lane slot consumption |
| API page size | default 20, max 100 | Reject/cap oversized request |
| Worker claim | in-app 100, email 50, maintenance 500 | Commit and yield after batch |
| Email attempt | 5 seconds, max 3 | Retry eligible error or terminal result |
| Health contributor | bounded per check within 1-second deep budget | typed timeout/unknown contribution |

## Observability and Alert Components

| Signal | Labels/evidence | Initial action |
|---|---|---|
| API/worker latency and outcome | operation, lane/channel, bounded outcome/reason | SLO dashboard and threshold alert |
| Queue depth and oldest age | lane and status | alert above 5-minute oldest age |
| Email circuit/retry/terminal rate | state, attempt, bounded reason | alert above 10% terminal/10 minutes |
| Override conflict/audit closure | operation/outcome | audit failure alerts immediately |
| HMAC verification | algorithm/schema/key ID and bounded result | mismatch creates critical integrity alert |
| Health contribution | component, required flag, state/reason | required readiness failure alerts immediately |
| Incident lifecycle | severity, state, outcome | dashboard, overdue acknowledgement/COE alert |
| Capacity | pool wait, lane utilization, storage/query evidence | 70%/growth scale review |

Direct user/content/trace/incident IDs, notification text, free-form reason and provider body are never metric labels. Protected structured events may contain a correlation ID and digested reference only when required.

## Retention and Recovery Ordering

1. Restore U06 schema, key metadata and immutable policy versions with U07.
2. Verify job dedup uniqueness, attempt ordering, lease expiry and fencing-token consistency.
3. Verify override expected/current version references and active/terminal closure.
4. Verify audit sequence, canonical schema, HMAC keys and prohibited-field absence.
5. Verify one-open-incident correlation and valid transition/COE linkage.
6. Verify U02 preference/role, U03/U04 command, U05 trace and U07 health/status contract compatibility.
7. Enable read-only operations and health.
8. Resume in-app lane, then email after channel health/circuit preflight.
9. Resume retention/maintenance and record recovery evidence in the incident.

## Verification Ownership

| Component group | Properties and gates |
|---|---|
| Preference/event/job | P-U06-01~05, primary-story examples and PostgreSQL dedup/claim/fencing tests |
| Override/audit | P-U06-06~10, concurrent CAS, HMAC rotation/integrity and prohibited-field tests |
| Health/alert/incident | P-U06-11~12, reference truth table, permutations, CAS race and state-machine tests |
| Channel resilience | fake adapter/clock/random timeout, retry, circuit and cross-lane failure injection |
| Persistence/recovery | migration, real PostgreSQL `skip=0`, retention/legal hold and isolated restore drill |
| Boundary/privacy | architecture, consumer/OpenAPI, role/non-enumeration, secret and telemetry scans |
| Capacity | 5 sustained/15 burst, 10,000 jobs, 100,000 audit/incident rows and query plans |

## NFR Traceability

| NFR group | Components and patterns |
|---|---|
| U06-NFR-001~009 | lane isolation, bounded budgets and evidence-driven scale evolution |
| U06-NFR-010~017 | API admission, health collector and scheduler SLO instrumentation |
| U06-NFR-018~025 | email deadline/retry/circuit, fencing, short transaction and audit fail-closed |
| U06-NFR-026~034 | idempotency, CAS, append-only facts, health truth table and recovery verifier |
| U06-NFR-035~046 | authorization facade, recent auth, HMAC audit, trace allowlist and secret boundary |
| U06-NFR-047~052 | retention coordinator, legal hold, de-link and checkpoints |
| U06-NFR-053~061 | telemetry, health, alert normalization, incident and COE components |
| U06-NFR-062~067 | framework-free boundaries, versioned ports, cache safety and maintainability |
| U06-NFR-068~075 | PBT/example/integration/failure/privacy/capacity/migration gates |

## Extension Compliance

| Rule group | Status | Design evidence |
|---|---|---|
| RESILIENCY-01~02 | Compliant | Criticality split, SLOs, 99.0%, RTO 4h and RPO 24h |
| RESILIENCY-03~04 | Compliant | Versioned policies/contracts, expand-and-contract and adapter evolution |
| RESILIENCY-05~07 | Compliant | Bounded telemetry, layered health, integrity/queue/capacity alerts |
| RESILIENCY-08~09 | N/A | Approved prototype exception with explicit worker/partition/broker/multi-zone gates |
| RESILIENCY-10 | Compliant | Lane bulkheads, timeout/retry/circuit, lease fencing and graceful isolation |
| RESILIENCY-11~13 | Compliant | Backup scope, integrity checks and staged restore re-entry |
| RESILIENCY-14~15 | Compliant | Monthly failure tests, quarterly drill, incident lifecycle and COE |
| PBT-01 | Compliant | P-U06-01~12 assigned to components and patterns |
| PBT-09 | Compliant | Existing locked Hypothesis/pytest stack retained |
| PBT-02~08, PBT-10 | Planned | Blocking Code Generation evidence with examples and reusable strategies |
| Security Baseline | N/A | Disabled; core authorization/audit/privacy controls remain blocking |

No blocking enabled-extension finding remains at U06 NFR Design.
