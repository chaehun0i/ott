# U04 Baseline Evidence

## Runtime

- Python: 3.12.13
- Docker Engine: 29.6.2
- Docker Compose: 5.3.1
- PostgreSQL: 17.10 on Debian bookworm
- Test endpoint: `127.0.0.1:65432/ott_feed`
- Alembic head before U04: `0003_u03_catalog_expand`

## Quality Baseline

- Ruff format check: 160 files already formatted.
- Ruff lint: passed.
- Strict MyPy: 115 source files passed.
- Full suite: 138 passed, zero skipped, one dependency deprecation warning.
- Branch-aware coverage: 84.36%, above the 80% gate.
- PostgreSQL-selected suite: 19 passed, 119 deselected, zero skipped.
- Deterministic Hypothesis seed: `260728`.

## Boundary Guard

The architecture contract rejects FastAPI, SQLAlchemy, HTTPX and psycopg imports from
U04 domain and application packages. The check is valid before package creation and
will inspect all U04 core source files as they are added.

## Baseline Finding

No blocking baseline failure remains. The Starlette `TestClient` warning originates
from the locked FastAPI dependency and does not change test outcomes; dependency
replacement is outside U04 scope and remains visible for later maintenance.
