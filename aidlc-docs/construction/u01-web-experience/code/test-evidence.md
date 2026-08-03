# U01 Test Evidence

## Automated gates (2026-08-03)

- Frontend: TypeScript strict and ESLint passed; 10 seeded PBT properties and 42 unit/component/contract tests passed.
- Browser: Playwright 1.62.1 on Chromium 151, Firefox 153, WebKit 26.5 and Pixel 7 emulation passed 24/24 journeys, including keyboard navigation, 200% reflow, Web Vitals/request budgets and axe serious/critical violations = 0.
- Performance: production initial route 78,984 gzip bytes and 4 initial asset requests; limit 200KB and 6 requests.
- Security: CSP parsed by Caddy, production source-map/secret/eval scan passed, `pnpm audit --audit-level high` reports 0 critical/high (3 moderate). React Router was pinned from vulnerable 7.18.2 to non-affected 6.30.4 because the advisory's 8.3.0 patched release was not present in the registry. License inventory generated with pnpm 11.18.0.
- Supply chain/runtime: Docker clean `pnpm install --frozen-lockfile` with Node 24.18.0 and pnpm 11.18.0 passed; unprivileged nginx image built and `/health/live` returned live.
- Backend telemetry: Ruff and mypy passed; 2 API validation tests passed.
- Infrastructure: base/local/remote Compose rendering passed; Caddy parser passed; promtool accepted 6 rule files including U01.

## Manual screen-reader gate

Status: **Verification Incomplete**

No actual NVDA/Chrome or VoiceOver/Safari session was available in this execution environment. The following required journeys therefore remain unexecuted and are not inferred from Playwright or axe results:

| Journey | Required environment | Result |
|---|---|---|
| Feed → Detail → Back | NVDA/Chrome or VoiceOver/Safari | Not executed |
| Search | Same | Not executed |
| Recommendation result announcement | Same | Not executed |
| Login Pending Intent resume | Same | Not executed |
| Consent withdrawal | Same | Not executed |
| Admin access denial | Same | Not executed |

OS, browser version, screen-reader version, input method, execution timestamp, expected/actual results and findings must be recorded when the manual run occurs. Until all six pass, Step 19 and Step 20 remain incomplete and final Code Generation approval is blocked.
