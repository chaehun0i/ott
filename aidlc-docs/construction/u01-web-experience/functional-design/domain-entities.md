# U01 Web Experience Domain Entities

## Ownership Principle

These are presentation models, not copies of backend entities. Server identifiers and versions are opaque. UI projections may be discarded and rebuilt from URL plus API responses.

## Navigation and State

| Entity | Required fields | Invariants |
|---|---|---|
| `UiRoute` | route name, path params, normalized query | only registered public or guarded routes |
| `FeedQueryState` | filters, sort, cursor/page | canonical serialization is stable and shareable |
| `SearchQueryState` | raw text, interpreted conditions, filters | raw text remains editable; server interpretation is labeled |
| `RemoteResource<T>` | status, data, error, fetchedAt | stale data requires prior success and visible timestamp |
| `PendingIntent` | action type, safe payload reference, return route, consumed | contains no credential; consumed at most once |
| `LocaleState` | selected locale, fallback locale | supported UI locales are `ko` and `en` |

## Content Presentation

| Entity | Required fields | Invariants |
|---|---|---|
| `ContentCardView` | contentId, localized title, status, providers, freshness | approved server item only; fallback language is marked |
| `ContentDetailView` | title, synopsis, genres, runtime, people, availability, sources | external link enabled only when server marks it valid |
| `AvailabilityView` | provider, region, status, externalUrl validity | unavailable or invalid destinations are never actionable |
| `FreshnessView` | lastSuccessfulRefreshAt, stale flag, source label | stale state never suppresses last successful data silently |
| `RecommendationCardView` | content, summary, reason, evidence, validation state | only validated or server-provided safe fallback result renders |
| `EvidenceView` | field, source, value/version | evidence expansion cannot expose private prompt or direct identifier |

## Recommendation Conversation

| Entity | Required fields | Invariants |
|---|---|---|
| `ConversationView` | sessionId, turns, current conditions, result set | sessionId is opaque and removed on reset/expiry |
| `ConversationTurnView` | role, localized text, timestamp, status | failed user turn remains retryable without duplicate success turn |
| `ConditionChip` | key, value, operation source | removing a chip sends refine; UI cannot silently mutate server state |
| `RecommendationRequestState` | submission token, status | only one active submission per conversation |

## Identity, Consent and Feedback

| Entity | Required fields | Invariants |
|---|---|---|
| `SessionView` | authentication status, safe role flags, expiry hint | contains no token or credential material |
| `ProfileFormView` | editable fields, original version, field errors | success is server-authoritative; conflict preserves draft |
| `ConsentView` | purpose, status, effectiveAt | withdrawn purpose disables and purges derived UI state immediately |
| `FeedbackCommand` | event type, contentId, context reference, idempotency key | emitted only within consent and authentication policy |
| `DataRightsJobView` | requestId, type, status, expiry | download action appears only for ready, unexpired server response |

## Operator Presentation

| Entity | Required fields | Invariants |
|---|---|---|
| `AdminOverrideForm` | contentId, expectedVersion, changes, reason | reason and expected version are mandatory |
| `TraceView` | traceId, versions, filters, validation, fallback | excludes direct identity, raw prompt and provider response |
| `IncidentView` | incidentId, status, severity, timestamps, evidence | only server-authorized fields render under `/admin` |

## State Ownership and Cleanup

- URL owns shareable Feed and Search state.
- Server owns account, consent, recommendation conditions, content status and operator decisions.
- Component state owns transient drafts, disclosure controls and focus restoration targets.
- Logout clears protected caches, Pending Intent, conversation and operator state.
- Consent withdrawal additionally clears all personalization-derived state without waiting for navigation.
- Locale preference may persist, but never carries identity or behavioral data.
