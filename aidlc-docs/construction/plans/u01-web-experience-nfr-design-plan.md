# U01 Web Experience NFR Design Plan

> **Single Source of Truth**: 이 파일은 U01 NFR Design의 패턴 결정, 사용자 답변 및 완료 체크박스를 관리한다. 답변이 유효하고 모호하지 않을 때만 최종 NFR Design 산출물을 생성한다.

## Context

- **Approved Inputs**: U01 Functional Design, NFR-U01-01~30, React 19.2, TypeScript strict, Vite 8.1, Node.js 24 LTS, pnpm, fast-check.
- **Required Categories**: Resilience, Scalability, Performance, Security and Logical Components.
- **Inherited Platform Decisions**: 단일 서버 프로토타입, U07 99.0%, RTO 4시간, RPO 24시간, Caddy/API same-origin 경계.
- **Enabled Extensions**: Resiliency Baseline (Full), Property-Based Testing (Full).
- **Disabled Extension**: Security Baseline. 핵심 CSP, cookie/CSRF, URL 및 telemetry 보호는 일반 NFR Design으로 유지한다.

## Execution Plan

### Step 1 - NFR Design Decision Collection

- [x] 승인된 U01 NFR Requirements, 기술 결정, Functional Rules 및 P-U01-01~10을 분석했다.
- [x] Resilience, Scalability, Performance, Security, Logical Components의 미결정 패턴을 식별했다.
- [x] 각 질문에 상호 배타적인 선택지와 마지막 `X) Other`를 포함했다.
- [x] Question 1~12의 모든 `[Answer]:` 값을 수집했다. 모든 답변은 `A`이다.
- [x] 답변 유효성, 상호 모순 및 NFR 충돌을 검증했다. clarification 필요가 없다.

### Step 2 - Resilience and State Patterns

- [x] route/region error boundary와 stale/degraded 상태 조합 패턴을 설계했다.
- [x] read cancellation, retry budget, mutation idempotency 및 auth recovery 패턴을 설계했다.
- [x] cache partition, protected-state purge 및 recommendation state machine을 설계했다.

### Step 3 - Performance and Scale Patterns

- [x] route chunk, prefetch, image loading 및 rendering budget 패턴을 설계했다.
- [x] query cache lifetime, request coalescing 및 bounded concurrency를 설계했다.
- [x] 초기 단일 서버와 scale trigger 이후 정적 자산·telemetry 확장 경계를 설계했다.

### Step 4 - Security, Accessibility and Logical Components

- [x] CSP bootstrap, cookie/CSRF, URL allowlist 및 private source-map 패턴을 설계했다.
- [x] semantic primitive, focus manager, route announcer 및 error association 패턴을 설계했다.
- [x] API Gateway Client, Query Coordinator, Telemetry Adapter와 Quality Gate 구성요소를 정의했다.

### Step 5 - Artifacts and Validation

- [x] `nfr-design-patterns.md`를 생성했다.
- [x] `logical-components.md`를 생성했다.
- [x] NFR-U01-01~30, BR-U01-01~28, P-U01-01~10과 확장 규칙 추적성을 검증했다.
- [x] Markdown과 질문·답변 구조를 검증했다.
- [x] 계획·상태·감사 로그를 갱신하고 NFR Design 검토를 요청한다.

## NFR Design Questions

각 `[Answer]:` 뒤에 선택한 문자 하나를 입력한다. 선택지에 없는 정책이면 `X`를 쓰고 같은 줄에 원하는 내용을 설명한다.

## Question 1
페이지 오류와 부분 API 실패를 어떤 Error Boundary 구조로 격리할까요?

A) App fatal boundary, route boundary, 독립 remote-region boundary의 3계층으로 분리하고 각 영역에 안전한 reset/retry를 제공한다

B) App 최상위 Error Boundary 하나로 모든 오류를 전체 화면 처리한다

C) Error Boundary 없이 각 component의 try/catch만 사용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 2
TanStack Query read retry와 cancellation 패턴은 무엇인가요?

A) superseded request는 AbortSignal로 취소하고 read만 최대 2회 bounded exponential backoff+jitter로 재시도하며 4xx와 mutation은 자동 재시도하지 않는다

B) 모든 요청을 최대 5회 재시도하고 cancellation은 사용하지 않는다

C) 자동 재시도와 cancellation을 모두 사용하지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 3
client cache와 보호 상태의 분리·삭제 패턴은 무엇인가요?

A) public/member/admin/recommendation query key namespace를 분리하고 logout·403·동의 철회·reset event가 관련 namespace를 원자적으로 cancel/remove한다

B) 하나의 global cache를 사용하고 stale time 만료에만 맡긴다

C) 모든 응답을 local storage에 영구 저장하고 로그인 상태와 무관하게 재사용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 4
route chunk와 prefetch 경계는 어떻게 구성할까요?

A) public shell/feed는 초기 chunk, search/detail은 intent prefetch, recommendation/account/admin은 인증·탐색 의도 후 lazy chunk로 분리한다

B) 모든 route를 하나의 초기 bundle로 구성한다

C) 모든 route를 즉시 prefetch해 navigation latency를 최소화한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 5
목록 rendering과 이미지 loading의 확장 패턴은 무엇인가요?

A) cursor/page 단위 bounded list, stable keys, responsive image source와 lazy loading을 사용하고 측정 결과가 threshold를 넘을 때만 virtualization을 도입한다

B) 전체 결과를 한 번에 불러오고 항상 virtualization을 사용한다

C) pagination 없이 무제한 infinite scroll만 사용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 6
CSP와 runtime configuration bootstrap은 어떻게 설계할까요?

A) same-origin 외부 설정 endpoint 또는 non-executable JSON으로 public config만 주입하고 Caddy nonce/hash CSP에서 inline executable script를 금지한다

B) `window.CONFIG` inline script와 `unsafe-inline` CSP를 사용한다

C) API base URL과 비밀정보를 build-time JavaScript 상수에 모두 포함한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 7
CSRF와 인증 만료 복구는 어떤 공유 component가 담당할까요?

A) API Client Boundary가 CSRF 취득·mutation 첨부·401 single-flight 재인증을 담당하고 Pending Intent는 성공 후 한 번만 소비한다

B) 각 page가 CSRF와 401 처리를 독립 구현한다

C) CSRF 없이 bearer token을 local storage에서 읽어 첨부한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 8
접근성 상호작용 primitive의 소유권은 무엇인가요?

A) native element 우선의 내부 semantic primitive layer가 focus, dialog/disclosure, live region, field error 계약을 소유하고 page는 이를 조합한다

B) 각 page가 필요한 keyboard와 ARIA 동작을 개별 구현한다

C) 시각 component library 기본 동작을 별도 검증 없이 사용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 9
browser telemetry 수집과 전송 패턴은 무엇인가요?

A) allowlisted schema로 메모리에서 bounded batch하고 `sendBeacon`/짧은 fetch로 전송하며 unload 실패는 폐기하고 원문·식별자는 수집 전에 제거한다

B) 모든 console과 network body를 local storage queue에 무기한 보존해 전송한다

C) backend audit endpoint에 browser telemetry를 domain audit event로 기록한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 10
OpenAPI client와 presentation mapper의 실패 처리 경계는 무엇인가요?

A) generated transport client는 HTTP/schema 결과만 제공하고 typed mapper가 presentation model과 safe URL을 검증하며 mapping 실패는 data-contract 오류로 격리한다

B) generated response를 component가 직접 사용하고 필요한 field를 optional chaining으로 처리한다

C) OpenAPI client 없이 endpoint마다 수동 fetch type을 작성한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 11
PBT stateful model과 seed 재현은 어디에 배치할까요?

A) pure state modules와 adapters에 fast-check model commands를 두고 CI 고정 seed와 실패 seed 출력을 모두 지원하며 shrunk case를 example regression으로 승격한다

B) component snapshot에 무작위 props만 전달하고 seed는 기록하지 않는다

C) PBT는 query string 함수에만 한정하고 stateful test를 제외한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 12
초기 규모를 넘었을 때 U01 확장 순서는 무엇인가요?

A) 정적 자산 CDN, 이미지 최적화 계층, telemetry sampling 순으로 분리하고 API/cache 소유권은 유지하며 측정된 budget 위반에서만 적용한다

B) 첫 scale trigger에서 SSR 서비스와 별도 BFF를 동시에 도입한다

C) 구조 변경 없이 browser cache 기간만 늘린다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Planned Artifacts

- `aidlc-docs/construction/u01-web-experience/nfr-design/nfr-design-patterns.md`
- `aidlc-docs/construction/u01-web-experience/nfr-design/logical-components.md`

## Preliminary Extension Assessment

### Resiliency Baseline

- Question 1~5, 9, 12가 RESILIENCY-05~07, 09~10의 failure isolation, bounded retry, capacity 및 telemetry 패턴을 결정한다.
- RESILIENCY-02~04, 08, 11~15는 U06/U07의 승인된 배포·복구·incident 결정을 상속한다.

### Property-Based Testing

- Question 3, 10~11은 P-U01-01~10의 pure/stateful model, adapter oracle, shrinking과 seed 재현 구조를 결정한다.
- PBT-02~08, PBT-10 구현 세부사항은 Code Generation 계획에서 차단 Gate로 연결한다.

### Security Baseline

- 확장은 비활성화로 N/A이다. Question 3, 6~10의 cache purge, CSP, cookie/CSRF, URL validation과 telemetry privacy는 일반 NFR Design으로 적용한다.
