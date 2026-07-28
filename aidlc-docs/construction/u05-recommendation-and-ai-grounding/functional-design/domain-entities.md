# U05 Recommendation and AI Grounding Domain Entities

## Aggregate Boundaries

| Aggregate | Root | Owned values/entities | Boundary |
|---|---|---|---|
| Recommendation Session | `RecommendationSession` | intent versions, patches, confirmation conflicts, epochs | Conversation state only; no direct identity data |
| Recommendation Request | `RecommendationRequest` | input snapshot, candidate set reference, ranking run, response state | One immutable execution attempt and its versions |
| Ranking Run | `RankingRun` | eligible candidates, score records, diversity decisions, final positions | C10-owned eligibility and final rank |
| Grounded Draft | `GroundedTextDraft` | localized text, atomic claims, evidence references | C09 draft; never directly exposable |
| Output Validation | `OutputValidationRun` | candidate checks, claim checks, replacement decisions | C11-owned exposure authorization |
| Recommendation Trace | `RecommendationTrace` | privacy-safe versions, decisions, codes and fallback path | U05-owned read-only handoff to U06 |

## Identifiers and Versions

| Type | Meaning | Rule |
|---|---|---|
| `RecommendationSessionId` | Pseudonymous conversation identifier | Never equals a U02 user ID |
| `SessionEpoch` | Reset boundary | Monotonically increases; closed epoch is immutable |
| `SessionVersion` | Optimistic patch version | Increases exactly once per accepted patch |
| `RecommendationRequestId` | One recommendation execution | Stable across trace and response |
| `RankingRunId` | One C10 execution | References exact input versions |
| `DraftId` | One C09 grounded draft set | Not an exposure authorization |
| `ValidationRunId` | One C11 validation execution | References candidate and claim versions |
| `TraceId` | U06-readable investigation reference | Pseudonymous and access-controlled by consumer |
| `PolicyVersion` | Intent/scoring/diversity/fallback policy identity | Immutable after activation |
| `CatalogSnapshotVersion` | Exact U03 approved snapshot | Required for every candidate |
| `MetadataVersion` | Evidence-bearing approved metadata identity | Required for every claim reference |
| `ValidationRuleVersion` | U04 predicate version | Unknown version fails closed |
| `FeatureDefinitionVersion` | U02 feature schema identity | Required when personalization contributes |

## Intent Model

### `RecommendationIntent`

An immutable language-neutral value containing:

- locale and region;
- included/excluded genres and moods;
- maximum runtime and optional content type;
- companion context and age eligibility;
- permitted OTT providers;
- freshness/novelty preference;
- explicit include/exclude content facts;
- requested result count;
- confirmation state and conflict codes;
- intent schema/parser version.

Each `IntentCondition` contains canonical field, typed value, source (`current_request`, `session`, `stored_preference`), explicitness, confidence and hard/soft classification. A hard condition must be explicit/confirmed or supplied by safety/eligibility policy.

### `IntentPatch`

Contains retained, added, changed and removed condition sets plus expected session version. The four sets are disjoint. Applying the same patch key twice produces the same session version; applying a different patch against an old version produces a conflict.

### `IntentConflict`

Contains stable conflict code, involved fields, safe localized explanation key and permitted resolutions. It contains no raw model reasoning.

## Candidate and Ranking Model

### `CandidateSnapshot`

References one U03 catalog snapshot, request region and an ordered collection of `CatalogCandidate` values. Every candidate is approved at the referenced snapshot and includes only U05-permitted metadata.

### `EligibilityProof`

Records passed checks for approval, withdrawal, region, OTT, runtime, age and explicit exclusions. Missing or unknown mandatory checks produce no proof.

### `EligibleCandidate`

Combines canonical content ID, catalog/metadata versions, eligibility proof and allowlisted ranking features. Construction is impossible without a complete proof.

### `FeatureSnapshot`

Contains pseudonymous request reference, consent state, feature definition/version, observed-at time and bounded preference/behavior values. It cannot contain email, provider subject, session token, raw event history or free-form profile text.

### `ScoreRecord`

Contains request-fit, consented-affinity, freshness, popularity and novelty components, effective weights, base score and policy version. Every numeric value is bounded; component inputs are replayable from permitted snapshots.

### `RankedCandidate`

Contains eligible candidate reference, base position, final position, diversity reason codes and score record. It cannot reference an ID outside the eligible input set.

### `RankingRun`

Lifecycle: `created` → `filtered` → `scored` → `diversified` → `candidate_validated` → `completed`. Any invariant failure transitions to `rejected`; completed and rejected runs are immutable.

## Grounding Model

### `EvidenceBundle`

Contains one content ID, catalog/metadata version, locale, allowlisted field values and `EvidenceReference` values. The bundle is immutable and candidate-local.

### `EvidenceReference`

Contains content ID, metadata version, field path and source reference. It does not contain raw provider payload or credential material.

### `AtomicClaim`

Contains localized text span, claim type and one or more evidence references. Every reference must point to the draft candidate. Unsupported claims cannot be represented as passed claims.

### `GroundedTextDraft`

Contains draft ID, candidate ID, locale, reason, spoiler-minimized summary, ordered atomic claims, model version and prompt-template version. State is `drafted`, `validated`, `replaced` or `rejected`. Only `validated` or approved template replacement text may enter a response.

## Validation and Response Model

### `CandidateValidationResult`

Records mandatory check results and stable failure codes for one ranked candidate. Pass requires a complete matrix; missing, error and unknown are failures.

### `ClaimValidationResult`

Records claim/evidence locality, metadata version and field support. It never stores rejected free text beyond a bounded digest and reason code.

### `OutputValidationRun`

Owns candidate and claim results, U04 rule contract version, replacement actions and terminal state. Terminal states are `passed`, `partial_safe`, `fallback_safe` and `failed_closed`.

### `SafeRecommendationItem`

Contains content ID, final rank, bounded score explanation, validated or template text, AI-drafted indicator, catalog/metadata versions and availability facts. Its constructor requires passed candidate validation and passed/replaced text validation.

### `RecommendationResponse`

Contains request/session/version references, confirmed intent summary, safe items, degradation/fallback code and trace ID. It never contains a draft object, raw prompt, chain-of-thought or failed claim text.

## Trace Model

`RecommendationTrace` links the request, session/version, intent schema, model/template, scoring/diversity/fallback policies, U02 feature definition, U03 catalog/metadata, U04 validation rule, candidate decisions, bounded scores, output validation codes and fallback path. It stores pseudonymous references only and is immutable after closure.

Trace lifecycle: `opened` → `decision_recorded` → `validation_recorded` → `closed`. An operational write failure may leave an incomplete trace marker but cannot change a validation outcome or authorize exposure.

## Relationships and Invariants

1. One session has many immutable versions within one epoch; reset starts a later epoch.
2. One accepted request references exactly one session version and one intent schema version.
3. One request has one active ranking run and may have bounded failed/retry attempts with distinct attempt IDs.
4. Every ranked candidate references exactly one eligible candidate from the request's U03 snapshot.
5. Every grounded draft references exactly one validated candidate and one evidence bundle.
6. Every atomic claim references evidence from that same content and metadata version.
7. One output validation run closes every exposed candidate/text path as passed, replaced or rejected.
8. Every response item has a passed eligibility result and validated/template text result.
9. No reset session reads a prior epoch's conditions.
10. No consent-withdrawn feature contributes to a score or AI input.
11. Trace data is sufficient to replay deterministic rules but insufficient to reconstruct direct identity or model chain-of-thought.

## Ownership and Contract Mapping

| External owner | U05 consumes | U05 must not consume or mutate |
|---|---|---|
| U02 | Consent-qualified pseudonymous feature snapshot | users, credentials, raw behavior, direct identifiers |
| U03 | Approved candidate/detail/availability snapshot and provenance references | unapproved/withdrawn rows or direct table writes |
| U04 | Versioned read-only validation predicate contract | raw provider data, quarantine internals or rule mutation |
| U07 | AI/runtime/clock/ID/transaction/telemetry ports | deployment policy ownership |
| U06 | Reads privacy-safe recommendation trace | U06 override/audit tables |

U05 owns no frontend artifact. Presentation, accessibility and client-side confirmation controls are U01 responsibilities consuming the future U05 API contract.
