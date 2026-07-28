# U02 Identity and Personalization Code Summary

## Outcome

U02 is implemented as a port-and-adapter package under `backend/src/ott_feed/identity`. Domain and
application code have no FastAPI, SQLAlchemy, Authlib, Argon2 or cryptography-library imports.
Framework, database, provider and cryptographic concerns remain in adapters and composition code.

## Delivered Components

| Area | Implementation |
|---|---|
| Identity | Email registration/verification, Argon2id password login/reset, Google OIDC validation and explicit linking |
| Session and authorization | 256-bit opaque tokens, HMAC lookup, rotation/revocation, fresh-auth and versioned fixed roles |
| Profile and library | Genre/OTT preferences, save, rating and completed-watch authoritative state |
| Consent and feedback | Immutable consent evidence, explicit guest-link authorization, fail-closed collection and deduplication |
| Personalization boundary | Versioned features, contribution ledger, CAS and request-scoped minimized U05 snapshots |
| Data rights | Fresh-auth export/deletion, encrypted 24-hour single-use artifact and category-idempotent deletion |
| Cryptography | AES-256-GCM envelope encryption, AAD binding, blind indexes and checkpointed key rotation |
| API | Versioned `/api/v1/identity/*` contracts, hardened cookies, CSRF/origin and Korean/English safe errors |
| Workers | High/normal/low lane budgets for feature, withdrawal, deletion, export and rotation work |
| Operations | PostgreSQL 17 migration, least-privilege roles, Compose secret files, metrics, alerts and recovery runbooks |

## Principal Paths

- Domain: `backend/src/ott_feed/identity/domain/`
- Use cases: `backend/src/ott_feed/identity/application/`
- Adapters and repositories: `backend/src/ott_feed/identity/adapters/`
- HTTP boundary: `backend/src/ott_feed/identity/api/`
- Migration: `backend/migrations/versions/0002_u02_identity_expand.py`
- Runtime and worker composition: `backend/src/ott_feed/main.py`, `backend/src/ott_feed/worker.py`
- API contract: `docs/api-contract.md`
- Deployment and recovery: `compose*.yaml`, `infra/`, `scripts/`, `docs/*runbook.md`

## Security and Privacy Disposition

- Password plaintext, provider token, session secret and direct identifiers are excluded from API,
  feature snapshots and telemetry labels.
- Email and OAuth claim values use envelope encryption; lookup values use domain-separated blind
  indexes. Export artifacts use separate encrypted single-use storage.
- Browser mutations require an exact allowed Origin and signed double-submit CSRF token. Session
  cookies use `HttpOnly` and `SameSite=Lax`; Remote requires `Secure`.
- Consent read/validation failures fail closed. Withdrawal and deletion use durable high-lane work;
  partial failure cannot reactivate an account or expose stale personalized features.
- Secret values are not present in Compose or source. Runtime secret-file references are validated
  at startup and deployment.

## Extension Compliance

| Extension | Result | Evidence |
|---|---|---|
| Resiliency Baseline | Compliant | Bounded provider retries, circuits, lane bulkheads, outbox recovery, failure injection and restore re-entry |
| Property-Based Testing | Compliant | PBT-U02-01~11 with deterministic seed, shrinking and lifecycle state machines |
| Security Baseline | N/A | Extension is disabled in state; mandatory core authentication, encryption, authorization and privacy gates passed |
| Frontend/accessibility | N/A for U02 | U02 supplies non-color status/message keys; U01 owns keyboard and assistive-technology UI validation |

## Remaining Production Transition Controls

Production still requires managed KMS/HSM, managed HA PostgreSQL, verified transactional email and
Google credentials, independent privacy/legal review, accessibility validation in U01 and periodic
restore/incident exercises. These do not invalidate the verified Local/CI U02 implementation but
remain blocking for production classification.
