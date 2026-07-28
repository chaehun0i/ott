# U05 Recommendation and AI Grounding Business Logic Model

## Scope and Ownership

U05 converts Korean or English viewing situations into a language-neutral intent, ranks only approved and eligible U03 content, drafts concise text from allowlisted evidence and exposes only results that pass final validation. It owns the recommendation decision pipeline and conversation state, but it does not approve metadata, mutate the catalog, read direct identity data, infer consent or perform operator overrides.

The responsibility boundary is strict:

- C09 AI Interaction interprets natural language and drafts text. It never decides candidate eligibility or final rank.
- C10 Recommendation Engine applies hard filters, score policy and diversity, and alone determines final candidate order.
- C11 Recommendation Output Validation rechecks catalog eligibility, request conditions and every grounded claim before exposure.
- C08 Recommendation Orchestrator enforces stage order, budgets, fallback and response assembly without bypassing C10 or C11.

## Recommendation Request Flow

### 1. Request and Context Admission

1. Accept locale, region, natural-language request, optional session version and an authenticated or anonymous request context.
2. Read only a pseudonymous, consent-qualified U02 feature snapshot. Direct identifiers, raw behavior events and withdrawn features are not valid U05 inputs.
3. Capture immutable input versions: intent schema, scoring policy, diversity policy, U03 catalog snapshot, U04 validation contract and feature definition.
4. Reject malformed or oversized input at the API boundary; external error details do not enter the domain trace.

### 2. Intent Interpretation and Confirmation

C09 produces a `RecommendationIntentDraft` containing locale-independent values for genres, moods, maximum runtime, companion context, OTT subscriptions, region, age constraints, inclusion/exclusion preferences and requested result count. Every value carries an origin of current request, confirmed conversation state or consented stored preference, plus confidence and explicitness.

The intent resolver applies this precedence:

1. Safety, legal, approval and availability constraints.
2. Latest explicit request and confirmed conversational changes.
3. Earlier retained session conditions.
4. Consented stored preferences as soft signals only.

An ambiguous or conflicting value is never silently promoted to a hard condition. The request enters `confirmation_required` with structured conflict codes and editable conditions. No candidate ranking or AI explanation call occurs until the user confirms or removes the uncertainty.

Korean and English inputs with equivalent meaning must produce equivalent canonical hard conditions. Locale affects parsing and presentation, not eligibility semantics.

### 3. Approved Candidate Snapshot and Hard Filtering

C10 requests a versioned U03 approved-catalog snapshot for the request region. Candidate generation excludes any record that is unapproved, withdrawn, outside regional/OTT availability, over the confirmed runtime, outside age eligibility or contrary to an explicit exclusion. Filtering occurs before scoring. AI-proposed content IDs are never accepted as candidate input.

Every surviving `EligibleCandidate` records the catalog version and hard-filter proof. A later stage cannot reintroduce a removed item. Empty eligibility proceeds to deterministic fallback broadening only for soft conditions; safety, approval, region, OTT, age and explicitly declared hard constraints are never relaxed automatically.

### 4. Personalization and Score Composition

Each eligible candidate receives bounded score components in `[0, 1]`:

- explicit request fit;
- consented preference and behavior affinity;
- catalog freshness;
- approved popularity;
- novelty relative to prior exposed recommendations.

A versioned policy defines non-negative weights whose sum is one. Missing or withdrawn personalization contributes no behavior-derived component and causes the remaining permitted weights to be normalized. The score record preserves component inputs, feature definition version and policy version for replay; it contains no direct identity value.

Ties are resolved deterministically by request-fit score, freshness, popularity and canonical content ID. Identical input snapshots and policy versions therefore produce the same pre-diversity order.

### 5. Diversity and Final Ranking

The diversity reranker processes only the eligible scored set. It removes duplicate content IDs and franchise-equivalent repetitions, then applies versioned bounds for repeated genre/provider similarity. Diversity may reorder or omit candidates but cannot add a new content ID or override a hard-filter proof. The final rank record retains both base and diversity-adjusted positions.

### 6. Candidate Validation Before Text Generation

C11 validates each ranked candidate against the exact U03 snapshot and current U04 `ValidationPredicateContract`. Checks include content identity, approval state, region/OTT availability, runtime/age constraints, explicit exclusions and rule-version compatibility. Failed candidates are removed before their metadata can be sent to C09.

The orchestrator fills an opened position from the already eligible reserve set and validates the replacement. It does not rerun AI intent interpretation or accept an unvalidated AI suggestion.

### 7. Evidence Bundle and Grounded Text Drafting

For each validated candidate, U05 constructs an allowlisted `EvidenceBundle`. It contains content ID, catalog/metadata version, localized title, approved synopsis fragments, genre, runtime, release facts, availability facts and selected provenance references. Provider credentials, raw U04 payloads, quarantine details and non-display metadata are excluded.

C09 drafts:

- a concise localized recommendation reason explicitly connected to confirmed request conditions; and
- a short spoiler-minimized summary.

The draft is split into atomic claims. Every claim cites the same candidate's content ID, metadata version, field path and source reference. AI-drafted text is identifiable in the response. Unsupported detail is omitted rather than inferred.

### 8. Final Output Validation and Safe Assembly

C11 validates each atomic claim against its evidence bundle and verifies candidate eligibility again at the response boundary. Outcomes are:

- `passed`: candidate and all exposed claims are safe;
- `template_replacement`: candidate is valid but one or more claims fail, so failed text is discarded and replaced by an approved metadata template;
- `candidate_rejected`: candidate eligibility or evidence locality fails, so the item is removed and a validated reserve candidate may be used;
- `response_fallback`: no validated AI-drafted item remains, so the whole result uses deterministic rule ranking and approved templates.

There is no route that serializes an unvalidated draft. One failed item does not fail safe siblings. The response includes degradation/fallback status without internal provider details.

## Conversation Adjustment Flow

Each turn is an immutable `IntentPatch` with retained, added, changed and removed conditions. Applying a patch requires the expected session version and creates a new version. Concurrent stale updates return a version conflict rather than overwriting newer intent.

The full eligibility, ranking, grounding and validation pipeline runs after every accepted patch. A reset closes the current session epoch and creates an empty intent state; no prior constraint or derived feature from the closed epoch can flow into the new recommendation unless U02 independently supplies a currently consented preference snapshot.

## Degraded Operation

| Failure | Functional response | Safety invariant |
|---|---|---|
| AI intent timeout before a valid intent | Return a safe dependency error or use only explicitly structured client conditions | No guessed hard condition |
| AI explanation timeout | Keep eligible deterministic ranking and use localized approved-metadata templates | Candidate validation remains mandatory |
| AI circuit open | Skip AI calls and use rule-based ranking/templates | No latency amplification or validation bypass |
| U02 feature unavailable or consent absent | Use request context plus approved freshness/popularity | No behavior-derived personalization |
| U03 unavailable | Do not manufacture candidates; return bounded unavailable state | Approved-catalog closure preserved |
| U04 contract incompatible | Fail closed before exposure | Unknown rule never passes |
| One candidate or claim fails | Remove/replace that item or claim and preserve safe siblings | Failed draft never leaks |
| Trace persistence fails | Serve only if candidate/text validation already passed and emit bounded operational failure | Trace failure cannot authorize unsafe output |

## Privacy-Safe Trace

The trace contains pseudonymous session/request IDs; intent, scoring, diversity, feature, model, prompt-template, catalog, metadata and validation-rule versions; candidate inclusion/exclusion codes; bounded score components; final positions; validation codes and fallback path. It excludes direct identifiers, raw prompts, raw behavior, provider payloads, credentials and model chain-of-thought. U06 receives a read-only trace view through `RecommendationTracePort`.

## Story and Requirement Traceability

| Flow | Stories | Requirements |
|---|---|---|
| Bilingual intent and confirmation | US-008, US-009, US-013 | FR-009~010, FR-036, AC-002 |
| Eligibility, scoring and diversity | US-010, supporting US-017/018 | FR-011~013, FR-017, FR-037, DR-008, DR-012, AC-011~012 |
| Grounded reason and summary | US-011 | FR-014~016, FR-038, FR-040, DR-013, AC-003, AC-013 |
| Conversation patch/reset | US-012 | FR-019~022, AC-004 |
| Fail-closed validation and replacement | US-022 | FR-039~041, DR-014, AC-011~014 |
| AI degradation | US-024 | FR-018, AC-006, RESILIENCY-10 |
| Privacy-safe trace handoff | supporting US-023 | FR-042, DR-008, DR-014 |
