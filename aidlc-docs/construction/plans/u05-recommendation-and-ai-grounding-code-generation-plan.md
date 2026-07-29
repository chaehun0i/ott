# U05 Recommendation and AI Grounding Code Generation Plan

> **Single Source of Truth**: This plan controls U05 Code Generation Part 1 and Part 2. Application code must not be changed before explicit approval. After approval, Steps 1 through 20 execute in order and every completed checkbox is marked `[x]` immediately.

## Part 1 - Planning Status

- [x] Read the approved U05 Functional Design, NFR Requirements, NFR Design and Infrastructure Design artifacts.
- [x] Read the final Unit/Story map and identify eight U05 primary stories.
- [x] Verify U02 Feature Snapshot, U03 Approved Catalog Read Port, U04 Validation Predicate Contract and U07 runtime dependencies.
- [x] Inspect the existing modular-monolith packages, tests, migrations, Compose and observability artifacts.
- [x] Confirm the locked Python, FastAPI, Pydantic, HTTPX, SQLAlchemy, PostgreSQL and Hypothesis stack is sufficient.
- [x] Set application paths under `backend/src/ott_feed/recommendation/` and tests under `backend/tests/recommendation/`.
- [x] Exclude frontend generation because U01 owns user-facing presentation.
- [x] Define 20 sequential generation steps with exact paths, story mapping and blocking gates.
- [x] Resolve all planning categories from approved artifacts; no blocking question remains.
- [ ] Obtain explicit approval for the complete plan and generation sequence.

## Unit Context

### Story and Requirement Coverage

| Scope | U05 responsibility | Planned steps |
|---|---|---|
| US-008, US-009 | Korean/English natural-language recommendation intent | 4, 5, 10, 14~20 |
| US-010 | Hard-condition-first personalized ranking and diversity | 6~8, 14, 18~20 |
| US-011 | Metadata-grounded reason and summary | 9~11, 14, 18~20 |
| US-012 | Conversational refinement and reset | 5, 12~15, 18~20 |
| US-013 | Ambiguity/conflict explanation and confirmation | 4~5, 14~15, 18~20 |
| US-022 | Metadata-based candidate/claim validation and safe replacement | 9, 11, 14, 18~20 |
| US-024 | Timeout, isolation and deterministic degraded operation | 3, 10~11, 14, 16~20 |
| FR-009~022, FR-036~042 | Recommendation, conversation, AI boundary and output validation | 3~20 |
| DR-008, DR-012~014 | Consent minimization, approved metadata closure and traceability | 3, 6, 9, 11~20 |

### Dependencies and Contracts

- **U02**: Consume only `FeatureService.snapshot`/purpose-limited Feature Snapshot and consent state. No direct identity or raw behavior access.
- **U03**: Consume only `ApprovedCatalogReadPort` values with approved state, region/OTT availability, metadata version and evidence references.
- **U04**: Consume the versioned `ValidationPredicateContract`; unknown or incomplete predicate results fail closed.
- **U06**: Publish a bounded `RecommendationTracePort` read contract without prompt text, direct identity or chain-of-thought.
- **U07**: Reuse request context, timeout, rate limit, health, telemetry, SQLAlchemy/Alembic and PostgreSQL runtime.
- **AI provider**: Use a provider-neutral HTTPX adapter with explicit schema, deadline, allowlist, response-size, retry, circuit, bulkhead and usage boundaries.

### Owned Persistence

U05 owns the `u05_recommendation` schema: sessions, session patches, request attempts, immutable intent/scoring/diversity/fallback/AI policy versions, activation pointers, candidate ranking proofs, candidate and claim validation outcomes, minimized recommendation traces, usage records and retention/recovery checkpoints.

Raw prompts, provider response bodies, failed drafts, direct user identity and chain-of-thought are prohibited persistent fields.

### Code Boundaries

- Application: `backend/src/ott_feed/recommendation/`
- Tests: `backend/tests/recommendation/`
- Shared strategies: `backend/tests/strategies/recommendation.py`
- Migration: `backend/migrations/versions/0005_u05_recommendation_expand.py`
- Shared composition: `backend/src/ott_feed/main.py`, `backend/src/ott_feed/worker.py`, `backend/migrations/role-grants.sql`, `compose.yaml`, `.env.example`, `infra/`
- AI-DLC summaries only: `aidlc-docs/construction/u05-recommendation-and-ai-grounding/code/`
- No application source is written under `aidlc-docs/`.

## Part 2 - Generation Steps

## Step 1 - Baseline and Boundary Guard

- [ ] Run Ruff, strict MyPy, full pytest/coverage and deterministic PBT against the current U07/U02/U03/U04 baseline.
- [ ] Run the selected real-PostgreSQL integration suite and record skip count, server version and migration head.
- [ ] Extend architecture tests so U05 domain/application code cannot import FastAPI, SQLAlchemy or concrete HTTPX/persistence adapters.
- [ ] Record baseline evidence before U05 changes.

**Paths**: `backend/tests/platform/contract/test_boundaries.py`, `aidlc-docs/construction/u05-recommendation-and-ai-grounding/code/baseline.md`.

## Step 2 - Dependency, Lock and Consumer Contract Verification

- [ ] Reverify actual `pyproject.toml` and `uv.lock` pins for Python 3.12, FastAPI, Pydantic, HTTPX, SQLAlchemy, psycopg, Alembic, pytest and Hypothesis.
- [ ] Confirm U05 adds no provider SDK, ML framework, Redis, broker, retry library or duplicate vector-store dependency.
- [ ] Add contract tests for the existing U02 Feature Snapshot, U03 Approved Catalog and U04 Validation Predicate boundaries before implementing U05.
- [ ] Record version and consumer-contract evidence without manually editing the lockfile.

**Paths**: `backend/pyproject.toml`, `backend/uv.lock`, `backend/tests/recommendation/contract/test_dependency_contracts.py`, `aidlc-docs/construction/u05-recommendation-and-ai-grounding/code/dependency-validation.md`.

## Step 3 - Package Skeleton, Configuration and Ports

- [ ] Create domain, application, adapter, persistence and API package boundaries.
- [ ] Define clock, ID, consent feature, approved catalog, validation predicate, AI provider, repository, telemetry and trace protocols.
- [ ] Add fail-fast typed settings for deadline allocation, candidates, claims, pool, response size, AI concurrency, retry, circuit and usage caps.
- [ ] Add configuration and protocol unit tests without network or database dependencies.

**Paths**: `backend/src/ott_feed/recommendation/`, `backend/src/ott_feed/recommendation/ports.py`, `backend/src/ott_feed/recommendation/config.py`, `backend/tests/recommendation/unit/test_config_and_ports.py`.

## Step 4 - Domain Values, Intent and Error Families

- [ ] Implement typed IDs, locale, conditions, conflicts, intent versions, degradation reasons, evidence references, atomic claims and stable error codes.
- [ ] Enforce 4 KiB request text, 32 conditions and canonical Korean/English values at construction boundaries.
- [ ] Keep all values immutable and framework-free.
- [ ] Add examples for invalid bounds, unknown states, conflict precedence and localization-neutral equality.

**Paths**: `backend/src/ott_feed/recommendation/domain/models.py`, `backend/src/ott_feed/recommendation/domain/errors.py`, `backend/src/ott_feed/recommendation/domain/policies.py`, `backend/tests/recommendation/unit/test_domain.py`.

## Step 5 - Intent Resolution and Conversational State Machine

- [ ] Implement deterministic explicit-term fallback, structured AI intent merge, ambiguity confirmation and conflict reporting.
- [ ] Implement patch/reset precedence, immutable epochs, optimistic versions and idempotent replay semantics.
- [ ] Prohibit fallback guesses for unresolved mood, companion or implicit hard conditions.
- [ ] Add Korean/English examples and P-U05-01 through P-U05-03 plus P-U05-11 stateful properties.

**Paths**: `backend/src/ott_feed/recommendation/application/intent.py`, `backend/src/ott_feed/recommendation/application/sessions.py`, `backend/tests/recommendation/unit/test_intent_and_sessions.py`, `backend/tests/recommendation/pbt/test_session_state_machine.py`.

## Step 6 - Approved Candidate Snapshot and Hard Eligibility

- [ ] Adapt U03 approved candidates into detached U05 snapshot values without direct table access.
- [ ] Apply region, OTT, runtime, release, age and mandatory metadata conditions before scoring.
- [ ] Require compatible U04 predicate version and complete candidate validation state.
- [ ] Add P-U05-04, filter-order and catalog-closure tests.

**Paths**: `backend/src/ott_feed/recommendation/adapters/catalog.py`, `backend/src/ott_feed/recommendation/application/eligibility.py`, `backend/tests/recommendation/unit/test_eligibility.py`.

## Step 7 - Deterministic Scoring and Personalization

- [ ] Implement versioned non-negative normalized weights for request fit, consented affinity, freshness, popularity and novelty.
- [ ] Exclude personalization entirely when consent/features are missing, expired or withdrawn.
- [ ] Implement stable tie-breaking and component score proofs.
- [ ] Add reference-oracle, monotonicity, determinism and consent-exclusion properties P-U05-05 through P-U05-07.

**Paths**: `backend/src/ott_feed/recommendation/domain/ranking.py`, `backend/src/ott_feed/recommendation/application/ranking.py`, `backend/tests/recommendation/unit/test_ranking.py`, `backend/tests/recommendation/pbt/test_ranking_properties.py`.

## Step 8 - Diversity and Reserve Selection

- [ ] Implement versioned provider, genre and franchise repetition caps without adding filtered candidates.
- [ ] Preserve deterministic order for equal diversity decisions and maintain a bounded reserve list.
- [ ] Revalidate reserve candidates before exposure and return fewer items after exhaustion.
- [ ] Add P-U05-08 permutation, duplicate and cap-boundary properties.

**Paths**: `backend/src/ott_feed/recommendation/application/diversity.py`, `backend/tests/recommendation/unit/test_diversity.py`, `backend/tests/recommendation/pbt/test_diversity_properties.py`.

## Step 9 - Evidence Bundles and Candidate Validation Matrix

- [ ] Build candidate-local allowlisted evidence bundles from approved metadata only.
- [ ] Implement complete candidate predicate matrices with passed/failed/unknown/missing/error states.
- [ ] Fail closed on unknown rule version, mismatched content/version or incomplete mandatory predicate closure.
- [ ] Add P-U05-09 and P-U05-10 evidence isolation and completeness properties.

**Paths**: `backend/src/ott_feed/recommendation/application/evidence.py`, `backend/src/ott_feed/recommendation/application/validation.py`, `backend/tests/recommendation/unit/test_evidence_and_validation.py`, `backend/tests/recommendation/pbt/test_grounding_properties.py`.

## Step 10 - Provider-Neutral AI Adapter and Resilience

- [ ] Implement strict Pydantic request/response schemas for intent and grounded claim drafts.
- [ ] Implement allowlisted HTTPS, redirect rejection, 256 KiB response limit and privacy-safe error translation.
- [ ] Implement stage deadlines, at most one remaining-budget-safe retry, jitter injection, semaphore, 20-call/50% circuit and usage caps.
- [ ] Add deterministic HTTPX fake-transport tests for timeout, rate, malformed/oversized schema, redirect, circuit and recovery behavior including P-U05-12.

**Paths**: `backend/src/ott_feed/recommendation/adapters/ai.py`, `backend/src/ott_feed/recommendation/application/resilience.py`, `backend/tests/recommendation/unit/test_ai_adapter.py`.

## Step 11 - Claim Validation and Safe Response Assembly

- [ ] Validate each atomic claim against the same candidate ID, metadata version, field path and source reference.
- [ ] Discard failed or unclosed draft text and replace it with localized evidence-derived templates.
- [ ] Ensure AI output can neither add candidates nor change ranking and that raw provider DTOs cannot reach serialization.
- [ ] Add zero-leakage tests for every failure branch and validated reserve substitution.

**Paths**: `backend/src/ott_feed/recommendation/application/grounding.py`, `backend/src/ott_feed/recommendation/application/responses.py`, `backend/tests/recommendation/unit/test_grounding_and_responses.py`.

## Step 12 - SQLAlchemy Models and Alembic Expand Migration

- [ ] Implement U05 SQLAlchemy rows, constraints and indexes in `u05_recommendation`.
- [ ] Add expand-only migration `0005_u05_recommendation_expand.py` after U04 head.
- [ ] Add migration-owner, API-runtime and maintenance-runtime grants while prohibiting cross-unit writes.
- [ ] Verify clean installation and U07 through U05 upgrade paths; prohibit destructive automatic downgrade.

**Paths**: `backend/src/ott_feed/recommendation/adapters/persistence/models.py`, `backend/migrations/versions/0005_u05_recommendation_expand.py`, `backend/migrations/role-grants.sql`.

## Step 13 - Repositories, Unit of Work and Decision Closure

- [ ] Implement session, request, policy, ranking, validation, trace, usage and retention repositories.
- [ ] Implement compare-and-set session mutation, unique idempotency and immutable policy/decision records.
- [ ] Commit decision closure only after external calls and full candidate/claim validation complete.
- [ ] Add repository unit tests and concurrent real-PostgreSQL session/idempotency tests.

**Paths**: `backend/src/ott_feed/recommendation/adapters/persistence/repositories.py`, `backend/src/ott_feed/recommendation/adapters/persistence/unit_of_work.py`, `backend/tests/recommendation/integration/test_postgresql_recommendation.py`.

## Step 14 - Recommendation Orchestrator and Deadline Pipeline

- [ ] Implement the 10-second monotonic pipeline with approved 0.5/2.75/1.5/4.25/0.5/0.5-second stage budgets.
- [ ] Keep U02/U03/U04 reads and AI calls outside U05 write transactions.
- [ ] Route U02 failure to non-personalized operation, AI failure to deterministic fallback and U03/U04 failure to fail-closed output.
- [ ] Add end-to-end application examples for all eight U05 primary stories.

**Paths**: `backend/src/ott_feed/recommendation/application/orchestrator.py`, `backend/tests/recommendation/unit/test_orchestrator.py`, `backend/tests/recommendation/unit/test_story_examples.py`.

## Step 15 - API Contracts, Routes and Composition

- [ ] Define bounded localized recommend, refine, reset, confirmation, degraded-state and safe-item Pydantic contracts.
- [ ] Add authenticated ownership/idempotency/version-aware routes under `/api/v1/recommendations`.
- [ ] Register facade, router, typed exception handling and recommendation rate-limit behavior in `create_app`.
- [ ] Add OpenAPI and previous-supported consumer contract tests with non-enumerating errors.

**Paths**: `backend/src/ott_feed/recommendation/api/contracts.py`, `backend/src/ott_feed/recommendation/api/router.py`, `backend/src/ott_feed/main.py`, `backend/tests/recommendation/contract/test_recommendation_api.py`.

## Step 16 - Telemetry, Health and Cost Accounting

- [ ] Implement bounded recommendation metrics, structured events and separate required/degradable health contributors.
- [ ] Record token/provider-equivalent usage and estimated cost without prompt or response content.
- [ ] Add U05 Prometheus alerts and Grafana dashboard provisioning for latency, fallback, circuit, validation, pool, retention and cost thresholds.
- [ ] Add telemetry prohibited-field and bounded-label tests.

**Paths**: `backend/src/ott_feed/recommendation/telemetry.py`, `backend/src/ott_feed/recommendation/health.py`, `infra/prometheus/u05-alerts.yml`, `infra/grafana/provisioning/dashboards/u05-recommendation.json`, `backend/tests/recommendation/unit/test_health_telemetry.py`.

## Step 17 - Retention, Recovery and Maintenance Command

- [ ] Implement bounded 500-record retention claims and monotonic checkpoints.
- [ ] Implement restore closure checks for session, policy, ranking, validation, trace privacy and U02/U03/U04 compatibility.
- [ ] Add AI-disabled deterministic re-entry and explicit AI activation preflight.
- [ ] Register one-shot maintenance handlers/command and add retention/recovery tests.

**Paths**: `backend/src/ott_feed/recommendation/application/retention.py`, `backend/src/ott_feed/recommendation/application/recovery.py`, `backend/src/ott_feed/recommendation/maintenance.py`, `backend/tests/recommendation/quality/test_recovery_gate.py`.

## Step 18 - Reusable Strategies, PBT and Quality Evaluation

- [ ] Add reusable strategies for bilingual intents, conflicts, consent snapshots, approved catalogs, scoring policies, evidence graphs, validation matrices and session commands.
- [ ] Complete P-U05-01 through P-U05-12 with deterministic seed/replay and shrinking evidence.
- [ ] Add curated synthetic Korean/English relevance, hard-condition, diversity and grounding evaluation fixtures.
- [ ] Implement version comparison and block activation on safety regression or below-threshold quality.

**Paths**: `backend/tests/strategies/recommendation.py`, `backend/tests/recommendation/pbt/`, `backend/tests/recommendation/quality/test_recommendation_quality_gate.py`, `backend/tests/recommendation/fixtures/`.

## Step 19 - PostgreSQL, Failure, Privacy and Capacity Gates

- [ ] Run U05 real-PostgreSQL migration/repository/concurrency tests with selected integration skip=0.
- [ ] Run AI/U02/U03/U04 failure injection and recovery tests across every degraded branch.
- [ ] Run secret, egress, persistence, telemetry and raw-draft non-leakage scans.
- [ ] Run fewer-than-10-user, 5 sustained/15 burst RPS and 100,000-content bounded capacity/latency evidence.

**Paths**: `backend/tests/recommendation/integration/`, `backend/tests/recommendation/quality/test_capacity_and_privacy_gate.py`, `aidlc-docs/construction/u05-recommendation-and-ai-grounding/code/verification-evidence.md`.

## Step 20 - Deployment Artifacts, Full Regression and Handoff

- [ ] Update Compose, `.env.example`, secret references, AI egress network, maintenance profile, Prometheus and Grafana wiring without committing secret values.
- [ ] Run Ruff format/check, strict MyPy, full pytest with branch coverage, PBT seed, all real-PostgreSQL integration with skip=0 and Compose validation.
- [ ] Verify overall coverage at least 80% and hard-filter, consent, claim and failed-draft safety branches at 100%.
- [ ] Generate code summary, API/operations notes, traceability, validation results and extension compliance; mark all plan/story checkboxes complete.

**Paths**: `compose.yaml`, `.env.example`, `infra/`, `backend/README.md`, `aidlc-docs/construction/u05-recommendation-and-ai-grounding/code/`.

## Planned Verification Commands

Commands use the existing `.venv` and real PostgreSQL configuration established by U07. Exact environment values and secrets remain local.

- Ruff format and check over `backend/src` and `backend/tests`.
- Strict MyPy over `backend/src`.
- Full pytest with branch coverage and the fixed project Hypothesis seed.
- `pytest -m integration` against actual PostgreSQL 17 with zero selected skips.
- U05-specific unit, contract, integration, PBT and quality selections.
- Alembic clean-install and U04-to-U05 upgrade verification.
- Docker Compose configuration validation.

## Planning Decision

The plan is ready for explicit approval. No U05 application, migration, test or infrastructure implementation may begin until the complete 20-step sequence is approved.
