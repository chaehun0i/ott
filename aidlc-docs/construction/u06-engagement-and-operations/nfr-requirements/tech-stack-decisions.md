# U06 Engagement and Operations Tech Stack Decisions

## Actual Locked Baseline

These decisions use the current `backend/pyproject.toml` and `backend/uv.lock`. U06 adds no runtime or development dependency during NFR Requirements.

| Area | Decision | Locked version or status |
|---|---|---|
| Runtime | CPython | `>=3.12.13,<3.13` |
| API/schema | FastAPI and Pydantic | 0.140.0 and 2.13.4 |
| Domain/application | Typed Python dataclasses and protocols | Standard library; framework-independent |
| Persistence/outbox | PostgreSQL, SQLAlchemy, psycopg | PostgreSQL 17.x, 2.0.51 and 3.3.4 |
| Migrations | Alembic | 1.18.5 |
| Channel HTTP | HTTPX where an HTTP adapter is needed | 0.28.1 |
| Job processing | Existing PostgreSQL Transactional Outbox and worker | Selected; no broker |
| Observability | Existing U07 structured events, Health Registry, Prometheus/Grafana | Selected; no new vendor |
| Testing | pytest, Hypothesis and pytest-cov | 9.1.1, 6.161.5 and 7.1.0 |
| Quality | Ruff and strict MyPy | 0.16.0 and 2.3.0 |

## ADR-U06-001 - Modular-Monolith U06 Package

- **Decision**: Implement Notification, Admin/Audit and Operations as separate domain/application subpackages inside the existing Python modular monolith.
- **Rationale**: They share the approved low-volume runtime but need explicit ownership and adapter boundaries.
- **Constraints**: U06 domain/application code imports no FastAPI, SQLAlchemy or concrete adapter. Architecture tests enforce U02~U05/U07 access only through public contracts.
- **Rejected**: Immediate microservices add network consistency and operational cost without measured scale benefit.

## ADR-U06-002 - PostgreSQL Transactional Outbox and Worker

- **Decision**: Use the existing PostgreSQL outbox/job pattern for notification events, scheduled delivery and one-shot maintenance.
- **Rationale**: Current load is fewer than 10 users with 5 sustained/15 burst RPS. PostgreSQL provides atomic job admission, idempotency, bounded claims and recovery without a new broker.
- **Constraints**: Claim batches max 500, leases are expiring, jobs carry stable deduplication keys and channel failures are isolated.
- **Reassessment triggers**: Queue age SLO misses, sustained worker/database utilization above 70%, workload doubling, independent worker scaling or measured lock contention.
- **Rejected**: Kafka or a managed queue adds deployment, credentials and dual-write concerns before a need exists.

## ADR-U06-003 - U06-Owned PostgreSQL Schema

- **Decision**: Persist notification jobs/deliveries, overrides, audit events and incidents in a dedicated U06 schema with migration-owner, API-runtime and maintenance-runtime roles.
- **Rationale**: Relational constraints support idempotency, optimistic concurrency, append-only ordering, bounded investigation and restore closure.
- **Constraints**: U06 runtime roles cannot write other unit schemas. Cross-unit operations use application ports and immutable receipts.
- **Rejected**: Direct U03/U04 writes violate ownership. Process memory loses delivery and incident recovery.

## ADR-U06-004 - In-App Projection and Existing Email Adapter Boundary

- **Decision**: Store in-app notification state in U06 and deliver email through a purpose-limited channel port resolved at composition time.
- **Rationale**: Channel independence permits in-app delivery during email failure and prevents destination details from entering domain records.
- **Constraints**: Adapter timeout 5 seconds, maximum three attempts, bounded errors, destination lookup at adapter boundary and no provider body persistence.
- **Deferred**: Concrete production email provider remains deployment configuration subject to credential, legal, quota and cost verification.

## ADR-U06-005 - Append-Only Audit with Canonical Digest

- **Decision**: Record immutable audit events with canonical allowlisted fields, monotonic identity and a digest for alteration detection.
- **Rationale**: This provides accountable privileged-action evidence within the existing stack without claiming full cryptographic non-repudiation.
- **Constraints**: Application runtime has insert/read but no update/delete path for audit rows; database maintenance is separately authorized and audited. Direct identity, secrets and unrestricted payloads are prohibited.
- **Rejected**: Mutable generic logs cannot prove before/after/version closure. An external audit SaaS is unnecessary for the prototype.

## ADR-U06-006 - Bounded Recommendation Trace Consumer

- **Decision**: Consume the U05 `RecommendationTracePort` through a strict Pydantic boundary and expose only allowlisted investigation fields.
- **Rationale**: U05 remains trace source of truth; U06 adds role enforcement, pagination and audit without duplicating sensitive decision state.
- **Constraints**: Raw request/prompt/response, behavior history, direct identity and chain-of-thought are absent by schema. Not-found and forbidden are non-enumerating.
- **Rejected**: Reading U05 tables or logs directly bypasses privacy and version contracts.

## ADR-U06-007 - Shared Health Registry and Deterministic Aggregation

- **Decision**: Extend the existing U07 Health Registry with typed U06 contributions and a pure deterministic aggregation policy for liveness, readiness, deep and degraded views.
- **Rationale**: One registry preserves consistent health semantics while pure aggregation supports P-U06-11 and bounded output.
- **Constraints**: Per-contributor timeout/freshness, required/optional classification and fixed reason vocabularies are mandatory.
- **Rejected**: Ad hoc endpoint checks create inconsistent traffic decisions. Provider bodies in health output leak details.

## ADR-U06-008 - Prometheus/Grafana and Structured Event Reuse

- **Decision**: Extend existing Prometheus rules, Grafana provisioning and structured telemetry rather than adding an observability vendor.
- **Rationale**: Current stack already supports latency, rates, queue age, health and alerts with repository-owned configuration.
- **Constraints**: Fixed bounded labels only; IDs and bodies stay out of metrics. Correlation IDs may appear only in protected structured events.
- **Rejected**: High-cardinality ID labels and duplicate telemetry stacks increase cost and privacy risk.

## ADR-U06-009 - Versioned Incident State Machine

- **Decision**: Implement incident correlation and lifecycle as deterministic domain logic persisted in PostgreSQL.
- **Rationale**: The approved lightweight process has no external incident platform and needs reproducible alert grouping, transition validation and COE linkage.
- **Constraints**: detected, acknowledged, mitigating, monitoring and resolved are the only initial states; resolution requires owner and recovery evidence.
- **Reassessment trigger**: Adoption of an organizational PagerDuty/ServiceNow/on-call process requires an adapter and contract migration, not replacement of historical records.

## ADR-U06-010 - Existing pytest and Hypothesis Stack

- **Decision**: Use locked pytest and Hypothesis for primary-story examples, P-U06-01~12, reference oracles and notification/incident state machines.
- **PBT-09 fit**: Hypothesis supplies domain strategies, automatic shrinking, deterministic seed replay and stateful RuleBasedStateMachine support within pytest.
- **Generators**: Central strategies cover approved/invalid events, preference matrices, delivery results, override patches, audit records, bounded trace views, health contributions, alert permutations and incident commands.
- **Gates**: Overall branch coverage at least 80%; critical authorization/deduplication/override/audit/trace/health/incident branches targeted at 100%; real PostgreSQL integration selection has zero skips.

## Compatibility and Migration Policy

1. U06 migrations extend the Alembic chain after U05 and must pass clean install plus upgrade from the current head on PostgreSQL 17.
2. Preference, event, override, audit, trace, health, alert and incident contracts version independently from database revisions.
3. Expand-and-contract preserves the previous supported API/consumer shape during image rollback.
4. Historical policy versions remain readable for audit and incident investigation but cannot authorize a new command unless active.
5. A future broker, email provider SDK or incident platform requires official compatibility, license/security review, lockfile update, migration, rollback and failure evidence.

## Deferred Decision Register

| Decision | Target stage | Reason |
|---|---|---|
| Exact PostgreSQL indexes, partitions, leases and pool allocation | NFR Design | Must fit the shared single-server budget and query plans |
| Exact backoff intervals, concurrency and circuit thresholds | NFR Design | Must allocate notification delivery SLO and saturation limits |
| Concrete email provider and credential/quota configuration | Configuration/Code Generation | No production provider selected |
| Exact Prometheus recording/alert rules and dashboard panels | NFR Design/Infrastructure Design | Must map thresholds and runbooks |
| Legal-hold administration and production retention approval | Production readiness | Requires legal/privacy review |
| External incident platform integration | Scale/operations review | No organizational platform currently exists |

## Extension Compliance

- **PBT-09 - Compliant**: pytest 9.1.1 and Hypothesis 6.161.5 are declared and locked, with custom generators, shrinking, seed replay and state-machine support.
- **PBT-01 - Compliant handoff**: P-U06-01~12 map to examples, oracles, invariants and stateful gates.
- **Resiliency - Compliant**: bounded jobs/calls, channel isolation, health freshness, alert correlation, recovery closure and incident response are selected requirements.
- **Security Baseline - N/A**: disabled. Dedicated schema/roles, audit integrity, trace allowlist, secret isolation and privacy scans remain mandatory core controls.

No blocking extension finding remains at U06 NFR Requirements.
