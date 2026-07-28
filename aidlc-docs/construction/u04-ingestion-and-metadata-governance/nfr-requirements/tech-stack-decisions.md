# U04 Ingestion and Metadata Governance Tech Stack Decisions

## Actual Locked Baseline

These decisions use the current `backend/pyproject.toml` and existing `uv.lock`; they do not claim or introduce an unverified dependency.

| Area | Decision | Locked version or status |
|---|---|---|
| Runtime | CPython | 3.12.13 range: `>=3.12.13,<3.13` |
| Contract validation | Pydantic | 2.13.4 |
| Persistence/transactions | PostgreSQL, SQLAlchemy, psycopg | PostgreSQL 17.x; SQLAlchemy 2.0.51; psycopg 3.3.4 |
| Migrations | Alembic | 1.18.5 |
| Provider HTTP | HTTPX async-capable adapter | 0.28.1 |
| Internal API/runtime | FastAPI and U07 platform boundary | FastAPI 0.140.0 |
| Job/outbox | Existing PostgreSQL-backed U07 worker | Selected; no new broker |
| Payload digest | Python standard-library SHA-256 | No new dependency |
| Testing | pytest, Hypothesis, pytest-cov | 9.1.1, 6.161.5, 7.1.0 |
| Quality | Ruff and mypy strict | 0.16.0 and 2.3.0 |
| Delivery | Docker Compose and GitHub Actions | Existing project baseline |

## ADR-U04-001 — PostgreSQL-Centered Durable Pipeline

- **Decision**: Store jobs, cursors, raw metadata references, normalized versions, merge evidence, validation results, quarantine and publication receipts in PostgreSQL.
- **Rationale**: U04 requires atomic page progress, immutable lineage, replay and idempotent U03 dispatch. The existing PostgreSQL worker avoids a second datastore at prototype scale.
- **Constraints**: External provider fetches and U03 calls never occur while holding a long database transaction. Claiming uses bounded rows and fencing/optimistic versions. U04 writes only U04 tables.
- **Rejected**: In-memory queues lose recovery state. A separate broker adds synchronization and operations without current throughput evidence.
- **Reassessment triggers**: Sustained demand above 10 records/second, bursts above 25, page processing over 4 hours, database queue contention or the need for independent worker scaling.

## ADR-U04-002 — Provider-Neutral HTTPX Adapter

- **Decision**: Implement ProviderPort adapters with HTTPX 0.28.1 behind provider-specific configuration and mapping.
- **Rationale**: HTTPX is already locked and supports explicit connection/response timeouts, pooling, async calls and test transports.
- **Constraints**: Endpoint allowlist, HTTPS, redirect policy, DNS/outbound restrictions, rate limits, byte/decompression limits and response redaction are mandatory. Provider DTOs cannot leak into domain rules.
- **Rejected**: Provider SDKs are not adopted until a selected provider requires one and its license/version is verified. Direct requests inside domain services violate the adapter boundary.

## ADR-U04-003 — Pydantic Boundary, Domain Dataclasses/Types

- **Decision**: Use Pydantic 2.13.4 for provider/configuration and U03/U05 boundary schemas while keeping domain entities framework-neutral.
- **Rationale**: This aligns with U07 contracts and provides bounded schema validation without coupling business rules to transport models.
- **Constraints**: Model limits must be applied before constructing unbounded nested payload structures. Mappers preserve source paths and stable reason codes.
- **Rejected**: Untyped dictionaries obscure provenance and validation compatibility. Pydantic models as persistence/domain aggregates create framework coupling.

## ADR-U04-004 — Immutable Versioned Policy Records

- **Decision**: Persist ProviderPolicy, NormalizationVersion, IdentityPolicyVersion, MergePolicyVersion and ValidationRuleVersion as immutable versioned records validated by typed schemas.
- **Rationale**: Reproducible validation and audit require historical logic/configuration references even after current policy changes.
- **Constraints**: Activation is an authorized state change; historical rows are not edited. Breaking U03/U05 predicate changes create a new contract version.
- **Rejected**: Mutable environment-only rules cannot reproduce prior decisions. Duplicated U05 validation logic would drift.

## ADR-U04-005 — PostgreSQL Outbox-Style Publication Dispatch

- **Decision**: Reuse the durable U07 job/outbox mechanism to dispatch `passed_pending_publication` and withdrawal commands to U03.
- **Rationale**: It supports at-least-once delivery with a stable U04 decision key and U03 idempotency without distributed transactions.
- **Constraints**: A timeout is an unknown result; reuse the same key. Receipt uniqueness and CatalogVersion reconciliation are mandatory. Technical delivery failure is not validation quarantine.
- **Rejected**: Best-effort in-process callbacks lose decisions. Two-phase commit across unit boundaries is unnecessary and brittle.

## ADR-U04-006 — No New Cache or Message Broker

- **Decision**: Do not add Redis, Kafka, RabbitMQ or a process-local correctness cache for U04 initially.
- **Rationale**: The selected capacity fits the existing PostgreSQL job model, and correctness depends on durable versioned state rather than cached decisions.
- **Consequences**: Query/index and claim design must meet throughput targets. Process-local memoization may be used only for immutable non-authoritative parsing data and cannot affect decisions.
- **Reassessment triggers**: Proven database contention, need for independent provider partitions, sustained throughput above the defined triggers or operational isolation requirements.

## ADR-U04-007 — Standard Digest and Licensed Raw Retention

- **Decision**: Use Python's standard SHA-256 implementation for payload equality/integrity fingerprints and enforce provider-specific raw-body retention.
- **Rationale**: No new package is needed, and a digest preserves reproducibility evidence after licensed payload expiry without retaining the payload itself.
- **Constraints**: A digest is not an authentication signature and cannot prove provider authenticity. If signed webhooks are added, use the provider's verified signature scheme separately.
- **Rejected**: Indefinite raw storage conflicts with provider-specific licensing. An unversioned cleanup policy cannot explain historical deletions.

## ADR-U04-008 — pytest and Hypothesis Quality Gate

- **Decision**: Use locked pytest 9.1.1 and Hypothesis 6.161.5 for U04 example, property and state-machine tests.
- **PBT-09 fit**: Hypothesis supports domain strategies, automatic shrinking, stateful models, explicit seeds and pytest integration.
- **Property inventory**: PBT-U04-01~12 covers raw round-trip, normalization idempotence, provenance preservation, identity oracle, merge commutativity, merge closure, validation closure, quarantine non-leakage, publication idempotence, stateful jobs, tombstone safety and cursor replay.
- **Generators**: Reusable strategies belong in `backend/tests/strategies/ingestion.py` and generate constrained policies, Unicode records, identifiers, field candidates, license/freshness boundaries, availability, tombstones and command sequences.
- **Gates**: Overall line coverage at least 80%; validation/quarantine/publication safety branches 100%; real PostgreSQL integration selection reports zero skips.

## ADR-U04-009 — Observability on Existing U07 Contracts

- **Decision**: Extend the existing structured telemetry, Prometheus-compatible metrics, health and dashboard conventions rather than adding a unit-specific observability stack.
- **Rationale**: Shared correlation/job IDs and metric naming allow U03 publication lag and U04 ingestion lag to be viewed together.
- **Constraints**: Labels are bounded; provider record IDs, URLs and reason text are not metric labels. Raw payloads and credentials are never telemetry.
- **Deferred**: Exact alert routing and dashboard panels are finalized in NFR Design/Infrastructure Design.

## Compatibility and Migration Policy

1. U04 migrations extend the current U07/U02/U03 Alembic chain and must pass clean installation and upgrade tests on PostgreSQL 17.
2. Expand-and-contract preserves compatibility with the previous application version during version-pinned rollback.
3. Policy/rule and U03/U05 contract versions are independent of database migration revision and remain explicitly linked.
4. Indexes for job claims, cursors, payload digests, decision states, quarantine reasons and publication keys are verified at 1,000,000-row scale.
5. No dependency is added during NFR Requirements. Any future provider SDK or retry/circuit package requires official compatibility, license, lockfile and vulnerability verification before use.

## Deferred Decision Register

| Decision | Target stage | Reason |
|---|---|---|
| Provider-specific connect/read/total timeout and retry budgets | NFR Design | Must allocate per-provider failure budgets |
| Worker concurrency, database pool and claim size tuning | NFR Design | Must align load targets with single-server resources |
| Circuit state thresholds and half-open probes | NFR Design | Dependency-specific failure behavior |
| Exact table/index partitioning or retention purge batches | NFR Design/Code Generation | Requires measured 1,000,000-row plans |
| Concrete providers and credentials | Code Generation/configuration | Requires legal/provider availability confirmation |
| Separate broker or cache | Scale review | Not justified by current capacity |

## Extension Compliance

- **PBT-09 — Compliant**: pytest 9.1.1 and Hypothesis 6.161.5 are present in `pyproject.toml` and locked; they support generators, shrinking, state machines and seed replay.
- **PBT-01 — Compliant handoff**: PBT-U04-01~12 are mapped to components, generator location and implementation gates.
- **Resiliency — Compliant**: durable PostgreSQL state, provider isolation, bounded dependency handoff, idempotent publication, replay and recovery evidence align with the enabled baseline.
- **Security Baseline — N/A**: disabled. Allowlisted outbound HTTP, secret separation, licensed retention and telemetry redaction remain core mandatory controls.

No blocking extension finding remains at U04 NFR Requirements.
