# U04 Ingestion and Metadata Governance Code Generation Plan

> **Single Source of Truth**: This plan controls U04 Code Generation Part 1 and Part 2. Application code must not be changed before explicit approval. After approval, Steps 1 through 20 execute in order and every completed step is marked `[x]` immediately.

## Part 1 - Planning Status

- [x] Read the approved U04 Functional Design, NFR Requirements, NFR Design and Infrastructure Design artifacts.
- [x] Read the final Unit/Story map and identify US-020 as the primary story.
- [x] Map the supporting contracts for US-003, US-010, US-011, US-021, US-022 and US-024.
- [x] Verify U07 runtime and U03 `ApprovedCatalogWritePort` dependencies are already available.
- [x] Inspect the existing modular-monolith packages, tests, migrations, Compose and infrastructure artifacts.
- [x] Confirm no new runtime dependency is required; use the locked SQLAlchemy, HTTPX, PostgreSQL and Hypothesis stack.
- [x] Set application paths under `backend/src/ott_feed/ingestion/` and tests under `backend/tests/ingestion/`.
- [x] Exclude frontend generation because U01 owns user-facing presentation.
- [x] Define 20 sequential generation steps with paths, test gates and traceability.
- [x] Resolve all planning categories from approved artifacts; no blocking question remains.
- [x] Obtain explicit approval for the complete plan and generation sequence.

## Unit Context

### Story and Requirement Coverage

| Scope | U04 responsibility | Planned steps |
|---|---|---|
| US-020 (primary) | Collect, normalize, validate, quarantine and safely reprocess provider metadata | 3~20 |
| US-003 (supporting) | Supply collection time, freshness and source-status facts to U03 | 10, 15~17, 19~20 |
| US-010, US-011, US-022 (supporting) | Publish versioned metadata-validation predicates without taking ownership of recommendation claim validation | 13, 16~19 |
| US-021 (supporting) | Provide authorized status and retry commands while U06 retains override/audit ownership | 14, 17~20 |
| US-024 (supporting) | Isolate provider/U03 failures and preserve the last approved catalog | 6, 9, 15~20 |
| FR-006, FR-030~032, FR-039~041 | Freshness, provenance and versioned validation-rule support | 10~17 |
| DR-001~006, DR-009~012, AC-014 | Lawful collection, canonical transformation, state closure, quarantine and approved publication | 4~20 |

### Dependencies and Contracts

- **U07**: PostgreSQL/SQLAlchemy/Alembic, durable jobs, health, telemetry, request context, configuration and recovery runtime.
- **U03**: U04 calls only `ApprovedCatalogWritePort` with an immutable passed or withdrawal decision and stable idempotency key. U04 never writes U03 tables directly.
- **U05**: Receives only a versioned, read-only `ValidationRuleContract`; raw payloads, quarantine details and provider credentials are excluded.
- **U06**: Uses authorized status/retry operations and bounded reason/status facts; operator override and audit remain U06-owned.
- **Providers**: Accessed through allowlisted HTTPX adapters with provider-specific policy, credential, rate, timeout and circuit boundaries.

### Owned Persistence

U04 owns the `u04_ingestion` schema: provider policies, ingestion jobs/attempts/cursors, raw observations and page membership, normalized versions, identity resolutions, source-field candidates, merged versions, validation rule versions/runs/results/decisions, quarantine cases, tombstones, publication jobs/receipts and retention/recovery progress.

### Code Boundaries

- Application: `backend/src/ott_feed/ingestion/`
- Unit tests: `backend/tests/ingestion/`
- Migration: `backend/migrations/versions/0004_u04_ingestion_expand.py`
- Shared composition: existing `backend/src/ott_feed/main.py`, `backend/src/ott_feed/worker.py`, migration grants, Compose and `infra/`
- AI-DLC summaries only: `aidlc-docs/construction/u04-ingestion-and-metadata-governance/code/`
- No application source is written under `aidlc-docs/`.

## Part 2 - Generation Steps

## Step 1 - Baseline and Boundary Guard

- [x] Run Ruff, strict MyPy, full pytest/coverage and deterministic PBT against the current U07/U02/U03 baseline.
- [x] Run the selected real-PostgreSQL integration suite and record skip count, server version and migration head.
- [x] Extend architecture tests so U04 domain/application code cannot import FastAPI, SQLAlchemy or concrete HTTPX/persistence adapters.
- [x] Record baseline evidence before U04 changes.

**Paths**: `backend/tests/platform/contract/test_boundaries.py`, `aidlc-docs/construction/u04-ingestion-and-metadata-governance/code/baseline.md`.

## Step 2 - Dependency, Lock and Contract Verification

- [x] Verify the existing Python 3.12.13, HTTPX, SQLAlchemy, psycopg, Alembic, PostgreSQL 17 and Hypothesis pins against `pyproject.toml` and `uv.lock`.
- [x] Confirm U04 requires no provider SDK, retry library, broker or cache dependency.
- [x] Verify the U03 write-port and U07 job/runtime contracts before implementation.
- [x] Record dependency and consumer-contract evidence without manually editing the lockfile.

**Paths**: `backend/pyproject.toml`, `backend/uv.lock`, `backend/src/ott_feed/catalog/ports.py`, `backend/src/ott_feed/platform/ports.py`, `aidlc-docs/construction/u04-ingestion-and-metadata-governance/code/dependency-validation.md`.

## Step 3 - Package Skeleton, Configuration and Ports

- [x] Create domain, application, adapter, persistence and API package boundaries.
- [x] Define provider, clock, ID, transaction, repository, U03 publication, telemetry and validation-contract protocols.
- [x] Add fail-fast typed settings for provider concurrency, claims, pools, timeouts, retry/circuit, retention, payload limits and backpressure.
- [x] Add package/configuration unit tests without network or database dependencies.

**Paths**: `backend/src/ott_feed/ingestion/`, `backend/src/ott_feed/ingestion/ports.py`, `backend/src/ott_feed/ingestion/config.py`, `backend/tests/ingestion/unit/`.

## Step 4 - Domain Values, Errors and Aggregate State Machines

- [x] Implement typed IDs, provider/legal policies, jobs, attempts, raw envelopes, normalized values, identity candidates, merge values, validation decisions, quarantine, tombstones and publication receipts.
- [x] Implement legal job/decision/quarantine/publication transitions and stable error/reason families.
- [x] Keep domain values immutable and free from framework, persistence and provider SDK imports.
- [x] Add example tests for invalid transitions, version references and decision closure.

**Paths**: `backend/src/ott_feed/ingestion/domain/`, `backend/tests/ingestion/unit/test_domain.py`.

## Step 5 - Provider Policy, Scheduling and Fairness

- [x] Implement immutable policy activation, effective windows, regions, allowed use, attribution, refresh and retention checks.
- [x] Implement incremental/full/revalidation scheduling with withdrawal and publication priority reservations.
- [x] Implement provider-fair selection, per-provider concurrency and backpressure decisions using explicit time.
- [x] Add deterministic scheduling and policy boundary tests.

**Paths**: `backend/src/ott_feed/ingestion/domain/policies.py`, `backend/src/ott_feed/ingestion/application/scheduling.py`, `backend/tests/ingestion/unit/test_scheduling.py`.

## Step 6 - Provider Registry and Safe HTTP Adapter

- [x] Implement provider adapter registration and provider-specific credential resolution.
- [x] Implement allowlisted HTTPS origins, redirect rejection, bounded response/record size and privacy-safe error translation.
- [x] Implement explicit connect/read/total deadlines, retry-after, bounded jittered retries, bulkhead and circuit behavior.
- [x] Add deterministic HTTPX fake-transport tests for timeout, rate limit, malformed data, redirect, size and provider isolation.

**Paths**: `backend/src/ott_feed/ingestion/adapters/providers/`, `backend/src/ott_feed/ingestion/application/resilience.py`, `backend/tests/ingestion/unit/test_provider_adapter.py`.

## Step 7 - SQLAlchemy Models and Alembic Expand Migration

- [x] Implement U04 SQLAlchemy rows, constraints and indexes in `u04_ingestion`.
- [x] Add expand-only migration `0004_u04_ingestion_expand.py` after U03 head.
- [x] Add migration-owner, worker-runtime and API-runtime grants while prohibiting direct U03 table writes.
- [x] Verify clean installation and U07→U02→U03→U04 upgrade paths; prohibit destructive automatic downgrade.

**Paths**: `backend/src/ott_feed/ingestion/adapters/persistence/models.py`, `backend/migrations/versions/0004_u04_ingestion_expand.py`, `backend/migrations/role-grants.sql`.

## Step 8 - Repositories, Unit of Work, Claims and Fencing

- [x] Implement policy, job/attempt/cursor, raw, normalized, merge, validation, quarantine and publication repositories.
- [x] Implement bounded `FOR UPDATE SKIP LOCKED` claims, leases, fencing versions and compare-and-set transitions.
- [x] Implement API/worker transaction profiles and translate database errors into typed U04 failures.
- [x] Add repository unit tests plus concurrent real-PostgreSQL claim tests.

**Paths**: `backend/src/ott_feed/ingestion/adapters/persistence/repositories.py`, `backend/src/ott_feed/ingestion/adapters/persistence/unit_of_work.py`, `backend/tests/ingestion/integration/test_postgresql_ingestion.py`.

## Step 9 - Durable Job Lifecycle and Cursor Reconciliation

- [x] Implement create/claim/heartbeat/retry/partial-success/fail/cancel/finish transitions with append-only attempts.
- [x] Advance a cursor only after every page record has a durable outcome and reconciled counts.
- [x] Recover expired leases and replay from the last durable cursor without skipping or duplicating terminal outcomes.
- [x] Add crash, duplicate page and count-mismatch tests.

**Paths**: `backend/src/ott_feed/ingestion/application/jobs.py`, `backend/src/ott_feed/ingestion/application/cursors.py`, `backend/tests/ingestion/unit/test_jobs.py`.

## Step 10 - Raw Observation, Codec and Governed Retention

- [x] Persist each bounded provider observation and page membership before transformation.
- [x] Implement stable digest/idempotency, tombstone parsing, attribution and policy-version lineage.
- [x] Implement raw-envelope codec and bounded restartable body expiry that preserves permitted digest/provenance/decision facts.
- [x] Add PBT-U04-01 and retention/replay examples.

**Paths**: `backend/src/ott_feed/ingestion/application/raw.py`, `backend/src/ott_feed/ingestion/application/retention.py`, `backend/tests/ingestion/pbt/test_ingestion_properties.py`.

## Step 11 - Pure Versioned Normalization

- [x] Implement provider-to-canonical transformation for identifiers, locales, runtime, dates, genres, people and availability candidates.
- [x] Preserve source paths and prevent invented authoritative identifiers.
- [x] Make normalization deterministic and idempotent for explicit version/time inputs.
- [x] Add bilingual, Unicode, boundary-date and PBT-U04-02/03 tests.

**Paths**: `backend/src/ott_feed/ingestion/application/normalization.py`, `backend/tests/ingestion/unit/test_normalization.py`, `backend/tests/ingestion/pbt/test_ingestion_properties.py`.

## Step 12 - Canonical Identity, Merge, Provenance and Tombstones

- [x] Implement ordered identifier/crosswalk/title identity tiers with new, matched and ambiguous outcomes.
- [x] Implement deterministic field-level authority/freshness merge retaining selected and alternative provenance.
- [x] Implement source-aware tombstones that cannot withdraw content while another valid authoritative source remains.
- [x] Add reference-oracle and PBT-U04-04/05/06/11 tests.

**Paths**: `backend/src/ott_feed/ingestion/application/identity.py`, `backend/src/ott_feed/ingestion/application/merge.py`, `backend/tests/ingestion/pbt/test_ingestion_properties.py`.

## Step 13 - Versioned Validation Engine and U05 Rule Contract

- [x] Implement immutable rules for schema, provenance, license, freshness, identity and availability.
- [x] Produce a complete rule-result matrix and fail closed for failed, missing, error or unknown mandatory results.
- [x] Publish a minimal versioned pure `ValidationRuleContract` for U05 without raw/provider/quarantine internals.
- [x] Add every failure-family example, consumer contract tests and PBT-U04-07/08 with 100% safety-branch coverage.

**Paths**: `backend/src/ott_feed/ingestion/application/validation.py`, `backend/src/ott_feed/ingestion/contracts.py`, `backend/tests/ingestion/contract/`, `backend/tests/ingestion/pbt/test_ingestion_properties.py`.

## Step 14 - Quarantine and Revalidation

- [x] Open quarantine cases for validation or ambiguity failures without conflating technical delivery failures.
- [x] Implement source-change, rule-change and authorized manual retry with stable attempt keys.
- [x] Resolve cases only through superseding immutable decisions and retain bounded reason/status facts for U06.
- [x] Add duplicate/manual-authorization/rule-change and non-leakage tests.

**Paths**: `backend/src/ott_feed/ingestion/application/quarantine.py`, `backend/src/ott_feed/ingestion/application/revalidation.py`, `backend/tests/ingestion/unit/test_quarantine.py`.

## Step 15 - Pipeline Orchestration and Transactional Decision Closure

- [x] Orchestrate persist-raw→normalize→identify→merge→validate with record-level isolation.
- [x] Commit passed decisions and publication work atomically; commit failed decisions and quarantine atomically.
- [x] Keep provider and U03 network calls outside U04 database transactions.
- [x] Add malformed sibling, partial-success, restart and PBT-U04-10/12 state-machine tests.

**Paths**: `backend/src/ott_feed/ingestion/application/pipeline.py`, `backend/tests/ingestion/unit/test_pipeline.py`, `backend/tests/ingestion/pbt/test_ingestion_state_machine.py`.

## Step 16 - Idempotent U03 Publication and Reconciliation

- [x] Map only immutable passed/withdrawal decisions to U03 commands with a stable publication key.
- [x] Store the returned CatalogVersion/receipt uniquely and treat timeout as an unknown outcome.
- [x] Reconcile or retry the same command without creating replacement decisions or direct U03 writes.
- [x] Add U03 contract tests, timeout-before/after-commit examples and PBT-U04-09.

**Paths**: `backend/src/ott_feed/ingestion/application/publication.py`, `backend/tests/ingestion/contract/test_u03_publication.py`, `backend/tests/ingestion/pbt/test_ingestion_properties.py`.

## Step 17 - Operator API, Worker, Health, Telemetry and Composition

- [x] Add authorized bounded status/retry endpoints and versioned validation-contract responses.
- [x] Register six U04 worker lanes with reserved withdrawal/publication capacity and configured budgets.
- [x] Add liveness/readiness/deep-health contributions and payload-free metrics/log attributes/alerts.
- [x] Wire U04 into existing application and worker factories without exposing provider secrets or raw payloads.

**Paths**: `backend/src/ott_feed/ingestion/api/`, `backend/src/ott_feed/ingestion/worker.py`, `backend/src/ott_feed/ingestion/health.py`, `backend/src/ott_feed/ingestion/telemetry.py`, `backend/src/ott_feed/main.py`, `backend/src/ott_feed/worker.py`.

## Step 18 - Example, Contract, Architecture and Property Tests

- [x] Complete US-020 examples and every critical provider/validation/quarantine/publication/retention failure family.
- [x] Complete API/OpenAPI, U03/U05 consumer, authorization, architecture, egress and telemetry privacy contracts.
- [x] Implement PBT-U04-01~12 with reusable strategies, shrinking, seed reporting and regression promotion.
- [x] Verify no failed/ambiguous/quarantined value can reach the U03 publication mapper.

**Paths**: `backend/tests/ingestion/unit/`, `backend/tests/ingestion/contract/`, `backend/tests/ingestion/pbt/`, `backend/tests/strategies/ingestion.py`, `docs/api-contract.md`.

## Step 19 - Real PostgreSQL, Failure, Capacity and Recovery Gates

- [x] Run clean/upgrade migrations, constraints, concurrent claims, cursor replay, retention and publication receipts on real PostgreSQL 17.
- [x] Inject worker crash, provider timeout/rate limit, U03 unknown outcome, rule change during backlog, payload expiry and restore inconsistency.
- [x] Verify 20 providers, 100,000 content records and 1,000,000 lineage/decision-row plans plus the four-hour full-sync budget.
- [x] Run selected `pytest -m integration` with zero skips and retain server/migration/query-plan/recovery evidence.

**Paths**: `backend/tests/ingestion/integration/`, `backend/tests/ingestion/quality/`, `scripts/restore.sh`, U04 test artifacts under `backend/`.

## Step 20 - Deployment Artifacts, Final Quality Gate and Handoff

- [x] Add dedicated `worker-ingestion`, provider egress, purpose-separated secret references, U04 database roles, monitoring dashboard/alerts and recovery procedures.
- [x] Run Ruff format/check, strict MyPy, full pytest/branch coverage, deterministic Hypothesis, OpenAPI, migration, lock and secret/telemetry scans.
- [x] Require overall coverage at least 80%, validation/quarantine/publication safety branches 100%, PBT-U04-01~12 and PostgreSQL integration skip=0.
- [x] Verify no direct U03 writes, no raw/provider-secret telemetry, no application code under `aidlc-docs/` and Docker/native PostgreSQL parity.
- [x] Create implementation, test, PBT, dependency and traceability summaries; update every plan/story/state checkbox and request standardized Code Generation approval.

**Paths**: `compose.yaml`, `backend/migrations/role-grants.sql`, `infra/`, `scripts/`, `docs/`, `aidlc-docs/construction/u04-ingestion-and-metadata-governance/code/`.

## Expected Scope

- **20 ordered generation steps** after explicit approval.
- **New application package**: `backend/src/ott_feed/ingestion/`.
- **New tests and strategies**: `backend/tests/ingestion/` and `backend/tests/strategies/ingestion.py`.
- **Migration chain**: new `0004` expand migration after the existing U03 head.
- **Shared modifications**: application/worker composition, role grants, Compose, observability, runbooks and API documentation.
- **No new package dependency and no frontend implementation**.

## Extension Execution Commitments

- **Resiliency Baseline**: provider bulkheads, timeout/retry/circuit, durable claims/cursors, idempotent U03 reconciliation, last-approved-catalog degradation, retention recovery and restore re-entry are blocking implementation gates.
- **Property-Based Testing**: PBT-U04-01~12 are mandatory with domain generators, shrinking, deterministic seed evidence and regression promotion.
- **Security Baseline**: disabled and N/A as an extension; core provider legality, least privilege, egress allowlist, payload limits, secret isolation and telemetry privacy remain blocking requirements.
