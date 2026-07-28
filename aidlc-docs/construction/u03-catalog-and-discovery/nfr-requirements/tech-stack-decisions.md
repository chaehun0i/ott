# U03 Catalog and Discovery Tech Stack Decisions

## Decision Summary

| Area | Decision | Status |
|---|---|---|
| Runtime/API | Python 3.12.13, FastAPI 0.140.0, Pydantic 2.13.4 | Inherited and locked |
| Persistence | PostgreSQL 17.x, SQLAlchemy 2.0.51, Alembic 1.18.5, psycopg 3.3.4 | Inherited and locked |
| Text search | PostgreSQL full-text search, `pg_trgm` and `unaccent` | Selected; extension gate required |
| Vector search | PostgreSQL `vector` extension with versioned embeddings | Selected; extension/library version verified in Code Generation |
| Embedding access | Provider-neutral async HTTP adapter over HTTPX 0.28.1 | Selected and HTTP client locked |
| Application cache | None | Selected by clarification |
| Projection processing | PostgreSQL outbox and existing worker process | Selected |
| Quality evaluation | Versioned JSON fixtures plus pytest evaluation | Selected |
| Testing/PBT | pytest 9.1.1, Hypothesis 6.161.5 | Inherited and locked |

## ADR-U03-001 — PostgreSQL-Centered Discovery

- **Decision**: Keep approved Catalog data, feed projections, text indexes and vector indexes in PostgreSQL for the prototype.
- **Rationale**: It preserves the authoritative approval boundary and transactional CatalogVersion/outbox semantics without adding another operational datastore for fewer than 10 concurrent users.
- **Constraints**: Search projection membership never replaces authoritative approval/availability rechecks. Query plans and index size must be tested at 100,000 contents.
- **Rejected**: Elasticsearch/OpenSearch adds synchronization and operational complexity before scale requires it.
- **Reassessment triggers**: Persistent search p95 breach, 100,000+ contents with index saturation, rebuild over 30 minutes, or the need for independent horizontal search scaling.

## ADR-U03-002 — PostgreSQL Text Search Configuration

- **Decision**: Use native full-text vectors for indexed documents, `pg_trgm` for exact/prefix/variant support and `unaccent` for controlled normalization where language semantics permit.
- **Rationale**: The combination supports deterministic title/person tiers and Korean/English query paths within the selected database.
- **Constraints**: Search configuration, tokenization and ranking weights are versioned. Locale-specific documents remain distinct. Raw user text is parameterized and never concatenated into SQL.
- **Rejected**: Application-only substring scans cannot meet the 100,000-content/1-second text-search target.
- **Deferred**: Exact language dictionaries, trigram thresholds and weight constants are tuned against the versioned golden set in NFR Design/Code Generation.

## ADR-U03-003 — Versioned Vector Search

- **Decision**: Store embeddings in PostgreSQL's `vector` extension and bind every vector to embedding provider, model identifier, dimension, normalization policy and embedding version.
- **Rationale**: It allows semantic search while keeping candidate IDs beside approved projections and supports atomic snapshot publication.
- **Constraints**: Vectors with an incompatible dimension/model version cannot mix in one query. The actual PostgreSQL extension and Python adapter versions must be checked against the real PostgreSQL 17 runtime before lock changes.
- **Dependency handoff**: Code Generation must add and lock a PostgreSQL vector integration library only after compatibility verification; absence of a verified version is a blocking implementation finding, not permission to emulate vectors in Python.
- **Rejected**: A separate vector service increases synchronization failure modes. Local brute-force vectors do not meet the capacity target.

## ADR-U03-004 — Provider-Neutral Embedding Adapter

- **Decision**: Define an `EmbeddingPort` and use an external provider adapter through the already locked HTTPX client.
- **Rationale**: The user selected external versioned embeddings while retaining provider portability and a deterministic fallback.
- **Timeouts**: Connection budget 300 milliseconds; total embedding/retrieval dependency budget 1.5 seconds.
- **Privacy**: Send only normalized search text and model parameters. Never send identity/profile data or unapproved content payloads from U03.
- **Failure behavior**: Timeout, circuit/open state, incompatible vector version or provider error switches to approved text/filter search and emits a stable degraded code.
- **Deferred**: Provider name, model ID, dimension and credential source are Code Generation configuration decisions and must not be hard-coded.

## ADR-U03-005 — No Application Cache

- **Decision**: Do not introduce process-local, Redis or reverse-proxy response caching for U03 initially.
- **Rationale**: The clarification chose PostgreSQL queries and versioned projections, eliminating cache coherence and multi-process divergence risks at prototype scale.
- **Consequences**: The 1.5-second feed/detail target must be met using schema/query/index design. Cache TTL and CatalogVersion cache purge are N/A.
- **Rejected**: Process-local cache was not selected; Redis adds an unnecessary service; reverse-proxy caching complicates required region/locale/query isolation.
- **Reassessment triggers**: Proven database-bound latency after query/index tuning, sustained database saturation or deployment with multiple API replicas.

## ADR-U03-006 — PostgreSQL Outbox Projection Worker

- **Decision**: Reuse the U07 PostgreSQL-backed job/outbox worker for feed/search projection events.
- **Rationale**: Atomic publication/outbox write and durable replay satisfy CatalogVersion ordering without a new broker.
- **Constraints**: Unique event receipt, contiguous applied version, bounded retry, dead-letter/gap signal, online snapshot rebuild and atomic projection swap are mandatory.
- **Rejected**: In-process best-effort events can lose changes. A separate broker is deferred until throughput or isolation requirements justify it.
- **Targets**: p95 projection lag 60 seconds, alert after sustained 5-minute lag and 30-minute rebuild at 100,000 contents.

## ADR-U03-007 — Search Quality Evaluation

- **Decision**: Store Korean and English golden query sets as versioned, reviewable test fixtures and evaluate Recall@10 and NDCG@10 from pytest.
- **Rationale**: It provides deterministic release evidence without introducing a separate evaluation platform.
- **Required metadata**: Fixture version, CatalogVersion, expected relevant IDs/grades, search configuration version, embedding model/version and evaluation timestamp.
- **Thresholds**: Recall@10 at least 0.80 and NDCG@10 at least 0.75 for each language.
- **Complementary testing**: US-004~US-006 examples remain required even when aggregate metrics pass.

## ADR-U03-008 — Query Privacy and Abuse Controls

- **Decision**: Exclude raw query text from telemetry and generate only a keyed, non-reversible fingerprint plus bounded operational dimensions.
- **Implementation direction**: Use a standard keyed digest from the Python standard library with an injected rotatable key. Never use an unkeyed raw-query hash.
- **Limits**: Anonymous 30 and authenticated 60 requests/minute, 500 Unicode characters, 50 total filter values and page size 50.
- **Rationale**: Search text can expose sensitive interests; bounded input also limits database and embedding cost.
- **Verification**: Log/metric/trace scans, rate-limit tests, Unicode boundary tests and SQL-expression injection tests.

## ADR-U03-009 — Testing and PBT

- **Decision**: Continue using pytest and Hypothesis from the locked development dependencies.
- **PBT-09 fit**: Hypothesis supports domain strategies, shrinking, seeds and pytest integration.
- **Property inventory**: PBT-U03-01~16 covers approved closure, filter oracle, deduplication, order, cursor round-trip/pagination, availability, locale fallback, freshness, ranking, normalization, stateful projection sequences, replay, rebuild and semantic fallback.
- **Generators**: Reusable strategies belong under `backend/tests/strategies/` and generate constrained Catalog revisions, locale maps, availability windows, cursor snapshots and event sequences.
- **Gates**: Overall line coverage at least 80%; CAT/AVAIL/PROJ closure branches 100%; example tests for US-001~US-006; integration selection must report zero skips.

## Compatibility and Migration Policy

1. U03 migrations build on the current U07/U02 Alembic chain and must pass clean-install and upgrade-path tests on real PostgreSQL.
2. `pg_trgm`, `unaccent` and `vector` extension availability is a deployment preflight gate. Failure cannot be hidden by skipped integration tests.
3. Schema changes use expand-and-contract and retain compatibility with the previous application version during version-pinned rollback.
4. Search configuration, FeedPolicyVersion, embedding version and projection schema version are persisted and included in evidence.
5. Exact new dependency versions are resolved against `backend/pyproject.toml`, `backend/uv.lock`, Python 3.12.13 and PostgreSQL 17, then documented before implementation.

## Deferred Decision Register

| Decision | Target stage | Reason |
|---|---|---|
| Embedding provider/model/dimension | Code Generation planning | Requires configured provider and compatibility/cost validation |
| PostgreSQL vector extension and Python adapter exact versions | Code Generation planning | Must verify against actual PostgreSQL 17 and lockfile |
| Text dictionary, trigram threshold and rank weights | NFR Design and Code Generation | Tune against golden datasets |
| Connection pool, statement timeout and vector index parameters | NFR Design | Needs capacity/latency budgets and measured query plans |
| Separate search engine or Redis | Scale review | Not justified by prototype capacity |

## Extension Compliance

- **PBT-09 — Compliant**: pytest 9.1.1 and Hypothesis 6.161.5 are selected, present and locked; code generation must retain them.
- **PBT-01 — Compliant handoff**: PBT-U03-01~16 are mapped to generators and implementation gates.
- **Resiliency — Compliant**: PostgreSQL-centered truth, outbox replay, semantic timeout/fallback, online rebuild and numeric monitoring targets align with enabled rules.
- **Security Baseline — N/A**: Extension is disabled. Query privacy, parameterization and input limits remain core constraints.

No blocking extension finding remains at U03 NFR Requirements.
