# U01 Requirements Traceability

Status: **Automated evidence complete; manual accessibility gate pending**

## Stories and acceptance scope

| Story scope | Requirement scope | Implementation | Automated evidence | Remaining evidence |
|---|---|---|---|---|
| US-001 through US-003 | FR-001 through FR-006, DR-006, AC-001, AC-008 | Feed, canonical filters, detail/back, freshness and degraded states | Feed/component/PBT/browser suites | Feed to Detail to Back screen-reader journey |
| US-004 through US-007 | FR-003, FR-007 through FR-009, FR-033 through FR-035, accessibility NFRs | Search, interpreted conditions, locale resources and semantic shell | Search/component/contract/PBT/axe/browser suites | Search screen-reader journey |
| US-008 through US-013 | FR-009 through FR-022, FR-036 through FR-040, AC-002 through AC-004 and AC-011 through AC-013 | Recommendation start/refine/reset, summary, reason and evidence disclosure | Recommendation component/PBT/contract/browser suites | Recommendation announcement screen-reader journey |
| US-014 through US-018 | FR-011, FR-012 and FR-023 through FR-027, DR-007, AC-005 and AC-007 | Pending Intent, account preferences, protected state and consent purge | Auth/state PBT, account component and browser suites | Login Pending Intent and consent-withdrawal screen-reader journeys |
| US-019 | FR-028 and FR-029 | Notification route and preference control | Component, route and browser regression | Covered by common manual navigation only; no separate blocker |
| US-021 | FR-030 through FR-032 | Admin denial and protected operator navigation | Contract/security/browser suites | Admin access-denial screen-reader journey |
| US-027 | FR-026, NFR security/privacy/accessibility and AC-007 | Safe session state, privacy telemetry, semantic controls and denial handling | Security scan, telemetry tests, PBT, axe and browser suites | The six-journey manual gate |

## Business rules

| Rules | Implementation and verification |
|---|---|
| BR-U01-01 through BR-U01-04 | URL query model, return navigation and Pending Intent; query/auth PBT and browser journeys |
| BR-U01-05 through BR-U01-10 | Approved API presentation and recommendation conversation state; contract, component and PBT suites |
| BR-U01-11 through BR-U01-16 | Cookie/session boundary, 401/403 behavior, consent purge and operator isolation; security, state PBT and browser suites |
| BR-U01-17 through BR-U01-22 | Remote boundaries, stale/degraded display, bounded retry, safe errors and external URL validation; unit, contract and quality suites |
| BR-U01-23 through BR-U01-28 | Locale, fallback, keyboard, live regions, error references and alternatives; component, axe, PBT and browser suites plus pending manual screen-reader gate |

## Non-functional requirements

| NFR scope | Evidence |
|---|---|
| NFR-U01-01 through NFR-U01-07 | Build budget 78,984 gzip bytes/4 requests, route splitting, lazy assets and Playwright performance assertions |
| NFR-U01-08 through NFR-U01-09 and NFR-U01-11 through NFR-U01-13 | axe, semantic component tests, keyboard journeys and 200% reflow across four browser projects |
| NFR-U01-10 | **Pending:** actual NVDA/Chrome or VoiceOver/Safari results for all six journeys |
| NFR-U01-14 through NFR-U01-17 | Locale resources, TypeScript checks and Chromium/Firefox/WebKit/mobile matrix |
| NFR-U01-18 through NFR-U01-23 | Error boundaries, protected-state transitions, bounded client behavior, PBT and browser regression |
| NFR-U01-24 through NFR-U01-30 | Caddy CSP/security headers, safe navigation, privacy telemetry, dependency audit and source-map/secret scans |

## Property-based requirements

| Properties | Automated evidence |
|---|---|
| P-U01-01 through P-U01-03 | Canonical query round-trip, idempotence and insertion-order invariants |
| P-U01-04 | Locale fallback oracle |
| P-U01-05 | Consent-withdrawal purge invariant |
| P-U01-06 | Pending Intent exactly-once state model |
| P-U01-07 | Recommendation reset invariant |
| P-U01-08 | Remote-resource transition invariant |
| P-U01-09 | Unique and resolvable error-reference graph |
| P-U01-10 | Logout/operator-denial protected-state model |

All ten properties passed with fast-check. Backend property suites also passed 53 tests using Hypothesis seed 260726. Traceability is complete for automated evidence; NFR-U01-10 remains the single release blocker.
