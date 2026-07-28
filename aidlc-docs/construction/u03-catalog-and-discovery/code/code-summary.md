# U03 Code Summary

## Created Capabilities

- Approved catalog domain with immutable revision history, monotonic CatalogVersion and publish/replace/withdraw/reactivate transitions
- Region-verified availability, locale fallback, freshness, multi-section feed, deterministic filters and keyset cursor values
- PostgreSQL `u03_catalog` schema with 15 tables, pg_trgm/unaccent/vector extensions, FTS/trigram/HNSW indexes and expand-only migration
- SQLAlchemy repositories, transaction profiles, approval closure, versioned outbox, projection receipts/gaps and generation registry
- Korean/English structured parsing, parameterized text retrieval, embedding deadline/circuit/bulkhead, pgvector retrieval and versioned RRF
- Incremental projection/replay workers, immutable online rebuild and atomic generation swap
- HMAC cursor/key rotation, semantic rate limits and versioned feed/detail/search APIs
- Privacy-safe telemetry, readiness/deep health, alerting, dashboards and deployment/rollback/backup guidance

Application code is under `backend/src/ott_feed/catalog/` and `backend/src/ott_feed/search/`. No application code was written under `aidlc-docs/`.
