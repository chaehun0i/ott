# U04 Dependency and Contract Validation

## Locked Runtime

`uv lock --check` resolved 55 packages without changing the lock and `uv sync
--frozen --dry-run` reported that the project environment would make no changes.

| Capability | Locked version | U04 use |
|---|---:|---|
| Python | `>=3.12.13,<3.13` | Existing project runtime |
| Alembic | 1.18.5 | U04 expand migration |
| HTTPX | 0.28.1 | Provider-neutral HTTP transport and deterministic test transport |
| SQLAlchemy | 2.0.51 | U04 persistence adapter |
| psycopg binary | 3.3.4 | PostgreSQL 17 runtime and integration tests |
| Hypothesis | 6.161.5 | PBT-U04-01~12 |

No provider SDK, retry package, broker or cache is needed. `pyproject.toml` and
`uv.lock` remain unchanged.

## U03 Contract

`ApprovedCatalogPublicationService.execute(PassedValidationCommand)` already
supports publish, replace, withdraw and reactivate with decision idempotency and
versioned outbox delivery. The older `ApprovedCatalogWritePort.publish` protocol
does not express the complete command surface. U04 will define a framework-free
command port and use a composition adapter around the existing U03 service; it
will not import U03 persistence or write `u03_catalog` directly.

## U07 Contract

The existing `HandlerRegistry` and durable `OutboxJob` runtime provide typed job
registration and bounded failure rescheduling. U04 will register its own lane and
handler names without coupling U07 to ingestion business types. Existing health,
telemetry and database ports remain sufficient.

## Result

The dependency and contract gates pass. The U03 protocol surface mismatch is a
known adapter task in Steps 3 and 16, not a new dependency or ownership violation.
