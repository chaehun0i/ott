# U01 Test Evidence

Execution time: 2026-08-04T11:30:06+09:00

Status: **Verification Incomplete**

All non-manual verification requested for the Step 20 handoff has been executed. These results are pre-executed evidence only: Step 20 is not entered or complete because its Step 19 screen-reader prerequisite has not passed.

## Automated verification

| Gate | Command or environment | Result |
|---|---|---|
| Frontend frozen install | Node 24.18.0, pnpm 11.18.0, `pnpm install --frozen-lockfile` locally and in Docker build | Pass |
| Format, type, lint | Prettier, TypeScript `--noEmit`, ESLint | Pass |
| Unit and component | Vitest, 15 files | 51 passed |
| Property based | fast-check/Vitest, P-U01-01 through P-U01-10 | 10 passed |
| Contract | Vitest contract selection | 8 passed |
| Coverage | Vitest V8 | Statements 87.31%, branches 84.73%, functions 81.81%, lines 89.18%; all thresholds pass |
| Browser and accessibility automation | Playwright 1.62.1, Chromium/Firefox/WebKit/Pixel 7; keyboard, 200% reflow, axe, performance | 24 passed |
| Performance | Production build and browser request assertions | Initial route 78,984 gzip bytes and 4 requests; limits 200 KB and 6 requests |
| Frontend security | CSP/source-map/secret/eval scan and `pnpm audit --audit-level high` | Pass; 0 critical/high, 3 moderate recorded |
| Production licenses | pnpm production inventory | MIT and Apache-2.0 only |
| Backend static checks | Ruff no-cache; strict MyPy | Pass; MyPy checked 213 source files |
| Backend full regression | CPython 3.12.13, Hypothesis seed 260726, live PostgreSQL URL | 326 passed, 0 skipped, branch-aware coverage 85.36% |
| Backend PBT | `pytest -m pbt`, seed 260726 | 53 passed, 0 skipped |
| Backend contract/quality | Contract plus performance, recovery, privacy and security quality directories | 56 passed, 0 skipped |
| PostgreSQL integration | pgvector 0.8.2 on PostgreSQL 17.10, `pytest -m integration -rs` | 34 passed, 0 skipped |
| OpenAPI drift | Fresh FastAPI export compared semantically; generated TypeScript client regenerated twice | No semantic drift; deterministic client generation |
| Compose | Base, local and remote overlays; immutable remote image variables | Pass |
| Caddy | Official `caddy fmt` and `caddy validate` | Pass |
| Prometheus | Official `promtool check config` | Pass; main config and 6 rule files |
| Web image runtime | Frozen Docker build, unprivileged nginx, `/health/live`, source-map search | Pass; live response and no source maps |

One non-blocking backend warning remains: Starlette reports that its `httpx` TestClient adapter is deprecated in favor of `httpx2`. It does not cause a skip or failure.

## Manual screen-reader gate

Status: **Not executed - blocking**

Automated axe, keyboard and browser tests do not replace this gate. Run all six journeys with either NVDA/Chrome or VoiceOver/Safari and record the exact OS, browser version, screen-reader version, input method, execution timestamp, expected result, actual result, Pass/Fail and findings.

| Journey | Required environment | Expected result | Actual result |
|---|---|---|---|
| Feed to Detail to Back | NVDA/Chrome or VoiceOver/Safari | Landmarks, headings, detail transition and restored feed context are announced and operable | Not executed |
| Search | Same | Search input, interpreted conditions and result count are announced and operable | Not executed |
| Recommendation result announcement | Same | New results, summary, reason and refinement state are announced once and remain operable | Not executed |
| Login Pending Intent resume | Same | Login context and the exactly-once resumed action are understandable and operable | Not executed |
| Consent withdrawal | Same | Confirmation and removal of personalized state are announced | Not executed |
| Admin access denial | Same | Denial is announced without disclosing protected operator data or actions | Not executed |

Until every row passes, Step 19 and Step 20 remain unchecked, Code Generation Complete is prohibited, and final approval must not be requested. This is the only remaining blocking item.
