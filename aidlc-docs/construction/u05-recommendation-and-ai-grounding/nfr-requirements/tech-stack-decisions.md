# U05 Recommendation and AI Grounding Tech Stack Decisions

## Actual Locked Baseline

These decisions use the current `backend/pyproject.toml` and existing `uv.lock`. No new package or external AI provider is selected in this stage.

| Area | Decision | Locked version or status |
|---|---|---|
| Runtime | CPython | `>=3.12.13,<3.13` |
| API/schema | FastAPI and Pydantic | 0.140.0 and 2.13.4 |
| AI HTTP adapter | HTTPX behind `AIProviderPort` | 0.28.1 |
| Domain ranking/validation | Pure Python typed domain code | Standard library; no ML framework |
| Persistence | PostgreSQL, SQLAlchemy, psycopg | PostgreSQL 17.x, 2.0.51 and 3.3.4 |
| Migrations | Alembic | 1.18.5 |
| Candidate/search source | Existing U03 ports and pgvector-backed projections | pgvector Python 0.5.0; U03-owned retrieval |
| Testing | pytest, Hypothesis and pytest-cov | 9.1.1, 6.161.5 and 7.1.0 |
| Quality | Ruff and strict MyPy | 0.16.0 and 2.3.0 |
| Delivery/telemetry | Existing U07 Docker Compose and observability | Selected; no new stack |

## ADR-U05-001 - Provider-Neutral AI Adapter

- **Decision**: Define intent and grounded-draft protocols behind `AIProviderPort` and use HTTPX for the initial adapter.
- **Rationale**: Provider/model selection remains deploy-time configuration. HTTPX is already locked and supports explicit timeouts, pooling and fake transports.
- **Constraints**: HTTPS allowlist, redirect rejection, file-injected credential, request/response/token bounds, schema validation, redaction, retry safety and circuit isolation are mandatory.
- **Rejected**: A provider SDK would couple core contracts and add an unverified dependency before a provider is selected. Direct AI calls inside C08/C10/C11 violate ownership.

## ADR-U05-002 - Pydantic Boundary and Framework-Free Domain

- **Decision**: Use Pydantic for API, AI and cross-unit boundary schemas; implement intent resolution, hard filtering, scoring, diversity, evidence and validation as immutable dataclasses/value objects and pure services.
- **Rationale**: Untrusted model output needs strict bounded validation while business invariants require deterministic framework-independent tests.
- **Constraints**: Pydantic acceptance never equals business approval. C11 must still validate candidate and claim closure.
- **Rejected**: Untyped model dictionaries hide missing/unknown states. Pydantic/ORM domain aggregates would couple core rules to adapters.

## ADR-U05-003 - Deterministic Rule Ranking Before Learned Ranking

- **Decision**: Start with versioned weighted request-fit, consented affinity, freshness, popularity and novelty scoring plus deterministic diversity reranking.
- **Rationale**: The prototype lacks sufficient consented outcome data for a trained ranking model. A transparent reference formula is replayable and supports P-U05-05~08.
- **Constraints**: Hard filters run first; weights are non-negative and normalized; feature versions and component scores are retained.
- **Reassessment triggers**: Sufficient consented training/evaluation data, an approved offline relevance lift, stable feature definitions and rollback/monitoring evidence.
- **Rejected**: LLM ranking violates C09/C10 separation. Introducing NumPy/scikit-learn or a model-serving stack has no current evidence.

## ADR-U05-004 - U03-Owned Candidate and Vector Retrieval

- **Decision**: Consume approved candidates/evidence through U03 ports and its existing text/vector projections; U05 creates no duplicate catalog/vector store.
- **Rationale**: U03 already owns approved closure, availability, freshness and search projections. One source prevents drift and unapproved candidates.
- **Constraints**: U05 snapshots exact catalog/metadata versions and revalidates before exposure. It never writes U03 tables.
- **Rejected**: A U05 vector database duplicates approval state. AI-provider candidate generation cannot prove catalog closure.

## ADR-U05-005 - PostgreSQL Session, Decision and Trace State

- **Decision**: Persist versioned sessions/patches, requests, ranking decisions, validation outcomes and minimized traces in a U05-owned PostgreSQL schema.
- **Rationale**: Optimistic session updates, idempotency, immutable versions, restore closure and U06 trace reads need durable relational constraints.
- **Constraints**: Read-only U02/U03/U04 calls occur outside U05 write transactions. Raw prompts/responses and failed drafts are not persistent recovery state.
- **Rejected**: Process memory loses conversational concurrency/recovery. Redis or a broker adds operations without current throughput evidence.

## ADR-U05-006 - Synchronous Orchestration with Stage Budgets

- **Decision**: Keep one synchronous recommendation request in the API process with explicit budgets and deterministic fallback; use background jobs only for offline evaluation/cleanup if later required.
- **Rationale**: The product requires an interactive response and current load is below 10 concurrent users.
- **Constraints**: Independent dependency bulkheads, cancellation/deadline propagation and no database transaction around external AI calls.
- **Reassessment triggers**: Sustained concurrency/latency beyond U05-NFR-006, provider batch APIs, streaming product requirements or independent AI worker scaling.
- **Rejected**: A mandatory asynchronous user job complicates conversation UX. Unbounded synchronous calls violate latency and saturation goals.

## ADR-U05-007 - No Correctness Cache or New Broker

- **Decision**: Add neither Redis nor a message broker for initial U05 correctness. Optional process-local memoization may cache immutable parser/static-template data only.
- **Rationale**: Correctness depends on versioned U02/U03/U04 snapshots and PostgreSQL state. Current scale does not justify distributed invalidation.
- **Constraints**: Cached data cannot extend consent, approval, availability or validation-rule lifetime.
- **Reassessment triggers**: Measured database contention, repeated immutable evidence reads dominating p95 or independent recommendation worker requirements.

## ADR-U05-008 - Claim-Level Grounding Contract

- **Decision**: Represent drafts as atomic claims with same-content content ID, metadata version, field path and source references; C11 authorizes exposure.
- **Rationale**: Whole-text confidence cannot prove FR-038~041. Structured evidence supports deterministic validation and template replacement.
- **Constraints**: Unknown/missing/error results fail closed. Failed free text is discarded and prohibited from telemetry/persistence.
- **Rejected**: Disclaimer-only safety, model self-critique and post-hoc content-ID checks do not validate claims.

## ADR-U05-009 - Existing pytest/Hypothesis Quality Stack

- **Decision**: Use locked pytest and Hypothesis for examples, contracts, P-U05-01~12 and stateful session testing.
- **PBT-09 fit**: Hypothesis provides domain strategies, shrinking, reproducible seeds, state-machine models and pytest integration.
- **Generators**: Reusable strategies will cover bilingual intents, conflicts, consent snapshots, approved catalogs, score policies, permutations, evidence graphs, validation matrices and patch/reset sequences.
- **Gates**: Overall coverage at least 80%; hard-filter/consent/claim/non-leakage safety branches 100%; real PostgreSQL integration selection has zero skips; primary stories retain explicit examples.

## ADR-U05-010 - Versioned Offline AI Evaluation

- **Decision**: Store curated bilingual evaluation fixtures and expected structured/grounded outcomes in version control without user data; compare every model/prompt/policy change to the active baseline.
- **Rationale**: External model behavior may change independently of application code. Versioned evaluation is required for reproducibility and rollback.
- **Constraints**: Fixtures use synthetic/licensed approved metadata, contain no secrets or direct identity, and separate deterministic safety gates from statistical relevance metrics.
- **Rejected**: Live-provider smoke tests alone are non-deterministic, costly and unavailable offline. Engagement metrics alone cannot protect hard constraints.

## ADR-U05-011 - Shared U07 Telemetry with Usage Accounting

- **Decision**: Extend existing structured telemetry, metrics, health and dashboard conventions with bounded U05 stage/quality/fallback/token/cost signals.
- **Rationale**: One observability stack supports correlation with U02/U03/U04 dependencies without exposing payloads.
- **Constraints**: No request/explanation/synopsis text, direct user ID, raw model response or provider error body in telemetry. Monetary limits remain deployment config until provider selection.
- **Deferred**: Exact dashboard panels, alert thresholds, circuit budgets and provider price configuration are NFR Design/Infrastructure Design work.

## Compatibility and Migration Policy

1. U05 persistence extends the existing Alembic chain after U04 and supports clean install plus upgrade from current head on PostgreSQL 17.
2. Intent, AI schema, scoring, diversity, prompt-template, trace and validation contracts version independently of database revision.
3. The previous supported API/consumer contract remains readable during expand-and-contract and image rollback.
4. Historical policy/model versions remain available for trace explanation but cannot authorize new responses unless active/compatible.
5. No dependency or AI SDK is added during NFR Requirements. Any future package requires official compatibility, license, lockfile and vulnerability verification.

## Deferred Decision Register

| Decision | Target stage | Reason |
|---|---|---|
| Exact connect/read/total timeout, retries and circuit thresholds | NFR Design | Must allocate the 10-second end-to-end budget |
| Candidate query/page/index and PostgreSQL pool budgets | NFR Design | Must align with shared single-server capacity |
| Concrete AI provider/model/endpoint and price | Configuration/Code Generation | Provider not selected; credential/legal/cost verification required |
| Exact scoring weights and diversity caps | Code Generation policy fixture | Must be versioned and quality-tested, not hardcoded in architecture |
| Exact prompt/evidence byte/token budgets | NFR Design | Must satisfy latency/cost/schema limits |
| Conversation retention override UI | U01/U02 integration | U05 owns enforcement; U01/U02 own user control/notice |
| Learned ranking model | Scale/quality review | Requires sufficient consented data and offline lift evidence |

## Extension Compliance

- **PBT-09 - Compliant**: pytest 9.1.1 and Hypothesis 6.161.5 are present in `pyproject.toml` and locked.
- **PBT-01 - Compliant handoff**: P-U05-01~12 map to generator, example, contract and stateful gates.
- **Resiliency - Compliant**: dependency isolation, deterministic degradation, versioned replay, recovery closure and monitoring/cost signals are requirements.
- **Security Baseline - N/A**: disabled. Consent, minimization, endpoint/secret controls and telemetry privacy remain core mandatory requirements.

No blocking extension finding remains at U05 NFR Requirements.
