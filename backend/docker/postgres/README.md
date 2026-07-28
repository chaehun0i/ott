# PostgreSQL Runtime

Compose uses the official pgvector PostgreSQL 17 bookworm image pinned by immutable digest. The runtime enables `pg_trgm`, `unaccent`, and `vector` through Alembic migration `0003_u03_catalog_expand`.

Do not replace the digest with `latest`. Validate a candidate image with extension creation, HNSW index creation, exact-vector comparison, clean migration, and integration tests before updating it.
