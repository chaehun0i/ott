# U01 Web Experience NFR Requirements Plan

> **Single Source of Truth**: 이 파일은 U01 NFR Requirements의 계획, 사용자 결정 및 완료 체크박스를 관리한다. 답변이 유효하고 모호하지 않을 때만 최종 NFR과 기술 스택 산출물을 생성한다.

## Context and Inherited Decisions

- **Approved Functional Scope**: URL 재현 가능한 Feed/Search, 독립 Detail route, 대화형 Recommendation, Account/Consent/Notification, 분리된 `/admin` UI.
- **Scale Baseline**: 초기 동시 사용자 10명 미만의 단일 서버 프로토타입.
- **Backend Latency Baseline**: Feed/Detail p95 2초, Search p95 3초, Recommendation p95 10초.
- **Availability and Recovery**: U07에서 확정된 99.0%, RTO 4시간, RPO 24시간, Backup and Restore 정책을 상속한다.
- **Backend Runtime**: Python 3.12, FastAPI/Pydantic, PostgreSQL, OpenAPI.
- **Frontend State**: 기존 프런트엔드 코드나 JavaScript package manifest가 없다.
- **Enabled Extensions**: Resiliency Baseline (Full), Property-Based Testing (Full).
- **Disabled Extension**: Security Baseline. 핵심 브라우저 보안과 개인정보 보호는 일반 NFR로 유지한다.

## Execution Plan

### Step 1 - Context and Baseline

- [x] 승인된 U01 Functional Design과 P-U01-01~10을 분석했다.
- [x] 기존 Backend API, OpenAPI 경계 및 U07 운영 기준을 확인했다.
- [x] U01의 접근성·체감 성능·다국어·브라우저 보안 요구를 식별했다.
- [x] 기존 프런트엔드 기술 스택이 없음을 확인했다.

### Step 2 - NFR Decisions

- [x] 성능, 접근성, 지원 브라우저, 기술 스택, 테스트 및 관측성의 미결정을 식별했다.
- [x] 모든 질문에 상호 배타적 선택지와 마지막 `X) Other`를 포함했다.
- [ ] Question 1~12의 모든 `[Answer]:` 값을 수집한다.
- [ ] 답변의 유효성·일관성·기존 기준 충돌 여부를 검증하고 필요한 경우 clarification 질문을 작성한다.

### Step 3 - NFR Requirements

- [ ] 페이지·상호작용·bundle·이미지 체감 성능 목표를 정의한다.
- [ ] 접근성 적합성, 키보드·스크린리더 및 다국어 품질 Gate를 정의한다.
- [ ] 브라우저 보안, 세션, CSP, 개인정보 및 외부 링크 기준을 정의한다.
- [ ] 부분 장애, 재시도, 캐시, 로깅 및 사용자 관측성 기준을 정의한다.
- [ ] `nfr-requirements.md`를 생성한다.

### Step 4 - Technology and Quality Gates

- [ ] UI framework, language, build/package, routing/data/form/i18n/style 기술 결정을 기록한다.
- [ ] unit, component, accessibility, PBT, contract 및 browser E2E 도구를 확정한다.
- [ ] PBT-09 framework와 P-U01-01~10의 실행 Gate를 연결한다.
- [ ] 정적 분석, type checking, coverage, bundle 및 OpenAPI drift Gate를 정의한다.
- [ ] `tech-stack-decisions.md`를 생성한다.

### Step 5 - Validation and Completion

- [ ] U01 Story/Functional Rule/NFR/Technology 추적성을 검증한다.
- [ ] Resiliency와 Property-Based Testing 확장 규칙 준수를 검증한다.
- [ ] Markdown 및 질문·답변 구조를 검증한다.
- [ ] 계획·상태·감사 로그를 갱신하고 NFR Requirements 검토를 요청한다.

## NFR Requirements Questions

각 `[Answer]:` 뒤에 선택한 문자 하나를 입력한다. 선택지에 없는 정책이면 `X`를 쓰고 같은 줄에 원하는 내용을 설명한다.

## Question 1
U01의 주 UI 기술 스택은 무엇으로 확정할까요?

A) React 19 + TypeScript strict + Vite 기반 SPA를 사용한다

B) Vue 3 + TypeScript strict + Vite 기반 SPA를 사용한다

C) 서버 렌더링 템플릿과 최소 JavaScript를 사용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 2
Node.js와 package 관리 기준은 무엇으로 정할까요?

A) Node.js 24 LTS를 고정하고 Corepack 기반 pnpm lockfile과 frozen install을 사용한다

B) Node.js 22 LTS와 npm lockfile을 사용한다

C) 시스템 Node.js 최신 버전과 lockfile 없는 설치를 허용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 3
라우팅·서버 상태·폼 상태의 기본 라이브러리 경계는 무엇인가요?

A) React Router + TanStack Query + React Hook Form/Zod를 사용하고 URL·서버·폼 상태 소유권을 분리한다

B) Redux Toolkit 하나에 route 이외의 모든 상태를 통합한다

C) 외부 상태 라이브러리 없이 React state와 직접 fetch만 사용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 4
스타일과 컴포넌트 접근 방식은 무엇으로 정할까요?

A) CSS Modules와 CSS custom properties로 design token을 관리하고 의미 기반 headless component를 필요한 곳에만 사용한다

B) utility-first CSS framework를 기본 스타일 체계로 사용한다

C) 완성형 UI component suite의 기본 theme와 interaction을 그대로 사용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 5
접근성 적합성과 검증 범위는 무엇인가요?

A) WCAG 2.2 AA를 기준으로 자동 axe, 키보드 전 여정, screen reader 핵심 여정 및 200% zoom/reflow를 release gate로 둔다

B) WCAG 2.1 AA 자동 검사와 키보드 smoke test까지만 release gate로 둔다

C) semantic HTML code review만 수행하고 자동·수동 접근성 gate는 두지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 6
지원 브라우저 기준은 무엇인가요?

A) 최신 안정 Chrome, Edge, Firefox와 Safari 최신 2개 major, iOS Safari/Android Chrome을 지원한다

B) Chromium 최신 안정 버전만 지원한다

C) 데스크톱 최신 브라우저만 지원하고 모바일 브라우저는 제외한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 7
프런트엔드 체감 성능과 bundle 예산은 무엇으로 확정할까요?

A) p75 LCP 2.5초 이하, INP 200ms 이하, CLS 0.1 이하와 초기 route JS gzip 200KB 이하를 gate로 둔다

B) backend p95 목표만 유지하고 Web Vitals와 bundle 예산은 측정만 한다

C) 기능 완성 후 운영 전환 단계에서 처음 성능 예산을 정한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 8
이미지와 route resource loading 전략은 무엇인가요?

A) route code splitting, 크기별 이미지, lazy loading, 고정 aspect ratio와 visible-card 우선 loading을 적용한다

B) 단일 JavaScript bundle과 원본 이미지를 사용하고 브라우저 cache에 맡긴다

C) 포스터 이미지를 초기 버전에서 표시하지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 9
프런트엔드 보안 기준은 무엇으로 정할까요?

A) strict CSP nonce/hash, HttpOnly/Secure/SameSite session cookie, CSRF contract, Trusted Types 준비, 외부 URL allowlist와 dependency audit를 gate로 둔다

B) 기본 same-origin 정책과 서버 인증만 적용하고 CSP는 운영 전환 시 추가한다

C) 브라우저 저장소에 bearer token을 저장하고 API 요청에 직접 첨부한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 10
테스트 도구와 PBT framework는 무엇으로 정할까요?

A) Vitest + Testing Library + axe-core + fast-check + Playwright를 사용하고 MSW로 API contract 시나리오를 격리한다

B) Vitest example test와 수동 브라우저 검사만 사용한다

C) Playwright E2E만 사용하고 unit/component/PBT를 두지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 11
프런트엔드 품질 Gate는 무엇인가요?

A) TypeScript strict, ESLint, formatting, unit/component/PBT, contract, axe, Playwright 핵심 여정, coverage와 bundle budget을 모두 통과해야 한다

B) TypeScript build와 unit test만 통과하면 된다

C) production build 성공만 필수로 한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 12
브라우저 telemetry와 개인정보 기준은 무엇인가요?

A) Web Vitals·route·API outcome·safe correlation ID만 수집하고 prompt, query 원문, content/user/session ID 및 개인정보는 수집하지 않는다

B) 문제 재현을 위해 입력 원문과 사용자 ID를 client log에 포함한다

C) 초기 버전에서는 오류나 성능 telemetry를 전혀 수집하지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Planned Artifacts

- `aidlc-docs/construction/u01-web-experience/nfr-requirements/nfr-requirements.md`
- `aidlc-docs/construction/u01-web-experience/nfr-requirements/tech-stack-decisions.md`

## Preliminary Extension Assessment

### Resiliency Baseline

- RESILIENCY-01, 05~07, 10은 public terminal consumer의 부분 장애, Web Vitals, 오류 상관관계 및 dependency isolation에 적용한다.
- RESILIENCY-02~04, 08~15의 배포·복구·운영 기준은 승인된 U06/U07 결정을 상속하며 U01에서 재결정하지 않는다.

### Property-Based Testing

- PBT-09에 따라 TypeScript UI에 fast-check를 후보 framework로 제시했다.
- P-U01-01~10은 generator, shrinking, seed 재현, stateful model과 example test 병행 기준으로 Code Generation에 전달한다.

### Security Baseline

- 확장은 비활성화로 N/A이다. CSP, cookie/CSRF, 외부 URL, dependency audit와 telemetry 최소화는 핵심 NFR 후보로 유지한다.
