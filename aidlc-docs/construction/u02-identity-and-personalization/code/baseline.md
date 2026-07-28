# U02 Code Generation Baseline

## Runtime Evidence

- Python: 3.12.13 from the existing U07 virtual environment
- PostgreSQL: isolated actual PostgreSQL 17.10 cluster on `127.0.0.1:55433`
- Database: `ott_feed_u02_test`
- Authentication: local-only trust in the isolated test cluster; not a Remote or Production configuration
- Docker: not required for the quality gate

## Pre-U02 Results

- Ruff: passed
- strict MyPy: 24 source files, no issues; cache redirected to a task-specific temporary directory because the workspace cache file was not writable by the process
- non-integration pytest: 26 passed, 1 deselected
- branch-aware coverage: 88.28%, above the 80% gate
- PostgreSQL integration: 1 passed, 26 deselected, 0 skipped
- Alembic: existing U07 head applied successfully to the isolated database

## Environment Notes

The earlier PostgreSQL 17.10 Windows service on port 55432 remains running, but its test-role password is not available in the current process. No credential or database state was changed. A separate cluster was initialized in the task-specific temporary directory on port 55433, preserving the existing service and providing a repeatable password-free local test path bound only to `127.0.0.1`.

Pytest temporary files, Coverage SQLite data and MyPy cache are directed to task-specific temporary paths because stale workspace/user temporary ACLs reject SQLite and pytest directory access. This does not alter test semantics.

## Boundary Guard

`backend/tests/platform/contract/test_boundaries.py` now asserts that U02 `domain` and `application` sources cannot import FastAPI, SQLAlchemy, Authlib, Argon2 or cryptography packages. The test is valid before the package exists and becomes an active architectural gate as U02 files are created.
