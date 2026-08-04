# U01 Test Evidence

Execution time: 2026-08-04T15:43:00+09:00

Status: **Verification Complete**

## Automated verification

| Gate | Command or environment | Result |
|---|---|---|
| Frontend frozen install | Node 24.18.0, pnpm 11.18.0, local and Docker `pnpm install --frozen-lockfile` | Pass |
| Format, type, lint and build | Prettier, TypeScript `--noEmit`, ESLint, Vite production build | Pass |
| Unit and component | Vitest, 15 files | 51 passed |
| Property based | fast-check/Vitest, P-U01-01 through P-U01-10 | 10 passed |
| Contract | Vitest contract selection | 8 passed |
| Coverage | Vitest V8 | Statements 87.31%, branches 84.73%, functions 81.81%, lines 89.18% |
| Automated accessibility | axe plus Testing Library semantic assertions | Pass; serious/critical axe violations = 0; role/name/value, headings, landmarks, announcements and error relationships verified |
| Browser and interaction | Playwright 1.62.1 on Chromium, Firefox, WebKit and Pixel 7 | 24 passed; keyboard-only, focus, 200% zoom/reflow and critical journeys included |
| Performance | Production build and browser request assertions | Initial route 78,984 gzip bytes and 4 requests; limits 200 KB and 6 requests |
| Frontend security | CSP/source-map/secret/eval scan and `pnpm audit --audit-level high` | Pass; 0 critical/high, 3 moderate recorded |
| Backend static checks | Ruff no-cache and strict MyPy | Pass; MyPy checked 213 source files |
| Backend full regression | CPython 3.12.13, Hypothesis seed 260726 and live PostgreSQL URL | 326 passed, 0 skipped, branch-aware coverage 85.36% |
| Backend PBT | `pytest -m pbt`, seed 260726 | 53 passed, 0 skipped |
| PostgreSQL integration | pgvector 0.8.2 on PostgreSQL 17.10, `pytest -m integration -rs` | 34 passed, 0 skipped |
| OpenAPI drift | Fresh FastAPI export and temporary generated TypeScript client compared with committed artifacts | No semantic or generated-client drift |
| Compose | Base, local and remote overlays with immutable remote image variables | Pass |
| Caddy and Prometheus | Official Caddy validator and `promtool check config` | Pass; Prometheus main config and 6 rule files |
| Web image | Frozen Docker production build | Pass |

One non-blocking warning remains: Starlette reports that its `httpx` TestClient adapter is deprecated in favor of `httpx2`. It causes no skip or failure.

## Native screen-reader verification disposition

Status: **Out of Scope for Prototype / Future Manual QA**

Actual NVDA/Chrome and VoiceOver/Safari sessions were not executed and are not claimed as executed. By explicit user-approved scope amendment on 2026-08-04, native screen-reader execution is not a prototype completion Gate. A future production-readiness cycle may manually assess Feed to Detail to Back, Search, recommendation announcements, Login Pending Intent resume, consent withdrawal and Admin denial.

The prototype accessibility Gate is satisfied by the mandatory automated evidence above: Chromium/Firefox/WebKit/mobile coverage, axe, keyboard-only operation, focus management, ARIA name/role/value and live-announcement assertions, semantic error relationships, and 200% zoom/320 CSS pixel reflow.
