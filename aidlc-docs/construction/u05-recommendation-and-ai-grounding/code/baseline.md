# U05 Code Generation Baseline

## Runtime

- Python: 3.12.13
- PostgreSQL: actual PostgreSQL 17.10 in `ott-u03-pg17`
- Isolated U05 endpoint: `127.0.0.1:65432/ott_feed_u05`
- Alembic head before U05: `0004_u04_ingestion_expand`
- Deterministic Hypothesis seed: `260729`

## Quality Baseline

- Ruff lint: passed.
- Strict MyPy: 153 source files passed. The writable-cache/sandbox issue was resolved by running the locked tool with explicit read permission; no source finding existed.
- Full suite with live PostgreSQL: 223 passed, zero skipped.
- Branch-aware coverage: 85.87%, above the 80% gate.
- Existing U07/U02/U03/U04 integration tests executed in the full suite with the live `TEST_DATABASE_URL`.

## PostgreSQL Preparation

An isolated local-only `ott_u05_test` role and `ott_feed_u05` database were created without reading or exposing the existing container environment. The required `vector`, `pg_trgm` and `unaccent` extensions were installed by the container administrator before applying the existing migration chain.

## Boundary Guard

The architecture contract now rejects FastAPI, SQLAlchemy, HTTPX, psycopg and Pydantic imports from future U05 domain/application packages. It passes before package creation and will inspect all U05 core source files as they are added.

No blocking baseline finding remains.
