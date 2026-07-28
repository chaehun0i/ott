# U04 Ingestion and Metadata Governance Functional Design Plan

## Context

- Unit: U04 Ingestion and Metadata Governance
- Components: C05 Content Ingestion, C06 Metadata Validation
- Service: S07 ContentIngestionService
- Primary story: US-020
- Supporting requirements: FR-006, FR-030~FR-032, FR-039~FR-041, DR-001~DR-006, DR-009~DR-012, AC-014
- Required dependencies: U03 ApprovedCatalogWritePort, U07 worker runtime, provider adapter and job store
- Enabled extensions: Resiliency Baseline (Full), Property-Based Testing (Full)
- Disabled extension: Security Baseline; skipped while core authentication, authorization and privacy requirements remain applicable

## Execution Steps

- [x] Read U04 unit scope, ownership, dependencies and construction sequence.
- [x] Read US-020 acceptance criteria and supporting requirement traceability.
- [x] Read U03 ApprovedCatalogWritePort lifecycle and closure contract.
- [x] Evaluate enabled Resiliency and Property-Based Testing extension requirements for Functional Design.
- [x] Identify unresolved functional decisions that materially affect the domain model and business rules.
- [x] Create context-specific decision questions using the required answer format.
- [x] Validate every answer and check for contradictions or ambiguity.
- [x] Generate `business-logic-model.md` with ingestion, normalization, validation, quarantine and publication flows.
- [x] Generate `business-rules.md` with rule precedence, state transitions, error outcomes and validation constraints.
- [x] Generate `domain-entities.md` with entity ownership, relationships, identifiers, versions and lifecycle invariants.
- [x] Document PBT-01 testable properties by component and carry them into the future code-generation plan.
- [x] Evaluate RESILIENCY-01~15 and PBT-01 compliance; resolve all blocking findings.
- [x] Validate Markdown and any embedded diagrams before writing final artifacts.
- [x] Update this plan, `aidlc-state.md` and `audit.md`, then present the standardized approval message.

## Functional Design Questions

Please enter one letter after every `[Answer]:` tag. Choose `X` and add a description if none of the listed policies match.

### Question 1: Canonical identity and duplicate matching

How should records from different providers be matched to the same canonical content?

A) Use deterministic identifier tiers first, then normalized title, release year and type; quarantine ambiguous matches for operator review

B) Merge only records sharing an authoritative external identifier; keep all other records separate

C) Use confidence-scored automatic matching and merge every record above a configured threshold

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

### Question 2: Field-level source precedence

When providers disagree about a metadata field, which merge policy should apply?

A) Use a versioned field-specific precedence policy based on source authority, license scope, locale and freshness, while preserving every source value

B) Use the most recently collected valid value for every field

C) Designate one primary provider whose value always wins when present

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

### Question 3: Batch partial failure

How should a provider synchronization job behave when only some records fail normalization or validation?

A) Process each record independently, publish valid records, quarantine invalid records and complete the job with a partial-success summary

B) Treat the whole provider batch atomically and publish nothing if any record fails

C) Allow partial success only while the failure ratio remains below a versioned threshold; otherwise hold the batch for review

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

### Question 4: Provider deletion and withdrawal signals

What should happen when a provider reports that content or regional availability was removed?

A) Record a source tombstone, recompute the merged record and request U03 withdrawal only when no valid authoritative source still supports visibility or availability

B) Immediately request U03 withdrawal whenever any provider reports removal

C) Never withdraw automatically; quarantine every deletion signal for operator approval

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

### Question 5: Quarantine revalidation

How should quarantined records return to the pipeline?

A) Revalidate automatically when source data or the validation-rule version changes, and also allow an authorized manual retry

B) Revalidate only through an authorized manual operation

C) Revalidate automatically on a fixed schedule regardless of whether data or rules changed

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

### Question 6: Unknown license or freshness state

How should records with an unknown license status or an unprovable freshness state be handled?

A) Fail closed and quarantine the record until both states are provable under the provider policy

B) Permit approval with a degraded data-quality status and let U03 display a warning

C) Permit approval only for non-link descriptive fields while blocking availability and outbound viewing links

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

### Question 7: Passed validation when U03 publication fails

What state should U04 expose when validation passes but the U03 ApprovedCatalogWritePort call fails temporarily?

A) Store a durable `passed_pending_publication` decision, retry idempotently and mark `published` only after U03 returns a CatalogVersion

B) Roll the record back to normalized state and repeat validation on every retry

C) Move the record to quarantine with a publication-failure code and require manual retry

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

### Question 8: Raw metadata retention

How should raw provider payload retention be governed?

A) Apply a versioned provider-specific retention policy derived from license terms; retain provenance and a digest after payload expiry

B) Retain every raw payload indefinitely for reproducibility

C) Delete raw payloads immediately after normalization and retain only normalized metadata

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

### Question 9: ValidationRuleContract shared with U05

Which part of U04 validation policy should U05 consume for recommendation output validation?

A) A versioned, read-only contract containing shared approval, identifier, license, freshness and regional-availability predicates, without ingestion internals

B) The complete U04 rule implementation including provider normalization and quarantine rules

C) Only the current rule-version identifier; U05 independently implements equivalent validation logic

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Planned Artifacts

- `aidlc-docs/construction/u04-ingestion-and-metadata-governance/functional-design/business-logic-model.md`
- `aidlc-docs/construction/u04-ingestion-and-metadata-governance/functional-design/business-rules.md`
- `aidlc-docs/construction/u04-ingestion-and-metadata-governance/functional-design/domain-entities.md`

## Preliminary Extension Assessment

### Resiliency Baseline

- RESILIENCY-01~04: inherited project workload classification, RTO/RPO, lightweight change process and version-pinned direct deployment decisions will be referenced; detailed U04 failure impact remains to be documented.
- RESILIENCY-05~10: ingestion metrics, health, capacity, bounded dependency calls, isolation and degradation behavior must be reflected where relevant; infrastructure mechanics remain for later NFR and Infrastructure Design stages.
- RESILIENCY-11~15: project backup/restore, recovery testing and incident decisions are inherited; U04 must define recoverable durable state and replay behavior without inventing new infrastructure.
- Current status: pending final artifact evaluation; no finding is closed before answer validation and artifact generation.

### Property-Based Testing

- PBT-01 applies in this stage.
- Candidate properties: normalization idempotence, serialization round-trip, merge element/provenance preservation, deterministic merge, quarantine non-leakage, replay idempotence and state-machine equivalence.
- PBT-02~10 are carried forward to NFR Requirements, Code Generation and Build and Test as defined by the extension enforcement table.
- Current status: pending formal per-component property identification in the final artifacts.
