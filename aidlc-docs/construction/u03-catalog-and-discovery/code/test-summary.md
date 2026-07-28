# U03 Test Summary

## Final Gates

- Ruff: passed
- strict MyPy: passed for 115 source files
- Full pytest: 138 passed, zero skipped
- Overall branch-aware coverage: 84.36%, threshold 80%
- CAT/AVAIL/PROJ critical branch subset: 100% statements and branches
- PostgreSQL integration selection: 19 passed, 115 deselected, zero skipped
- Clean migration: `0001` to `0002` to `0003`; 15 U03 tables and U03 role grants verified
- uv lock check: 55 packages resolved without drift
- Compose, Grafana JSON and OpenAPI contracts: valid

The only warning is the existing Starlette notice that its `httpx` TestClient integration is deprecated in favor of `httpx2`; it does not affect runtime or Gate results.
