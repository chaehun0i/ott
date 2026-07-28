# U04 Ingestion and Metadata Governance Business Logic Model

## Scope and Boundary

U04 owns provider synchronization, raw-payload governance, normalization, canonical identity matching, source-aware merging, metadata validation, quarantine, revalidation and the publication decision lifecycle. Only a passed decision may call U03 `ApprovedCatalogWritePort`.

U04 does not write U03 approved catalog tables, answer user catalog queries, rank recommendations, generate AI text, validate generated claims or apply operator overrides. U05 consumes only the versioned read-only `ValidationRuleContract`; U06 owns operator actions and audit; U07 supplies worker, job, persistence and adapter runtime.

## Decision Summary

| Concern | Selected policy |
|---|---|
| Canonical identity | Deterministic identifier tiers, then normalized title, year and type; ambiguous matches are quarantined |
| Merge precedence | Versioned field-specific source authority, license scope, locale and freshness; every source value is preserved |
| Batch failure | Record-level isolation; valid records progress and invalid records quarantine; job may complete as partial success |
| Provider deletion | Persist a source tombstone, recompute merged support and withdraw only when no valid authoritative source remains |
| Quarantine return | Automatic revalidation on source or rule-version change plus authorized manual retry |
| Unknown license/freshness | Fail closed and quarantine until both are provable |
| U03 publication failure | Durable `passed_pending_publication`; idempotent retry; `published` only after CatalogVersion receipt |
| Raw retention | Versioned provider-specific policy; retain provenance and digest after allowed payload retention expires |
| U05 rule sharing | Versioned read-only approval, identifier, license, freshness and regional-availability predicates only |

## End-to-End Pipeline

1. The scheduler creates or resumes an `IngestionJob` for one provider and provider cursor. The logical key `(provider_id, provider_cursor, policy_version)` prevents duplicate active work.
2. The worker claims a bounded page and invokes the provider adapter under the provider's usage, attribution, regional, retention and request-limit policy.
3. Each received record becomes an immutable `RawMetadataRecord` with payload digest, retrieval facts, provider record ID and applicable retention policy. A repeated digest for the same provider record is an idempotent observation.
4. Normalization maps raw fields to the internal canonical schema without discarding source values. A deterministic normalization version identifies the transformation.
5. Identity resolution evaluates authoritative IDs in declared order. If none match, it evaluates the normalized title, release year and content type tuple. Zero matches creates a new canonical identity candidate, one unambiguous match selects it and multiple or conflicting matches quarantine the record.
6. The merge policy evaluates each field independently using versioned source authority, license scope, locale and freshness. The selected value keeps its source reference; rejected alternatives remain queryable as provenance.
7. Validation runs a fixed fail-closed sequence: schema, required fields, provenance, license, freshness, canonical identifier consistency, locale, regional availability and OTT link scope. Every rule emits a structured result under one `ValidationRuleVersion`.
8. A failed result creates or updates a `QuarantineRecord` with stable reason codes and never calls U03. A passed result creates a `ValidationDecision` in `passed_pending_publication`.
9. The publication dispatcher calls U03 `ApprovedCatalogWritePort` with an idempotency key derived from the decision ID and version. Success stores the returned CatalogVersion and transitions the decision to `published`.
10. Provider tombstones recompute source support. U04 sends a validated withdrawal command only when no currently valid authoritative source supports the content or affected regional availability.
11. The job advances its durable cursor only after every record in the claimed page reaches a durable terminal or retryable state. It completes as `succeeded`, `partially_succeeded` or `failed` with counts by outcome.

## Record Processing State Model

| Current state | Event | Next state | Guarantee |
|---|---|---|---|
| received | raw persisted | raw_stored | Payload digest and provenance exist |
| raw_stored | normalization succeeds | normalized | Normalization version is recorded |
| raw_stored | normalization fails | quarantined | Stable reason code exists |
| normalized | identity and merge succeed | validation_pending | Every chosen field has provenance |
| normalized | identity is ambiguous | quarantined | No canonical merge is applied |
| validation_pending | any validation rule fails | quarantined | U03 is never invoked |
| validation_pending | all rules pass | passed_pending_publication | Immutable passed decision exists |
| passed_pending_publication | U03 succeeds | published | CatalogVersion is recorded |
| passed_pending_publication | U03 transiently fails | passed_pending_publication | Retry does not repeat validation |
| quarantined | source or rule version changes | validation_pending | A new validation run is linked to prior history |
| quarantined | authorized retry | validation_pending | Actor and reason are recorded |
| published | valid tombstone removes final support | withdrawal_pending | Prior approved revision remains until U03 accepts withdrawal |
| withdrawal_pending | U03 succeeds | withdrawn | Withdrawal CatalogVersion is recorded |

Terminal states are historical facts, not destructive updates. Reprocessing creates a new attempt and preserves earlier raw, normalized, validation and quarantine evidence.

## Canonical Identity and Merge Flow

Identity tiers are evaluated in deterministic order defined by `IdentityPolicyVersion`:

1. Provider-specific immutable work ID mapped through an approved crosswalk.
2. Shared authoritative external ID plus compatible content type.
3. Normalized original title, release year and content type.

Conflicting authoritative IDs or more than one candidate at the same decisive tier produce `IDENTITY_AMBIGUOUS`. Fuzzy similarity may be recorded as review evidence but cannot auto-merge.

For each field, `MergePolicyVersion` selects among valid candidates by source authority, legal scope for the target use, locale fit, freshness and a stable provider ID tie-breaker. Merge order cannot change the result. The merged representation includes a field-level evidence map and does not erase losing values.

## Validation and Quarantine Flow

Validation is complete only when every mandatory rule returns pass. Unknown is not pass. A rule can be not applicable only when its versioned applicability predicate proves that status.

Quarantine reason families are:

- `SCHEMA_*`: malformed type, required field or normalization failure.
- `PROVENANCE_*`: missing provider record, attribution or source evidence.
- `LICENSE_*`: unknown, expired or incompatible storage/display rights.
- `FRESHNESS_*`: missing observation time or policy threshold exceeded.
- `IDENTITY_*`: mismatch, collision or ambiguous canonical match.
- `AVAILABILITY_*`: invalid region, OTT, time window or outbound link scope.
- `PUBLICATION_*`: reserved for non-transient contract conflicts; transient U03 outages remain pending publication rather than quarantine.

Quarantined data is absent from U03 commands, U03 projections and U05 contracts. A new raw version, a new validation-rule version or an authorized retry creates a new validation attempt. Repeating the same attempt key is a no-op.

## Publication and Withdrawal Contract

`PassedValidation` includes canonical content ID, normalized version, selected fields, field provenance, verified availability, source/license assertions, rule version, validation time and decision ID. It excludes raw payloads and quarantine details.

U03 publication is an independently committed operation. U04 therefore retains a durable pending decision and retries with the same idempotency key. A timeout is treated as an unknown outcome: U04 queries or retries the same command rather than creating a new decision. Only the returned CatalogVersion proves publication.

For deletion, an individual provider tombstone removes that source's support. The merged aggregate and availability are recalculated. A withdrawal command is emitted only for the content or regional availability no longer supported by any valid authoritative source.

## ValidationRuleContract for U05

The contract is immutable per version and exposes pure predicates for:

- approved state and metadata version compatibility;
- canonical content identifier validity;
- license validity for the requested use;
- freshness under a named policy and evaluation time;
- regional OTT availability and time-window validity.

It does not expose provider payloads, normalization adapters, merge internals, quarantine records or operator data. U05 records the exact contract version used, while U04 remains the sole owner of rule publication.

## Failure Isolation and Recovery

- One malformed record cannot roll back valid records from the same provider page.
- Provider failures stop only that provider's worker budget; other providers continue.
- A failed sync never deletes the last published U03 revision.
- Cursor advancement occurs after durable record outcomes, allowing replay without omission.
- Retryable provider and U03 failures use bounded attempts supplied by later NFR design; exhausted work remains durable for operator recovery.
- Raw expiry removes only the permitted payload body. Digest, provenance, policy and derived history remain.
- Replay from the last durable cursor and re-dispatch of pending publications are deterministic and idempotent.

## Required Functional Signals

The design emits non-sensitive facts required by later observability work: job outcome and duration, provider rate-limit state, records by pipeline state, quarantine reasons, oldest pending publication, cursor age, validation-rule version, replay count and withdrawal count. Health semantics distinguish process health, provider degradation, queue backlog and U03 publication dependency failure.

## Testable Properties (PBT-01)

| ID | Component | Category | Property |
|---|---|---|---|
| P-U04-01 | Raw codec | Round-trip | Encoding then decoding any valid raw envelope preserves provider ID, record ID, digest and retrieval facts |
| P-U04-02 | Normalizer | Idempotence | Normalizing an already normalized representation under the same version yields the same value |
| P-U04-03 | Normalizer | Invariant | Normalization preserves all source field references and never invents an authoritative identifier |
| P-U04-04 | Identity resolver | Oracle | Tiered resolution equals a simple reference evaluator for generated crosswalks and candidate sets |
| P-U04-05 | Merge policy | Commutativity | Permuting provider input order does not change selected values or provenance |
| P-U04-06 | Merge policy | Invariant | Every input source value remains represented and every selected field references one valid source candidate |
| P-U04-07 | Validator | Invariant | A decision passes if and only if every applicable mandatory rule passes; unknown never passes |
| P-U04-08 | Quarantine boundary | Easy verification | No failed or ambiguous decision can produce an ApprovedCatalogWritePort command |
| P-U04-09 | Publication dispatcher | Idempotence | Replaying the same passed decision produces at most one observable U03 catalog transition |
| P-U04-10 | Job state machine | Stateful/model | Random claim, retry, quarantine, revalidate and publish sequences match a simplified reference state machine |
| P-U04-11 | Tombstone merge | Invariant | Removing one source cannot withdraw content while another valid authoritative source still supports it |
| P-U04-12 | Cursor replay | Idempotence | Replaying a durable page yields equivalent terminal record states and does not skip later records |

These properties must be referenced by the U04 code-generation plan. Domain-specific generators must cover Unicode titles, locale variants, conflicting IDs, boundary timestamps, empty availability, source permutations, duplicate deliveries and rule-version changes.

## Traceability

| Requirement or story | Functional coverage |
|---|---|
| US-020 | State-tracked collection, normalization, validation, quarantine and bounded reprocessing |
| FR-006, DR-006 | Last successful collection, source and quality/freshness status |
| FR-030~FR-032 support | Source values and precedence preserved; U06 override remains outside U04 |
| FR-039~FR-041 support | Versioned shared predicates and fail-closed boundary for U05; claim validation remains U05-owned |
| DR-001~DR-002 | Provider legality, attribution, retention and regional policy gating |
| DR-003~DR-004 | Canonical normalization, provenance-preserving deterministic merge |
| DR-005 | Provider cursor, request-limit awareness and durable reprocessing |
| DR-009~DR-011 | Raw, normalized, pending, published and quarantined states with rule version and reason codes |
| DR-012, AC-014 | Only U03-published passed metadata becomes recommendation eligible |

## Extension Compliance

### Resiliency Baseline

| Rule | Status | Functional-design rationale |
|---|---|---|
| RESILIENCY-01 | Compliant | U04 is High criticality; outage delays freshness but the last approved catalog remains available; U03 and U07 dependencies are explicit |
| RESILIENCY-02 | Compliant | Inherits approved hours-level RTO/RPO and backup/restore strategy; durable cursors and decisions bound recoverable work |
| RESILIENCY-03 | Compliant | Inherits the documented prototype exemption; rule, policy and decision versions preserve change history |
| RESILIENCY-04 | Compliant | Inherits version-pinned redeploy rollback and direct deployment; contracts and state transitions are version compatible |
| RESILIENCY-05 | Compliant | Required metrics, logs and correlation facts are enumerated without selecting infrastructure |
| RESILIENCY-06 | Compliant | Shallow, queue/provider and U03 dependency health semantics are defined for later implementation |
| RESILIENCY-07 | Compliant | Cursor age, backlog, oldest pending publication, quarantine and rate-limit degradation signals are required |
| RESILIENCY-08 | N/A | Deployment topology is outside technology-agnostic Functional Design; the approved single-server prototype exception is inherited |
| RESILIENCY-09 | N/A | Auto-scaling and service quotas are NFR/Infrastructure Design concerns, not business logic |
| RESILIENCY-10 | Compliant | Provider isolation, bounded retry handoff, durable pending state and last-valid-catalog degradation prevent cascading failure |
| RESILIENCY-11 | Compliant | Inherits Backup and Restore; deterministic replay defines U04 recovery behavior |
| RESILIENCY-12 | Compliant | Identifies raw, cursor, decision, quarantine and policy state that must be protected; retention limits raw payload scope |
| RESILIENCY-13 | Compliant | Cursor replay, pending-publication dispatch and revalidation procedures define recoverable transitions |
| RESILIENCY-14 | Compliant | Replay, duplicate delivery, dependency outage and rule-change scenarios are captured as property and recovery tests |
| RESILIENCY-15 | Compliant | Stable reason codes, version history and required operational signals support incident detection and learning |

No blocking Resiliency finding remains at this stage.

### Property-Based Testing

| Rule | Status | Functional-design rationale |
|---|---|---|
| PBT-01 | Compliant | Twelve categorized properties are identified per functional component and carried forward |
| PBT-02~PBT-10 | N/A | These rules are enforced in their designated later NFR, Code Generation and Build and Test stages |

No blocking PBT finding remains at this stage.

### Security Baseline

Disabled by the approved Extension Configuration. Core authorization for manual retry, minimization of shared contracts and non-sensitive operational signals remain normal project requirements.
