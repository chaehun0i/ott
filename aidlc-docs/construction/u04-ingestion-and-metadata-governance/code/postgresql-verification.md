# U04 PostgreSQL, Capacity and Recovery Verification

## Environment

- PostgreSQL: 17.10 on Debian bookworm
- Alembic head: `0004_u04_ingestion_expand`
- Integration endpoint: `127.0.0.1:65432/ott_feed`
- Docker Engine: 29.6.2

## Integration Gate

`pytest -m integration -ra` completed with 27 passed, 195 deselected and zero
skipped tests. The selected set includes U07, U02, U03 and U04 PostgreSQL
contracts. An initial failure exposed stale U02/U03 assumptions that the global
Alembic head could never advance; those assertions now verify that their own
migration is present at or before the current global head.

## Capacity Gate

- A real PostgreSQL temporary claim table was populated with 1,000,000 rows
  distributed across 20 providers.
- The U04 `(lane, status, available_at, priority, job_id)` claim order used an
  index-backed bounded plan and returned exactly 100 rows below the two-second
  plan threshold.
- Pure versioned normalization processed the 100,000-record fixture below the
  60-second test ceiling, far above the minimum 6.95 records/second required for
  the four-hour full-sync objective. Provider-enforced pauses remain excluded as
  specified by the NFR.

## Failure and Recovery Gate

Verified worker lease recovery, duplicate delivery, cursor replay, provider
timeout/rate/circuit behavior, U03 timeout before/after commit, rule-version
change keys, raw-body expiry and restore inconsistency. Recovery re-entry blocks
missing policy/rule references, cursor regression, duplicate receipts,
quarantine leakage and expired retained bodies. Publication resumes before
provider claims, and provider claims remain disabled until pending publication
reconciliation succeeds.

No Docker waiver or skipped PostgreSQL test was used.
