# U01 Web Experience Business Rules

## Navigation and Query Rules

- BR-U01-01: Feed filters and sort have one canonical URL encoding; equivalent inputs serialize identically.
- BR-U01-02: Detail navigation records a safe return URL and restores list query and focus target.
- BR-U01-03: Unknown or invalid query values are ignored or normalized with a visible correction; they never reach a backend unchecked.
- BR-U01-04: A Pending Intent contains only an allowed action and opaque content reference, expires with the login attempt, and is consumed at most once.

## Content, Search and Recommendation Rules

- BR-U01-05: UI displays only items returned by the approved U03/U05 contracts and does not repair or invent missing metadata.
- BR-U01-06: Search displays the server-interpreted conditions separately from raw input and permits explicit modification.
- BR-U01-07: Recommendation cards show summary and reason by default; evidence is available through an accessible disclosure.
- BR-U01-08: Recommendation refine and condition removal use the U05 session contract. Local changes remain pending until accepted by the server.
- BR-U01-09: Reset clears session identifier, turns, conditions, results and retry state as one UI transition.
- BR-U01-10: Invalid or expired recommendation sessions cannot reuse stale results as if they belong to a new request.

## Authentication, Consent and Authorization Rules

- BR-U01-11: Credentials and tokens are never stored in application-readable persistence or rendered in diagnostic output.
- BR-U01-12: 401 triggers reauthentication; 403 produces access denied and never retries as another role.
- BR-U01-13: Server authorization is final. Client route guards improve navigation only and are not a security boundary.
- BR-U01-14: Successful consent withdrawal immediately removes personalized projections and switches to non-personalized results.
- BR-U01-15: Feedback is emitted only when its purpose is consented, and uses an idempotency key to prevent duplicate replay.
- BR-U01-16: Operator data is confined to `/admin`; authorization failure clears operator cache and never falls back into public views.

## Error, Freshness and Resiliency Rules

- BR-U01-17: Independent successful regions remain usable when a sibling dependency fails.
- BR-U01-18: Stale data is shown only with last successful update, degraded reason and a local retry action.
- BR-U01-19: A retry targets the failed request and preserves unrelated successful state.
- BR-U01-20: Destructive commands are not automatically retried unless the server contract and idempotency key make replay safe.
- BR-U01-21: Error presentations expose a safe correlation reference but no stack, secret, credential or private input.
- BR-U01-22: External OTT actions are enabled only for validated URLs, identify the destination and open with safe new-tab behavior.

## Localization and Accessibility Rules

- BR-U01-23: UI text changes immediately between Korean and English without losing route, form draft or focus context.
- BR-U01-24: Content fallback order is selected locale, original title/text, then defined fallback locale; fallback is visibly identified.
- BR-U01-25: Every interactive action is keyboard operable with visible focus and deterministic focus restoration.
- BR-U01-26: Loading, result-count, error and consent changes use appropriate live announcements without duplicating visual text excessively.
- BR-U01-27: Field errors are connected to controls and summarized; focus moves to the summary only after invalid submit.
- BR-U01-28: Images have meaningful alternatives or empty alternatives when decorative; color is never the sole status indicator.

## Testable Properties (PBT-01)

| ID | Property | Category | Expected property test |
|---|---|---|---|
| P-U01-01 | parse(serialize(normalize(query))) equals normalize(query) | Round-trip | generated valid filter/sort/query sets |
| P-U01-02 | normalize(normalize(query)) equals normalize(query) | Idempotence | malformed, duplicate and Unicode query inputs |
| P-U01-03 | independent filter insertion order yields the same canonical URL | Commutativity | generated filter permutations |
| P-U01-04 | locale fallback always selects the first available value in the defined chain | Oracle | generated localized field maps vs simple reference selector |
| P-U01-05 | consent withdrawal leaves no personalized cache, conversation or pending feedback | Invariant | generated UI states containing personalization subsets |
| P-U01-06 | Pending Intent is executed zero times on failure and exactly once on success | Stateful | login success/failure/retry command sequences |
| P-U01-07 | recommendation reset produces the same empty state regardless of prior valid turns | Invariant | generated conversation histories |
| P-U01-08 | stale projection always has prior data, timestamp, reason and retry action | Easy verification | generated remote-resource transitions |
| P-U01-09 | field error IDs and described-by references remain unique and resolvable | Invariant | generated form schemas and validation results |
| P-U01-10 | protected state is absent after logout or operator 403 | Stateful | generated navigation/auth/command sequences |

P-U01-01~10 must be carried into U01 Code Generation planning. Example tests remain mandatory for primary journeys, keyboard focus recovery, login intent replay, degraded rendering and consent withdrawal.

## Extension Compliance

### Resiliency Baseline

| Rule | Status | Rationale |
|---|---|---|
| RESILIENCY-01 | Compliant | C01 dependencies and user impact are documented; U01 is the terminal public consumer. |
| RESILIENCY-02~04 | N/A | Availability, recovery and deployment decisions are owned by established U07 design. |
| RESILIENCY-05~07 | Supporting | U01 exposes safe error references and user-visible health degradation; platform telemetry remains U06/U07. |
| RESILIENCY-08~09 | N/A | No topology or capacity decision is made in technology-agnostic Functional Design. |
| RESILIENCY-10 | Compliant | Partial failure, bounded requests through server contracts and graceful degradation are explicit. |
| RESILIENCY-11~14 | N/A | U01 owns no persistent business data or DR execution. |
| RESILIENCY-15 | Supporting | Incident presentation is defined; incident process is owned by U06. |

No blocking resiliency finding remains.

### Property-Based Testing

PBT-01 is compliant through P-U01-01~10 with explicit property categories. PBT-02~10 are deferred to their required NFR, Code Generation and Build/Test stages. No blocking PBT finding remains.

### Security Baseline

Disabled and therefore N/A. Core authentication, authorization, consent and sensitive-data rules remain enforced through BR-U01-11~16 and BR-U01-21.
