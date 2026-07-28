# U02 Identity and Personalization Code Generation Plan

> **Single Source of Truth**: 이 파일은 U02 Code Generation Part 1과 Part 2의 실행 순서 및 완료 상태를 관리한다. 승인 전에는 application code를 변경하지 않으며, 승인 후에는 번호 순서대로 실행하고 각 단계가 끝난 같은 interaction에서 `[x]`로 갱신한다.

## Part 1 - Planning Status

- [x] U02 Functional Design, NFR Requirements, NFR Design 및 Infrastructure Design을 읽었다.
- [x] US-014~US-018, US-027과 U01·U03·U05·U06·U07 contract를 확인했다.
- [x] 기존 U07 application, migration, tests, `backend/pyproject.toml`과 `backend/uv.lock` 구조를 확인했다.
- [x] application code 위치를 `backend/src/ott_feed/identity/`, test 위치를 `backend/tests/identity/`로 확정했다.
- [x] U02가 기존 modular monolith와 PostgreSQL/outbox runtime에 추가되는 brownfield-style unit임을 확인했다.
- [x] Frontend는 U01 소유이므로 U02 Code Generation에서 제외하고 versioned API contract만 제공하기로 했다.
- [x] 이 상세 실행 계획과 승인 prompt를 생성했다.
- [x] 사용자가 전체 Code Generation 계획과 순서를 명시적으로 승인했다.

## Unit Context

### Primary Stories

| Story | U02 Capability | Planned Steps |
|---|---|---|
| US-014 | email registration, verification, login, Google OAuth and sessions | 4~5, 8, 13, 16~18 |
| US-015 | genre preference and OTT subscription profile | 4, 9, 13, 16~18 |
| US-016 | save, rating and completed watch history | 4, 9, 13, 16~18 |
| US-017 | feedback intake and personalization feature update | 4, 10~11, 13~14, 16~18 |
| US-018 | consent, guest link, withdrawal, export and deletion | 4, 10~13, 16~18 |
| US-027 | roles, account linking and data-rights administration | 4, 8, 12~13, 16~18 |

### Dependencies and Contracts

- **U07**: FastAPI factory, request context, configuration, SQLAlchemy/psycopg, Alembic, idempotency, outbox, worker registry, health와 telemetry.
- **U03**: `ContentId` existence/eligibility read port. U03 구현 전에는 typed fake/deny-safe adapter를 사용한다.
- **U05**: pseudonymous, consent-bound `FeatureSnapshot` read contract.
- **U06**: minimal security/data-rights audit event port와 role/preference read contract.
- **U01**: cookie, CSRF, session, consent, export/deletion status와 safe localized error의 OpenAPI consumer contract.
- **External**: Google OAuth/OIDC, transactional email과 private export storage는 port 뒤에 두며 test에서는 fake adapter를 사용한다.

### Owned Database Entities

`users`, `credentials`, `oauth_links`, `role_assignments`, `sessions`, `verification_challenges`, `user_profiles`, `genre_preferences`, `ott_subscriptions`, `watch_items`, `ratings`, `watch_history`, `consent_decisions`, `consent_current`, `guest_link_authorizations`, `behavior_events`, `event_deduplication`, `personalization_features`, `feature_contributions`, `data_rights_requests`, `export_artifacts`, `deletion_steps`, `key_rotation_progress`.

All U02 tables are created in the `u02_identity` schema. U07 shared `outbox_jobs` is extended compatibly with lane/priority support instead of duplicated.

## Dependency Baseline for Step 2

The existing locked Python baseline remains `>=3.12.13,<3.13`. Code Generation will resolver-test and pin these current candidates rather than editing `uv.lock` by hand:

| Capability | Candidate | Validation Required |
|---|---|---|
| Password hashing | `argon2-cffi==25.1.0` | Python 3.12 install/wheel, hash/verify/rehash, benchmark |
| AES-GCM and key wrapping primitives | `cryptography==49.0.0` | Windows/Linux Python 3.12 wheels, tamper/round-trip |
| OAuth/OIDC client | `Authlib==1.7.2` | HTTPX/FastAPI compatibility, Google OIDC validation |

Primary package records: [argon2-cffi on PyPI](https://pypi.org/project/argon2-cffi/), [cryptography on PyPI](https://pypi.org/project/cryptography/), [Authlib on PyPI](https://pypi.org/project/Authlib/). Exact pins enter `backend/pyproject.toml` only after `uv` resolves them with the existing dependency set and Python 3.12.13.

## Part 2 - Generation Steps

## Step 1 - Baseline and Boundary Guard

- [x] Run the existing format/lint/type/unit/contract/PBT suite and record the pre-U02 baseline.
- [x] Confirm the live Local PostgreSQL 17.10 connection and existing U07 integration test can run with zero skips.
- [x] Add boundary-test expectations that U02 domain/application code cannot import FastAPI, SQLAlchemy, Authlib, Argon2 or cryptography adapters.

**Paths**: `backend/tests/platform/contract/test_boundaries.py`, `aidlc-docs/construction/u02-identity-and-personalization/code/baseline.md`.

## Step 2 - Dependency and Lock Update

- [x] Dry-run the three candidate packages against Python 3.12.13 and current pins.
- [x] Update `backend/pyproject.toml`, regenerate `backend/uv.lock` with the configured `uv` runtime and install the synchronized environment.
- [x] Record selected versions, wheel/platform evidence, resolver result and rejection rationale without claiming a package is verified before resolution.

**Paths**: `backend/pyproject.toml`, `backend/uv.lock`, `aidlc-docs/construction/u02-identity-and-personalization/code/dependency-validation.md`.

## Step 3 - Identity Package Skeleton, Configuration and Ports

- [x] Create the U02 modular package and public application ports.
- [x] Extend typed settings for Argon2 policy, session/cookie, key versions, OAuth, email, export, pool and worker-lane configuration with fail-fast validation.
- [x] Define clocks, ID generation, transaction, repository, hashing, crypto, OAuth, email, object storage, catalog validation, audit and feature consumer protocols.

**Paths**: `backend/src/ott_feed/identity/__init__.py`, `backend/src/ott_feed/identity/ports.py`, `backend/src/ott_feed/identity/config.py`, `backend/src/ott_feed/platform/config.py`.

## Step 4 - Domain Models, State Machines and Policies

- [x] Implement typed identifiers, enums, immutable values and aggregate models from the Functional Design.
- [x] Implement identity/session, role, profile/library, consent, feedback/feature and data-rights transition policies.
- [x] Implement BR-U02-001~051 without framework or persistence imports and expose safe domain errors.

**Paths**: `backend/src/ott_feed/identity/domain/models.py`, `backend/src/ott_feed/identity/domain/policies.py`, `backend/src/ott_feed/identity/domain/errors.py`.

## Step 5 - Security Adapters

- [x] Implement Argon2id hash envelope, benchmark helper, needs-rehash and bounded-executor adapter.
- [x] Implement CSPRNG 256-bit session token and domain-separated peppered HMAC lookup.
- [x] Implement signed double-submit CSRF plus Origin/Referer validation contract.
- [x] Implement AES-256-GCM record encryption, wrapped record DEK, associated data and versioned blind indexes without plaintext fallback.

**Paths**: `backend/src/ott_feed/identity/adapters/security.py`, `backend/tests/identity/unit/test_security.py`, `backend/tests/identity/pbt/test_crypto_properties.py`.

## Step 6 - SQLAlchemy Models and Alembic Expand Migration

- [x] Implement U02 SQLAlchemy persistence models under the `u02_identity` schema.
- [x] Create expand-only `0002_u02_identity_expand.py` with constraints, optimistic versions, blind indexes, outbox lane columns/indexes and retention/status fields.
- [x] Update role grants for migration owner, API runtime and worker runtime while preserving U07 compatibility.
- [x] Verify upgrade on a clean and migrated PostgreSQL database; prohibit destructive automatic downgrade.

**Paths**: `backend/src/ott_feed/identity/adapters/persistence/models.py`, `backend/migrations/versions/0002_u02_identity_expand.py`, `backend/migrations/role-grants.sql`.

## Step 7 - Repositories and Unit of Work

- [x] Implement repository adapters for identity, session, profile, library, consent, behavior and data-rights aggregates; the dedicated feature CAS repository remains in its planned Step 11.
- [x] Implement expected-version optimistic updates, unique-conflict translation, request-scoped transaction and fail-closed consent reads.
- [x] Extend outbox repository operations for high·normal·low lanes without breaking U07 callers.

**Paths**: `backend/src/ott_feed/identity/adapters/persistence/repositories.py`, `backend/src/ott_feed/identity/adapters/persistence/unit_of_work.py`, `backend/src/ott_feed/platform/application/outbox.py`.

## Step 8 - Registration, Authentication, OAuth Linking and Sessions

- [x] Implement registration, verification, password login/reset, generic enumeration-safe failures and progressive rehash.
- [x] Implement multiple sessions, inactivity/absolute expiry, individual/all revoke, token rotation and fresh-auth evidence.
- [x] Implement fixed roles, authorization-version checks and explicit Google account linking/unlink invariants.

**Paths**: `backend/src/ott_feed/identity/application/authentication.py`, `backend/src/ott_feed/identity/application/sessions.py`, `backend/src/ott_feed/identity/application/authorization.py`.

## Step 9 - Profile and Library Services

- [x] Implement partial profile updates, liked/disliked genre exclusivity and three-state OTT subscription.
- [x] Implement idempotent save/unsave, integer rating 1~5, unrate and completed watch history.
- [x] Atomically increment versions and publish explicit feature refresh jobs.

**Paths**: `backend/src/ott_feed/identity/application/profile.py`, `backend/src/ott_feed/identity/application/library.py`.

## Step 10 - Consent and Feedback Intake

- [x] Implement immutable consent ledger, current projection, policy/notice version and fail-closed eligibility.
- [x] Implement explicit guest-link authorization and withdrawal-triggered source/derived cleanup.
- [x] Implement typed behavior events, client idempotency, fallback duplicate window and U03 ContentId validation.

**Paths**: `backend/src/ott_feed/identity/application/consent.py`, `backend/src/ott_feed/identity/application/feedback.py`.

## Step 11 - Feature Projection and Snapshot Boundary

- [x] Implement explicit synchronous recompute and implicit worker aggregation with contribution ledger.
- [x] Enforce user-level monotonic FeatureVersion, compare-and-swap, deduplication and stale ConsentVersion rejection.
- [x] Generate request-scoped pseudonyms and allow-listed FeatureSnapshot DTOs without direct identifiers.

**Paths**: `backend/src/ott_feed/identity/application/features.py`, `backend/src/ott_feed/identity/adapters/persistence/feature_repository.py`.

## Step 12 - Data Export, Deletion and Key Rotation

- [x] Implement fresh-authenticated export/deletion requests and safe status DTOs.
- [x] Implement encrypted 24-hour one-time export artifact lifecycle behind an object-storage port.
- [x] Implement category-idempotent deletion with terminal closure verification and permanent account disable during retry.
- [x] Implement 500-row checkpointed dual-read/new-write key rotation and old-version drain validation.

**Paths**: `backend/src/ott_feed/identity/application/data_rights.py`, `backend/src/ott_feed/identity/application/key_rotation.py`, `backend/src/ott_feed/identity/adapters/export_storage.py`.

## Step 13 - Google OAuth and Email Adapters

- [x] Implement Google OAuth/OIDC state, nonce, issuer, audience, redirect and provider-subject validation through Authlib/HTTPX.
- [x] Apply connect 3-second/overall 10-second timeout, no callback retry and bounded discovery/JWKS circuit/cache.
- [x] Implement provider-neutral email adapter with Local mail sink, CI fake and Remote provider configuration; never log challenge links/tokens.

**Paths**: `backend/src/ott_feed/identity/adapters/google_oauth.py`, `backend/src/ott_feed/identity/adapters/email.py`.

## Step 14 - HTTP API Contracts and Application Wiring

- [x] Create versioned Pydantic request/response contracts and `/api/v1/identity/*` router.
- [x] Set Secure·HttpOnly·SameSite=Lax cookies and enforce CSRF/origin on state-changing browser routes.
- [x] Provide safe Korean/English message keys, non-color status semantics and OpenAPI contracts for U01.
- [x] Wire U02 dependencies into the existing FastAPI application factory without embedding secrets or provider clients in domain code.

**Paths**: `backend/src/ott_feed/identity/api/contracts.py`, `backend/src/ott_feed/identity/api/dependencies.py`, `backend/src/ott_feed/identity/api/router.py`, `backend/src/ott_feed/main.py`, `docs/api-contract.md`.

## Step 15 - Worker Registry, Health and Privacy-Safe Telemetry

- [x] Register feature, withdrawal, deletion, export and rotation handlers with lane budgets.
- [x] Add U02 readiness/deep-health contribution, bounded metrics and alert signals.
- [x] Add telemetry label allow-list tests that reject email, UserId, OAuth subject, session token/ID, raw payload and object reference.

**Paths**: `backend/src/ott_feed/identity/worker.py`, `backend/src/ott_feed/worker.py`, `backend/src/ott_feed/identity/telemetry.py`, `backend/src/ott_feed/platform/health.py`.

## Step 16 - Example Unit and Contract Tests

- [x] Add example tests for every BR-U02-001~051 core decision branch and error/degradation path.
- [x] Add API tests for cookie, CSRF, enumeration safety, session rotation, consent, feedback, export/deletion and localized error contracts.
- [x] Verify domain/application boundary and direct-identifier non-disclosure contracts.

**Paths**: `backend/tests/identity/unit/`, `backend/tests/identity/contract/`.

## Step 17 - Property-Based Tests

- [x] Implement PBT-U02-01~11 with Hypothesis, including state machines for session, consent, library and data-rights lifecycles.
- [x] Cover idempotency, mutual exclusion, monotonic FeatureVersion, no duplicate contribution, encryption round-trip/tamper failure and deletion closure.
- [x] Preserve shrinking, deterministic seed reporting and regression promotion guidance.

**Paths**: `backend/tests/identity/pbt/`, `backend/tests/strategies/identity.py`.

## Step 18 - PostgreSQL Integration and Failure-Injection Tests

- [x] Test migrations, repository constraints, optimistic conflicts, outbox atomicity/lanes, feature ordering, export single-use, deletion retry and rotation restart on actual PostgreSQL.
- [x] Inject Google timeout, consent read failure, session write failure, backlog and retry exhaustion with expected isolation/fail-closed behavior.
- [x] Run `pytest -m integration` with zero skipped tests using the verified PostgreSQL 17.10 path; skipped marker-selected tests fail the U02 gate.

**Paths**: `backend/tests/identity/integration/`, test reports under `backend/`.

## Step 19 - Deployment and Configuration Artifacts

- [x] Extend Compose environment/service/secret definitions for U02 API, worker, key files, email and export configuration without storing secret values.
- [x] Extend Prometheus/Grafana/OTel configuration for U02 metrics, dashboards, alerts and label protection.
- [x] Update deployment/rollback/backup/restore instructions for schema, key versions, export exclusion and forward-only sensitive jobs.

**Paths**: `compose.yaml`, `compose.local.yaml`, `compose.remote.yaml`, `infra/`, `scripts/`, `docs/`.

## Step 20 - Quality Gate, Documentation and Handoff

- [x] Run Ruff format/check, strict MyPy, complete pytest with deterministic Hypothesis seed, branch coverage and zero integration skips.
- [x] Verify U02 overall line coverage >=80% and BR-U02-001~051 core branch coverage evidence.
- [x] Verify migration from U07 schema, clean install, OpenAPI, dependency lock, no secret/PII telemetry and no application code under `aidlc-docs/`.
- [x] Create code summaries and a requirements/story/test traceability matrix.
- [x] Mark all plan and story checkboxes complete, update `aidlc-state.md`, log completion and request standardized Code Generation approval.

Story completion is scoped to U02-owned acceptance criteria. U05 cold-start ranking, U01
accessibility and external production legal review remain unchecked under their owning gates, as
recorded in the traceability summary.

**Paths**: `aidlc-docs/construction/u02-identity-and-personalization/code/code-summary.md`, `aidlc-docs/construction/u02-identity-and-personalization/code/test-summary.md`, `aidlc-docs/construction/u02-identity-and-personalization/code/traceability.md`.

## Expected Scope

- **20 sequential generation steps** after plan approval.
- **Application changes**: existing `backend/` modular monolith, migration, Compose, infra and operational docs.
- **New unit package**: `backend/src/ott_feed/identity/`.
- **New unit tests**: `backend/tests/identity/` and `backend/tests/strategies/identity.py`.
- **Documentation summaries only**: `aidlc-docs/construction/u02-identity-and-personalization/code/`.
- **No frontend generation**: U01 will consume the U02 OpenAPI contract later.

## Extension Execution Commitments

- **Resiliency Baseline**: dependency isolation, backpressure, outbox recovery, backup/restore re-entry, failure injection and operational evidence are implemented and tested.
- **Property-Based Testing**: all 11 approved candidates are implemented with Hypothesis; shrinking stays enabled and minimal failures become regression tests.
- **Security Baseline**: disabled and N/A as an extension; U02 core authentication, session, encryption, least-privilege and privacy requirements remain blocking implementation gates.
