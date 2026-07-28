# U02 Business Logic Model

## Scope and Boundary

U02는 Identity, Authorization, Profile, Consent, Library, Feedback Event와 Personalization Feature를 소유한다. U02가 제공하는 추천 context에는 요청 범위 pseudonymous subject와 동의된 feature·version만 포함한다. 이메일, OAuth subject, credential, 원본 행동 payload는 U05와 외부 AI에 전달하지 않는다.

Primary trace는 US-014~US-018과 US-027이며 FR-011~012, FR-022~027, DR-007~008, AC-005와 AC-007을 구현 경계로 삼는다.

## Actors and Ports

| Actor or Consumer | Input | U02 Output |
|---|---|---|
| Visitor | registration, email verification, login, Google OAuth callback | Identity or explicit authentication error |
| Member | profile, library, consent, export and deletion commands | versioned state and job status |
| Content Operator | authorized operational request | role-scoped authorized context |
| System Administrator | role and security administration request | least-privilege authorization decision and audit event |
| U01 | account and personalization API commands | versioned DTO and error contract |
| U05 | consent and feature query | request-scoped pseudonymous FeatureSnapshot |
| U06 | identity role and notification preference query | minimal role or preference view |
| U07 | request identity, idempotency, outbox and persistence runtime | durable transaction and job execution |

## Identity Lifecycle

### Email Registration and Verification

1. Normalize the email for comparison while preserving the display form separately.
2. Reject an already-bound verified email without disclosing whether the account exists to unauthenticated callers.
3. Hash the password through the credential port and create a pending user plus single-use verification challenge in one transaction.
4. Verification consumes the challenge once, marks the email verified and activates the Member role.
5. Login is denied until email verification succeeds.
6. Repeated registration or verification commands use U07 idempotency and return the same safe outcome.

### Email Authentication and Sessions

1. Authenticate a normalized email and password without exposing which field failed.
2. Create a server-side session record with issued, last-seen and expiry timestamps plus a device label supplied as untrusted display metadata.
3. Multiple device sessions are allowed.
4. A member can revoke one session or all sessions. A revoked or expired session cannot authorize protected work.
5. Authorization resolves the current role on each sensitive operation rather than trusting a client claim.

### Google OAuth and Account Linking

1. Validate provider state, callback binding and the provider-issued identity through the Google adapter.
2. An existing OAuth link authenticates its owning user.
3. A verified provider email alone never merges accounts.
4. Linking to an existing email account requires an authenticated session, fresh reauthentication and an explicit link command.
5. Provider subject uniqueness prevents one Google identity from being attached to multiple users.
6. Unlink is rejected when it would remove the user's last usable authentication method.

## Authorization Model

Roles are Member, ContentOperator and SystemAdministrator. Permissions are fixed, versioned sets owned by the application policy rather than arbitrary client-provided values.

- Member manages only their own profile, sessions, library, consent and data rights.
- ContentOperator receives only content-operation permissions consumed by U06 and cannot administer identities.
- SystemAdministrator can manage operational role assignments but cannot read credentials or bypass consent boundaries.
- A role change increments identity authorization version and invalidates cached authorization contexts.

## Preference and Library Flows

### Preferences and OTT Subscriptions

- Genre preference is an explicit `liked`, `disliked` or absent state. Liked and disliked are mutually exclusive.
- OTT subscription is `subscribed`, `not_subscribed` or `unspecified`.
- An update replaces only fields named in the command, increments ProfileVersion and emits a feature-refresh event.
- Explicit preferences are eligible for cold-start personalization when optional personalization consent is active.

### Watch Items, Ratings and History

- Saving a content item is idempotent for user and content.
- A rating is an integer from 1 through 5; a new rating replaces the previous current value and retains modification provenance.
- Watch history stores completion state and the most recent watched timestamp. The initial model does not infer progress percentage.
- Removing or changing library data immediately updates the authoritative profile view and schedules recomputation of derived features.
- Content identifiers are references to U03; U02 does not copy or modify catalog metadata.

## Consent and Feedback Flow

### Consent Model

Processing is separated into required service processing and optional personalization. External AI receives no direct identifier under either purpose. Each optional decision records policy version, notice version, source and decision time.

### Feedback Recording

1. Validate authenticated subject, event schema, content reference and purpose.
2. Read a current ConsentSnapshot before accepting a personalization event.
3. Apply client idempotency key within subject and event type scope. If absent, apply a narrow server-side duplicate window for the same subject, content and event type.
4. Explicit actions such as save and rating update their authoritative state and derived feature synchronously.
5. Implicit actions such as click, recommendation dismiss and OTT outbound navigation are stored durably, then processed asynchronously.
6. Event payload contains pseudonymous subject reference, content ID, event type, occurred time, source surface, recommendation version and minimal context; it excludes email, OAuth identifiers and provider tokens.

### Guest Linking

- Guest events remain under a guest pseudonym.
- Signup or login does not link them automatically.
- A separate explicit consent command names the guest scope to link and records the policy version.
- Already expired, withdrawn or ineligible guest events are not linked.

## Consent Withdrawal

1. Persist the withdrawn consent version as the authoritative decision.
2. Immediately fail closed for new personalization events and U05 feature reads.
3. Revoke outstanding feature snapshots by advancing ConsentVersion.
4. Enqueue deletion of personalization source events and derived features.
5. Completion is reached only when both source events and derived features are deleted and caches are invalidated.
6. Required service data, minimal consent evidence and legally required tombstones remain separated and cannot be used for personalization.

## Feature Snapshot Flow

1. Authenticate the internal U05 caller and requested purpose.
2. Verify active optional personalization consent at the requested instant.
3. Create a new request-scoped pseudonymous subject ID that is not stable across unrelated recommendation requests.
4. Return only consented genre, OTT, library-derived and behavior-derived features plus FeatureVersion, ConsentVersion and generated time.
5. If consent is absent, withdrawn, stale or deletion is pending, return a non-personalized context rather than stale features.

## Data Export and Deletion

### Export

- Fresh reauthentication is required.
- A snapshot job collects identity profile, linked providers without tokens, preferences, library, consents and eligible behavior data.
- The export artifact is encrypted, expires, is single-user authorized and records generation status without logging its contents.

### Account Deletion

1. Require fresh reauthentication and an idempotent deletion command.
2. Immediately disable login and revoke all sessions.
3. Enqueue deletion across credentials, OAuth links, profile, library, events, features and export artifacts.
4. Preserve only separately stored legal or operational tombstones containing no reusable personalization data.
5. Retry failed deletion steps until closure; partial completion never reactivates the account.
6. A terminal deletion result lists category completion without exposing deleted values.

## Failure Semantics

| Failure | Decision |
|---|---|
| OAuth unavailable | Isolate the adapter failure; email authentication remains available |
| Duplicate command | Replay the prior safe result through idempotency |
| Consent cannot be read | Fail closed and do not record or expose personalized features |
| Feature worker failure | Preserve durable event, retry asynchronously and serve last eligible snapshot only if consent/version still match |
| Export failure | Mark retryable job failure without exposing partial artifact |
| Deletion step failure | Keep account disabled, retain pending status and retry |
| U03 content reference unavailable | Reject new library/event mutation rather than invent content metadata |

## Traceability

| Flow | Story and Requirement |
|---|---|
| Email, OAuth, session and roles | US-014, US-027, FR-023, NFR 7.3 |
| Genre, OTT and library | US-015, US-016, FR-011, FR-024 |
| Feedback and feature refresh | US-017, FR-012, FR-025, DR-007, AC-005 |
| Consent, guest link, export and deletion | US-018, US-027, FR-022, FR-026, FR-027, DR-008, AC-007 |
| Pseudonymous U05 handoff | US-017, US-018, US-023 supporting, DR-007, DR-008 |
