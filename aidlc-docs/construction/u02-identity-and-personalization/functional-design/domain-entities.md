# U02 Domain Entities

## Aggregate Overview

| Aggregate | Root | Main Members | Consistency Boundary |
|---|---|---|---|
| Identity | User | Credential, OAuthLink, RoleAssignment, Session | authentication state, usable login method and authorization version |
| Profile | UserProfile | GenrePreference, OttSubscription | mutually exclusive preference state and ProfileVersion |
| Library | UserLibrary | WatchItem, Rating, WatchHistoryEntry | one current record per user and content type |
| Consent | ConsentLedger | ConsentDecision, GuestLinkAuthorization | latest decision per purpose and immutable history |
| Feedback | BehaviorEventStream | BehaviorEvent, EventDeduplication | append-only eligible events and idempotency |
| Personalization | PersonalizationFeatureSet | FeatureValue, FeatureSnapshotLease | consent-bound derived state and version |
| DataRights | DataRightsRequest | ExportArtifact, DeletionStep | authorized asynchronous lifecycle and closure |

## Identity Aggregate

### User

| Field | Type | Rule |
|---|---|---|
| user_id | UserId | opaque, immutable |
| status | pending_verification, active, disabled, deletion_pending, deleted | controlled transition only |
| primary_email | NormalizedEmail | unique among non-deleted identities |
| email_verified_at | Instant optional | required for active email login |
| authorization_version | positive integer | increments on role/security change |
| created_at, updated_at | Instant | server clock |
| row_version | positive integer | optimistic concurrency |

### Credential

- `credential_id`, `user_id`, password hash envelope, hash policy version, created time, last changed time and disabled time.
- Plain passwords never enter the domain entity or persistence model.
- Only one active password credential exists per user in the initial model.

### OAuthLink

- `oauth_link_id`, `user_id`, provider=`google`, provider subject, verified email claim snapshot, linked time and revoked time.
- Provider subject is unique within provider.
- Provider token material belongs to the OAuth secret adapter, not this entity.

### RoleAssignment

- Role is Member, ContentOperator or SystemAdministrator.
- Assignment records grant time, granting actor, reason and revoke time.
- A user can hold multiple roles, while authorization evaluates the union of versioned fixed permissions.

### Session

- `session_id`, `user_id`, hashed session secret reference, device label, issued time, last seen time, expiry, revoked time and revoke reason.
- Active requires not expired, not revoked and owning user status active.

## Profile Aggregate

### UserProfile

- `user_id`, locale, profile_version, created time and updated time.
- Contains maps keyed by canonical genre ID and OTT provider ID.

### GenrePreference

- State is `liked` or `disliked`; absence represents unspecified.
- A genre cannot be liked and disliked in the same ProfileVersion.
- Provenance is explicit user command, never inferred behavior.

### OttSubscription

- State is `subscribed`, `not_subscribed` or `unspecified`.
- U02 stores the member declaration, while U03 owns actual regional availability.

## Library Aggregate

| Entity | Natural uniqueness | Value |
|---|---|---|
| WatchItem | user_id + content_id | saved_at or absent |
| Rating | user_id + content_id | integer 1~5, rated_at, modified_at |
| WatchHistoryEntry | user_id + content_id | completed flag, last_watched_at |

Every mutation records source surface, request correlation and row version. Deletion removes the current record and emits a feature invalidation event.

## Consent Aggregate

### ConsentPurpose

- `required_service`: records the processing notice acknowledged for service execution; it is not represented as optional personalization permission.
- `personalization`: optional and must be granted for behavior learning and personalized FeatureSnapshot output.

### ConsentDecision

| Field | Purpose |
|---|---|
| consent_decision_id | immutable evidence identifier |
| user_id or guest_subject_id | exactly one subject type |
| purpose | versioned ConsentPurpose |
| decision | granted or withdrawn |
| policy_version, notice_version | exact text/policy reference |
| source | UI/API surface and locale |
| decided_at | server acceptance time |
| supersedes_id | previous decision link |

Consent history is immutable. The current decision is a projection selected by subject, purpose and sequence.

### GuestLinkAuthorization

- Links one guest pseudonym to one user only after an explicit grant.
- Records allowed event interval, policy version, grant time and consumed time.
- Consumption is single-use and cannot include events made after withdrawal.

## Feedback Aggregate

### BehaviorEvent

- `event_id`, pseudonymous subject reference, content ID, event type, occurred time, received time, source surface, recommendation version, minimal typed attributes, consent decision ID and processing status.
- Event types: content_click, save, unsave, rate, unrate, recommendation_refresh, recommendation_dismiss, ott_outbound and watch_complete.
- Direct email, OAuth subject, credential material, raw provider response and free-form PII are forbidden.

### EventDeduplication

- Primary key: subject scope + event type + client idempotency key.
- Fallback fingerprint: subject scope + content + event type + bounded time bucket + normalized typed attributes.
- A duplicate points to the first EventId and cannot create another feature contribution.

## Personalization Aggregate

### PersonalizationFeatureSet

- Keyed internally by UserId and FeatureVersion.
- Stores explicit genre/OTT features, library-derived features and aggregated behavior-derived features with provenance.
- Carries the ConsentVersion used for derivation and becomes ineligible when that version is no longer current and granted.

### FeatureSnapshot

| Field | Rule |
|---|---|
| request_subject | newly derived request-scoped pseudonym |
| feature_version | immutable snapshot version |
| consent_version | current granted personalization decision |
| generated_at, valid_until | bounded lifetime |
| features | allow-listed typed values only |

The mapping from request subject to UserId exists only inside the U02 request boundary and expires with the request context.

## Data Rights Aggregate

### DataRightsRequest

- Type is export or deletion.
- Status is requested, authorized, processing, completed or failed_retryable; deletion additionally supports partially_completed while retrying.
- Records requester, reauthentication proof reference, requested time, idempotency key and status version.

### ExportArtifact

- Encrypted object reference, checksum, created time, expiry and download-consumed state.
- The database does not store an unencrypted export body.

### DeletionStep

- Categories: sessions, credentials, oauth_links, profile, library, behavior_events, features and export_artifacts.
- Each step records attempt count, completion time and safe failure code.
- Deletion is terminal only when every required step is complete and account status is deleted.

## Ownership and Reference Rules

- U02 owns all entities in this document and never writes U03/U05/U06 tables.
- ContentId is an external reference validated through an U03 read contract.
- Outbox job identity and lease mechanics are owned by U07; U02 owns job payload schema and business outcome.
- Audit event transport is a U06 contract; U02 emits minimal security and data-rights facts without credential or export content.

