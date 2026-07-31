# U06 Engagement and Operations Business Logic Model

## Scope and Ownership

U06 owns member notification delivery, authorized content-operation coordination, privacy-safe recommendation trace investigation, health aggregation, alert correlation and incident lifecycle management. It does not approve content, mutate another unit's tables, alter recommendation ranking or validation, or execute deployment and backup operations.

- C13 Notification consumes only approved U03 events and current U02 notification preferences.
- C14 Admin Content coordinates version-conditional commands through U03 and U04 ports and records every outcome.
- C14 Trace Query exposes a bounded U05 trace view without direct identifiers, raw prompts, provider responses or model reasoning.
- C14 Operations aggregates U07 health contributions and converts correlated alerts into auditable incidents.

## Notification Flow

### 1. Event Admission

1. Accept a versioned U03 event only when the content is approved, not withdrawn, regionally relevant and one of the supported event types: new release, upcoming release or availability change.
2. Reject quarantine, expired, withdrawn, raw-provider and unknown-schema events before audience selection.
3. Construct an immutable event identity from content ID, event type, effective release/availability time and source event version.
4. Record an ignored outcome for invalid or duplicate events without creating a delivery job.

### 2. Audience and Preference Resolution

1. Read interest subscriptions and notification preferences through U02 using a pseudonymous member reference.
2. Require both a matching content interest and an enabled event-type/channel combination.
3. Support in-app and email independently. Disabling one channel does not disable the other.
4. Recheck preferences and content approval immediately before delivery so withdrawal or opt-out cancels pending work.

### 3. Deduplication, Scheduling and Delivery

The stable deduplication key is member reference, content ID, event type, effective time and channel. Reprocessing the same event returns the existing job or terminal result. A materially changed event version may supersede a pending job but cannot duplicate an already delivered equivalent notification.

Each channel owns an independent delivery attempt sequence. Attempts are bounded by retry count, next-attempt time and expiry. A channel failure never blocks another channel and never fails Feed, Search or Recommendation requests. Terminal failure is retained as an operational fact and contributes to alerts.

### 4. Cancellation

Pending jobs become cancelled when the member opts out, the interest is removed, the content loses approval, the event is superseded or the delivery expires. Delivered messages are not retroactively deleted by the job processor, but their delivery record remains linked to the preference and event versions used at send time.

## Admin Content Override Flow

### 1. Admission and Authorization

1. Resolve the actor through U02 and require a current content-operation permission.
2. Separate read-only investigation from mutation permission.
3. Require target content ID, expected catalog version, allowed field set, reason, requested start and optional expiry.
4. Reject direct approval changes, validation-rule changes, unapproved source payloads and unrestricted free-form patch paths.

### 2. Conflict and Policy Evaluation

An override applies only to allowlisted descriptive fields, availability corrections and exposure state. It is field-scoped and carries author, reason, base version, start, expiry and status. Active overrides take precedence only for their fields. Automatic values continue to advance as new approved versions and are displayed as conflicts when different.

The command uses compare-and-set semantics against the expected U03 version. A stale command returns a conflict containing current version metadata but no hidden record fields. Expired or explicitly revoked overrides stop applying, after which the newest approved automatic value is visible.

### 3. Cross-Unit Commit and Audit Closure

U06 writes a pending operation record, calls the U03/U04 application port outside a long U06 transaction, then closes the operation as applied, rejected, conflicted or failed. It never writes U03/U04 tables directly. Every attempt produces an append-only audit event covering actor role and pseudonymous reference, command type, target, reason, correlation ID, allowed before/after values or versions and outcome.

## Recommendation Trace Investigation Flow

1. Require an authenticated operator with trace-investigation permission and a valid trace ID.
2. Fetch only the U05 `RecommendationTracePort` bounded view.
3. Return intent/ranking/policy/model/metadata/rule versions, candidate counts and decision codes, bounded score components, validation results and fallback path.
4. Exclude member identity, raw natural-language input, raw provider request/response, prompt text, credentials, behavior history and chain-of-thought.
5. Audit success, not-found and denied outcomes using the trace ID and correlation ID. A not-found response does not reveal whether another user's trace exists.

## Health, Alert and Incident Flow

### 1. Health Aggregation

U06 maintains separate views:

- `liveness`: the process can execute;
- `readiness`: all required contributors can serve their critical path;
- `deep`: required and optional dependency details for authorized operators;
- `degraded`: required paths remain available but a non-critical dependency or quality objective is impaired.

Every contribution contains component name, required/optional class, state, stable reason code, observed time and freshness limit. Stale or missing required evidence fails readiness. Stale or failed optional evidence produces degraded state without removing healthy traffic.

### 2. Alert Correlation

Alerts are normalized to service, symptom, impact scope, severity, first/last observation and evidence references. The correlation key groups repeated signals for the same service, symptom and impact. A signal opens or updates an incident only after its severity and duration policy is satisfied. Recovery signals move the incident to monitoring rather than deleting it.

### 3. Incident Lifecycle

The allowed lifecycle is `detected`, `acknowledged`, `mitigating`, `monitoring`, `resolved`. Transitions are forward-only except a monitoring incident may return to mitigating when the same symptom recurs. Each transition records actor/system source, owner, impact, action, evidence and time. Resolution requires recovery evidence and an owner. A resolved incident links a lightweight correction-of-errors record and tracked follow-up actions.

Backup, restore, deployment and rollback execution remain U07-owned. U06 links their status and evidence into the incident but cannot mark a failed U07 operation successful.

## Degraded Behavior

| Failure | Functional response | Preserved invariant |
|---|---|---|
| U02 preference unavailable | Delay notification audience resolution within expiry | No notification without current permission/preferences |
| Email adapter unavailable | Retry only email within bounds; in-app continues | Channel isolation |
| U03 event or content becomes invalid | Cancel pending jobs | Approved-content closure |
| U03/U04 override port unavailable | Keep operation pending/failed and do not mutate locally | No cross-unit table write or assumed success |
| U05 trace unavailable | Return bounded unavailable/not-found response and audit it | No reconstruction from logs or AI content |
| Optional health contributor fails | Report degraded with reason | Required readiness remains accurate |
| Alert storm | Correlate into one incident and bounded updates | No unbounded incident creation |
| Audit persistence fails | Fail closed for admin mutation and privileged trace response | No unaudited privileged action |

## Story and Requirement Traceability

| Flow | Stories | Requirements |
|---|---|---|
| Approved event notification and preferences | US-019 | FR-028, FR-029 |
| Versioned content override and audit | US-021 | FR-030, FR-031, FR-032 |
| Privacy-safe recommendation trace investigation | US-023, supporting US-022 | FR-042, DR-008, DR-014 |
| Health, alert and incident response | US-025, supporting US-024/026/028 | NFR 7.7, NFR 8.5, RESILIENCY-05~07, RESILIENCY-15 |
| Role and privacy boundary | supporting US-027 | NFR 7.3, NFR 7.4 |
