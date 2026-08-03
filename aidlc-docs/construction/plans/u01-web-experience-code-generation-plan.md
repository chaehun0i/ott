# U01 Web Experience Code Generation Plan

> **Single Source of Truth**: Part 2는 아래 Step 1~20을 정의된 순서대로만 실행한다. 각 Step 완료와 같은 상호작용에서 해당 체크박스를 `[x]`로 갱신한다. 이 계획에 없는 application code나 infrastructure 변경은 수행하지 않는다.

## Approval Status

- **Infrastructure Design**: Approved on 2026-08-03.
- **Code Generation Part 1**: Approved on 2026-08-03.
- **Code Generation Part 2**: In progress from Step 1.
- **Automatic GitHub Actions**: Paused; local and controlled manual verification only.

## Unit Context

| Item | U01 scope |
|---|---|
| Primary story | US-007 multilingual and accessible common UI |
| Supporting stories | US-001~US-006, US-008~US-019, US-021, US-027 |
| Functional rules | BR-U01-01~28 |
| NFR | NFR-U01-01~30 |
| Property tests | P-U01-01~10 |
| Upstream contracts | U02 Identity/Profile/Consent/Feedback, U03 Feed/Detail/Search, U05 Recommendation/Conversation, U06 Notification/Admin/Incident, U07 OpenAPI/Error/Session/Runtime |
| Persistent data | None; browser cache is non-authoritative and protected state is purgeable |
| Runtime | React/TypeScript static SPA in a non-root read-only Web container behind Caddy |

## Code Locations

Application code remains in the workspace root and never under `aidlc-docs/`.

| Layer | Planned paths |
|---|---|
| Frontend manifest/build | `frontend/package.json`, `frontend/pnpm-lock.yaml`, `frontend/tsconfig*.json`, `frontend/vite.config.ts`, `.node-version` |
| Application source | `frontend/src/app/`, `frontend/src/routes/`, `frontend/src/features/`, `frontend/src/shared/` |
| API contracts | `frontend/openapi/`, `frontend/src/shared/api/generated/`, `frontend/src/shared/api/` |
| Locale/assets/styles | `frontend/src/locales/`, `frontend/src/assets/`, `frontend/src/styles/` |
| Tests | `frontend/src/**/*.test.ts(x)`, `frontend/tests/{pbt,contract,e2e,a11y,performance}/` |
| Runtime/deployment | `frontend/Dockerfile`, `frontend/web-server.conf`, `frontend/public/config/runtime.json`, `compose.yaml`, `compose.remote.yaml`, `infra/caddy/Caddyfile`, `infra/blackbox/`, `infra/prometheus/`, `infra/grafana/` |
| Backend integration | minimal typed client-telemetry API under existing `backend/src/ott_feed/` and tests only as required by approved infrastructure |
| Documentation | `aidlc-docs/construction/u01-web-experience/code/` Markdown summaries only |

## Planning Completion

- [x] U01 Functional, NFR and Infrastructure Design artifacts를 읽고 구현 경계를 추출했다.
- [x] Primary/Supporting story, dependency map, BR/NFR와 P-U01-01~10을 확인했다.
- [x] 기존 backend, Compose, Caddy, Blackbox, Prometheus/Grafana 구조를 확인했다.
- [x] exact application/test/config 경로와 20개 순차 Step을 정의했다.
- [x] registry/lockfile, Compose resource, PBT, 접근성, browser, privacy, CSP와 full regression Gate를 포함했다.
- [x] 계획 승인 전 application code와 infrastructure file을 변경하지 않았다.

## Review Remediation

- [x] Step 19의 수동 스크린리더 검증을 실제 통과가 필요한 blocking Gate로 강화했다. 실행 불가나 일부 미실행은 `Verification Incomplete`이며 Step 19·20과 최종 완료를 차단한다.
- [x] 수동 evidence에 검증 환경, OS/browser/screen-reader 버전, 핵심 여정별 결과와 발견 사항을 기록하도록 명시했다.
- [x] 최소 수동 여정에 Feed→Detail→Back, Search, Recommendation 결과 announcement, 로그인 Pending Intent 재개, 동의 철회, Admin 접근 거부를 포함했다.
- [x] Step 6의 선택자 정책을 role·accessible name 우선으로 변경하고 `data-testid`는 안정적인 semantic selector가 없는 경우에만 허용했다.
- [x] 기존 20-Step 실행 순서와 나머지 blocking Gate를 변경하지 않았다.

## Part 2 Execution Plan

### Step 1 - Registry, Runtime and Minimal Web Infrastructure Admission

- [x] 공식 registry에서 Node 24.18.0 LTS, React 19.2.8, Vite 8.2.0, pnpm 11.18.0과 선택 package의 stable 호환 버전을 재검증하고 exact `package.json`, `pnpm-lock.yaml`, `.node-version`을 생성했다. TypeScript 7.0.2는 typescript-eslint/openapi-typescript peer 범위를 벗어나므로 호환 가능한 5.9.3으로 고정했으며 clean `pnpm install --frozen-lockfile`과 peer Gate를 통과했다.
- [x] feature code보다 먼저 최소 `frontend/Dockerfile`, web-server config, runtime config skeleton과 Compose `web` service를 추가했다. base/remote `docker compose config`에서 CPU `0.5`, memory `256m`, user `101:101`, read-only, edge network only, no secret/DB/private network, healthcheck, JSON rotation과 remote immutable image reference를 검증했다.

### Step 2 - Frontend Workspace and Quality Skeleton

- [x] Vite React/TypeScript strict workspace, path aliases, CSS Modules/token, locale bootstrap과 empty AppShell을 생성했다.
- [x] TypeScript strict/noUncheckedIndexedAccess, ESLint, formatting, Vitest coverage, axe, fast-check와 Playwright configuration을 연결했다.
- [x] formatting, typecheck, lint, unit smoke, production build를 통과하고 initial route manifest gzip 80,045 bytes로 200KB budget 이내임을 확인했다.

### Step 3 - Generated OpenAPI Client and Typed Transport Boundary

- [ ] 실제 Backend OpenAPI schema를 deterministic artifact로 추출하고 TypeScript client를 생성한다. generated code drift 명령을 추가한다.
- [ ] `ApiClientBoundary`의 AbortSignal, CSRF, credentialed same-origin, typed outcome와 safe correlation mapping을 구현한다.
- [ ] MSW contract fixture가 schema와 success/401/403/409/422/429/5xx/network/abort 결과를 검증하도록 한다.

### Step 4 - Pure Presentation Models and Mappers

- [ ] Content, Feed/Search query, Recommendation, Session/Consent, Notification/Admin presentation entities를 구현한다.
- [ ] transport-to-presentation mapper, locale fallback과 `SafeExternalDestination` allowlist validation을 구현한다.
- [ ] missing/invalid/unsafe field가 invented metadata나 unsafe link로 변환되지 않는 example test를 추가한다.

### Step 5 - Canonical URL, Locale and Query Properties

- [ ] Feed/Search query normalize/parse/serialize codec와 Korean/English fallback을 구현한다.
- [ ] P-U01-01~04의 round-trip, idempotence, commutativity, locale oracle fast-check test와 reusable constrained generators를 추가한다.
- [ ] shrinking과 seed replay가 가능한 별도 PBT command를 검증한다.

### Step 6 - Semantic Primitive and Accessibility Foundation

- [ ] Button, Link, Field, ErrorSummary, Disclosure, Dialog, LiveRegion, RemoteRegion primitive를 native-first로 구현한다.
- [ ] 테스트 선택자는 role·accessible name·label·text와 같은 사용자 인지 가능한 semantic selector를 우선한다. 반복 목록이나 비가시적 기술 상태처럼 안정적인 semantic selector가 없고 테스트 목적상 필요한 경우에만 stable `data-testid`를 사용하며, 모든 interactive element에 일괄 추가하지 않는다.
- [ ] keyboard/name-role-value/focus/error association example test와 axe test, P-U01-09 error-reference property를 추가한다.

### Step 7 - App Shell, Routing, Focus and Error Boundaries

- [ ] App fatal, route, remote-region 3계층 boundary와 AppShell/primary navigation/locale selector/route announcer를 구현한다.
- [ ] public/member/admin route guard, lazy route boundaries, detail return focus와 safe 404/access-denied flow를 구현한다.
- [ ] route navigation, boundary reset, focus restoration과 Korean/English announcement test를 추가한다.

### Step 8 - Query Coordinator and Protected State Purge

- [ ] public/member/recommendation/admin query key factory, bounded retry/cancellation/coalescing policy를 구현한다.
- [ ] logout, consent withdrawal, recommendation reset, admin 403의 atomic cancel/remove coordinator를 구현한다.
- [ ] P-U01-05, P-U01-07, P-U01-08, P-U01-10의 invariant/stateful test와 explicit regression examples를 추가한다.

### Step 9 - Authentication Recovery and Pending Intent

- [ ] CSRF lifecycle, 401 single-flight recovery, login return route와 non-sensitive one-time Pending Intent를 구현한다.
- [ ] 실패 시 0회, 성공 시 정확히 1회 실행되는 P-U01-06 stateful model과 login/logout/session-expiry examples를 추가한다.
- [ ] credential/token이 props, browser persistence, telemetry 또는 logs에 나타나지 않는 privacy test를 추가한다.

### Step 10 - Feed, Filters and Content Detail

- [ ] U03 Feed/Detail API와 canonical URL filter/sort/pagination, freshness/stale/degraded UI를 구현한다.
- [ ] responsive content card/image, validated OTT external action, independent detail route와 back/focus restoration을 구현한다.
- [ ] US-001~US-003 example/component/contract/accessibility test를 추가한다.

### Step 11 - Search and Interpreted Conditions

- [ ] 단일 Korean/English search input, server-interpreted condition chips, filter/pagination과 empty/error flow를 구현한다.
- [ ] superseded search cancellation, bounded debounce/submit, condition modification과 URL reproduction을 구현한다.
- [ ] US-004~US-006 contract, race, Unicode, keyboard와 accessibility test를 추가한다.

### Step 12 - Recommendation Conversation

- [ ] U05 recommendation start/refine/reset, turns, current conditions, summary/reason/evidence disclosure와 safe fallback projection을 구현한다.
- [ ] request deduplication, session expiry, preserved draft, pending state와 result announcement를 구현한다.
- [ ] US-008~US-013 component/contract/example/accessibility test와 Step 8 conversation properties를 연결한다.

### Step 13 - Account, Library, Consent and Data Rights

- [ ] U02 profile/preferences/subscriptions/library/ratings/history/consent/export/delete 화면과 accessible forms를 구현한다.
- [ ] server validation/version conflict, consent withdrawal purge, destructive confirmation과 data-right job state를 구현한다.
- [ ] US-014~US-018, US-027 example/contract/privacy/accessibility test를 추가한다.

### Step 14 - Notification and Operator Routes

- [ ] U06 notification preferences, `/admin` shell, content override, trace와 incident route를 구현한다.
- [ ] recent-auth/role UI projection, expected version/reason, forbidden/missing non-disclosure와 admin cache purge를 구현한다.
- [ ] US-019, US-021, US-027 contract/example/keyboard/accessibility test를 추가한다.

### Step 15 - Browser Telemetry and Privacy Boundary

- [ ] allowlisted Web Vitals/route/API outcome/error event, sanitizer, bounded memory batch와 sendBeacon/fetch adapter를 구현한다.
- [ ] 최소 same-origin backend ingestion contract를 구현하여 schema, size, rate, forbidden field와 bounded label을 검증하고 기존 telemetry adapter로 연결한다.
- [ ] prompt/query/body/direct IDs/credential 거부, overflow/drop과 telemetry outage non-blocking test를 추가한다.

### Step 16 - Route Chunk, Asset and Performance Gates

- [ ] Feed initial, Search/Detail intent-prefetch, Recommendation/Account/Admin lazy chunk graph를 구현하고 forbidden eager import 검사기를 추가한다.
- [ ] responsive image/source set/lazy loading/fixed aspect ratio와 immutable asset/no-cache HTML contract를 구현한다.
- [ ] initial route gzip `200KB`, LCP/INP/CLS scenario와 request-count budget을 측정하는 blocking scripts/tests를 추가한다.

### Step 17 - Web Runtime, Caddy, Health and Network Integration

- [ ] Step 1 skeleton을 final unprivileged read-only runtime image, SPA/static 404 rules, `/health/live`, runtime config validation과 no-public-source-map contract로 완성한다.
- [ ] Caddy `/api/*` priority, web catch-all, zstd/gzip, immutable/no-cache headers, strict CSP 및 security headers를 구현한다.
- [ ] Compose/remote overlay network, health, resource, logging과 image digest contract를 완성하고 config/header/container-content tests를 통과시킨다.

### Step 18 - Synthetic Monitoring, Dashboard and Operational Evidence

- [ ] Blackbox public `/`/known asset check, Web Vitals/API outcome/JS error/drop metrics와 Prometheus/Grafana mapping을 추가한다.
- [ ] JSON stdout+Docker rotation을 원본으로, Loki를 optional search replica로 유지하며 privacy label/log 검사기를 추가한다.
- [ ] unhealthy-running은 alert와 operator runbook 대상이며 자동 health restart로 주장하지 않는 운영 evidence를 작성한다.

### Step 19 - Browser, Accessibility, Security and Supply-Chain Gates

- [ ] Playwright Chromium/Firefox/WebKit/mobile 핵심 여정, keyboard-only, 200% zoom/reflow와 automated axe suite를 통과시킨다.
- [ ] NVDA/Chrome 또는 VoiceOver/Safari 조합으로 수동 스크린리더 핵심 여정을 실제 실행하고 모두 통과시킨다. 최소 여정은 Feed→Detail→Back, Search, Recommendation 결과 announcement, 로그인 Pending Intent 재개, 동의 철회, Admin 접근 거부이다. Evidence에는 OS, browser와 screen-reader 이름·정확한 버전, 입력 방식, 실행 일시, 각 여정의 단계·기대 결과·실제 결과·Pass/Fail 및 발견 사항을 기록한다.
- [ ] 수동 검증 환경이 없거나 한 여정이라도 미실행·실패하면 상태를 `Verification Incomplete`로 유지한다. 이 상태에서는 Step 19를 `[x]`로 바꾸거나 Step 20 완료, Code Generation 최종 완료 표시 및 승인 요청을 수행하지 않는다. 자동 axe/Playwright 통과는 이 Gate를 대체하지 않는다.
- [ ] CSP parser, unsafe inline/eval, external URL, secret/source-map scan, frozen lock, dependency/license audit와 critical/high finding 0 gate를 통과시킨다.

### Step 20 - Full Regression, Traceability and Code Summary

- [ ] Step 19의 수동 스크린리더 evidence가 지정된 도구 조합과 최소 6개 여정을 모두 실제 Pass로 기록했는지 먼저 검증한다. `Verification Incomplete`, Fail 또는 누락이 있으면 Step 20에 진입하거나 완료 처리하지 않는다.
- [ ] frontend type/lint/format/build/unit/component/PBT/contract/a11y/browser/performance/security suite와 backend full test, real PostgreSQL integration skip=0을 모두 실행한다.
- [ ] Compose base/local/remote config, Caddy, web image/resource/network/health/logging, OpenAPI drift와 clean frozen install을 재검증한다.
- [ ] US-001~US-019/US-021/US-027, BR-U01-01~28, NFR-U01-01~30, P-U01-01~10 traceability와 `code-generation-summary.md`, `test-evidence.md`, `traceability.md`를 생성한다.
- [ ] 20개 Step과 story checkbox를 모두 완료하고 상태·감사 로그를 갱신한 뒤 Code Generation 최종 승인을 요청한다.

## Story and Step Traceability

| Story group | Implementation steps | Verification steps |
|---|---|---|
| US-001~US-003 | 4~8, 10 | 16, 19~20 |
| US-004~US-007 | 5~7, 11 | 16, 19~20 |
| US-008~US-013 | 4, 8, 12 | 16, 19~20 |
| US-014~US-018 | 8~9, 13 | 15, 19~20 |
| US-019, US-021, US-027 | 8~9, 14 | 15, 18~20 |

## PBT Compliance Plan

| Rule | Planning status | Evidence target |
|---|---|---|
| PBT-01 | Compliant | P-U01-01~10 carried into Steps 5~9 |
| PBT-02~06 | Planned, blocking | URL round-trip, normalization/purge/reset invariants, locale oracle and auth/cache state models |
| PBT-07 | Planned, blocking | reusable query, locale, form, remote-state and auth command generators |
| PBT-08 | Planned, blocking | fast-check shrinking, fixed CI seed and reported replay seed |
| PBT-09 | Planned admission | exact stable fast-check version locked and frozen-installed in Step 1 |
| PBT-10 | Planned, blocking | explicit critical journey examples alongside every property family |

No PBT completion claim is allowed before Steps 5~9 and Step 20 evidence pass.

## Resiliency, Security and Release Gates

- Step 1 package/lock/runtime and minimal Compose admission must pass before feature implementation.
- Web must render as 0.5 CPU/256MB, non-root/read-only, edge-network-only with no secret/DB/private network.
- Docker restart is process-exit behavior only; unhealthy-running is alert plus operator action.
- API and SPA route precedence, static asset 404 behavior, CSP and health consumers are independently tested.
- Browser telemetry is best-effort observability data, never audit/domain truth, and rejects raw input/direct identifiers.
- PBT, accessibility, browser, privacy/security, performance and supply-chain gates are blocking.
- NVDA/Chrome 또는 VoiceOver/Safari 실제 수동 검증은 대체 불가능한 blocking Gate이다. 최소 6개 여정이 모두 Pass이고 환경·정확한 버전·여정·결과 evidence가 완전할 때만 Step 19와 Step 20을 완료할 수 있다.
- 수동 스크린리더 검증을 실행할 수 없거나 일부만 실행한 경우 `Verification Incomplete`로 유지하며, Code Generation 완료 선언·최종 체크·승인 요청을 금지한다.
- Backend PostgreSQL integration selection must complete with skip=0; frontend success cannot mask a backend integration skip.
- Automatic GitHub Actions triggers remain paused throughout U01 Code Generation.

## Planned Summaries

- `aidlc-docs/construction/u01-web-experience/code/code-generation-summary.md`
- `aidlc-docs/construction/u01-web-experience/code/test-evidence.md`
- `aidlc-docs/construction/u01-web-experience/code/traceability.md`

## Approval Gate

Part 2 must not start until the user explicitly approves this complete 20-Step plan and execution sequence. Part 2가 승인되더라도 Step 19 수동 스크린리더 Gate가 실제 통과하지 않으면 최종 Code Generation 승인 요청을 제시할 수 없다.
