# U01 Web Experience NFR Requirements

## Scope

이 문서는 U01 브라우저 애플리케이션의 측정 가능한 품질 기준을 정의한다. Backend 처리 시간은 기존 U02~U07 기준을 상속하며, U01은 사용자 체감 성능, 접근성, 브라우저 호환성, 안전한 상태 관리와 부분 장애 표현을 추가로 책임진다.

## Performance and Capacity

| ID | Requirement | Verification gate |
|---|---|---|
| NFR-U01-01 | 정상적인 모바일 p75에서 LCP 2.5초 이하를 유지한다. | production build를 대상으로 browser performance test와 운영 Web Vitals를 측정한다. |
| NFR-U01-02 | p75 INP 200ms 이하, CLS 0.1 이하를 유지한다. | Feed, filter, detail, recommendation 핵심 여정에서 측정한다. |
| NFR-U01-03 | 초기 public route JavaScript는 gzip 200KB 이하이다. | build manifest의 app route chunk 합계를 검사한다. |
| NFR-U01-04 | route 단위 code splitting을 적용하고 admin, account 및 recommendation 기능을 초기 Feed bundle에서 분리한다. | build chunk graph를 검사한다. |
| NFR-U01-05 | 포스터는 표시 크기에 맞는 source set, lazy loading, 고정 aspect ratio를 사용한다. 첫 화면 visible card만 우선 로드한다. | component 및 Playwright network/layout 검사로 확인한다. |
| NFR-U01-06 | Backend 목표는 Feed/Detail p95 2초, Search p95 3초, Recommendation p95 10초를 상속한다. U01은 요청 즉시 pending 상태를 표시한다. | MSW delay test와 통합 E2E로 상태 전이를 확인한다. |
| NFR-U01-07 | 초기 동시 사용자 10명 미만을 지원하며 브라우저 상태는 server capacity를 증폭하는 polling이나 무제한 retry를 만들지 않는다. | request-count assertion과 retry policy test로 확인한다. |

## Accessibility and Usability

| ID | Requirement | Verification gate |
|---|---|---|
| NFR-U01-08 | 모든 public, member, operator 핵심 화면은 프로토타입의 자동화 가능한 WCAG 2.2 AA 기준을 충족한다. | axe serious/critical violation 0, semantic component test와 Chromium/Firefox/WebKit/mobile Playwright 핵심 여정이 모두 통과해야 한다. |
| NFR-U01-09 | Feed→Detail→Back, Search, Recommendation start/refine/reset, Login replay, Consent withdrawal, Admin override는 keyboard만으로 완료할 수 있다. | Playwright keyboard journey로 검증한다. |
| NFR-U01-10 | 핵심 여정은 heading, landmark, accessible name/role/value, live announcement 및 error relationship을 표준 접근성 트리에 노출해야 한다. | Testing Library role/accessibility-name assertion, axe, ARIA semantic component test와 Playwright announcement/focus journey로 검증한다. 실제 NVDA/Chrome 또는 VoiceOver/Safari 실행은 프로토타입 범위 밖이며 Future Manual QA로 분류한다. |
| NFR-U01-11 | 200% zoom과 320 CSS pixel 폭에서 정보나 기능 손실 없이 reflow한다. | desktop zoom과 mobile viewport 검사로 확인한다. |
| NFR-U01-12 | focus indicator는 가시적이며 route, modal, error, detail-return 전환에서 예상 지점으로 이동·복원된다. | component와 E2E focus assertion으로 확인한다. |
| NFR-U01-13 | 상태는 색만으로 전달하지 않고 이미지 대체 텍스트, form label 및 error association을 제공한다. | axe와 semantic component test로 확인한다. |

### Prototype accessibility scope

프로토타입의 필수 접근성 Gate는 Playwright Chromium/Firefox/WebKit/mobile, axe, keyboard-only 핵심 여정, focus 이동·복원, ARIA name/role/value와 live-region assertion, 200% zoom 및 320 CSS pixel reflow이다. 실제 NVDA/Chrome 또는 VoiceOver/Safari 수동 실행은 **Out of Scope for Prototype**이며 **Future Manual QA** 후보이다. 수동 실행을 완료한 것으로 간주하거나 주장하지 않으며, U01 프로토타입 완료를 차단하지 않는다.

## Localization and Browser Support

- NFR-U01-14: 모든 UI string, 상태, 오류, 동의 문구는 한국어와 영어 resource key로 제공하며 literal 누락 검사를 통과해야 한다.
- NFR-U01-15: 콘텐츠 fallback은 선택 언어, 원문, 정의된 fallback 순서이며 fallback 사용을 사용자에게 표시한다.
- NFR-U01-16: 최신 안정 Chrome, Edge, Firefox와 Safari 최신 2개 major, iOS Safari, Android Chrome을 지원한다.
- NFR-U01-17: browser matrix의 최소 한 desktop Chromium, Firefox, WebKit 및 mobile viewport 핵심 smoke test가 release gate이다.

## Reliability and Degraded Operation

- NFR-U01-18: 페이지 내 독립 API 영역은 failure boundary로 격리한다. 한 영역 오류가 sibling 성공 데이터를 제거하지 않는다.
- NFR-U01-19: stale 데이터에는 마지막 성공 시각, degraded 이유, 영향 범위와 국소 retry를 반드시 표시한다.
- NFR-U01-20: superseded read는 취소하고, 재시도는 bounded exponential backoff와 jitter를 사용한다. mutation은 명시적 idempotency 보장 없이는 자동 retry하지 않는다.
- NFR-U01-21: offline을 별도 지원 모드로 주장하지 않는다. network 단절은 보존 가능한 draft와 재시도 가능한 오류로 표현한다.
- NFR-U01-22: client cache는 편의적이며 서버 원본을 대체하지 않는다. logout, consent withdrawal, 403과 recommendation reset 시 정의된 보호 상태를 즉시 제거한다.
- NFR-U01-23: U07의 99.0%, RTO 4시간, RPO 24시간과 Backup and Restore 정책을 상속한다. U01에는 영속 비즈니스 데이터가 없어 별도 RPO가 없다.

## Browser Security and Privacy

- NFR-U01-24: 인증 session은 HttpOnly, Secure, SameSite cookie 기반이며 JavaScript가 credential 또는 bearer token을 읽거나 local storage에 보관하지 않는다.
- NFR-U01-25: state-changing request는 U02/U07 CSRF 계약을 사용한다.
- NFR-U01-26: production은 strict CSP를 nonce/hash 기반으로 적용하고 inline script 및 임의 third-party origin을 허용하지 않는다. Trusted Types 적용 준비 상태를 유지한다.
- NFR-U01-27: 외부 OTT URL은 server validation과 client allowlist를 모두 통과해야 하며 새 탭은 opener를 분리한다.
- NFR-U01-28: dependency audit에서 알려진 critical/high 취약점은 release 차단이다. 예외는 만료일과 완화책이 있는 기록을 요구한다.
- NFR-U01-29: browser telemetry에는 Web Vitals, route template, API operation/outcome, safe correlation ID만 허용한다. prompt, search 원문, content/user/session ID, credential 및 개인정보는 금지한다.
- NFR-U01-30: source map은 공개 정적 경로에 배포하지 않고 승인된 오류 분석 경로에서만 사용한다.

## Observability

- Web Vitals는 route template과 device class처럼 bounded dimension만 사용한다.
- API error는 server correlation ID와 연결하되 request/response body는 기록하지 않는다.
- client error는 release version, safe component boundary, error category를 포함한다.
- telemetry 전송 실패는 사용자 여정을 차단하지 않으며 무제한 queue를 만들지 않는다.
- U06/U07 운영 dashboard는 frontend LCP, INP, CLS, JavaScript error rate, API failure rate를 선택적으로 포함한다.

## Quality Gates

1. TypeScript strict compile, ESLint 및 formatting 통과.
2. Unit/component/example test와 P-U01-01~10 fast-check test 통과.
3. axe 자동 검사와 keyboard Playwright 핵심 여정 통과.
4. OpenAPI-generated client drift가 없어야 하며 MSW contract fixture가 schema에 부합해야 한다.
5. Chromium, Firefox, WebKit browser smoke test 통과.
6. statement/branch/function/line coverage는 각각 80% 이상이며 business rules와 accessibility adapters는 branch 90% 이상.
7. 초기 route gzip 200KB 및 Web Vitals 예산 통과.
8. production dependency audit에서 허용되지 않은 critical/high finding 0건.

## Traceability

| Concern | Requirements and stories | Functional rules |
|---|---|---|
| Perceived performance | NFR 7.1, US-001~US-013 | BR-U01-05~10, BR-U01-17~20 |
| Accessibility/localization | US-007, US-018, US-027, NFR 7.4 | BR-U01-23~28 |
| Privacy/security | US-014, US-018, US-021, US-027 | BR-U01-11~16, BR-U01-21~22 |
| Resiliency | US-003, US-024~US-025 | BR-U01-17~22 |

## Extension Compliance

### Resiliency Baseline

| Rule | Status | Rationale |
|---|---|---|
| RESILIENCY-01 | Compliant | Public Web Experience is classified as the terminal user-facing consumer with U02/U03/U05/U06/U07 dependencies. |
| RESILIENCY-02~04 | Compliant by inheritance | U07 availability, RTO/RPO, delivery and rollback decisions are unchanged. |
| RESILIENCY-05~07 | Compliant | Web Vitals, bounded client errors, API outcomes and dashboard integration are defined. |
| RESILIENCY-08~09 | N/A | U01 adds no independent server topology; capacity remains the approved single-server prototype baseline. |
| RESILIENCY-10 | Compliant | cancellation, bounded retry, failure isolation and degraded modes are specified. |
| RESILIENCY-11~14 | N/A | U01 owns no persistent business data or DR mechanism. |
| RESILIENCY-15 | Supporting | client evidence connects to U06 incident handling through safe correlation IDs. |

No blocking resiliency finding remains.

### Property-Based Testing

PBT-09 is satisfied by selecting fast-check for TypeScript and Vitest integration. P-U01-01~10 remain mandatory Code Generation gates with shrinking and seed reproduction. No blocking PBT finding remains.

### Security Baseline

Disabled and N/A as an extension. NFR-U01-24~30 preserve required browser security and privacy as core requirements.
