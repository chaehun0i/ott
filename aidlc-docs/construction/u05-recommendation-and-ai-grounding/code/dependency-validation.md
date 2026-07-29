# U05 Dependency and Consumer Contract Validation

## Locked Runtime

| Dependency | Locked value |
|---|---|
| Python | `>=3.12.13,<3.13` |
| FastAPI | 0.140.0 |
| Pydantic | 2.13.4 |
| HTTPX | 0.28.1 |
| SQLAlchemy | 2.0.51 |
| psycopg binary | 3.3.4 |
| Alembic | 1.18.5 |
| pytest | 9.1.1 |
| Hypothesis | 6.161.5 |

`backend/pyproject.toml` and `backend/uv.lock` contain the same selected versions. U05 uses the existing stack and adds no provider SDK, ML framework, Redis, broker, retry package or vector store.

## Verified Consumer Contracts

- U02 `FeatureService.snapshot(user_id, request_id)` produces request-scoped, consent-qualified values.
- U03 `ApprovedCatalogReadPort.get_approved(content_id, region)` is the approved-candidate boundary.
- U04 `ValidationPredicateContract` requires contract/rule versions and a positive runtime bound.
- U07 retains runtime, request deadline, database, health and telemetry ownership.

Contract tests are located at `backend/tests/recommendation/contract/test_dependency_contracts.py`. No lockfile change is required.
