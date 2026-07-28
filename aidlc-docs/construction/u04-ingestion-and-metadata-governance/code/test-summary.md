# U04 Final Test Summary

## Quality Gate

| Gate | Result |
|---|---|
| Ruff format | 228 files formatted |
| Ruff check | Passed |
| Strict MyPy | 153 source files passed |
| Full pytest | 223 passed, 0 failed, 0 skipped |
| Overall branch coverage | 85.87% (minimum 80%) |
| U04 validation/quarantine/publication branches | 100% |
| PostgreSQL integration selection | 27 passed, 196 deselected, 0 skipped |
| PostgreSQL server | 17.10 on Debian |
| Alembic head | `0004_u04_ingestion_expand` |
| Hypothesis seed | `260728` with CI profile and shrinking enabled |

The sole warning is the upstream Starlette deprecation notice for its current TestClient HTTPX integration. It is not a test failure and does not weaken a U04 assertion.

## Contract and Artifact Gate

- OpenAPI contains all three U04 routes and contains neither `provider_token` nor `payload_body`.
- `uv lock --check` resolved 55 locked packages without changes.
- Docker Compose, Prometheus YAML references and the U04 Grafana JSON parse successfully.
- No ignored file is tracked, no local/secret artifact filename is tracked except the intentional `.env.example`, and no private-key/cloud-key pattern is present.
- The only credential-shaped URL is the fixed disposable PostgreSQL test fixture in the manually triggered CI workflow.
- No Python, JavaScript, TypeScript, Java, Go or Rust application source exists under `aidlc-docs/`.

## PostgreSQL and Capacity Evidence

The real PostgreSQL suite covers clean/upgrade migration behavior, constraints, concurrent `SKIP LOCKED` claims, fencing, replay and publication receipts. The capacity suite covers 20 providers, a 1,000,000-row index-backed claim plan and 100,000 normalization records. No Docker waiver or skipped integration test satisfies this gate.
