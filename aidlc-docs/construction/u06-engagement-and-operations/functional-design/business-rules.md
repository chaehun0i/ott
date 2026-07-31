# U06 Engagement and Operations Business Rules

## Notification Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| NTF-01 | Only versioned U03 approved new-release, upcoming-release and availability events are admissible | Ignore event and record bounded reason |
| NTF-02 | Quarantined, withdrawn, expired, raw-provider and unknown-schema events never create jobs | Reject before audience lookup |
| NTF-03 | Delivery requires active interest and enabled event-type/channel preference at send time | Cancel or omit channel |
| NTF-04 | In-app and email are independent channels | Isolate failure to affected channel |
| NTF-05 | Member, content, event type, effective time and channel form the stable deduplication key | Return existing outcome on replay |
| NTF-06 | Preference removal, interest removal, approval withdrawal, supersession or expiry cancels pending delivery | Transition to cancelled/expired |
| NTF-07 | Retry count, delay and expiry are bounded by versioned channel policy | Mark terminal failure and alert |
| NTF-08 | Notification failure cannot fail Feed, Search or Recommendation requests | Continue core request path |

## Override and Authorization Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| OVR-01 | Server-side U02 authorization is required for every operation | Deny without target disclosure |
| OVR-02 | Read-only investigation and content mutation permissions are separate | Deny unauthorized command |
| OVR-03 | Only allowlisted description, availability-correction and exposure fields may be overridden | Reject entire patch |
| OVR-04 | Approval and validation-rule decisions cannot be overridden by U06 | Reject boundary violation |
| OVR-05 | Every mutation requires reason, expected catalog version and correlation ID | Reject malformed command |
| OVR-06 | Active override wins only for its declared fields and time window | Preserve approved automatic values elsewhere |
| OVR-07 | Expired/revoked override reveals the newest approved automatic value | Close override and refresh projection |
| OVR-08 | Stale expected version never overwrites newer U03 state | Return conflict with current version |
| OVR-09 | U06 calls U03/U04 application ports and never writes their tables | Fail closed and raise boundary signal |
| OVR-10 | Privileged action is successful only after application receipt and audit closure | Do not report unverified success |

## Audit and Trace Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| AUD-01 | Every mutation, denied mutation and privileged trace query has an append-only audit outcome | Fail closed for action/response |
| AUD-02 | Audit retains actor role/pseudonym, action, target, reason, correlation, allowed versions/fields and result | Reject incomplete audit event |
| AUD-03 | Direct identity, secrets, tokens, raw prompts/provider responses and unrestricted payloads are prohibited | Drop event and raise privacy alert |
| AUD-04 | Audit revisions are new events; existing events are never edited or deleted by business operations | Reject rewrite |
| TRQ-01 | Trace access requires explicit investigation permission and exact trace ID | Deny non-enumerating response |
| TRQ-02 | Trace view exposes only bounded U05 versions, counts, codes, scores, validation and fallback fields | Remove prohibited section |
| TRQ-03 | Trace not-found and forbidden outcomes are externally indistinguishable where enumeration is possible | Return common response code |
| TRQ-04 | U06 never reconstructs missing trace data from application logs or AI content | Report unavailable/incomplete |

## Health, Alert and Incident Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| OPS-01 | Liveness, readiness, deep health and degradation are distinct states | Reject ambiguous aggregate |
| OPS-02 | Missing, stale, unknown or unhealthy required contribution fails readiness | Set readiness unhealthy |
| OPS-03 | Optional dependency failure sets degraded state without changing liveness | Preserve traffic eligibility |
| OPS-04 | Every contribution uses bounded component and reason vocabularies | Reject unbounded label |
| OPS-05 | Equivalent service, symptom and impact signals share a correlation key | Update existing alert/incident |
| OPS-06 | Incident creation requires versioned severity and duration policy | Retain signal without premature incident |
| OPS-07 | Incident transitions follow detected, acknowledged, mitigating, monitoring, resolved | Reject invalid transition |
| OPS-08 | Monitoring may return to mitigating only for recurrence of the correlated symptom | Record recurrence and transition |
| OPS-09 | Resolution requires owner and recovery evidence | Keep incident monitoring |
| OPS-10 | Resolved incidents link a lightweight COE and corrective actions | Mark follow-up incomplete until linked |
| OPS-11 | U07 execution status cannot be overwritten by an operator display decision | Display source status and evidence |

## Retention and Privacy Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| PRV-01 | U06 stores pseudonymous member/actor references and purpose-limited destination references | Reject direct identifier |
| PRV-02 | Delivery error and alert evidence uses stable codes/digests, not provider bodies or message content | Redact and raise prohibited-field signal |
| PRV-03 | Notification bodies derive only from approved localized metadata templates | Cancel unsupported content |
| RET-01 | Pending operational state cannot outlive its business expiry | Expire deterministically |
| RET-02 | Audit and incident retention follows an explicit later NFR policy and legal hold supersedes normal deletion | Defer deletion under hold |
| RET-03 | Retention processing is bounded and checkpointed | Resume without reprocessing terminal records |

## Testable Properties - PBT-01

| ID | Component | Category | Property |
|---|---|---|---|
| P-U06-01 | Preference codec | Round-trip | Encoding then decoding any valid event/channel preference preserves meaning and source version |
| P-U06-02 | Event admission | Invariant/easy verification | Every admitted event references approved U03 content and a supported event type |
| P-U06-03 | Notification deduplication | Idempotence | Replaying any valid event/recipient/channel combination produces no additional visible delivery |
| P-U06-04 | Notification cancellation | Stateful/model | Random opt-in, interest, event, approval and delivery sequences match a simple job-state model after every command |
| P-U06-05 | Channel isolation | Invariant | Failure of one channel never changes another channel's valid state or a core request outcome |
| P-U06-06 | Override projection | Oracle | Field-wise override resolution equals a simple automatic-value plus active-override reference model |
| P-U06-07 | Override scope | Invariant | Output differs from approved input only at allowlisted active override fields |
| P-U06-08 | Override expiry/revoke | Idempotence | Repeated expiry or revoke produces the same terminal state and visible automatic value |
| P-U06-09 | Audit stream | Induction/invariant | Appending any valid event preserves all previous events in identical order and adds exactly one event |
| P-U06-10 | Trace privacy | Easy verification | No generated trace view or audit event contains a prohibited direct-identity, prompt, provider-response or secret field |
| P-U06-11 | Health aggregation | Oracle/commutativity | Aggregate state equals the reference truth table and is independent of contribution arrival order |
| P-U06-12 | Incident lifecycle | Stateful/model | Random valid alert and transition sequences match the reference incident state machine after each command |

Reusable generators are required for approved/invalid events, preference matrices, deduplication keys, delivery outcomes, versioned override patches, audit events, bounded trace views, health contributions, alert permutations and incident commands. Example-based tests remain mandatory for every primary story, access-denied path and degraded failure family.

## Extension Compliance

### Resiliency Baseline

| Rule | Status | Functional-design evidence |
|---|---|---|
| RESILIENCY-01 | Compliant | Core feed/recommendation paths are isolated from medium-criticality notifications; privileged operations and incident response are high-criticality control paths |
| RESILIENCY-02 | Compliant handoff | Approved 99.0% prototype target, RTO 4 hours and RPO 24 hours are referenced through U07 recovery status |
| RESILIENCY-03 | N/A at this stage | Production change governance is U07-owned; U06 retains immutable audit references |
| RESILIENCY-04 | N/A at this stage | Deployment/rollback execution is outside functional business logic |
| RESILIENCY-05 | Compliant | Metrics/log/trace decision facts, alert correlation and dashboard-consumable states are defined |
| RESILIENCY-06 | Compliant | Liveness, readiness, deep and degraded health semantics are explicit |
| RESILIENCY-07 | Compliant | Capacity, stale evidence, backup/deploy failure and repeated delivery failure can produce bounded signals |
| RESILIENCY-08 | N/A | Approved single-server prototype exception; production topology remains a transition gate |
| RESILIENCY-09 | N/A at this stage | Fixed prototype capacity; NFR Requirements will quantify limits and review triggers |
| RESILIENCY-10 | Compliant | Channel failures, cross-unit port failures and alert storms are isolated with bounded behavior |
| RESILIENCY-11 | Compliant handoff | U07 owns Backup and Restore; U06 consumes and links its status without redefining strategy |
| RESILIENCY-12 | Compliant handoff | Audit, incident and delivery persistence are included in U07 backup closure planning |
| RESILIENCY-13 | Compliant | Incident evidence and U07 status references preserve recovery/failback investigation flow |
| RESILIENCY-14 | Compliant handoff | Channel outage, stale health, alert storm and recovery recurrence are executable test scenarios for later stages |
| RESILIENCY-15 | Compliant | Incident ownership, response transitions, COE and corrective-action linkage are defined |

### Property-Based Testing

- PBT-01: compliant through P-U06-01~12 with explicit component and property-category mapping.
- PBT-02~08 and PBT-10: N/A for executable verification at Functional Design; the inventory is a mandatory Code Generation handoff.
- PBT-09: N/A until U06 NFR Requirements confirms the existing Python/Hypothesis stack.

### Security Baseline

Disabled in `aidlc-state.md` and N/A as an extension. OVR-01~10, AUD-01~04, TRQ-01~04 and PRV-01~03 preserve the project's core authorization, audit and privacy requirements.

No blocking enabled-extension finding remains at U06 Functional Design.
