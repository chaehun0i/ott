# U06 Engagement and Operations Domain Entities

## Aggregate Boundaries

| Aggregate | Root | Owned values/entities | Boundary |
|---|---|---|---|
| Notification Preference Projection | `NotificationPreference` | event-type/channel switches, source version | Read projection of U02 preference; U02 remains source of truth |
| Notification Job | `NotificationJob` | event snapshot, recipient reference, channel jobs, attempts | Delivery coordination only; no content approval or identity data |
| Admin Override | `AdminOverride` | field patches, lifecycle, conflict and application receipt | Coordinates U03/U04 command; never directly mutates their data |
| Audit Stream | `AuditEvent` | actor context, command, target, versions, outcome | Append-only privileged-action evidence |
| Trace Investigation | `TraceInvestigation` | query authorization, bounded result, audit reference | Read-only U05 trace consumer |
| Health Snapshot | `HealthSnapshot` | component contributions and aggregate states | Observation only; cannot change contributor health |
| Incident | `Incident` | correlated alerts, transitions, evidence, COE actions | Operational response record; U07 retains execution ownership |

## Identifiers and Versions

| Type | Meaning | Rule |
|---|---|---|
| `NotificationEventId` | One admitted approved-content event | Stable across reprocessing |
| `NotificationJobId` | One member/event delivery group | Unique for the deduplication key |
| `DeliveryAttemptId` | One channel attempt | Unique and append-only |
| `MemberReference` | Pseudonymous U02 subject reference | Must not be an email or direct user identifier |
| `OverrideId` | One field-scoped operator override | Immutable identity across lifecycle changes |
| `OperationId` | One requested admin command | Idempotent request identity |
| `AuditEventId` | One append-only audit fact | Never reused or updated |
| `TraceInvestigationId` | One privileged query attempt | Links request outcome and audit event |
| `HealthSnapshotId` | One aggregate observation | Contains source observation versions |
| `AlertSignalId` | One normalized alert observation | May join an existing incident |
| `IncidentId` | One correlated operational event | Stable through resolution and COE |
| `PolicyVersion` | Notification, override, health or incident policy | Immutable after activation |

## Notification Model

### `NotificationPreference`

Contains member reference, enabled event types, independently enabled channels, locale, region, quiet-time policy reference, source version and observed time. It contains no email address; a delivery adapter resolves the current destination through a purpose-limited U02 contract.

### `InterestSubscription`

Contains member reference, content ID, subscription state and version. Only active subscriptions can contribute to audience selection. Removal immediately invalidates undelivered jobs.

### `ApprovedNotificationEvent`

Contains content ID, event type, effective time, region, catalog version, approved title reference and source event version. Construction requires an approved U03 state. Raw provider and quarantine events cannot construct this value.

### `NotificationJob`

States are `pending`, `scheduled`, `processing`, `partially_delivered`, `delivered`, `cancelled`, `expired` and `failed`. It owns one `ChannelDelivery` per enabled channel. Terminal jobs are immutable except for retention metadata.

### `ChannelDelivery` and `DeliveryAttempt`

`ChannelDelivery` records channel, destination reference, state, next attempt and expiry. `DeliveryAttempt` records attempt number, bounded result code, provider receipt digest and time. It excludes rendered secret tokens and raw provider error bodies.

## Admin and Audit Model

### `AdminActorContext`

Contains pseudonymous actor reference, active roles/permissions, authentication strength reference, session/correlation ID and evaluated time. Authorization is evaluated for every command and is not inferred from a client-provided role string.

### `AdminOverride`

Contains target content ID, allowlisted typed field changes, reason, author reference, base catalog version, start, optional expiry and status. States are `requested`, `applying`, `active`, `conflicted`, `rejected`, `expired`, `revoked` and `failed`. Active and terminal revisions are immutable.

### `OverrideApplicationReceipt`

Contains operation ID, U03/U04 command version, previous/current catalog versions, applied fields and bounded outcome code. It proves external application but does not duplicate entire catalog rows.

### `AuditEvent`

Contains event ID/time, actor role and pseudonymous reference, action, target type/reference, reason code or bounded reason, correlation ID, before/after allowed field values or version digests, result and policy version. Audit records exclude credentials, session tokens, direct identity, raw prompts/responses and unrestricted payloads.

## Trace Investigation Model

### `TraceQuery`

Contains investigation ID, actor context, trace ID, requested bounded sections and correlation ID. It cannot request raw prompt, model response, chain-of-thought or member profile sections.

### `TraceView`

Contains U05 request/session pseudonymous references, intent/ranking/diversity/model/template/catalog/metadata/rule versions, candidate counts, decision/failure codes, bounded score components, validation outcomes and fallback path. It is an immutable projection and carries the U05 trace version.

## Health and Incident Model

### `HealthContribution`

Contains component name, criticality, required flag, state (`healthy`, `degraded`, `unhealthy`, `unknown`), stable reason code, observed time, freshness limit and bounded evidence references. It contains no log body or user input.

### `HealthSnapshot`

Contains liveness, readiness, deep and degraded views plus the exact contribution versions. Its aggregate state is derived, never manually overridden.

### `AlertSignal`

Contains source, service, symptom, impact scope, severity, observed interval, value/threshold references and correlation key. Repeated equivalent signals update occurrence evidence instead of creating unlimited records.

### `Incident`

Contains correlation key, severity, affected capabilities, state, owner, first/last detection, alert references, impact summary, mitigation/recovery evidence and resolution time. The lifecycle is detected to acknowledged to mitigating to monitoring to resolved, with monitoring allowed to return to mitigating on recurrence.

### `CorrectionOfErrors`

Contains incident reference, contributing factors, detection/response gaps, corrective actions, owners and due dates. It does not assign blame or copy sensitive logs.

## Relationships and Invariants

1. One approved event may create at most one job per member and stable event identity.
2. One job owns at most one delivery per supported channel.
3. A disabled preference, removed interest or unapproved content cannot have a deliverable pending job.
4. Reprocessing an event or delivery command cannot create an extra externally visible notification.
5. Every admin override references an expected U03 catalog version and an allowlisted field set.
6. Every privileged mutation and trace investigation has exactly one terminal audit outcome.
7. Audit events are append-only and cannot be rewritten by override lifecycle changes.
8. Trace views contain sufficient versioned decisions for investigation but no direct identity or model-internal content.
9. Readiness is unhealthy when any fresh required contribution is unhealthy, unknown or missing.
10. Optional dependency failure may degrade but cannot by itself make liveness false.
11. Equivalent alert signals map to the same open incident regardless of arrival order.
12. An incident cannot resolve without an owner and recovery evidence.

## Ownership and Contract Mapping

| External owner | U06 consumes | U06 must not consume or mutate |
|---|---|---|
| U02 | Role/permission decision, pseudonymous member, interest and notification preference/destination contracts | credentials, raw profile, direct identity tables |
| U03 | Approved event/content view and versioned content-operation command | unapproved records or catalog tables |
| U04 | Validation/quarantine status and authorized correction contract | validation rules or raw provider payloads |
| U05 | Privacy-safe `RecommendationTracePort` view | prompt, response body, chain-of-thought, ranking mutation |
| U07 | health contributions, alert input, job runtime and backup/deploy status | backup, restore, deploy or rollback execution ownership |

U06 owns no frontend component. U01 consumes future notification-settings, admin-operation, trace and incident API contracts.
