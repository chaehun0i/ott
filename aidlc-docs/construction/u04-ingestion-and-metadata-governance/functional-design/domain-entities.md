# U04 Ingestion and Metadata Governance Domain Entities

## Aggregate Boundaries

| Aggregate | Root | Owned state | External references |
|---|---|---|---|
| Provider Governance | `ProviderPolicy` | Legal use, attribution, retention, refresh, regions, limits and policy versions | U07 adapter configuration reference |
| Ingestion Job | `IngestionJob` | Cursor, claims, attempts, page outcomes and summary counts | ProviderPolicy, U07 worker identity |
| Metadata Lineage | `RawMetadataRecord` | Raw observation, digest, normalized versions and source-field candidates | ProviderPolicy, IngestionJob |
| Canonical Resolution | `CanonicalIdentityCandidate` | Candidate matches, decisive tier and ambiguity evidence | U03 canonical ContentId when known |
| Validation | `ValidationDecision` | Rule run, results, passed/quarantined state and publication receipt | NormalizedMetadata, U03 CatalogVersion |
| Quarantine | `QuarantineRecord` | Failure history and revalidation attempts | ValidationDecision, authorized actor reference |

U04 stores only its aggregates. U03 `ApprovedContent` and `CatalogVersion`, U06 operator overrides and U07 runtime records remain foreign references accessed through contracts.

## Entity Definitions

### ProviderPolicy

| Field | Meaning |
|---|---|
| `provider_policy_id` | Immutable policy version identifier |
| `provider_id` | Stable provider identity |
| `status` | draft, active, suspended or retired |
| `allowed_uses` | Collection, storage, display and link purposes explicitly permitted |
| `attribution_requirements` | Required source labels or notices |
| `retention_policy` | Payload retention duration and post-expiry evidence rules |
| `regions` | Regions in which provider data may be used |
| `refresh_policy` | Expected collection cadence and freshness thresholds |
| `request_policy` | Rate, concurrency and retry-after requirements |
| `effective_window` | Policy validity interval |

An ingestion job can use only one active policy version. Later policy changes never rewrite the policy recorded on historical observations.

### IngestionJob

| Field | Meaning |
|---|---|
| `job_id` | Stable job identifier |
| `provider_id` | Target provider |
| `provider_policy_id` | Governing immutable policy |
| `start_cursor` | Cursor from which the job begins |
| `durable_cursor` | Last fully reconciled page position |
| `status` | scheduled, running, retry_pending, succeeded, partially_succeeded, failed or cancelled |
| `claim_version` | Optimistic claim/fencing version |
| `started_at`, `finished_at` | Lifecycle times |
| `summary` | Reconciled counts by record outcome |

The logical page key prevents multiple workers from producing distinct outcomes for the same provider cursor and policy version.

### IngestionAttempt

An attempt records a worker claim, page key, start/end time, dependency outcome, retry classification and next eligible time. Attempts are append-only. Job status is derived from durable record outcomes rather than the last worker process exit alone.

### RawMetadataRecord

| Field | Meaning |
|---|---|
| `raw_record_id` | Immutable U04 record identity |
| `provider_id`, `provider_record_id` | Original provider identity pair |
| `job_id`, `page_key` | Collection lineage |
| `retrieved_at` | Observation time |
| `payload_digest` | Digest used for idempotency and post-expiry evidence |
| `payload_body` | Optional retained raw body under policy |
| `payload_expired_at` | Governed body removal time, if expired |
| `provider_policy_id` | Legal and retention basis |
| `tombstone_kind` | None, content removal or availability removal |

Payload expiry is not entity deletion. The identity, digest, provenance and derived links remain.

### NormalizedMetadata

| Field | Meaning |
|---|---|
| `normalized_metadata_id` | Immutable normalized version |
| `raw_record_id` | Source raw observation |
| `normalization_version` | Pure transformation version |
| `content_type` | Canonical movie, series or supported type |
| `identifiers` | Provider and authoritative identifier candidates |
| `localized_fields` | Titles, synopsis and locale-tagged text candidates |
| `descriptive_fields` | Runtime, release dates, genres, people and age data |
| `availability_candidates` | Region, OTT, window and link candidates |
| `source_field_map` | Canonical path to original path/value references |

The pair `(raw_record_id, normalization_version)` is unique.

### CanonicalIdentityCandidate

| Field | Meaning |
|---|---|
| `resolution_id` | Identity-resolution attempt |
| `normalized_metadata_id` | Input normalized version |
| `identity_policy_version` | Ordered tier policy |
| `candidate_content_ids` | Candidate U03 canonical IDs with tier evidence |
| `decision` | new, matched or ambiguous |
| `selected_content_id` | Present only for a unique match or allocated new identity |
| `decisive_tier` | Tier producing the decision |

Ambiguous decisions cannot create `MergedMetadata` or publication commands.

### SourceFieldCandidate

This value object contains canonical field path, source value, normalized value, locale, provider ID, raw record ID, authority classification, license scope, observation time and validity window. It is the indivisible evidence unit used by merging.

### MergedMetadata

| Field | Meaning |
|---|---|
| `merged_metadata_id` | Immutable merged version |
| `canonical_content_id` | Target canonical ID |
| `merge_policy_version` | Field precedence rules |
| `input_normalized_ids` | Complete contributing input set |
| `selected_fields` | Canonical values selected per path |
| `field_provenance` | Selected field to SourceFieldCandidate mapping |
| `alternative_candidates` | Non-selected candidates retained by field |
| `availability` | Merged region/OTT windows with evidence |
| `computed_at` | Deterministic evaluation time |

The same input set, policy version and evaluation time must yield the same merged representation regardless of input order.

### ValidationRuleVersion

| Field | Meaning |
|---|---|
| `rule_version` | Immutable contract version |
| `status` | draft, active or retired |
| `rules` | Ordered mandatory rule definitions and applicability predicates |
| `compatible_contract_versions` | U03/U05 contract compatibility |
| `effective_window` | Version activation period |

Historical decisions always resolve their original rule version.

### ValidationRun

| Field | Meaning |
|---|---|
| `validation_run_id` | One evaluation attempt |
| `merged_metadata_id` | Evaluated input |
| `rule_version` | Exact rule set |
| `evaluated_at` | Explicit evaluation time |
| `attempt_key` | Idempotency key for input, rule and trigger |
| `trigger` | ingestion, source_change, rule_change or manual_retry |
| `actor_reference` | Present only for authorized manual retry |

### RuleResult

A result contains rule ID, applicability, pass/fail/error state, stable reason code and evidence references. It contains no provider secret and no raw payload body.

### ValidationDecision

| Field | Meaning |
|---|---|
| `decision_id` | Immutable decision identity |
| `validation_run_id` | Producing run |
| `state` | quarantined, passed_pending_publication, published, withdrawal_pending or withdrawn |
| `reason_codes` | Failure reasons for quarantined decisions |
| `publication_key` | Stable U03 idempotency key for passed decisions |
| `catalog_version` | U03 receipt proving publication or withdrawal |
| `published_at` | Receipt time |

A state transition appends history. It never converts a failed rule result into a passed result.

### QuarantineRecord

| Field | Meaning |
|---|---|
| `quarantine_id` | Stable quarantine case identity |
| `decision_id` | Failed decision |
| `reason_codes` | One or more stable reasons |
| `opened_at`, `resolved_at` | Case lifecycle |
| `latest_attempt_id` | Latest revalidation attempt |
| `resolution` | unresolved, superseded_by_pass or permanently_rejected |

Resolution does not delete the original case. U03 and U05 contracts never expose this entity.

### ProviderTombstone

A tombstone references provider ID, provider record ID, affected content or availability scope, observation time, raw record and policy version. It removes only that source's current support. Withdrawal requires a separate merged-support decision.

### PublicationReceipt

| Field | Meaning |
|---|---|
| `publication_key` | U04 decision idempotency key |
| `decision_id` | Passed or withdrawal decision |
| `catalog_version` | U03 returned version |
| `outcome` | published, withdrawn or already_applied |
| `received_at` | Receipt time |

Receipt uniqueness by publication key proves observable idempotence from U04's perspective.

## Value Objects

- `ProviderId`, `ProviderRecordId`, `ContentId`, `CatalogVersion` are opaque identifiers.
- `ProviderCursor` is an opaque provider token plus stable page fingerprint.
- `PolicyVersion`, `NormalizationVersion`, `IdentityPolicyVersion`, `MergePolicyVersion` and `ValidationRuleVersion` are immutable semantic versions or content-addressed IDs.
- `Region` and `Locale` use canonical registered forms.
- `AvailabilityWindow` contains region, OTT, start, optional end, link evidence and verification status.
- `PayloadDigest` identifies exact bytes without revealing the body.
- `ReasonCode` is a stable machine-readable code separated from localized operator text.
- `EvaluationTime` is supplied explicitly to deterministic freshness, license and availability predicates.

## Relationships

| From | Cardinality | To | Constraint |
|---|---:|---|---|
| ProviderPolicy | 1:N | IngestionJob | Job policy is immutable |
| IngestionJob | 1:N | IngestionAttempt | Attempts append only |
| IngestionJob | 1:N | RawMetadataRecord | Each observation has one collecting job |
| RawMetadataRecord | 1:N | NormalizedMetadata | At most one per normalization version |
| NormalizedMetadata | 1:N | CanonicalIdentityCandidate | One per identity policy version/attempt |
| MergedMetadata | N:M | NormalizedMetadata | Complete ordered-independent input set is retained |
| MergedMetadata | 1:N | ValidationRun | One per rule version and trigger attempt |
| ValidationRun | 1:N | RuleResult | All applicable mandatory rules represented |
| ValidationRun | 1:1 | ValidationDecision | Exactly one immutable decision |
| ValidationDecision | 0:1 | QuarantineRecord | Present only for failed decision |
| ValidationDecision | 0:1 | PublicationReceipt | Present only after U03 acknowledgement |

## Ownership and Access Rules

1. U04 alone writes provider, raw, normalized, merge, validation and quarantine state.
2. U04 calls U03 through `ApprovedCatalogWritePort`; it has no direct U03 table write path.
3. U04 reads the minimum U03 canonical identity/version facts necessary for matching and publication compatibility through versioned ports.
4. U05 reads only `ValidationRuleContract` versions and pure predicate data.
5. U06 initiates authorized retry or override through service commands; U04 stores only an actor reference and reason needed for audit linkage.
6. U07 provides storage/runtime but does not decide validation or quarantine outcomes.

## Aggregate Invariants

- Every selected merged field has exactly one valid source candidate.
- Every passed decision references one merged version, one complete rule version and one evaluation time.
- A decision with any mandatory fail, error or unknown result cannot be pending publication.
- A quarantine decision has at least one reason code and no publication receipt.
- A published or withdrawn decision has exactly one U03 CatalogVersion receipt.
- A cursor cannot advance past a record lacking a durable outcome.
- Raw body expiry cannot break digest, provenance or decision lineage.
- A tombstone cannot withdraw support provided by another valid authoritative source.
- Historical policy, rule and decision versions are immutable.

## Persistence-Neutral Consistency Boundaries

- Persisting a raw observation and its page membership is atomic within U04.
- Advancing a job cursor and reconciling page outcome counts is atomic within U04.
- Creating a validation run, all rule results and its decision is atomic within U04.
- U03 publication is not part of the U04 transaction; durable pending state and idempotent receipt reconciliation bridge the boundary.
- Quarantine revalidation creates a new transaction and never rewrites the earlier decision.

## PBT Entity Generators

Future code generation must provide reusable generators for valid ProviderPolicy versions, Unicode/locale-aware RawMetadataRecord values, conflicting identifier sets, source-field permutations, license/freshness boundary times, regional availability windows, tombstone combinations, rule-result matrices and valid job command sequences. Generators must maintain domain constraints while deliberately producing ambiguity, duplicate delivery and boundary timestamps.
