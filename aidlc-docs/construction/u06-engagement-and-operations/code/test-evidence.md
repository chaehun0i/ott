# U06 Test Evidence

## Final Gates

| Gate | Result |
|---|---|
| Ruff | Passed, all files |
| Strict MyPy | Passed, 212 source files |
| Full suite | 324 passed, zero skipped |
| Branch coverage | 85.36%, required minimum 80% |
| PostgreSQL integration | 34 passed, 290 deselected, zero skipped on PostgreSQL 17.10 |
| U06 PBT | P-U06-01~12 passed with Hypothesis seed 260726 and shrinking enabled |
| U06 quality | 6 privacy/capacity/recovery tests passed |
| Compose | Base, maintenance profile and remote overlay rendered; CPU 1.0/1.0/0.5; no placeholder command |
| Migration | Head `0006_u06_engagement_expand`; append-only audit trigger verified |

## Defect Found by PBT

The health permutation property generated duplicate component names with different reason values and minimized an order-dependent result. Health aggregation now uses a total ordering across component, required flag, state, observation/freshness and reason. The property passes after the fix.

The full suite initially exposed a cold-path timing flake in the existing U02 `FeatureSnapshot` round-trip property. Reusing one module-level Pydantic `TypeAdapter` removed repeated cold construction without disabling Hypothesis deadlines, shrinking or seed reproduction.

## PostgreSQL Environment

- PostgreSQL 17.10 in the existing local `ott-u03-pg17` test container.
- Isolated database `ott_feed_u06_baseline` with required vector, trigram and unaccent extensions.
- Migration chain 0001 through 0006 applied before final verification.
- Integration marker completed with skip count zero; no Docker or PostgreSQL waiver was used.
