# U01 Web Experience NFR Design Patterns

## Design Drivers

U01은 public terminal consumer이며 U02, U03, U05, U06, U07의 실패와 지연을 사용자에게 안전하게 표현해야 한다. 설계는 URL·server cache·form·component 상태를 분리하고, 인증·동의·운영자 상태가 공개 화면 cache와 섞이지 않도록 한다.

## Resilience Patterns

### Three-Level Failure Isolation

1. `AppFatalBoundary`는 boot, router, locale resource처럼 앱 전체를 시작할 수 없는 오류만 처리한다.
2. `RouteErrorBoundary`는 route loader, lazy chunk 및 page composition 오류를 해당 route에 격리한다.
3. `RemoteRegionBoundary`는 Feed section, recommendation results, notification panel처럼 독립 API 영역의 오류를 격리한다.

Boundary reset은 영향받은 query와 component state만 초기화한다. sibling 성공 데이터와 URL state는 유지한다. 예외 메시지나 stack은 사용자에게 노출하지 않고 safe correlation reference만 표시한다.

### Bounded Request Policy

- superseded read는 API client가 전달한 `AbortSignal`로 취소한다.
- read retry는 최대 2회이며 bounded exponential backoff와 jitter를 적용한다.
- 4xx, validation, authorization, abort 및 mutation은 자동 retry하지 않는다.
- mutation replay는 server idempotency contract와 동일 idempotency key가 있는 경우에만 명시적으로 허용한다.
- 401 복구는 single-flight로 합쳐 다중 재인증 요청을 막는다. 성공 후 Pending Intent를 한 번만 소비한다.

### Remote Resource State Machine

`idle → pending → success|empty|error`를 기본으로 하고 prior success가 있는 refetch 실패만 `stale` 또는 `degraded`가 된다. stale/degraded에는 data, fetchedAt, reason, scope, retry action이 모두 있어야 한다. error reset은 무한 retry loop를 만들지 않는다.

### Protected Cache Partition and Purge

Query keys는 `public`, `member`, `recommendation`, `admin` namespace로 구분한다.

- logout: 진행 중인 protected query를 cancel하고 member/recommendation/admin cache, Pending Intent 및 form secret을 remove한다.
- consent withdrawal: personalization 목적 query, conversation, pending feedback를 cancel/remove한 뒤 public non-personalized query로 전환한다.
- recommendation reset: session query, turns, conditions, results와 retry token을 하나의 transition으로 제거한다.
- operator 403: admin query와 drafts를 즉시 제거하며 public cache로 projection하지 않는다.

Purge coordinator는 remove 완료 후 성공 announcement를 발생시켜 삭제 전 상태가 다시 render되는 race를 막는다.

## Performance Patterns

### Route and Asset Boundaries

- 초기 chunk: AppShell, locale bootstrap, public navigation, Feed route.
- intent prefetch: Search와 Detail은 pointer/focus intent 또는 viewport 근접 시 bounded prefetch한다.
- lazy protected chunk: Recommendation, Account와 Admin은 route intent 및 필요한 auth state 확인 후 가져온다.
- 모든 route를 eager prefetch하지 않으며 connection quality와 save-data preference를 존중한다.

Build manifest analyzer는 초기 route gzip 200KB를 계산한다. route import graph가 account/admin/recommendation을 초기 chunk로 역참조하면 실패한다.

### Bounded List and Image Policy

- server cursor/page가 렌더링 상한을 결정하며 stable opaque content ID를 key로 사용한다.
- responsive source set, width/height 또는 aspect ratio, native lazy decoding/loading을 적용한다.
- 첫 viewport의 핵심 포스터만 우선 load하고 나머지는 lazy load한다.
- virtualization은 항목 수와 INP/heap 측정이 정해진 threshold를 위반한 경우에만 ADR로 도입한다. 기본 접근성·focus 순서를 우선한다.

### Cache and Concurrency

- TanStack Query가 같은 query key 요청을 coalesce한다.
- stale time은 resource 유형별로 서버 freshness contract보다 짧게 설정하며 무제한 polling은 금지한다.
- filter/search 입력은 debounce하되 submit 가능한 명시적 action을 유지한다.
- prefetch와 telemetry는 사용자 요청보다 낮은 우선순위이며 bounded concurrent slot을 사용한다.

## Security and Privacy Patterns

### CSP-Compatible Bootstrap

Runtime public configuration은 same-origin JSON endpoint 또는 non-executable JSON payload에서 읽는다. 허용 항목은 API base path, locale default, release version 등 공개 값뿐이다. credential, provider secret 및 signing key는 포함하지 않는다.

Caddy는 nonce/hash 기반 strict CSP를 제공하며 executable inline script와 `unsafe-inline`을 허용하지 않는다. production build는 eval 기반 code와 공개 source map을 차단한다. Trusted Types 도입을 방해하는 raw HTML sink는 별도 adapter 이외에서 금지한다.

### Session and CSRF Boundary

API Client Boundary만 credentialed same-origin request와 CSRF token lifecycle을 처리한다. component에는 token이 전달되지 않는다. HttpOnly session cookie는 JavaScript에서 읽을 수 없으며 local/session storage에 bearer credential을 기록하지 않는다.

### Safe External Navigation

generated transport response는 곧바로 link가 되지 않는다. Presentation Mapper가 scheme, provider host allowlist, server validation flag를 검사하여 `SafeExternalDestination`만 생성한다. 새 탭은 opener를 차단하며 목적지와 새 창임을 accessible name에 포함한다.

### Privacy-Safe Telemetry

Telemetry schema는 route template, release, metric name/value, API operation/outcome, error category, safe correlation ID만 허용한다. prompt, search text, content/user/session/trace ID, request/response body는 schema 이전 sanitizer에서 제거한다.

메모리 queue는 개수와 byte 상한이 있고 batch 전송한다. `sendBeacon` 또는 짧은 keepalive fetch 실패 시 데이터를 폐기하며 local storage나 domain audit에 승격하지 않는다.

## Accessibility Patterns

### Semantic Primitive Layer

native element를 우선하는 내부 primitive가 `Button`, `Link`, `Field`, `ErrorSummary`, `Disclosure`, `Dialog`, `LiveRegion` 계약을 제공한다. page는 ARIA 동작을 재구현하지 않고 primitive를 조합한다. custom widget은 native 대안이 없고 keyboard·screen reader contract test가 있을 때만 허용한다.

### Focus and Announcement Coordination

- route 완료: page heading focus와 짧은 route announcement.
- detail return: origin card가 있으면 복원, 없으면 result heading.
- dialog close: invoker 복원.
- invalid submit: error summary focus 후 각 error link가 field로 이동.
- async result: settled count 또는 오류를 한 번만 announce하며 loading 변화마다 반복하지 않는다.

## Scalability Evolution

초기에는 Caddy가 hashed static asset을 제공한다. 측정된 budget 또는 origin bandwidth 위반 시 다음 순서로 확장한다.

1. immutable static asset CDN 도입;
2. responsive image optimization/storage 계층 분리;
3. telemetry sampling과 별도 collector 조정.

API query ownership과 same-origin security boundary는 유지한다. SSR/BFF는 SEO, first-load 또는 aggregation 요구가 측정으로 입증되고 별도 ADR이 승인될 때만 도입한다.

## PBT Design Mapping

| Property | Design subject | Model/oracle |
|---|---|---|
| P-U01-01~03 | canonical URL codec | pure normalized query reference model |
| P-U01-04 | locale fallback | ordered first-available oracle |
| P-U01-05 | consent purge | protected namespace set model |
| P-U01-06 | Pending Intent replay | login state command model |
| P-U01-07 | recommendation reset | conversation empty-state invariant |
| P-U01-08 | remote-resource transitions | explicit state transition oracle |
| P-U01-09 | accessible error references | generated form schema graph validator |
| P-U01-10 | logout/operator denial purge | auth-navigation state command model |

fast-check shrinking remains enabled. CI uses a documented fixed seed and prints the actual replay seed on failure. Every shrunk defect becomes an example regression test.

## NFR Traceability

- NFR-U01-01~07: route/asset, bounded list, image, cache and concurrency patterns.
- NFR-U01-08~17: semantic primitives, focus/announcement, localization and browser test boundaries.
- NFR-U01-18~23: three-level isolation, request policy, state machine and purge coordinator.
- NFR-U01-24~30: CSP bootstrap, session/CSRF, safe navigation and privacy telemetry.
