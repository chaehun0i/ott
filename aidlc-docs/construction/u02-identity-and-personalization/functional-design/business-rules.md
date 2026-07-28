# U02 Business Rules

## Identity and Authentication

| Rule | Definition |
|---|---|
| BR-U02-001 | Email login uses a password credential and verified email ownership. |
| BR-U02-002 | Email normalization is deterministic; unverified callers receive non-enumerating outcomes. |
| BR-U02-003 | Password plaintext is never stored, logged or returned. |
| BR-U02-004 | A verification challenge is single-use, purpose-bound and expires. |
| BR-U02-005 | An expired, revoked or deleted-user session cannot authorize any protected command. |
| BR-U02-006 | Multiple sessions are allowed and a member can revoke one or all of their sessions. |
| BR-U02-007 | Google is the only enabled initial OAuth provider; the provider boundary remains extensible. |
| BR-U02-008 | A verified provider email does not automatically link an account. Existing-account reauthentication and explicit confirmation are mandatory. |
| BR-U02-009 | One provider subject can belong to at most one user. |
| BR-U02-010 | Unlinking the final usable authentication method is forbidden. |

## Authorization

| Rule | Definition |
|---|---|
| BR-U02-011 | Roles are Member, ContentOperator and SystemAdministrator with versioned fixed permissions. |
| BR-U02-012 | Member access is restricted to the authenticated member's resources. |
| BR-U02-013 | ContentOperator cannot grant roles or read identity secrets. |
| BR-U02-014 | SystemAdministrator cannot bypass consent or retrieve credential material. |
| BR-U02-015 | Every protected command authorizes server-side against current user status, role and authorization version. |
| BR-U02-016 | Role and security changes increment authorization version and invalidate stale authorization contexts. |

## Preferences and Library

| Rule | Definition |
|---|---|
| BR-U02-017 | A genre has at most one explicit state: liked, disliked or unspecified. |
| BR-U02-018 | An OTT provider state is subscribed, not_subscribed or unspecified. |
| BR-U02-019 | Preference updates use optimistic version checks and increment ProfileVersion exactly once on success. |
| BR-U02-020 | A user-content pair has at most one current saved item, rating and history entry of each type. |
| BR-U02-021 | Repeating a save command is idempotent and does not create a duplicate record or contribution. |
| BR-U02-022 | Rating is an integer in the closed range 1 through 5. |
| BR-U02-023 | Initial watch history records completion and most recent watch time; progress percentage is out of scope. |
| BR-U02-024 | Removing or changing library state invalidates any feature derived from the previous state. |

## Consent, Privacy and Feedback

| Rule | Definition |
|---|---|
| BR-U02-025 | Required service processing and optional personalization are distinct purposes. |
| BR-U02-026 | Personalization events and personalized features require a current granted personalization ConsentSnapshot. |
| BR-U02-027 | Failure to read or validate consent fails closed. |
| BR-U02-028 | External AI receives no email, OAuth subject, credential, session secret or raw event payload. |
| BR-U02-029 | Consent decisions are immutable evidence; a new decision supersedes but does not mutate the prior decision. |
| BR-U02-030 | Withdrawal immediately blocks new personalization collection and feature disclosure. |
| BR-U02-031 | Withdrawal schedules deletion of personalization source events and all derived features. |
| BR-U02-032 | Minimal consent evidence and required operational tombstones cannot be reused for personalization. |
| BR-U02-033 | Guest behavior is never linked implicitly at signup or login. |
| BR-U02-034 | Guest linking requires a separate explicit grant and consumes only the named eligible guest scope. |
| BR-U02-035 | Explicit save and rating actions update authoritative state and features synchronously. |
| BR-U02-036 | Implicit click, dismiss and OTT outbound events are persisted before asynchronous feature processing. |
| BR-U02-037 | Client idempotency key is primary; a bounded server fingerprint is used only when the key is absent. |
| BR-U02-038 | A duplicate event cannot add a second feature contribution. |
| BR-U02-039 | Recommendation and feed version references are recorded for evaluation without storing unnecessary direct identifiers. |

## Feature Snapshot

| Rule | Definition |
|---|---|
| BR-U02-040 | U05 receives a request-scoped pseudonymous subject, allow-listed feature values, FeatureVersion and ConsentVersion only. |
| BR-U02-041 | Request pseudonyms are not stable across unrelated requests and cannot be reversed outside U02. |
| BR-U02-042 | A snapshot is eligible only while its ConsentVersion remains the current granted decision. |
| BR-U02-043 | Missing, withdrawn or stale consent yields a non-personalized context, never a stale personalized snapshot. |
| BR-U02-044 | Explicit preference provenance remains distinct from inferred behavior provenance. |

## Data Rights

| Rule | Definition |
|---|---|
| BR-U02-045 | Export and deletion require fresh reauthentication and user-scoped authorization. |
| BR-U02-046 | Export includes readable user data and decision history but excludes password hashes, provider tokens and server secrets. |
| BR-U02-047 | Export artifacts are encrypted, expire and cannot be downloaded by another identity. |
| BR-U02-048 | Accepted deletion immediately disables login and revokes all sessions. |
| BR-U02-049 | Deletion is asynchronous, idempotent and retryable; partial failure never reactivates the account. |
| BR-U02-050 | Deletion completes only after all owned personal and personalization categories are removed and caches invalidated. |
| BR-U02-051 | Retained tombstones contain no reusable profile, library, behavior or feature values. |

## State Transition Constraints

### User Status

- pending_verification → active: valid email verification only
- pending_verification → disabled: expiry or administrative safety action
- active → disabled: security or administrative action
- active or disabled → deletion_pending: authorized deletion request
- deletion_pending → deleted: all deletion steps complete
- deleted has no outgoing transition

### Consent

- absent → granted
- granted → withdrawn
- withdrawn → granted only through a new explicit decision and a new ConsentVersion
- deletion_pending prevents new grant or feature output

### Data Rights Request

- requested → authorized → processing → completed
- processing → failed_retryable → processing
- deletion processing may expose partially_completed status but cannot return to requested or authorized

## Property-Based Test Candidates

| Property | Invariant or Oracle | Trace |
|---|---|---|
| PBT-U02-01 Save idempotency | Applying save N times yields one current WatchItem and one feature contribution. | US-016, BR-U02-020~021 |
| PBT-U02-02 Rating bound | Every accepted rating is an integer 1~5; every other value is rejected without state change. | US-016, BR-U02-022 |
| PBT-U02-03 Preference exclusivity | A genre cannot be liked and disliked in the same ProfileVersion. | US-015, BR-U02-017~019 |
| PBT-U02-04 Session revocation | Once revoked or expired, no future authorization decision succeeds for that session. | US-014, BR-U02-005~006 |
| PBT-U02-05 Account linking uniqueness | Reordering or retrying link commands never binds one provider subject to two users. | US-014, BR-U02-008~010 |
| PBT-U02-06 Consent non-bypass | Without current grant, every event collection and personalized snapshot path fails closed. | US-017~018, BR-U02-025~031 |
| PBT-U02-07 Duplicate isolation | Duplicate keys or equivalent fallback fingerprints yield the original EventId and no extra contribution. | US-017, BR-U02-037~038 |
| PBT-U02-08 Withdrawal closure | After withdrawal completion, source personalization events and derived features for the purpose are empty. | US-018, BR-U02-030~032 |
| PBT-U02-09 Snapshot minimization | Serialized FeatureSnapshot contains only allow-listed fields and never direct identifier patterns. | US-017~018, DR-007~008, BR-U02-040~044 |
| PBT-U02-10 Deletion terminality | All command sequences reaching deleted can never transition to active or produce a session/feature. | US-018, BR-U02-048~051 |
| PBT-U02-11 Serialization round trip | Versioned ConsentDecision, Profile and FeatureSnapshot DTOs preserve semantic equality. | PBT-03, U07 contract |

## Error Categories

- `IdentityValidationError`: invalid email, password policy, verification challenge or OAuth callback
- `AuthenticationError`: safe invalid credentials, expired or revoked session
- `AuthorizationError`: unauthenticated, forbidden role or wrong resource owner
- `IdentityConflictError`: verified email, provider subject or optimistic version conflict
- `ConsentRequiredError`: no eligible current grant
- `LibraryValidationError`: invalid content reference, rating or transition
- `DataRightsError`: reauthentication required, artifact expired or terminal request conflict
- `DependencyError`: OAuth, U03 reference, persistence or worker unavailable

Errors expose stable codes, correlation ID and retryability only. They do not expose account existence, credential state, provider payload, personal data or export content.

## Extension Compliance

| Extension | Status | Rationale |
|---|---|---|
| Resiliency | Compliant | OAuth isolation, durable event-first processing, retryable export/deletion and fail-closed consent paths are explicit. |
| Property-Based Testing | Compliant | Eleven domain properties cover idempotency, bounds, state, isolation, privacy closure and round trip. |
| Security Baseline | N/A | Disabled in aidlc-state; core authentication, authorization and privacy requirements remain mandatory and traced. |
| Frontend | N/A | U02 owns no UI. U01 receives account/privacy contract and accessibility responsibility. |

