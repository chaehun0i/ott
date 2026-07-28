# U03 Baseline Evidence

## Runtime

- Docker Engine: 29.6.2
- Docker Compose: 5.3.1
- PostgreSQL: 17.10 on Debian bookworm
- pgvector extension: 0.8.2
- Test container port: 65432 to avoid an existing host listener on 55432

## Quality Baseline

- Ruff: passed
- strict MyPy: passed when executed outside the restricted SQLite-cache sandbox
- Existing suite: 91 tests passed and one optional PostgreSQL test skipped before a database URL was supplied; branch coverage was 81.35%
- PostgreSQL-selected suite after migration: 12 passed, 87 deselected, zero skipped
- Alembic head before U03: `0002_u02_identity_expand`

## Compatibility Adjustment

The U02 PostgreSQL assertion now accepts the server's `17.10` prefix because distribution images append package metadata to `server_version`. The major/minor patch requirement remains exact while allowing the official pgvector Debian image format.

## Boundary Guard

The architecture contract rejects FastAPI, SQLAlchemy, HTTPX and pgvector imports from U03 domain and application packages.
