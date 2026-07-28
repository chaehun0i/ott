# U03 Catalog and Discovery Code Generation Plan

> **Single Source of Truth**: 이 파일은 U03 Code Generation Part 1과 Part 2의 실행 순서와 완료 상태를 관리한다. 사용자 승인 전에는 application code를 변경하지 않으며, 승인 후에는 Step 1부터 Step 20까지 정의된 순서로 실행하고 각 단계 완료 즉시 `[x]`로 갱신한다.

## Part 1 — Planning Status

- [x] U03 Functional Design, NFR Requirements, NFR Design과 Infrastructure Design을 읽었다.
- [x] US-001~US-006과 U01·U02·U04·U05·U06·U07 contract를 확인했다.
- [x] 기존 U07/U02 application, test, migration, Compose, infra, `backend/pyproject.toml`과 `backend/uv.lock` 구조를 확인했다.
- [x] Docker Engine 29.6.2, Docker Desktop 4.83.0과 Compose 5.3.1 연결을 실제로 확인했다.
- [x] Application code 위치를 `backend/src/ott_feed/catalog/`과 `backend/src/ott_feed/search/`, test 위치를 `backend/tests/catalog/`, `backend/tests/search/`로 확정했다.
- [x] U03이 기존 modular monolith와 PostgreSQL/outbox runtime에 추가되는 Brownfield-style unit임을 확인했다.
- [x] Frontend는 U01 소유이므로 U03에서는 제외하고 versioned OpenAPI contract만 제공하기로 했다.
- [x] 20개 상세 실행 Step, Story trace와 승인 prompt를 작성했다.
- [x] 사용자가 전체 Code Generation 계획과 실행 순서를 명시적으로 승인했다.

## Unit Context

### Primary Stories

| Story | U03 capability | Planned steps |
|---|---|---|
| US-001 | 승인된 신작·공개 예정·인기·종료 예정 통합 피드 | 4~9, 13~16, 17~20 |
| US-002 | 복수 필터, 상세와 합법적 지역·OTT 이동 링크 | 4~7, 9, 15, 17~20 |
| US-003 | 출처, 마지막 정상 갱신과 stale 상태 | 4~9, 16~20 |
| US-004 | 제목·인물 text search와 filter | 4~7, 10, 15~20 |
| US-005 | 한국어 자연어·의미 검색과 locale fallback | 4~7, 10~12, 15~20 |
| US-006 | 영어 자연어·의미 검색과 공통 조건 schema | 4~7, 10~12, 15~20 |

### Dependencies and Contracts

- **U07**: FastAPI factory, request context, Pydantic/OpenAPI, PostgreSQL/SQLAlchemy/Alembic, outbox dispatcher, rate limit, health, telemetry, delivery and recovery runtime.
- **U02**: Authenticated subject and optional subscription context; U03 does not read U02 tables directly.
- **U04**: `PassedValidation`, withdrawal and revalidation outcome through `ApprovedCatalogWritePort`; raw/quarantined data is excluded.
- **U05**: `ApprovedCatalogReadPort`, `AvailabilityPort` and Search Port returning current regional approved candidates.
- **U06**: Authorized content override/read Port plus operational alert/audit references.
- **U01**: Versioned feed/detail/search OpenAPI DTOs with locale, source/freshness, cursor, version and degraded-state fields.
- **External**: Provider-neutral embedding Port over HTTPX; unit and integration tests use deterministic fake/failure adapters.

### Owned Database Entities

`approved_contents`, `catalog_revisions`, `content_localizations`, `catalog_sources`, `content_availability`, `feed_projection_generations`, `feed_projection_entries`, `search_projection_generations`, `search_documents`, `content_embeddings`, `active_projection_generations`, `projection_event_receipts`, `projection_version_state`, `projection_gaps`, `search_quality_runs`.

All U03 tables are created in `u03_catalog`. U07 shared `outbox_jobs` is extended compatibly with U03 unit/job-type indexes and claims rather than duplicated.

## Dependency and Image Baseline for Step 2

The current Python baseline remains `>=3.12.13,<3.13`. Step 2 resolver-tests and pins candidates rather than editing the lockfile manually.

| Capability | Candidate | Required validation |
|---|---|---|
| Python vector adapter | `pgvector==0.5.0` | Python 3.12, SQLAlchemy 2.0.51 and psycopg 3.3.4 compatibility; wheel/hash and vector round-trip |
| PostgreSQL vector extension | `pgvector 0.8.2` | PostgreSQL 17 extension creation, HNSW, exact scan and migration compatibility |
| PostgreSQL container | `pgvector/pgvector:0.8.2-pg17-bookworm` | Image digest, architecture, health, `pg_trgm`·`unaccent`·`vector` preflight |

Primary records: [pgvector Python on PyPI](https://pypi.org/project/pgvector/), [pgvector PostgreSQL repository and Docker tags](https://github.com/pgvector/pgvector). Final pins/digests enter project artifacts only after actual resolver, Docker pull and PostgreSQL execution succeed.

## Part 2 — Generation Steps

## Step 1 — Baseline, Docker and Boundary Guard

- [x] Run the current Ruff, strict MyPy, full pytest/coverage and deterministic PBT baseline before U03 changes.
- [x] Start or inspect the Docker PostgreSQL test path and verify the existing U07/U02 migration/integration suite with selected integration skips equal to zero.
- [x] Record Docker Engine/Compose, PostgreSQL server and migration baseline evidence.
- [x] Add boundary-test expectations that U03 domain/application code cannot import FastAPI, SQLAlchemy, HTTPX or pgvector adapters.

**Paths**: `backend/tests/platform/contract/test_boundaries.py`, `aidlc-docs/construction/u03-catalog-and-discovery/code/baseline.md`.

## Step 2 — Dependency, PostgreSQL Image and Lock Verification

- [x] Verify PyPI `pgvector==0.5.0` metadata/hash and resolve it against Python 3.12.13 and current pinned dependencies.
- [x] Pull and pin the PostgreSQL 17/pgvector 0.8.2 image by digest; verify `pg_trgm`, `unaccent`, `vector`, HNSW and server compatibility in a disposable database.
- [x] Update `backend/pyproject.toml`, regenerate `backend/uv.lock`, synchronize the environment and update the Compose PostgreSQL image only after both gates pass.
- [x] Record exact versions, digest, resolver/runtime evidence and rejected fallback rationale.

**Paths**: `backend/pyproject.toml`, `backend/uv.lock`, `compose.yaml`, `backend/docker/postgres/`, `aidlc-docs/construction/u03-catalog-and-discovery/code/dependency-validation.md`.

## Step 3 — Package Skeleton, Configuration and Ports

- [x] Create U03 catalog/search packages and public Port contracts without framework coupling.
- [x] Add typed configuration for locale/search policies, query/closure budgets, embedding model/dimension, circuit/bulkhead, pool/worker budgets, key files and quality thresholds with fail-fast validation.
- [x] Define clock, ID, transaction, Catalog repository, projection repository, outbox, embedding, rate-limit, telemetry and generation registry protocols.

**Paths**: `backend/src/ott_feed/catalog/`, `backend/src/ott_feed/search/`, `backend/src/ott_feed/catalog/ports.py`, `backend/src/ott_feed/search/ports.py`, `backend/src/ott_feed/catalog/config.py`, `backend/src/ott_feed/search/config.py`, `backend/src/ott_feed/platform/config.py`.

## Step 4 — Domain Models, Errors and State Machines

- [x] Implement typed identifiers, immutable Catalog revisions, localization, availability, CatalogVersion, projection generation, cursor and structured query values.
- [x] Implement publish/replace/withdraw/reactivate and projection/gap/generation state transitions.
- [x] Implement CAT/FEED/AVAIL/FRESH/LOC/SEARCH/PROJ business errors and invariants without persistence/framework imports.

**Paths**: `backend/src/ott_feed/catalog/domain/`, `backend/src/ott_feed/search/domain/`.

## Step 5 — Feed, Filter, Localization and Freshness Policies

- [x] Implement versioned multi-section membership and popularity/freshness score policy with deterministic tie-breakers.
- [x] Implement AND-across/OR-within filter semantics, regional verified availability, direct/detail link selection and duplicate removal.
- [x] Implement locale fallback, actual-locale reporting, provider/category freshness thresholds and 24-hour default.
- [x] Implement pure cursor query fingerprint/sort tuple models for later signed transport.

**Paths**: `backend/src/ott_feed/catalog/domain/policies.py`, `backend/src/ott_feed/catalog/domain/feed.py`, `backend/src/ott_feed/catalog/domain/localization.py`.

## Step 6 — SQLAlchemy Models, Extensions and Alembic Expand Migration

- [x] Implement U03 SQLAlchemy rows under `u03_catalog`, including generation/version constraints and pgvector types.
- [x] Create expand-only `0003_u03_catalog_expand.py` after `0002`, enable/version-check extensions and create FTS, trigram, HNSW, closure and claim indexes.
- [x] Extend outbox schema/indexes compatibly for unit/job type and add U03 role grants.
- [x] Prohibit destructive automatic downgrade and verify clean plus U07/U02 upgrade paths.

**Paths**: `backend/src/ott_feed/catalog/adapters/persistence/models.py`, `backend/src/ott_feed/search/adapters/persistence/models.py`, `backend/migrations/versions/0003_u03_catalog_expand.py`, `backend/migrations/role-grants.sql`.

## Step 7 — Repositories, Unit of Work and Closure Guard

- [x] Implement Catalog, availability, feed/search projection, receipt/gap and generation registry repositories with typed error translation.
- [x] Implement separate API/worker transaction profiles, statement budgets and compare-and-set version writes.
- [x] Implement `ApprovedClosureGuard` that rechecks current revision, withdrawal, license and exact-region availability and fails closed on read failure.

**Paths**: `backend/src/ott_feed/catalog/adapters/persistence/repositories.py`, `backend/src/ott_feed/search/adapters/persistence/repositories.py`, `backend/src/ott_feed/catalog/adapters/persistence/unit_of_work.py`, `backend/src/ott_feed/catalog/application/closure.py`.

## Step 8 — Approved Catalog Publication and Versioned Outbox

- [x] Implement `ApprovedCatalogWritePort` service for publish/replace/withdraw/reactivate from passed U04 decisions.
- [x] Atomically write immutable revision, current visibility, monotonic CatalogVersion and versioned outbox event.
- [x] Enforce decision/version idempotency, provenance/license requirements and immediate withdrawal blocking.

**Paths**: `backend/src/ott_feed/catalog/application/publication.py`, `backend/src/ott_feed/catalog/application/commands.py`, shared outbox adapter extensions.

## Step 9 — Feed and Detail Query Services

- [x] Implement snapshot feed sections, filters, deterministic keyset pagination and final closure recheck.
- [x] Implement localized detail, verified regional availability, direct-watch/detail link preference, source and freshness state.
- [x] Enforce required region, page/filter limits and no application response cache.

**Paths**: `backend/src/ott_feed/catalog/application/feed.py`, `backend/src/ott_feed/catalog/application/detail.py`.

## Step 10 — Text Search and Structured Query Parsing

- [x] Implement Korean/English query normalization and the shared structured-condition schema with unresolved terms.
- [x] Implement exact title, prefix, locale FTS and person tiers over parameterized PostgreSQL queries.
- [x] Apply filters, deterministic locale/popularity/content-ID tie-breakers and final closure.

**Paths**: `backend/src/ott_feed/search/application/parser.py`, `backend/src/ott_feed/search/application/text_search.py`, `backend/src/ott_feed/search/adapters/persistence/text_repository.py`.

## Step 11 — Embedding Adapter, Deadline, Circuit and Privacy

- [x] Implement provider-neutral HTTPX embedding adapter with model/dimension/version contract and response validation.
- [x] Apply connect 300ms/total 1.5-second deadline, concurrency four, 20-call/50%/30-second circuit and two half-open probes.
- [x] Disable user-path retries, allow only background retry-safe attempts, restrict redirect/host behavior and never log raw query/provider payload.

**Paths**: `backend/src/ott_feed/search/adapters/embedding.py`, `backend/src/ott_feed/search/application/resilience.py`, `backend/tests/search/unit/test_embedding_adapter.py`.

## Step 12 — Vector Retrieval and Hybrid Ranking

- [x] Implement compatible-generation HNSW and exact-vector oracle retrieval with pgvector/SQLAlchemy.
- [x] Implement exact-title priority, hard-filter exclusion and versioned Reciprocal Rank Fusion with deterministic tie-breaker.
- [x] Implement semantic-to-approved-text fallback for timeout, open circuit, model mismatch or missing compatible generation.

**Paths**: `backend/src/ott_feed/search/adapters/persistence/vector_repository.py`, `backend/src/ott_feed/search/application/hybrid_search.py`, `backend/src/ott_feed/search/domain/ranking.py`.

## Step 13 — Incremental Projection Worker, Replay and Gap Barrier

- [x] Register incremental and embedding job handlers with U03 lane/concurrency budgets.
- [x] Implement `FOR UPDATE SKIP LOCKED` claims, per-content ordering, unique receipts and idempotent compare-and-set application.
- [x] Implement contiguous CatalogVersion barrier, gap detection, replay/reconciliation, restart lease recovery and alert signals.

**Paths**: `backend/src/ott_feed/catalog/worker.py`, `backend/src/ott_feed/search/worker.py`, `backend/src/ott_feed/worker.py`, shared outbox repository extensions.

## Step 14 — Online Rebuild, Quality Gate and Atomic Generation Swap

- [x] Implement immutable feed/text/vector candidate generation build with concurrency one and online-SLO pause.
- [x] Validate closure, duplicates, version continuity, bilingual golden metrics, exact-vector recall and smoke latency.
- [x] Atomically swap active generation, retain previous rollback generation and preserve prior state on build/swap failure.

**Paths**: `backend/src/ott_feed/search/application/rebuild.py`, `backend/src/ott_feed/search/application/quality.py`, `backend/src/ott_feed/search/adapters/persistence/generations.py`.

## Step 15 — HMAC Cursor/Fingerprint, Rate Limits and HTTP API Contracts

- [x] Implement purpose-separated current/previous HMAC key loaders, authenticated opaque cursor round-trip and keyed query fingerprints.
- [x] Add anonymous/authenticated and semantic cost buckets with query/filter/page limits before expensive work.
- [x] Create versioned feed/detail/search Pydantic contracts and routers with locale, source, freshness, versions, cursor and degraded reason fields.
- [x] Wire only stable safe errors and OpenAPI contracts for U01/U05 consumers.

**Paths**: `backend/src/ott_feed/search/adapters/security.py`, `backend/src/ott_feed/search/api/`, `backend/src/ott_feed/catalog/api/`, `backend/src/ott_feed/main.py`, `docs/api-contract.md`.

## Step 16 — Health, Privacy-Safe Telemetry and Application Wiring

- [x] Add U03 liveness/readiness/deep-health contributions for PostgreSQL extensions, active generation and separately degraded embedding capability.
- [x] Implement allowlisted metrics/log attributes and alerts for gap, lag, closure drops, fallback, zero-result, stale ratio, disk and rebuild.
- [x] Wire U03 repositories, services, adapters and worker registry into the existing application factory without domain leakage.

**Paths**: `backend/src/ott_feed/catalog/telemetry.py`, `backend/src/ott_feed/search/telemetry.py`, `backend/src/ott_feed/catalog/health.py`, `backend/src/ott_feed/search/health.py`, `backend/src/ott_feed/main.py`, `backend/src/ott_feed/worker.py`.

## Step 17 — Example Unit and Contract Tests

- [x] Add examples for CAT/FEED/AVAIL/FRESH/LOC/SEARCH/PROJ critical branches and US-001~US-006 acceptance paths.
- [x] Add API/OpenAPI tests for region, filters, locale fallback, cursor, source/freshness, degraded behavior and stable errors.
- [x] Add architecture/privacy tests rejecting framework imports, raw query/vector/provider payload telemetry and cross-Unit table writes.

**Paths**: `backend/tests/catalog/unit/`, `backend/tests/search/unit/`, `backend/tests/catalog/contract/`, `backend/tests/search/contract/`.

## Step 18 — Property-Based Tests

- [x] Implement PBT-U03-01~16 with reusable domain strategies and a stateful projection reference model.
- [x] Cover closure, filter oracle, dedup/order, cursor round-trip/pagination, availability, locale, freshness, ranking, query normalization, replay/rebuild and semantic fallback.
- [x] Preserve Hypothesis shrinking, deterministic seed logging and regression promotion guidance.

**Paths**: `backend/tests/catalog/pbt/`, `backend/tests/search/pbt/`, `backend/tests/strategies/catalog.py`, `backend/tests/strategies/search.py`.

## Step 19 — Docker PostgreSQL Integration, Failure, Quality and Performance Gates

- [x] Run clean/upgrade migrations, extension/version/HNSW, repository constraints, publication/outbox atomicity, claims/gaps/replay and generation swap on Docker PostgreSQL 17+pgvector.
- [x] Inject embedding timeout/circuit, PostgreSQL closure failure, duplicate/out-of-order/gap events, worker restart, rebuild validation and pointer-swap failure.
- [x] Evaluate 100,000-content capacity fixtures, query plans, load targets, 30-minute rebuild and Korean/English Recall@10/NDCG@10 thresholds.
- [x] Run `pytest -m integration` with zero skips and retain actual PostgreSQL/Docker evidence.

**Paths**: `backend/tests/catalog/integration/`, `backend/tests/search/integration/`, `backend/tests/search/quality/`, test reports under `backend/`.

## Step 20 — Deployment Artifacts, Final Quality Gate and Handoff

- [x] Extend Compose, PostgreSQL image/build, secret references, worker budgets, Caddy routes, Prometheus/Grafana/OTel, deployment/rollback and backup/restore artifacts without secret values.
- [x] Run Ruff format/check, strict MyPy, full pytest with deterministic Hypothesis seed, branch coverage, selected integration skip=0, OpenAPI and lock checks.
- [x] Verify overall line coverage at least 80%, CAT/AVAIL/PROJ critical branch coverage 100%, US-001~US-006 examples and PBT-U03-01~16.
- [x] Verify clean/U07-U02 upgrade migrations, role grants, no raw-query telemetry, no application code under `aidlc-docs/` and Docker/native verification parity.
- [x] Create code/test/dependency/PBT/traceability summaries, mark plan/story checkboxes, update state and request standardized Code Generation approval.

**Paths**: `compose.yaml`, `backend/docker/postgres/`, `infra/`, `scripts/`, `docs/`, `aidlc-docs/construction/u03-catalog-and-discovery/code/`.

## Expected Scope

- **20 sequential generation steps** after explicit plan approval.
- **Application changes**: existing `backend/` modular monolith, migration chain, Compose, infra and operational docs.
- **New unit packages**: `backend/src/ott_feed/catalog/` and `backend/src/ott_feed/search/`.
- **New unit tests**: `backend/tests/catalog/`, `backend/tests/search/` and reusable strategies.
- **Documentation summaries only**: `aidlc-docs/construction/u03-catalog-and-discovery/code/`.
- **No frontend generation**: U01 consumes the U03 OpenAPI contract later.

## Extension Execution Commitments

- **Resiliency Baseline**: Deadline/circuit/bulkhead, approved fallback, ordered outbox recovery, online generation rollback, backup/rebuild re-entry and failure injection are implemented and evidenced.
- **Property-Based Testing**: All 16 properties are implemented with Hypothesis, shrinking remains enabled and failures retain seed/minimal counterexample/regression evidence.
- **Security Baseline**: Disabled and N/A as an extension; U03 core approval closure, regional/license safety, HMAC integrity, rate limit and query privacy remain blocking gates.
