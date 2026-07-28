# U02 Test and Gate Summary

## Final Automated Gate

| Gate | Result |
|---|---|
| Ruff format | Passed; 89 files already formatted |
| Ruff check | Passed |
| strict MyPy | Passed; 59 source files |
| Full pytest | Passed; 98 tests, 0 failures |
| PostgreSQL integration | Passed; 12 selected tests, 0 skipped, 86 deselected |
| Property-based tests | Passed; PBT-U02-01~11 plus crypto properties, seed `270727` |
| Overall branch-aware coverage | 85% |
| U02 identity line coverage | 87.06%; 2,079 of 2,388 statements |
| Dependency lock | Passed; uv 0.11.32 resolved 54 locked packages with `lock --check` |
| OpenAPI | Passed; 20 versioned paths and no password hash/token-HMAC schemas |

The only emitted warning is the FastAPI compatibility alias warning for Starlette `TestClient`
using the currently pinned HTTPX integration. It does not affect runtime or test behavior and is
not a skipped or failed test.

## PostgreSQL Evidence

- Engine: PostgreSQL 17.10, x86-64 Windows build
- Isolated endpoint: `127.0.0.1:55433`
- Verified revision: `0002_u02_identity_expand`
- U02 schema tables: 23
- Clean database upgrade: passed, 23 tables
- U07 revision `0001_u07_platform_expand` to U02 head: passed, 23 tables
- Runtime role grants: applied and verified for schema usage and worker update privilege
- Repository evidence: unique active Google subject, optimistic conflicts, identity/outbox atomicity,
  lane priority, FeatureVersion ordering and contribution deduplication

The earlier U07 integration test was corrected to create only its owned outbox table. It no longer
drops/recreates global metadata or removes U02 partial unique indexes, so test order and repeated
runs remain isolated.

## Security and Privacy Gate

| Check | Result |
|---|---|
| CSRF token and exact Origin | Passed |
| Secure/HttpOnly/SameSite cookie contract | Passed |
| Enumeration-safe and localized errors | Passed |
| Argon2id and AES-GCM round trip/tamper | Passed |
| OAuth issuer/audience/nonce/redirect and bounded JWKS | Passed |
| Consent fail closed and withdrawal closure | Passed |
| Snapshot direct-identifier minimization | Passed |
| Telemetry label allow-list | Passed for email, UserId, OAuth subject, session ID/token, payload and object reference rejection |
| Secret-source scan | Passed; findings are secret-file path references only |
| Encrypted one-time export and deletion terminality | Passed |

## Failure Injection

Google connection timeout, consent read failure, session rotation write failure, high-lane retry
exhaustion, deletion category partial failure and 500-row key-rotation restart were injected. Each
path remained isolated, fail closed or recoverable according to its policy.

## Reproduction

Run with an actual migrated PostgreSQL URL:

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://ott_feed@127.0.0.1:55433/ott_feed_u02_test'
.venv\Scripts\pytest.exe -q -ra --hypothesis-seed=270727 --cov --cov-branch
.venv\Scripts\pytest.exe -q -ra -m integration
```

Any skipped integration test fails the U02 verification policy even if pytest exits successfully.
