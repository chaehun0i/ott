# U04 Ingestion and Metadata Governance Business Rules

## Rule Conventions

All decisions are evaluated against explicit policy versions and an evaluation time. A missing, unknown or contradictory mandatory fact is a failure, never an implicit pass. Stable rule IDs and reason codes are persisted with every validation attempt.

## Provider and Collection Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| ING-01 | A provider must have an active policy covering legal source, attribution, allowed storage, display use, regions, refresh schedule and request limits before a job can run. | Reject job configuration |
| ING-02 | `(provider_id, provider_cursor, policy_version)` identifies one logical synchronization page; duplicate claims must converge on the same outcomes. | Idempotent no-op or resume |
| ING-03 | A cursor advances only after all records in the claimed page have durable outcomes. | Keep cursor and retry unresolved records |
| ING-04 | Each record is isolated. One record failure cannot roll back valid sibling records. | Quarantine failed record; job becomes partial success |
| ING-05 | Provider request-limit and retry-after signals have precedence over scheduling demand. | Defer provider work |
| ING-06 | A provider outage or exhausted retry budget cannot withdraw the last valid approved catalog revision. | Preserve U03 state and expose stale/degraded ingestion status |
| ING-07 | A repeated provider record with an unchanged payload digest and policy version does not create a new normalization or validation result. | Return existing outcome |

## Raw Data and Retention Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| RAW-01 | Every raw record stores provider ID, provider record ID, retrieval time, payload digest, policy version and cursor reference. | Quarantine as provenance failure |
| RAW-02 | Payload bodies are retained only for the duration and purpose allowed by the provider-specific retention policy. | Block collection if no lawful handling policy exists |
| RAW-03 | Payload expiry removes the body but preserves digest, provenance, policy reference and derived lineage. | Scheduled governed expiry |
| RAW-04 | Raw payloads and quarantine details never appear in U03 publication or U05 ValidationRuleContract. | Contract validation failure |
| RAW-05 | A tombstone is an immutable source observation and must not erase prior lineage. | Append tombstone history |

## Normalization Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| NORM-01 | A normalization run is identified by raw record ID and normalization version. | Duplicate run returns existing result |
| NORM-02 | Normalization must be deterministic and idempotent under the same version. | Quarantine as normalization defect |
| NORM-03 | Unicode normalization, locale tags, time zones, durations, dates, content types, regions and OTT IDs use canonical internal forms. | Quarantine invalid fields |
| NORM-04 | Source values and their field paths are preserved even when the normalized value differs. | Quarantine missing lineage |
| NORM-05 | Normalization cannot manufacture an authoritative ID, license grant, availability or attribution. | Quarantine as unsupported assertion |

## Identity and Merge Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| ID-01 | Identity tiers are authoritative crosswalk, shared authoritative ID, then normalized original title plus release year and type. | Continue to next tier |
| ID-02 | A match must be unique at the decisive tier and content types must be compatible. | `IDENTITY_AMBIGUOUS` quarantine |
| ID-03 | Conflicting authoritative IDs cannot be resolved by title similarity. | `IDENTITY_CONFLICT` quarantine |
| ID-04 | Fuzzy similarity is review evidence only and never an automatic merge authority. | Preserve as candidate evidence |
| MERGE-01 | Field selection uses the applicable `MergePolicyVersion`; global last-write-wins is prohibited. | Reject unversioned merge |
| MERGE-02 | Precedence evaluates source authority, allowed use, locale, freshness and stable provider ID tie-breaker. | Quarantine if no valid candidate remains |
| MERGE-03 | Input order cannot affect merged values or provenance. | Treat as deterministic merge defect |
| MERGE-04 | Every selected field references one retained source candidate, and losing candidates remain preserved. | Reject merged representation |
| MERGE-05 | An authorized U06 override is outside U04 merge ownership and must not be overwritten through direct U04 table access. | Use U03/U06 service contract |

## Validation Rules

Validation order is deterministic for reproducible reporting, but a record passes only when all applicable mandatory rules pass.

| Rule | Pass condition | Failure code family |
|---|---|---|
| VAL-01 Schema | Canonical types, field shapes and cardinalities are valid. | `SCHEMA_*` |
| VAL-02 Required fields | Canonical ID, content type, display title, provenance and required timestamps exist. | `SCHEMA_REQUIRED_*` |
| VAL-03 Provenance | Every selected field and availability assertion resolves to a lawful provider observation. | `PROVENANCE_*` |
| VAL-04 License | Storage, display, attribution and outbound-link use are explicitly permitted at evaluation time. | `LICENSE_*` |
| VAL-05 Freshness | Observation time exists and falls within the versioned provider/category threshold. | `FRESHNESS_*` |
| VAL-06 Identity | Canonical and provider identifiers are internally consistent and unambiguous. | `IDENTITY_*` |
| VAL-07 Region/OTT | Region and OTT IDs are supported and the availability window is well formed. | `AVAILABILITY_*` |
| VAL-08 Link scope | An outbound URL is official, allowed, region-compatible and temporally valid. | `AVAILABILITY_LINK_*` |
| VAL-09 Rule closure | Every applicable mandatory rule is pass; unknown, error or missing is not pass. | `VALIDATION_INCOMPLETE` |

Unknown license or unprovable freshness always quarantines the record. The degraded display of an already approved stale revision is owned by U03 and does not authorize U04 to publish a newly unproven revision.

## Quarantine and Revalidation Rules

| Rule | Definition |
|---|---|
| QR-01 | A quarantined record stores the failed decision, all reason codes, rule version, evaluated time and lineage references. |
| QR-02 | Quarantine is a non-public state and cannot call U03 publication or enter U03/U05 projections. |
| QR-03 | A changed raw version or ValidationRuleVersion automatically creates a new revalidation attempt. |
| QR-04 | An authorized manual retry requires actor, reason and target rule version; it creates history rather than mutating the failed run. |
| QR-05 | Repeating the same revalidation attempt key returns the existing outcome. |
| QR-06 | Successful revalidation does not delete or relabel the original quarantine event. |

## Publication and Withdrawal Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| PUB-01 | Only an immutable passed decision can construct `PassedValidation`. | Block command creation |
| PUB-02 | Decision ID plus decision version is the U03 idempotency key. | Reuse existing result |
| PUB-03 | A passed decision remains `passed_pending_publication` until U03 returns a CatalogVersion. | Retry without revalidation |
| PUB-04 | A timeout or unknown result cannot create a replacement decision. | Query or retry same command |
| PUB-05 | A U03 version conflict is classified as non-transient and requires deterministic reconciliation, not blind retry. | Hold for reconciliation |
| PUB-06 | A provider tombstone removes only that provider's support. | Recompute merged support |
| PUB-07 | Content withdrawal occurs only when no valid authoritative source supports visibility. Regional availability withdrawal is scoped to the unsupported region/OTT window. | Preserve remaining support |
| PUB-08 | A failed provider sync never acts as a tombstone. | Preserve published state |

## Job Summary Rules

| Status | Definition |
|---|---|
| `succeeded` | Every record reached published, withdrawn or an idempotent unchanged outcome |
| `partially_succeeded` | At least one record succeeded and at least one record quarantined or remained retryable |
| `failed` | No record succeeded and the job cannot currently progress |
| `retry_pending` | Unresolved dependency or rate-limit work remains within policy |
| `cancelled` | An authorized cancellation stopped new work; already durable record outcomes remain |

Counts by received, unchanged, normalized, quarantined, pending publication, published, withdrawn and retryable must reconcile to the number of records observed for the job.

## ValidationRuleContract Rules

| Rule | Definition |
|---|---|
| CONTRACT-01 | The contract is immutable and addressable by version. |
| CONTRACT-02 | It exposes pure approval, identifier, license, freshness and regional availability predicates. |
| CONTRACT-03 | It contains no raw payload, provider credentials, normalization implementation, quarantine detail or operator identity. |
| CONTRACT-04 | U05 records the exact version used and must fail closed when the version is unavailable or incompatible. |
| CONTRACT-05 | A breaking predicate change requires a new contract version and U03/U05 contract regression tests. |

## Cross-Rule Invariants

1. Quarantine non-leakage: no quarantined or ambiguous record can produce a U03 write command.
2. Approved closure support: every U03 publication command contains a passed rule result and field-level provenance.
3. Last-valid preservation: dependency failure does not remove a prior approved revision.
4. Merge determinism: equivalent source sets yield the same selected fields regardless of delivery order.
5. History preservation: revalidation, retry, raw expiry and tombstones do not erase decision lineage.
6. Publication idempotence: replaying a passed decision cannot create multiple observable catalog revisions for the same decision version.
7. Source support safety: one provider deletion cannot withdraw content still supported by another valid authoritative source.
8. Contract separation: U04 provides shared predicates; U05 owns recommendation candidate and claim validation outcomes.

## Error Classification

| Category | Examples | Retry behavior |
|---|---|---|
| Record validation | Schema, provenance, license, freshness, identity, availability | Quarantine; revalidate on data/rule change |
| Provider transient | Timeout, unavailable, rate limited | Bounded retry and cursor resume |
| Provider permanent | Unauthorized policy, unsupported contract | Stop provider job and require configuration correction |
| U03 transient | Timeout, unavailable | Keep passed decision pending and retry idempotently |
| U03 conflict | Incompatible or stale version | Deterministic reconciliation, no blind retry |
| Internal invariant | Impossible state, count mismatch, missing lineage | Stop affected record/job and emit incident signal |

## Requirement Traceability

| Rules | Requirements |
|---|---|
| ING-01~07, RAW-01~05 | DR-001, DR-002, DR-005, DR-006, US-020 |
| NORM-01~05, ID-01~04, MERGE-01~05 | DR-003, DR-004, FR-032 |
| VAL-01~09, QR-01~06 | DR-009~DR-011, AC-014 |
| PUB-01~08 | DR-012, U03 ApprovedCatalogWritePort closure |
| CONTRACT-01~05 | FR-039~FR-041 support, U05 integration |
