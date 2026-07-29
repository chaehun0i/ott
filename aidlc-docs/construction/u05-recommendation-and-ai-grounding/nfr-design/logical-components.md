# U05 Recommendation and AI Grounding Logical Components

## Component Inventory

| Component | Responsibility | Must not do |
|---|---|---|
| `RecommendationFacade` | Own deadline, orchestration order, fallback and safe response contract | Calculate scores or approve drafts |
| `RequestAdmissionGuard` | Enforce ownership, rate/idempotency, size/count and deadline bounds | Interpret natural language |
| `ConsentContextReader` | Read U02 purpose-limited feature snapshot and convert unavailable/withdrawn state to non-personalized context | Read users or raw behavior |
| `IntentInterpreter` | Invoke AI schema adapter and create versioned intent/conflicts | Rank candidates or silently confirm ambiguity |
| `DeterministicIntentFallback` | Extract only allowlisted explicit genre/runtime/OTT terms when AI is unavailable | Guess mood/companion or create hard conditions from unresolved text |
| `SessionCoordinator` | Apply CAS/idempotent patch/reset and maintain epoch/version closure | Call AI inside its transaction |
| `ApprovedCandidateReader` | Read bounded immutable U03 catalog/availability/evidence snapshots | Query U03 tables directly or return unapproved rows |
| `RankingEngine` | Hard filter, bounded score, stable sort and reference-oracle behavior | Generate text or accept AI candidate IDs |
| `DiversityReranker` | Deduplicate and reorder within the eligible set under versioned caps | Add or restore filtered candidates |
| `CandidateValidator` | Apply complete U03/U04 candidate predicate matrix before drafting and serialization | Repair metadata or change rank policy |
| `EvidenceBundleBuilder` | Project candidate-local allowlisted approved fields and references | Include raw provider/quarantine/private fields |
| `AIProviderAdapter` | Bounded HTTPS schema calls, usage accounting and safe errors | Leak provider DTOs/errors into domain code |
| `GroundedDraftService` | Request localized reason/summary drafts as atomic claims | Mark its own output safe |
| `ClaimValidator` | Prove same-content evidence and complete claim-result closure | Regenerate failed claims |
| `SafeResponseAssembler` | Build response from passed/replaced types only and fill validated reserves | Serialize raw draft or unknown state |
| `PolicyRegistry` | Manage immutable intent/score/diversity/fallback/AI versions and activation pointers | Mutate historical policy |
| `QualityEvaluationRunner` | Run deterministic bilingual, ranking, grounding, latency and cost gates | Use production user data as fixtures |
| `RecommendationTraceRecorder` | Persist minimized decision/version/code trace and expose U06 read port | Store prompt/response or chain-of-thought |
| `RetentionRecoveryCoordinator` | Purge/checkpoint retention and verify restore re-entry closure | Reopen reset/deleted state |
| `RecommendationTelemetry` | Emit bounded metrics/log/health/cost signals | Emit request, synopsis, draft or identity text |

## Port Boundaries

| Port | Provider | Contract requirements |
|---|---|---|
| `ConsentFeaturePort` | U02 | Pseudonymous, purpose/version/expiry, no raw history or direct ID |
| `ApprovedRecommendationCatalogPort` | U03 | Snapshot version, approved candidates, region/OTT availability and evidence references |
| `ValidationPredicatePort` | U04 | Versioned pure mandatory predicates; unknown version fails closed |
| `AIProviderPort` | External adapter through U07 runtime | Structured intent/draft schema, usage metadata and safe typed failures |
| `RecommendationTracePort` | U05 provides to U06 | Bounded privacy-safe trace view only |
| `Clock`, `IdGenerator`, `TelemetryPort` | U07 | Explicit time/IDs and bounded attributes |
| U05 repositories/unit of work | U05 persistence adapter | Session, request, policy, ranking, validation, trace and retention ownership |

U05 has no direct U02/U03/U04 table write. Cross-unit snapshots are immutable detached values. The domain/application packages do not import FastAPI, SQLAlchemy, HTTPX or concrete adapters.

## Normal Interaction

1. `RequestAdmissionGuard` creates the monotonic deadline and validates request/session ownership, bounds and idempotency.
2. `SessionCoordinator` resolves the active version; stale conflict exits immediately.
3. `ConsentContextReader` obtains a valid U02 snapshot or empty non-personalized context.
4. `IntentInterpreter` creates a canonical intent. Ambiguity returns confirmation without ranking.
5. `ApprovedCandidateReader` gets one U03 snapshot and the compatible U04 rule version.
6. `RankingEngine` applies hard filters and scores; `DiversityReranker` produces final/reserve order.
7. `CandidateValidator` closes candidate predicates before evidence is built.
8. `EvidenceBundleBuilder` creates bounded candidate-local evidence.
9. `GroundedDraftService` calls the AI adapter under remaining budget.
10. `ClaimValidator` and `CandidateValidator` close every exposed path.
11. `SafeResponseAssembler` replaces failed text/items or invokes deterministic fallback.
12. `RecommendationTraceRecorder` closes minimized decision state and `RecommendationTelemetry` records bounded outcomes.

## Degraded Interactions

### AI intent failure

The circuit/bulkhead returns a typed dependency state. `DeterministicIntentFallback` extracts only explicit recognized conditions. If sufficient, the normal candidate/ranking/validation path runs with templates; otherwise the response requests structured clarification. Model knowledge never creates a candidate.

### AI drafting failure or usage cap

The already validated ranked set remains authoritative. `SafeResponseAssembler` builds localized approved templates from the same evidence and marks `degraded_reason=ai_unavailable` or `ai_budget_exhausted`.

### U02 failure/withdrawal

`ConsentContextReader` produces empty feature context and records non-personalized mode. No stale feature cache is allowed. Explicit request conditions continue.

### U03/U04 failure

`RecommendationFacade` fails closed before response items. AI fallback is not eligible because approved identity/validation cannot be proven.

### Candidate/claim failure

The validator rejects only the failing item/claim, selects a reserve candidate when budget remains and repeats complete validation. Failed draft content is discarded.

## Persistence Components and Constraints

| Repository | Owned records | Key constraints |
|---|---|---|
| `SessionRepository` | sessions, epochs, versions, patches | unique active epoch; unique idempotency key; optimistic version |
| `RequestRepository` | request attempts and immutable input versions | unique request/attempt lineage |
| `PolicyRepository` | intent/score/diversity/fallback/AI config versions | immutable version; one active pointer per policy kind |
| `RankingRepository` | candidates, filter proofs, scores and positions | candidate belongs to request snapshot; bounded position uniqueness |
| `ValidationRepository` | candidate/claim results and closure | complete mandatory matrix; terminal immutable outcome |
| `TraceRepository` | minimized trace and operational closure | allowlisted fields; pseudonymous lookup; no free-text body |
| `RetentionRepository` | purge/recovery checkpoints | fenced bounded claims and monotonic checkpoint |

Cross-record decision closure is one U05 transaction after external calls complete. A passed candidate and safe response metadata cannot commit without the matching validation matrix and version references.

## Concurrency and Resource Budgets

| Resource | Initial budget | Saturation behavior |
|---|---:|---|
| AI calls per API process | 4 | 100 ms queue then deterministic fallback |
| U05 PostgreSQL connections per API process | 2 | 100 ms acquisition then bounded dependency error/fallback as safe |
| Candidate input | 1,000 | Reject/limit before score allocation |
| Scored candidates | 500 | Truncate by deterministic pre-order |
| Reserve candidates | 100 | Return fewer items after reserve exhaustion |
| Exposed/evidence candidates | 20 | Reject oversized request or cap to policy |
| Atomic claims per item | 64 | Reject AI schema output and template-replace |
| Retention cleanup batch | 500 records | Checkpoint and yield |

Scale review evaluates CPU, memory, pool wait, AI semaphore, U03 query plans, trace writes and provider quota together. U05 does not add Redis, broker or a second vector store before measured evidence justifies it.

## Health and Telemetry Contributions

| Check | Readiness effect |
|---|---|
| U05 database/session/policy access | Required |
| U03 approved candidate port | Required |
| U04 compatible validation rules | Required |
| U02 feature port | Optional degraded to non-personalized |
| AI provider/circuit/usage cap | Optional degraded to deterministic fallback |
| Trace recorder | Degraded/alert; configured audit-critical policy applies |

Metrics contain only bounded route/stage/outcome/reason/version/circuit labels. Content IDs are permitted only in protected trace storage where required for DR-014, not metric labels or general logs.

## Recovery Ordering

1. Restore U05 schema and immutable policy/config history.
2. Verify session epoch/version and patch idempotency constraints.
3. Verify ranking input references and complete candidate/claim validation matrices.
4. Verify trace allowlist and absence of prompt/draft bodies.
5. Verify U02/U03/U04 current contract compatibility.
6. Enable deterministic recommendation with AI disabled.
7. Enable AI only after configuration/evaluation compatibility and health pass.

## Verification Ownership

| Component group | Properties and gates |
|---|---|
| Intent/session | P-U05-01~03, P-U05-11, bilingual fixtures and PostgreSQL CAS |
| Candidate/ranking/diversity | P-U05-04~08, reference oracle, 100,000-content/load evidence |
| Evidence/claim/output | P-U05-09~10, complete matrix and zero-leakage safety branches |
| AI adapter/fallback | P-U05-12, fake transport, timeout/rate/circuit/usage-cap injection |
| Persistence/recovery | integration `skip=0`, migration, constraints, retention and restore re-entry |
| Boundary/privacy | architecture, consumer/OpenAPI, secret/egress and telemetry scans |

## NFR Traceability

| NFR group | Components/patterns |
|---|---|
| U05-NFR-001~007 | admission bounds, bulkheads, resource table and scale review |
| U05-NFR-008~014 | deadline allocation, cancellation and latency telemetry |
| U05-NFR-015~024 | AI resilience, degradation matrix, CAS/idempotency and output isolation |
| U05-NFR-025~030 | retention repository and restore re-entry ordering |
| U05-NFR-031~040 | quality runner, immutable activation registry and evaluation gate |
| U05-NFR-041~048 | consent reader, context/evidence allowlists, secret/egress and trace privacy |
| U05-NFR-049~054 | telemetry, layered health, alerts and usage/cost caps |
| U05-NFR-055~063 | versioned ports, architecture, PBT, contract and PostgreSQL gates |

## Extension Compliance

| Rule group | Status | Design evidence |
|---|---|---|
| RESILIENCY-01~02 | Compliant | Critical/degradable split, 99.0%, RTO/RPO and fallback objectives |
| RESILIENCY-03~04 | Compliant | Immutable activation, comparison evidence and pointer rollback |
| RESILIENCY-05~07 | Compliant | Layered health, bounded telemetry, safety/threshold alerts |
| RESILIENCY-08~09 | N/A | Approved single-server/no-autoscale prototype with numeric transition triggers |
| RESILIENCY-10 | Compliant | Deadline, bounded retry, bulkhead, circuit and deterministic fallback |
| RESILIENCY-11~13 | Compliant | Backup scope, restore closure and staged re-entry |
| RESILIENCY-14~15 | Compliant | Failure/recovery/model-change tests and privacy-safe trace evidence |
| PBT-01 | Compliant | P-U05-01~12 assigned to logical components and gates |
| PBT-09 | Compliant | Existing locked Hypothesis/pytest stack retained |
| PBT-02~08, PBT-10 | Planned | Blocking Code Generation evidence with examples and reusable strategies |
| Security Baseline | N/A | Disabled; core privacy/security design remains blocking |

No blocking enabled-extension finding remains at U05 NFR Design.
