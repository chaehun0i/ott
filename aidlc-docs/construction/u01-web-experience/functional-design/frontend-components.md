# U01 Web Experience Frontend Components

## Component Hierarchy

- `AppShell`
  - `SkipLink`, `GlobalHeader`, `PrimaryNavigation`, `LocaleSelector`, `RouteAnnouncer`
  - Public routes: `FeedPage`, `SearchPage`, `ContentDetailPage`, `RecommendationPage`
  - Member routes: `LibraryPage`, `AccountPage`, `NotificationSettingsPage`
  - Operator boundary: `AdminShell` with `AdminContentPage`, `TracePage`, `IncidentPage`
  - Shared overlays: `LoginDialogOrPage`, `ToastRegion`, `ErrorSummary`

## Page Responsibilities

| Component | Inputs/state | User interactions | API integration |
|---|---|---|---|
| `FeedPage` | canonical `FeedQueryState`, `RemoteResource<Feed>` | filter, sort, paginate, open detail | U03 `GET /feed` |
| `SearchPage` | raw query, interpreted conditions, filters | submit, edit/remove condition, paginate | U03 `POST /search` |
| `ContentDetailPage` | contentId, return location, detail resource | save/rate, external OTT, return | U03 `GET /contents/{content_id}`; U02 feedback/library |
| `RecommendationPage` | conversation, draft, request state | start, refine, remove condition, reset | U05 recommendation endpoints |
| `AccountPage` | profile, consent, data-rights jobs | update, withdraw, export, delete | U02 identity/profile/consent/data-rights |
| `NotificationSettingsPage` | preferences and delivery state | enable/type/channel changes | U06 notification contract |
| `AdminContentPage` | content projection, override form | submit versioned override | U06 `POST /admin/content/{content_id}/override` |
| `TracePage` | safe trace projection | trace lookup | U06 `GET /admin/traces/{trace_id}` |
| `IncidentPage` | incident list and filters | refresh/filter/open | U06 `GET /admin/incidents` |

## Shared Components

| Component | Props | Local state | Rules |
|---|---|---|---|
| `ContentCard` | localized content, freshness, actions | disclosure open | card title is one link; buttons have distinct names |
| `FilterBar` | schema, selected values, result count | mobile disclosure | changes serialize to canonical URL |
| `ConditionChips` | server conditions, pending keys | none | removal emits command; disabled while pending |
| `RecommendationReason` | summary, reason, evidence | evidence expanded | summary/reason visible; evidence accessible on demand |
| `RemoteRegion` | resource state, retry callback | none | renders loading/empty/stale/degraded/error consistently |
| `ProtectedAction` | action descriptor, session status | pending intent | successful login consumes intent once |
| `ExternalOttLink` | validated destination and provider | none | disabled when invalid; announces new tab |
| `LocalizedText` | translations, original, selected locale | none | follows and labels fallback chain |
| `ConsentControl` | purpose and status | confirm open/submitting | success purges related caches before announcement |

## Form Validation

- Client validation provides immediate completeness and format feedback but does not replace server rules.
- Submitted drafts remain intact on validation, conflict, rate-limit and recoverable server errors.
- Errors use stable unique IDs, `aria-describedby`, a page summary and a link/focus target to each field.
- Version conflicts display the latest server value and require explicit review before resubmission.
- Destructive account or consent commands require a consequence summary and explicit confirmation.

## Focus and Announcement Flows

- Route change focuses the page heading after the route announcement.
- Detail back navigation restores focus to the originating card when it still exists, otherwise to the results heading.
- Filter changes announce the settled result count, not each keystroke.
- Recommendation submission announces processing once, then result count or a recoverable error.
- Modal/sheet close returns focus to its invoker; hidden content is removed from the focus order.
- Consent withdrawal announces completion after personalized state is purged.

## API Client Boundary

- Generated OpenAPI types are the only transport shapes used by page adapters.
- A mapper converts each transport response to presentation entities and rejects unknown unsafe action URLs.
- The client applies explicit request cancellation on superseded reads and never retries unsafe writes automatically.
- 401, 403, 409, 422, 429 and 5xx map to distinct typed UI outcomes; unknown failures use a safe generic outcome.
- CSRF and session handling remain in the shared API boundary and are never exposed as component props.

## Responsive Behavior

- The same semantic order is retained across viewport sizes.
- Primary navigation collapses without hiding route availability.
- Filters become an accessible disclosure or sheet on narrow layouts; applying them updates the same canonical URL.
- Detail uses its own route on all viewports, preserving predictable history and deep links.
- Admin retains a separate layout and does not collapse privileged controls into public content cards.

## Component Test Matrix

| Area | Example tests | Property tests |
|---|---|---|
| Routing/query | deep link, back/focus restoration | P-U01-01~03 |
| Localization | Korean/English and missing translation | P-U01-04 |
| Consent/auth | withdrawal, login replay, logout, 403 | P-U01-05~06, P-U01-10 |
| Recommendation | start/refine/reset and expiry | P-U01-07 |
| Degraded UI | stale data and local retry | P-U01-08 |
| Forms/accessibility | invalid submit and error navigation | P-U01-09 |
