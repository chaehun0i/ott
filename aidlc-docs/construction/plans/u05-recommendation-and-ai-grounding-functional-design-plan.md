# U05 Recommendation and AI Grounding Functional Design Plan

> **Single Source of Truth**: This file controls U05 Functional Design planning, user decisions and completion checkboxes. Final design artifacts are not generated until every answer is valid and ambiguity-free.

## Unit Context

- **Goal**: Convert Korean or English natural-language situations into structured intent, rank only approved and eligible catalog candidates, generate evidence-grounded summaries/reasons, validate every exposed result and support conversational adjustment.
- **Owned Components**: C08 Recommendation Orchestrator, C09 AI Interaction, C10 Recommendation Engine, C11 Recommendation Output Validation.
- **Owned Services**: S03 RecommendationApplicationService, S04 RecommendationConversationService.
- **Primary Stories**: US-008, US-009, US-010, US-011, US-012, US-013, US-022, US-024.
- **Supporting Stories**: US-005, US-006, US-017, US-018 and US-023 through consumer/provider contracts.
- **Required Dependencies**: U02 PersonalizationFeaturePort and ConsentPort; U03 ApprovedCatalogReadPort and AvailabilityPort; U04 ValidationRuleContract; U07 AI adapter, database, timeout and API runtime.
- **Owned Data**: recommendation sessions/requests/candidates, ranking runs, explanation drafts, output-validation results and privacy-safe recommendation traces.
- **Hard Boundary**: AI structures intent and drafts grounded text. Recommendation Engine alone determines eligibility and final rank. Validation alone authorizes exposure.
- **Enabled Extensions**: Resiliency Baseline (Full), Property-Based Testing (Full).
- **Disabled Extension**: Security Baseline; core consent, de-identification, least-privilege and data-minimization requirements remain mandatory.

## Execution Plan

### Step 1 - Context and Traceability

- [x] Read the U05 unit definition, dependency graph and primary/supporting story map.
- [x] Read FR-009~022, FR-036~042, DR-008, DR-012~014 and AC-002~004, AC-006, AC-011~014.
- [x] Read the implemented U02 feature/consent, U03 approved-catalog and U04 validation-contract boundaries.
- [x] Confirm U05 owns no catalog approval, metadata mutation, direct identity access or operator override.

### Step 2 - Planning and Questions

- [x] Identify unresolved business decisions that materially affect recommendation behavior.
- [x] Create Questions 1~12 with mutually exclusive choices and an `X) Other` option.
- [ ] Collect every `[Answer]:` value and validate it against the offered choices.
- [ ] Check all answers for contradiction or ambiguity; create a clarification file if needed.

### Step 3 - Business Logic Model

- [ ] Design intent extraction, ambiguity confirmation and bilingual semantic-equivalence behavior.
- [ ] Design candidate retrieval, hard filtering, personalization, diversity and deterministic final ranking.
- [ ] Design grounded text drafting, atomic claim evidence and fail-closed output validation.
- [ ] Design conversational patch/reset, AI failure fallback and partial-result replacement.
- [ ] Generate `business-logic-model.md` with story and requirement traceability.

### Step 4 - Domain Entities

- [ ] Define session, request, intent, constraint patch, candidate, score, rank, draft, claim, evidence, validation and trace entities.
- [ ] Define identifiers, immutable versions, relationships, lifecycle states and ownership boundaries.
- [ ] Generate `domain-entities.md`.

### Step 5 - Business Rules and Testable Properties

- [ ] Define hard/soft constraint precedence, consent behavior, score/diversity rules and fallback closure.
- [ ] Define claim/evidence validation, non-leakage, trace minimization and session transition rules.
- [ ] Apply PBT-01 to round-trip, invariant, idempotence, oracle, stateful and easy-verification candidates.
- [ ] Generate `business-rules.md`.

### Step 6 - Validation and Completion

- [ ] Verify story/FR/DR/AC traceability and U02/U03/U04/U07 contract alignment.
- [ ] Evaluate RESILIENCY-01~15 and PBT-01 compliance, including applicable/N/A rationale.
- [ ] Validate Markdown syntax and parsing compatibility before final file creation.
- [ ] Update this plan, `aidlc-state.md` and `audit.md`, then request standardized Functional Design approval.

## Functional Design Questions

Enter one letter after every `[Answer]:` tag. Select `X` and add a description when none of the policies match.

## Question 1
How should explicit request constraints, conversational changes and stored preferences be prioritized?

A) Safety/eligibility rules first, then the latest explicit request and confirmed conversation changes, then consented stored preferences as soft signals

B) Stored preferences override the current request whenever sufficient history exists

C) Combine all conditions with equal weight and let ranking resolve conflicts

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 2
What should happen when an intent value is ambiguous, low-confidence or conflicts with another hard condition?

A) Return the structured conditions and conflict codes for user confirmation; do not promote the uncertain value to a hard filter before confirmation

B) Choose the most probable interpretation automatically and disclose it with the results

C) Ignore the ambiguous condition and continue without showing a confirmation step

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 3
How should Recommendation Engine candidate generation and eligibility work?

A) Read a versioned U03 approved-catalog snapshot, apply region/OTT/runtime/release/age hard filters first, then score only the surviving candidates

B) Score the full catalog first and remove ineligible candidates after ranking

C) Allow the AI provider to propose candidates and use U03 only to enrich the final list

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 4
How should the initial personalized score be composed?

A) Use a versioned weighted score from request fit, consented preference/behavior affinity, freshness, popularity and novelty, retaining each bounded component for explanation and replay

B) Use only behavior similarity once any behavior history exists

C) Ask the AI provider to assign one overall relevance score without component values

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 5
How should diversity and repetition control affect final ranking?

A) Apply versioned reranking with per-franchise/title deduplication and bounded genre/provider similarity, without allowing diversity to reintroduce an ineligible item

B) Preserve pure score order and remove only exact duplicate content IDs

C) Reserve an equal number of positions for every genre regardless of request fit

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 6
How should personalization behave when consent is absent, withdrawn or no usable history exists?

A) Exclude behavior-derived features and use request context plus non-personalized approved freshness/popularity signals; withdrawal takes effect fail-closed

B) Continue using previously derived features but stop collecting new events

C) Refuse recommendation and require personalization consent

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 7
What are the session semantics for follow-up requests such as “brighter” or “another genre”?

A) Represent each turn as an explicit versioned patch of retained, added, changed and removed conditions; reset creates a new empty state that cannot inherit old constraints

B) Reparse the entire conversation on every turn and replace state with the AI provider's latest interpretation

C) Append every condition permanently until the session expires; only reset can remove one

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 8
How should AI-generated summaries and recommendation reasons be grounded?

A) Draft atomic claims from allowlisted approved fields, attach each claim to content ID, metadata version, field path and source reference, then validate every claim before exposure

B) Give the AI full approved content records and validate only content IDs afterward

C) Generate free text from titles and rely on a disclaimer instead of claim-level evidence

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 9
What content style policy should apply to recommendation reasons and summaries?

A) Return a concise localized reason tied to the user's conditions plus a short spoiler-minimized summary; omit unsupported details and label AI-drafted text

B) Return a detailed plot synopsis and a general recommendation reason even when some details lack evidence

C) Use metadata templates only and do not generate localized AI text

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 10
How should item-level output validation failures be handled?

A) Remove the invalid claim or item, backfill from already eligible validated candidates when possible and fall back to an approved metadata template without exposing the failed draft

B) Fail the entire recommendation response when any one item or claim fails

C) Return the item with a warning that validation was incomplete

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 11
What should happen when the AI provider times out or is unavailable?

A) Continue with deterministic rule-based eligible ranking and localized approved-metadata templates, marking the response as degraded without weakening validation

B) Retry until the provider responds, even if the user request exceeds its latency budget

C) Return no recommendations and ask the user to retry later

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 12
What should a privacy-safe recommendation trace retain?

A) Retain pseudonymous session/request IDs, intent/ranking/policy/model/metadata/rule versions, candidate/filter/score outcomes, validation codes and fallback path; exclude direct identifiers, raw prompts and model chain-of-thought

B) Retain the full prompt, model response and user profile to maximize reproducibility

C) Retain only the final content IDs and timestamp

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Planned Artifacts

- `aidlc-docs/construction/u05-recommendation-and-ai-grounding/functional-design/business-logic-model.md`
- `aidlc-docs/construction/u05-recommendation-and-ai-grounding/functional-design/business-rules.md`
- `aidlc-docs/construction/u05-recommendation-and-ai-grounding/functional-design/domain-entities.md`

U05 owns no frontend component, so `frontend-components.md` is N/A. U01 will consume the future recommendation and conversation API contracts.

## Preliminary Extension Assessment

### Resiliency Baseline

- AI dependency timeout, bounded retry, circuit isolation and deterministic degradation are applicable to the functional flows; infrastructure mechanics remain for NFR and Infrastructure Design.
- U03 approved-catalog continuity and U02 consent withdrawal are fail-closed dependencies, not AI fallback inputs.
- RESILIENCY-08 and RESILIENCY-09 retain the approved single-server/fixed-capacity prototype exceptions pending later NFR assessment.

### Property-Based Testing

- PBT-01 applies to intent schema round-trip, bilingual hard-condition equivalence, hard-filter closure, scoring bounds, deterministic ranking, diversity non-reintroduction, evidence locality, validation non-leakage, session patch/reset and fallback equivalence.
- PBT-02~10 implementation responsibilities will be handed to NFR Requirements and Code Generation after the property inventory is approved.

### Security Baseline

- The extension is disabled and N/A. Core consent enforcement, de-identification, data minimization and trace access boundaries remain mandatory requirements.
