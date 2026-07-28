# U04 Code Generation Summary

## Outcome

U04 implements provider-policy enforcement, bounded HTTP collection, durable job and cursor recovery, governed raw observations, deterministic normalization and identity/merge, fail-closed versioned validation, quarantine/revalidation and idempotent U03 publication. Application code is located under `backend/src/ott_feed/ingestion/`; no application source is stored under `aidlc-docs/`.

## Runtime and Persistence

- PostgreSQL schema `u04_ingestion` is introduced by `0004_u04_ingestion_expand` with U04 API, worker and migration roles.
- The API role is read-only in U04. The worker role mutates U04 and has no direct U03 table grant.
- `worker-ingestion` has a dedicated provider-egress network and purpose-separated database/provider credential files.
- Database URLs can be loaded through `DATABASE_URL_FILE`, preventing Compose environment leakage.
- Prometheus alerts, a Grafana dashboard and fail-closed restore re-entry procedures cover publication lag, circuits, quarantine and lease recovery.

## Boundaries

- U03 receives only immutable passed or withdrawal commands through an application port.
- U05 receives only the versioned `ValidationRuleContract`.
- U06 retains operator override and audit ownership; U04 exposes authorized bounded status and retry operations.
- Raw payloads and provider credentials are excluded from APIs, health output and telemetry attributes.

## Delivery Status

GitHub Actions automatic triggers remain intentionally paused. Manual workflow dispatch and the locally executed Python/PostgreSQL gates remain available.
