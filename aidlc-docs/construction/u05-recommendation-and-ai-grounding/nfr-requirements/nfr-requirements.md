# U05 Recommendation and AI Grounding NFR Requirements

## Scope and Criticality

U05 is High criticality for recommendation eligibility, hard-condition preservation, grounded claims and consent enforcement. AI intent/drafting availability is Medium because deterministic rule-based ranking and approved metadata templates preserve a safe degraded recommendation path. U03 approved catalog and U04 validation compatibility are hard dependencies: model knowledge cannot replace either one.

U05 inherits the prototype monthly availability objective of 99.0% excluding planned maintenance, RTO 4 hours, RPO 24 hours, single-region/single-server exception and versioned Backup and Restore strategy.

## Capacity and Scale

- **U05-NFR-001**: Baseline load verification must reproduce 10 concurrent users with mixed initial recommendation, refinement, reset and deterministic fallback requests.
- **U05-NFR-002**: The initial service must sustain 5 recommendation requests/second for 10 minutes and a 15 requests/second burst for 60 seconds without violating hard-condition or grounding closure.
- **U05-NFR-003**: One request may examine at most 1,000 approved candidates, score at most 500 eligible candidates, retain at most 100 reserve candidates and expose at most 20 items.
- **U05-NFR-004**: One AI drafting call may receive evidence for at most 20 validated candidates; default response assembly targets 10 items.
- **U05-NFR-005**: Intent conditions, session patches, evidence fields, atomic claims and trace decisions require explicit configurable count/byte limits before parsing or persistence.
- **U05-NFR-006**: Scale review is mandatory above 10 concurrent users, 5 sustained requests/second, 15 burst requests/second, 100,000 approved contents, p95 database pool wait above 100 ms or sustained AI concurrency saturation above 70% for 15 minutes.
- **U05-NFR-007**: Candidate, AI and database concurrency use independent bulkheads; one slow AI request cannot consume all API or U03/U02 read capacity.

## Latency and Throughput

- **U05-NFR-008**: Under normal AI conditions, the end-to-end recommendation API must meet p50 5 seconds, p95 10 seconds and p99 15 seconds, measured at the server boundary.
- **U05-NFR-009**: A deterministic fallback response must meet p95 3 seconds and p99 5 seconds when U03/U04 are healthy.
- **U05-NFR-010**: Intent interpretation has a 3-second total stage budget; explanation drafting has a 5-second total stage budget. Exact connect/read/retry allocation is NFR Design work.
- **U05-NFR-011**: U02/U03 snapshot acquisition, hard filtering, scoring/diversity and pre-draft candidate validation together must meet p95 2 seconds at the 100,000-content boundary.
- **U05-NFR-012**: Final claim validation, safe replacement and response serialization must meet p95 500 ms for 20 items and configured evidence limits.
- **U05-NFR-013**: A refinement or reset runs the complete pipeline and has the same latency target as an initial recommendation; stale-version conflicts return without an AI call.
- **U05-NFR-014**: Load evidence reports p50/p95/p99, throughput, timeout/error/fallback rates, pool wait, stage saturation, candidate counts, evidence size and external-AI latency separately.

## Availability, Reliability and Consistency

- **U05-NFR-015**: U05 participates in the monthly 99.0% prototype objective; normal and degraded successful responses are reported separately.
- **U05-NFR-016**: AI provider timeout, rate limit, unavailable or circuit-open conditions switch to deterministic eligible ranking and approved templates without weakening C11 validation.
- **U05-NFR-017**: U02 feature failure or absent/withdrawn consent yields non-personalized ranking; it cannot fail the safe recommendation path when explicit request context is valid.
- **U05-NFR-018**: U03 unavailability or unknown U04 validation contract fails closed; no cached/model-created candidate may substitute for an unverifiable approved snapshot.
- **U05-NFR-019**: Every external AI call uses explicit connection, response and total deadlines, bounded retries only for safe transient failures, jittered backoff, a concurrency bulkhead and circuit state.
- **U05-NFR-020**: Retry reuses the same request/attempt lineage; it cannot create a second session patch, ranking decision or externally observable duplicate trace.
- **U05-NFR-021**: Identical intent, feature, catalog, policy and rule versions produce identical filter/score/order results. AI text may vary only within validated claim/evidence closure.
- **U05-NFR-022**: Session patch applies by expected version and idempotency key. Duplicate patch converges; stale distinct patch returns a conflict.
- **U05-NFR-023**: Item/claim failure is isolated. Safe siblings remain available, reserve backfill is revalidated and failed draft text never appears in response, logs or templates.
- **U05-NFR-024**: A trace persistence failure never authorizes output or changes validation; the system emits a bounded operational signal and follows the configured audit-critical response policy.

## Recovery and Retention

- **U05-NFR-025**: Durable session versions, requests, ranking decisions, validation results and minimized traces are included in encrypted daily backup with 30-day off-host retention.
- **U05-NFR-026**: Transient prompts, provider responses, chain-of-thought and failed free-text drafts are not backup data and must not be persisted for recovery.
- **U05-NFR-027**: Conversation history is disabled for personalization unless consent permits it; users can reset the active epoch and request deletion through U02 data-rights orchestration.
- **U05-NFR-028**: Default recommendation session history retention is 30 days after last activity, configurable by disclosed policy; consent withdrawal or authorized deletion starts earlier purge/closure.
- **U05-NFR-029**: Restore verification checks session-version monotonicity, reset-epoch isolation, ranking input version references, validation closure, trace minimization and absence of failed draft bodies.
- **U05-NFR-030**: Service re-entry verifies U02/U03/U04 contract compatibility before accepting new requests; incompatible historical rules remain readable for trace explanation but cannot authorize a new response.

## AI Quality and Grounding

- **U05-NFR-031**: All exposed content IDs must be in the referenced approved U03 snapshot and pass every hard condition; the required release gate is 100% over examples, generated properties and evaluation fixtures.
- **U05-NFR-032**: All exposed atomic claims must resolve to same-content approved evidence under the referenced metadata/rule versions; unsupported-claim leakage tolerance is zero in the release gate.
- **U05-NFR-033**: The bilingual intent evaluation set contains at least 100 Korean and 100 English cases, including equivalent pairs, ambiguity, conflicts, negation, runtime boundaries, companions and OTT exclusions.
- **U05-NFR-034**: Canonical hard-condition exact match must be 100% for the safety/eligibility subset and at least 95% across the full curated intent set; a model/parser change cannot reduce either threshold.
- **U05-NFR-035**: Equivalent Korean/English cases must have identical canonical hard-condition values in 100% of the paired release set.
- **U05-NFR-036**: Ranking evaluation records hard-condition pass rate, catalog closure, NDCG@10 or an approved relevance proxy, precision@10, diversity, duplicate/franchise repetition and novelty by cold-start/consented cohort.
- **U05-NFR-037**: A model, prompt-template, scoring, diversity, feature or validation-rule version change requires offline comparison against the active baseline and explicit activation evidence.
- **U05-NFR-038**: AI reason/summary evaluation measures evidence precision, claim coverage, unsupported claim count, spoiler-policy violations, locale correctness and template replacement rate.
- **U05-NFR-039**: Quality is evaluated with click, save, OTT-move, rating, re-recommend and conversational conversion metrics, but no single engagement metric may override hard-condition or grounding safety.
- **U05-NFR-040**: Production feedback is interpreted only by consented cohorts with minimum sample-size/confidence reporting; no protected or directly identifying attribute becomes a ranking feature.

## Core Security and Privacy

- **U05-NFR-041**: AI input is limited to canonical intent, pseudonymous purpose-limited features and allowlisted approved evidence. Email, OAuth subject, session token, IP, raw behavior and free-form profile data are prohibited.
- **U05-NFR-042**: AI provider credentials are file/secret-provider injected, purpose separated, rotated independently and excluded from code, image, `.env`, logs, traces, tests and backups.
- **U05-NFR-043**: AI endpoint scheme/host/port is allowlisted; redirect, response size, decompression, schema depth, token/output and candidate/evidence bounds are enforced.
- **U05-NFR-044**: Recommendation APIs enforce authentication/consent where required, ownership of session IDs, optimistic versioning, request size limits, rate limits and non-enumerating errors.
- **U05-NFR-045**: Recommendation traces contain only pseudonymous references, version IDs, bounded scores and stable reason codes; raw prompts/responses and chain-of-thought are prohibited.
- **U05-NFR-046**: Third-party AI transfer purpose, field categories, retention and provider identity are represented in the U02 consent/notice contract. No transfer occurs outside that permitted purpose.
- **U05-NFR-047**: Consent withdrawal is fail closed for behavior-derived features and conversation-history personalization on the next request; cached feature state cannot extend consent.
- **U05-NFR-048**: Log/metric/trace label allowlists prohibit request text, explanation text, content synopsis, direct/persistent user IDs, provider token and external error bodies.

## Observability and Cost

- **U05-NFR-049**: Metrics include stage latency/outcome, candidate counts, filter reasons, fallback path, circuit/rate state, validation failures, template replacements, trace failures and session conflicts using bounded labels.
- **U05-NFR-050**: Shallow health confirms process liveness. Deep health reports U02 feature, U03 catalog, U04 rule and AI provider status separately; AI degradation does not fail global readiness while deterministic safe fallback is available.
- **U05-NFR-051**: Critical alerts cover hard-condition/catalog/grounding leakage, unknown validation version and privacy-field telemetry. Threshold alerts cover p95 latency, AI error/circuit, fallback rate, trace backlog and validation replacement rate.
- **U05-NFR-052**: Every request records input/output token counts or provider-equivalent usage, estimated cost, evidence size and model version without recording prompt content.
- **U05-NFR-053**: Per-request and daily AI usage limits are configurable. Exceeding a limit opens deterministic fallback rather than failing the whole recommendation capability.
- **U05-NFR-054**: Monetary budgets remain deployment configuration until a provider is selected; activation requires a documented unit price, daily cap, alert threshold and worst-case 10-user load estimate.

## Maintainability, Testing and Usability Contracts

- **U05-NFR-055**: Intent, score, diversity, fallback, prompt-template, model and validation contracts are immutable versions with consumer compatibility and rollback evidence.
- **U05-NFR-056**: Domain/application code remains independent of FastAPI, SQLAlchemy and concrete AI/U02/U03/U04 adapters. C09/C10/C11 boundaries require architecture tests.
- **U05-NFR-057**: Overall measured source coverage remains at least 80%; hard-filter, consent exclusion, claim validation and failed-draft non-leakage branches require 100% coverage.
- **U05-NFR-058**: P-U05-01~12 require Hypothesis domain strategies, shrinking, recorded seed/replay, example companions and stateful session testing.
- **U05-NFR-059**: Contract tests cover U02 feature/consent, U03 approved candidate/evidence, U04 validation predicates, U06 trace view, AI schema and OpenAPI current/previous supported versions.
- **U05-NFR-060**: Real PostgreSQL integration tests cover session concurrency/idempotency, immutable ranking/validation/trace persistence and restore constraints with selected `pytest -m integration` reporting zero skips.
- **U05-NFR-061**: Quality gates include deterministic AI fake transports plus an opt-in provider smoke test that never becomes the sole release evidence or exposes credentials/artifacts.
- **U05-NFR-062**: APIs return localized structured intent/conflict, processing/degraded state, safe items and fallback codes suitable for U01 accessibility; color or free text is never the sole state signal.
- **U05-NFR-063**: Recommendation response and trace schemas remain bounded, documented in OpenAPI/consumer contracts and backward compatible for the previous supported version.

## Verification Handoff

| Requirement group | Mandatory later evidence |
|---|---|
| 001~007 | 10-user load, sustained/burst capacity, bounded candidates/evidence and bulkhead saturation |
| 008~014 | Stage and end-to-end p50/p95/p99, fallback latency and conflict fast path |
| 015~024 | timeout/rate/circuit injection, deterministic fallback, idempotency and isolation |
| 025~030 | retention/purge, backup exclusion, isolated restore and contract re-entry |
| 031~040 | bilingual/relevance/diversity/grounding evaluation and version-change comparison |
| 041~048 | consent/minimization, endpoint/secret/schema bounds and telemetry scans |
| 049~054 | health, metrics, alerts, token/cost accounting and fallback caps |
| 055~063 | architecture, coverage, PBT, consumer/OpenAPI and PostgreSQL `skip=0` gates |

## Extension Compliance

### Resiliency Baseline

| Rule | Status | U05 treatment |
|---|---|---|
| RESILIENCY-01 | Compliant | High safety workload and degradable AI stages are separated |
| RESILIENCY-02 | Compliant | 99.0%, RTO 4 hours, RPO 24 hours and Backup and Restore retained |
| RESILIENCY-03 | Compliant | Versioned model/prompt/policy/rule activation and comparison evidence |
| RESILIENCY-04 | Compliant | Inherits versioned deployment/rollback; schema/policy compatibility is a gate |
| RESILIENCY-05 | Compliant | Stage, fallback, validation, privacy and trace alert requirements |
| RESILIENCY-06 | Compliant | Layered health separates hard dependencies from AI degradation |
| RESILIENCY-07 | Compliant | Latency, saturation, fallback, quality and cost monitoring defined |
| RESILIENCY-08 | N/A | Approved single-server prototype; production transition must reassess multi-zone |
| RESILIENCY-09 | N/A | No autoscaling at prototype scale; numeric capacity/review triggers are defined |
| RESILIENCY-10 | Compliant | AI timeouts, bounded retry, bulkhead, circuit and safe fallback required |
| RESILIENCY-11 | Compliant | Backup and Restore remains the selected DR strategy |
| RESILIENCY-12 | Compliant | Minimized durable U05 state included; transient AI content excluded |
| RESILIENCY-13 | Compliant | Restore closure and contract-compatible re-entry specified |
| RESILIENCY-14 | Compliant | Failure, restore, consent and model-change tests are mandatory handoff evidence |
| RESILIENCY-15 | Compliant | Stable codes, versioned traces and quality comparison support correction |

### Property-Based Testing

- PBT-01: compliant handoff from the twelve approved U05 properties.
- PBT-09: compliant through the locked pytest 9.1.1 and Hypothesis 6.161.5 stack.
- PBT-02~08 and PBT-10: planned as blocking Code Generation/Build and Test evidence; not executable at this documentation stage.

### Security Baseline

Disabled and N/A as an extension. U05-NFR-041~048 remain mandatory core privacy/security controls.

No blocking enabled-extension finding remains at U05 NFR Requirements.
