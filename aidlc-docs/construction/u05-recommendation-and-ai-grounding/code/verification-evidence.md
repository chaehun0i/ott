# U05 PostgreSQL, Failure, Privacy and Capacity Evidence

## PostgreSQL Gate

- Engine: actual PostgreSQL 17.10 with pgvector 0.8.2.
- Migration: existing U04 database and clean database both reached `0005_u05_recommendation_expand`.
- Selected integration result: 31 passed, 256 deselected, zero skipped.
- Full regression result: 288 passed, zero skipped, with 86.04% overall branch-aware coverage using Hypothesis seed `260729`.
- Coverage includes U07 through U05 schemas, U05 optimistic session CAS/idempotency, AI failure injection and restore closure.

The first full selection exposed a stale U04 assertion that required the global Alembic head to remain exactly `0004`. It was corrected to verify U04 is present at revision 4 or later, matching the already established U02/U03 forward-compatible contract. The rerun passed with zero skips.

## Failure and Privacy Gate

- AI timeout becomes `ai_unavailable` without exposing provider error text.
- Missing U03 candidates fails closed.
- Incomplete U02/U03/U04 restore compatibility blocks re-entry.
- Trace persistence has no prompt, response body, draft, chain-of-thought, email or direct user ID field.
- Telemetry allowlists exclude request, synopsis, explanation and direct identity content.

## Capacity Gate

- Pure hard filtering processed 100,000 approved candidate values below the 5-second local test ceiling.
- Fifteen deterministic burst requests completed below the 3-second fallback ceiling.
- Online orchestration still caps input at 1,000, scored candidates at 500, reserves at 100 and exposed candidates at 20.

No Docker waiver or skipped PostgreSQL integration test was used.
