# U05 Recommendation and AI Grounding NFR Design Patterns

## End-to-End Deadline and Cancellation

One monotonic deadline is created at API admission and passed through every U05 component. A stage may use only its remaining budget and must not start an external call when the response reserve would be violated.

| Stage | Normal maximum | Design behavior |
|---|---:|---|
| Admission, session and consent-qualified context | 500 ms | Bounds, ownership, idempotency and U02 snapshot |
| AI intent interpretation | 2,750 ms | Includes connect/read and at most one safe retry |
| U03/U04 snapshot, hard filter, scoring, diversity and candidate validation | 1,500 ms | Pure bounded work plus read ports |
| AI grounded drafting | 4,250 ms | Includes connect/read and at most one safe retry when budget permits |
| Final claim validation and safe response assembly | 500 ms | No external AI call |
| Response reserve | 500 ms | Serialization, cancellation and fallback margin |

The total is 10 seconds. A stage ending early donates time to the reserve, not to unbounded retries. Client cancellation propagates to pending AI/U02/U03 calls; committed session patches and validation records remain durable.

Deterministic fallback avoids both AI stages and targets p95 3 seconds. A stale session version is rejected during admission without catalog or AI work.

## AI Adapter Resilience

### Timeouts and Retry

- Connect timeout: 300 ms per attempt.
- Intent response/read allowance: first attempt up to 2,100 ms; one retry is allowed only for connection failure, rate-limit without a prohibitive `Retry-After`, or no-response transient failure and only when at least 900 ms plus response reserve remains.
- Draft response/read allowance: first attempt up to 3,400 ms; one retry is allowed only when at least 1,200 ms plus response reserve remains.
- Retry backoff uses deterministic-testable bounded jitter between 50 and 150 ms.
- Schema, policy, authentication, size, unsupported-model and partial-response failures are not retried in the user request.
- Every retry keeps the same request/attempt lineage and never reapplies a session patch.

### Bulkhead and Circuit

The API process begins with an AI semaphore of 4 calls, leaving request capacity for rule-based fallback and non-AI endpoints. Intent and drafting share the provider circuit but expose separate stage metrics. Queue wait is bounded to 100 ms; saturation opens fallback rather than waiting behind the full external timeout.

The initial circuit window is 20 completed calls. A failure ratio at or above 50% opens the circuit for 30 seconds; two half-open probes determine recovery. Provider authentication/schema incompatibility opens immediately and requires configuration correction rather than automatic probing. Exact values remain typed configuration and are load/failure tested before activation.

### Degradation Matrix

| Condition | Response path |
|---|---|
| AI intent available | Structured intent and normal pipeline |
| AI intent unavailable, deterministic parser recognizes explicit bounded conditions | Confirm recognized conditions, rule ranking and approved templates |
| AI intent unavailable, request has no safely recognized condition | Safe dependency response requesting structured refinement; no guessed hard condition |
| AI drafting unavailable | Existing eligible rank plus approved localized templates |
| AI usage cap reached | Same deterministic fallback as provider circuit open |
| U02 features unavailable/consent absent | Non-personalized scoring; AI receives no behavior context |
| U03 catalog unavailable | Fail closed; no recommendation item |
| U04 rule contract unknown/incompatible | Fail closed; no recommendation item |

## Bounded Data and Backpressure

Admission enforces maximums before nested object construction: 4 KiB request text, 32 intent conditions, 32 patch operations, 1,000 fetched candidates, 500 scored candidates, 100 reserves, 20 exposed items, 20 evidence bundles, 32 fields and 64 atomic claims per item, 256 KiB AI response and 512 KiB complete internal response object. NFR Design values are initial configuration defaults; lowering them is backward compatible, while increases require latency/cost/security evidence.

Candidate processing uses bounded pages and iterators. The ranker holds compact immutable value objects rather than ORM rows or raw metadata. Evidence bundles are built only after candidate validation and contain allowlisted fields.

Backpressure order is: reject stale session conflict, reject request-rate excess, use non-personalized context when U02 is unavailable, enter AI fallback on AI semaphore/circuit/usage saturation, and return fail-closed unavailable only for U03/U04 hard-dependency loss. Queueing never exceeds the remaining deadline.

## Database Pool and Transaction Isolation

U05 initially reserves at most two shared PostgreSQL API connections per process with a 100 ms acquisition target and a 5-second statement timeout. Candidate reads occur through U03 ports and return detached immutable snapshots. External AI calls never run inside a database transaction.

Transactions are short and purpose-specific:

1. Session patch transaction: validate expected version/idempotency key, append immutable patch/version and commit.
2. Request-open transaction: store version references and initial trace marker.
3. Decision-close transaction: atomically store ranking run, candidate decisions, validation closure, safe response metadata and trace outcome.
4. Retention transaction: claim a bounded batch and purge/close eligible session/trace state with checkpoints.

The response assembler consumes only a committed or in-memory validation closure. A trace-write operational failure cannot convert rejected data into a safe item. The configured audit-critical policy may return the already-safe response with an incomplete-trace alert, but it cannot bypass closure.

## Session Concurrency and Idempotency

`RecommendationSession` uses `(session_id, epoch, version)` optimistic concurrency and a unique `(session_id, idempotency_key)` patch constraint. Duplicate same-key requests return the stored version/result reference. A different patch against a stale expected version returns conflict before any AI call.

Reset increments the epoch and closes the previous one atomically. Queries always specify the active epoch. Retention/deletion uses fencing/checkpoints so replay cannot reopen a closed epoch. Stateful P-U05-11 compares random patch/reset sequences to a simple reference map after every command.

## Deterministic Ranking and Policy Activation

Intent, score, diversity, fallback and validation policies are immutable versioned records. A policy candidate progresses through `draft`, `evaluated`, `active`, `superseded` or `rejected`. Activation uses compare-and-swap on the current active version and stores evaluation evidence.

The ranking engine is pure: hard-filter closure, bounded score components, normalized non-negative weights, stable ties and diversity subset invariants are verified independently of persistence. A previous active policy remains available for immediate pointer rollback. Historical policy versions are trace-readable but never silently reactivated.

No correctness cache stores consent, approval, availability, score or validation decisions. Optional local memoization is limited to immutable parser dictionaries and approved templates keyed by version.

## Model, Prompt and Quality Activation Gate

An `AIConfigurationVersion` binds provider, model, intent schema, prompt-template, evidence schema, output schema, price metadata and activation status. Secrets are referenced by name only. A candidate version cannot activate until it passes:

- at least 100 Korean and 100 English curated intent cases;
- 100% hard-condition exact match on the safety subset;
- at least 95% canonical intent exact match overall;
- 100% equivalent-pair hard-condition parity;
- 100% catalog/hard-filter closure and same-content evidence precision;
- zero unsupported exposed claims and zero failed-draft leakage;
- latency, schema-size, fallback and configured cost caps;
- comparison against the active baseline with no safety regression.

Live-provider smoke tests are opt-in supplementary evidence. Deterministic fake transport and fixture evaluation are always required. Activation/rollback changes only a version pointer after compatibility evidence is stored.

## Claim-Level Validation Closure

Candidate validation occurs before evidence construction and again before serialization. Claim results form a complete matrix for every atomic claim. Missing, unknown, error and mismatched-content results are failures.

Safe output construction accepts only:

- validated candidate plus fully validated draft;
- validated candidate plus an approved template generated from the same evidence bundle; or
- a validated reserve candidate processed through the same pipeline.

Failed free text is discarded immediately after a bounded digest/reason result and is prohibited from logs, traces, templates and backups. No exception handler serializes a draft type. Architecture and contract tests enforce this type boundary.

## Consent and Privacy Propagation

Each request reads a versioned U02 consent-qualified feature snapshot. The snapshot carries purpose, consent version, feature definition, observed-at and expiry. U05 rejects direct identifiers or raw history at its port. An expired/withdrawn snapshot becomes an empty non-personalized snapshot before scoring or AI context assembly.

AI context is an allowlist projection of canonical intent and candidate-local evidence. Provider transfer metadata records purpose and field categories without prompt content. Logs/metrics/traces use bounded enums and pseudonymous request references; request text, synopsis, draft text, direct user ID, token, provider error body and chain-of-thought are structurally excluded.

## Retention, Backup and Restore Re-entry

Active/session history defaults to 30 days since last activity. Consent withdrawal, reset scope and U02-authorized deletion can close or purge earlier. Daily encrypted backup includes session versions, minimized request/ranking/validation/trace state and policy/config versions. It excludes prompt/response bodies, failed drafts, secrets and provider transient data.

Restore re-entry checks schema head, session version monotonicity, epoch closure, idempotency uniqueness, ranking input references, complete validation matrices, safe response closure, trace field allowlist and U02/U03/U04 contract compatibility. AI stays degraded until configuration compatibility passes; new recommendations remain closed if U03/U04 cannot be verified.

## Observability, Health and Cost Control

Metrics use bounded stage/outcome/reason/policy/model labels. Histograms cover admission, intent, snapshot, filter/score/diversity, drafting, validation, assembly and total latency. Gauges/counters cover AI semaphore wait, circuit state, token/usage units, estimated cost, candidate/evidence counts, fallback, template replacement, trace backlog and session conflicts.

Shallow health is process-only. Readiness requires U03 and compatible U04 rules; U02 feature/AI failures report degraded components while safe non-personalized/fallback paths remain ready. Deep health probes each dependency with a bounded non-user-data request.

Immediate safety alerts cover catalog/hard-condition/grounding leakage, unknown validation version and prohibited telemetry fields. Threshold alerts cover total p95 above 10 seconds, fallback p95 above 3 seconds, AI failure/circuit/fallback rate, semaphore saturation, trace backlog, template replacement and daily usage cap. Cost-cap exhaustion deliberately opens fallback.

## Verification Pattern Matrix

| Pattern | Required verification |
|---|---|
| Deadline/retry/circuit | Fake-clock/transport tests, cancellation and failure injection |
| Bounds/backpressure | Boundary examples, generated oversized inputs and 10-user load |
| Ranking policy | P-U05-04~08, oracle comparison and deterministic replay |
| Session CAS/idempotency | Concurrent PostgreSQL tests and stateful P-U05-11 |
| Evidence/closure | P-U05-09~10, complete-matrix and serialization non-leakage tests |
| Fallback | P-U05-12 plus AI timeout/rate/circuit/usage-cap examples |
| Consent/privacy | withdrawal race, expired snapshot and telemetry/backup scans |
| Recovery | isolated restore, epoch/version/reference/closure verification |
| Quality activation | curated bilingual fixtures and baseline comparison |

Overall coverage must remain at least 80%. Hard-filter, consent exclusion, claim validation and failed-draft non-leakage branches require 100%. Selected real PostgreSQL integration tests must report zero skips.

## Extension Compliance

RESILIENCY-01~02 are reflected by criticality and inherited targets; RESILIENCY-03~04 by versioned activation/rollback; RESILIENCY-05~07 by metrics, alerts and layered health; RESILIENCY-08~09 retain approved prototype N/A exceptions with numeric transition triggers; RESILIENCY-10 by AI isolation/fallback; RESILIENCY-11~13 by Backup and Restore closure; RESILIENCY-14 by failure/recovery/model-change verification; RESILIENCY-15 by stable traces and evaluation evidence.

PBT-01 properties are assigned to concrete patterns. PBT-02~08 and PBT-10 are mandatory Code Generation evidence. PBT-09 remains compliant through locked Hypothesis. Security Baseline is disabled; core consent, secret, egress, bounds and telemetry controls remain blocking.

No blocking enabled-extension finding remains.
