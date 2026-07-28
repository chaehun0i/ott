# U02 Requirements, Story and Test Traceability

## Story Coverage

| Story | U02 implementation evidence | Test evidence | Status |
|---|---|---|---|
| US-014 | Authentication, Google adapter, session and authorization services | application service, OAuth, API cookie/CSRF and PostgreSQL uniqueness tests | Complete for U02 |
| US-015 | Versioned genre/OTT profile and explicit feature refresh | domain rules, service tests and PBT-U02-03 | Complete for U02; U05 owns cold-start ranking blend |
| US-016 | Idempotent save, bounded rating and completed-watch state | service tests, PBT-U02-01~02 and PostgreSQL repositories | Complete |
| US-017 | Consent-gated deduplicated behavior events and FeatureVersion projection | feedback/feature tests, PBT-U02-06~09 and telemetry gate | Complete |
| US-018 | Immutable consent, explicit guest link, export and deletion saga | service, API, PBT-U02-08/10 and failure-injection tests | Complete |
| US-027 | Encryption, secret files, authorization, validation and safe audit dimensions | security/PBT/API/integration/secret scan | Complete for U02; U01 accessibility and external legal review remain separate gates |

## Functional and Data Requirements

| Requirement | Implementation | Verification |
|---|---|---|
| FR-011 | Genre and OTT explicit profile snapshot for downstream cold start | profile service and PBT-U02-03 |
| FR-012 | Explicit/implicit signals and versioned feature projection | feedback and feature services, contribution dedup tests |
| FR-022 | Personalization consent and deletion control boundary | consent and data-rights services |
| FR-023 | Email/password and Google login | auth, OAuth, session and API contract tests |
| FR-024 | Profile, save, rating and watch history | library/profile service and PBT-U02-01~03 |
| FR-025 | Purpose-bound feedback events | consent failure, event dedup and PostgreSQL tests |
| FR-026 | Consent, status, encrypted export and deletion | API/service/integration/PBT-U02-08/10 |
| FR-027 | Explicit scoped guest linking only | guest authorization and consent tests |
| DR-007 | Pseudonymous typed events without unnecessary direct identifiers | feedback, telemetry allow-list and privacy scan |
| DR-008 | Request-scoped allow-listed FeatureSnapshot for U05 | PBT-U02-09 and feature snapshot tests |

## Business Rule Groups

| Rules | Primary evidence |
|---|---|
| BR-U02-001~010 | Authentication, challenge, OAuth/linking, session and unique-index tests |
| BR-U02-011~016 | Role policy, fresh-auth and authorization-version tests |
| BR-U02-017~024 | Profile/library service tests and PBT-U02-01~03 |
| BR-U02-025~039 | Consent/feedback service tests, PBT-U02-06~08 and failure injection |
| BR-U02-040~044 | Feature CAS, minimized snapshot and PBT-U02-09 |
| BR-U02-045~051 | Export/deletion service, PostgreSQL retry, one-time artifact and PBT-U02-10 |

## Property Requirements

PBT-U02-01 through PBT-U02-11 are implemented under
`backend/tests/identity/pbt/`. Deterministic seed `270727`, shrinking and regression-promotion
guidance are recorded in `pbt-evidence.md`. PostgreSQL integration tests remain separate and cannot
be replaced by in-memory properties.

## Cross-Unit Boundaries

- U01 consumes the OpenAPI contract and owns accessible browser interaction.
- U03 validates referenced ContentId values; the U02 catalog port fails closed when unavailable.
- U05 receives only request-scoped pseudonyms and allow-listed FeatureSnapshot values.
- U06 receives bounded privacy-safe audit and operational dimensions.
- U07 owns database/outbox/runtime infrastructure; its tests no longer mutate U02-owned schema.
