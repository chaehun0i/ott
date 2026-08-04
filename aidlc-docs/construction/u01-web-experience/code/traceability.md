# U01 Requirements Traceability

Status: **Complete for Prototype Scope**

## Stories and acceptance scope

| Story scope | Requirement scope | Implementation | Verification evidence |
|---|---|---|---|
| US-001 through US-003 | FR-001 through FR-006, DR-006, AC-001, AC-008 | Feed, canonical filters, detail/back, freshness and degraded states | Feed/component/PBT plus four-project Playwright journeys |
| US-004 through US-007 | FR-003, FR-007 through FR-009, FR-033 through FR-035, NFR-U01-08 through NFR-U01-17 | Search, interpreted conditions, locale resources and semantic shell | Search/component/contract/PBT, axe, keyboard/focus, ARIA and browser matrix |
| US-008 through US-013 | FR-009 through FR-022, FR-036 through FR-040, AC-002 through AC-004 and AC-011 through AC-013 | Recommendation start/refine/reset, summary, reason and evidence disclosure | Recommendation component/PBT/contract, live-announcement and browser journeys |
| US-014 through US-018 | FR-011, FR-012, FR-023 through FR-027, DR-007, AC-005 and AC-007 | Pending Intent, account preferences, protected state and consent purge | Auth/state PBT, role/name component assertions and browser journeys |
| US-019 | FR-028 and FR-029 | Notification route and preference control | Component, route and browser regression |
| US-021 | FR-030 through FR-032 | Admin denial and protected operator navigation | Contract/security and browser denial journey |
| US-027 | FR-026, security/privacy/accessibility NFRs and AC-007 | Safe session state, privacy telemetry, semantic controls and denial handling | Security scan, telemetry tests, PBT, axe, keyboard/focus, ARIA and browser matrix |

## Automated accessibility mapping

| Requirement | Mandatory prototype evidence | Result |
|---|---|---|
| NFR-U01-08 | axe serious/critical violations = 0, semantic component tests and four-project browser matrix | Pass |
| NFR-U01-09 | Playwright keyboard-only critical journeys | Pass |
| NFR-U01-10 | Testing Library role/name/value, heading/landmark, live announcement and error-relationship assertions plus Playwright focus/announcement journeys | Pass |
| NFR-U01-11 | 200% zoom and mobile 320 CSS pixel reflow | Pass |
| NFR-U01-12 | Route focus movement, restoration and visible keyboard navigation | Pass |
| NFR-U01-13 | axe, alternative text, labels and error association component tests | Pass |
| NFR-U01-16 through NFR-U01-17 | Chromium, Firefox, WebKit and mobile Playwright projects | 24 passed |

Actual NVDA/Chrome or VoiceOver/Safari execution is **Out of Scope for Prototype / Future Manual QA**. It was not executed and is not part of the evidence claimed above.

## Business rules

| Rules | Implementation and verification |
|---|---|
| BR-U01-01 through BR-U01-04 | URL query model, return navigation and Pending Intent; query/auth PBT and browser journeys |
| BR-U01-05 through BR-U01-10 | Approved API presentation and recommendation conversation; contract, component and PBT suites |
| BR-U01-11 through BR-U01-16 | Session boundary, 401/403 behavior, consent purge and operator isolation; security, state PBT and browser suites |
| BR-U01-17 through BR-U01-22 | Remote boundaries, stale/degraded display, bounded retry, safe errors and external URL validation |
| BR-U01-23 through BR-U01-28 | Locale, fallback, keyboard, focus, live regions, error references and alternatives; component, axe, PBT and browser suites |

## Non-functional requirements

| NFR scope | Evidence |
|---|---|
| NFR-U01-01 through NFR-U01-07 | Build budget 78,984 gzip bytes/4 requests, route splitting, lazy assets and Playwright performance assertions |
| NFR-U01-08 through NFR-U01-13 | Automated accessibility mapping above |
| NFR-U01-14 through NFR-U01-17 | Locale resources, TypeScript and Chromium/Firefox/WebKit/mobile matrix |
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

All ten frontend properties passed with fast-check. Backend Hypothesis property suites passed 53 tests using seed 260726. No prototype traceability gap remains.
