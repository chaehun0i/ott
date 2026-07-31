# U06 Engagement and Operations NFR Design Plan

> **Single Source of Truth**: 이 파일은 U06 NFR Design의 패턴 결정, 사용자 답변과 완료 체크박스를 관리한다. 모든 답변이 유효하고 모호하지 않을 때까지 최종 설계 산출물을 생성하지 않는다.

## Context

- **Approved Inputs**: U06 Functional Design, U06-NFR-001~075, ADR-U06-001~010.
- **Required Categories**: Resilience, Scalability, Performance, Security and Logical Components.
- **Inherited Decisions**: Modular Monolith, PostgreSQL 17, Transactional Outbox, 월 99.0%, RTO 4시간, RPO 24시간, 단일 서버 프로토타입, 월별 Dependency Failure Test와 분기별 Restore Drill, 경량 Incident/COE Process.
- **Enabled Extensions**: Resiliency Baseline (Full), Property-Based Testing (Full).
- **Disabled Extension**: Security Baseline. 핵심 권한·감사·비식별 요구는 일반 NFR 설계로 유지한다.

## Execution Plan

### Step 1 - NFR Design Decision Collection

- [x] U06 NFR, ADR, Functional Rule과 U02~U05/U07 Contract를 읽는다.
- [x] 다섯 필수 NFR Design Category의 미결 패턴을 식별한다.
- [x] 상호 배타적 선택지와 마지막 `X) Other`를 포함한 Question 1~14를 작성한다.
- [x] 모든 `[Answer]:` 값을 수집하고 유효성·모순·기존 결정 충돌을 검증한다. Question 1~14는 모두 유효한 `A`다.
- [x] 모호성이 있으면 별도 clarification 질문을 작성하고 해결한다. 모든 답변이 일관되어 추가 질문은 필요하지 않다.

### Step 2 - Resilience and Processing Patterns

- [x] Notification lane, claim/lease, retry, circuit breaker, cancellation과 recovery 패턴을 설계한다.
- [x] U03/U04/U05/U07 Port 실패 격리와 감사 fail-closed 패턴을 설계한다.
- [x] Alert correlation, Incident state machine, recovery evidence와 COE 패턴을 설계한다.
- [x] 월별 Failure Test와 분기별 Restore Drill Scenario를 설계한다.

### Step 3 - Performance, Scale and Persistence Patterns

- [x] Worker concurrency, shared connection budget, batch, pagination과 rate limit 패턴을 설계한다.
- [x] Deduplication, optimistic version, append-only audit와 주요 query index 패턴을 설계한다.
- [x] Retention lane, checkpoint와 legal-hold 패턴을 설계한다.
- [x] Scale Trigger 이후 Worker/Broker evolution 경계를 설계한다.

### Step 4 - Security, Observability and Logical Components

- [x] 역할·최근 인증·Idempotency·non-enumeration enforcement pattern을 설계한다.
- [x] Audit digest/key rotation, trace allowlist와 telemetry privacy pattern을 설계한다.
- [x] Health aggregation, bounded Metrics/Events, Alert Router와 Dashboard component를 설계한다.
- [x] 모든 Logical Component와 Port, 상태 소유권, Transaction 경계를 정의한다.

### Step 5 - Artifacts and Validation

- [x] `nfr-design-patterns.md`를 생성한다.
- [x] `logical-components.md`를 생성한다.
- [x] U06-NFR-001~075, ADR-U06-001~010, RESILIENCY-01~15와 P-U06-01~12 traceability를 검증한다.
- [x] Markdown 문법과 표 구조를 검증한다.
- [x] 계획·상태·감사 기록을 갱신하고 표준 NFR Design 승인 지점을 제시한다.

## NFR Design Questions

각 `[Answer]:` 뒤에 선택한 문자 하나를 입력한다. 적합한 정책이 없으면 `X`를 선택하고 원하는 내용을 함께 작성한다.

## Question 1
Notification Worker의 bulkhead와 우선순위 lane은 어떻게 구성합니까?

A) in-app, email, retention/maintenance를 별도 bounded lane으로 분리하고 인앱을 우선하되 각 lane이 다른 lane의 Slot을 고갈시키지 못하게 한다

B) 모든 Job을 하나의 FIFO lane과 공통 concurrency로 처리한다

C) 사용자별 전용 lane을 만들어 완전히 직렬 처리한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 2
PostgreSQL Outbox Job claim과 장애 복구 패턴은 무엇입니까?

A) `FOR UPDATE SKIP LOCKED` bounded claim, expiring lease, heartbeat와 attempt fencing token을 사용해 stale worker completion을 거부한다

B) 전체 Queue에 하나의 전역 Advisory Lock을 사용한다

C) 상태를 processing으로 바꾸고 lease 없이 Worker 재시작 시 운영자가 수동 복구한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 3
Email Channel circuit breaker의 초기 패턴은 무엇입니까?

A) 최근 20회 중 최소 10회 관측 후 실패율 50%에서 열고 30초 후 제한된 half-open probe를 허용하며 in-app lane에는 영향을 주지 않는다

B) 실패 1건에서 즉시 5분 동안 회로를 연다

C) 회로 차단 없이 개별 Timeout·Retry만 적용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 4
세 번의 Email Retry 지연 패턴은 무엇입니까?

A) 5초, 30초, 5분 기반 exponential schedule에 deterministic-test 가능한 bounded jitter를 더하고 30분/이벤트 만료를 절대 상한으로 둔다

B) 매 10분 고정 간격으로 세 번 재시도한다

C) Provider의 Retry-After 값만 따르고 자체 상한을 두지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 5
U06의 PostgreSQL connection budget은 어떻게 배분합니까?

A) 공유 상한 안에서 API 4, notification worker 2, maintenance 1 연결을 기본 예산으로 두고 timeout·overflow 0을 적용한다

B) 각 Process가 기본 10개와 overflow 20개를 독립적으로 사용한다

C) 단일 연결을 API와 모든 Worker가 순차 공유한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 6
초기 U06 Table의 index와 partition 패턴은 무엇입니까?

A) dedup key unique index, pending claim partial/composite index, override target/status/expiry, audit/incident time-keyset index를 사용하고 초기에는 partition하지 않는다

B) 모든 Table을 월 단위 partition하고 각 column마다 단일 index를 생성한다

C) Primary Key 외에는 index를 두지 않고 Application filtering을 사용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 7
Audit alteration detection용 digest 패턴은 무엇입니까?

A) canonical allowlisted event bytes에 versioned HMAC-SHA-256을 적용하고 Secret file key ring으로 현재·이전 key 검증과 점진적 회전을 지원한다

B) 비밀키 없는 SHA-256 hash만 저장한다

C) Database row 전체를 직렬화한 평문 checksum만 저장한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 8
고영향 운영 Command의 최근 인증과 재전송 보호 패턴은 무엇입니까?

A) U02에서 최근 15분 내 인증된 Session을 확인하고 expected version, idempotency key, Origin/CSRF 검증과 제한된 rate bucket을 함께 요구한다

B) 활성 Session이면 인증 시각과 관계없이 허용하고 idempotency key만 사용한다

C) System Administrator 역할 문자열을 Client가 보내면 추가 검증 없이 허용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 9
Health contribution 집계와 Deep Check fan-out 패턴은 무엇입니까?

A) 각 contributor를 bounded parallel timeout으로 평가하고 immutable snapshot을 만든 뒤 pure truth-table aggregator가 required/optional·freshness를 계산한다

B) Contributor를 순차 호출하고 첫 실패에서 나머지를 중단한다

C) 최근 성공 상태를 만료 없이 cache하여 의존성 호출을 생략한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 10
Alert correlation과 Incident update의 concurrency 패턴은 무엇입니까?

A) versioned correlation key unique constraint와 optimistic compare-and-set으로 하나의 open Incident를 갱신하고 중복 Alert는 occurrence로 병합한다

B) 분산 전역 Lock으로 모든 Alert 처리를 직렬화한다

C) 중복을 허용하고 이후 수동으로 Incident를 병합한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 11
운영 API rate limiting과 비용 격리 패턴은 무엇입니까?

A) actor+operation 기준 process-local fixed-window bucket을 사용하고 Admin mutation·Trace query를 별도 제한하며 확장 시 shared limiter로 교체한다

B) 공통 IP bucket 하나만 사용한다

C) 운영자 API에는 rate limit을 적용하지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 12
초기 U06 cache 패턴은 무엇입니까?

A) 권한·Preference·승인·Trace correctness cache는 사용하지 않고, immutable policy와 localization template만 version-keyed process cache로 허용한다

B) Redis를 추가해 권한, Preference, Trace와 Health를 모두 cache한다

C) 모든 조회를 10분 process cache하고 별도 invalidation은 사용하지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 13
Scale Trigger 이후 U06 확장 순서는 무엇입니까?

A) Worker process 수평 분리, lane별 concurrency 조정, PostgreSQL query/partition 검토 후에도 Queue SLO가 미달할 때 Broker Adapter를 도입한다

B) 첫 Trigger에서 U06 전체를 독립 Microservice와 Kafka Cluster로 전환한다

C) 계속 단일 Process만 수직 확장하고 구조 변경을 금지한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 14
U06 복원력 Mechanism은 어떤 방식으로 검증합니까?

A) 기존 U07 결정대로 월별 Email/U02~U05 dependency failure·stale health·alert storm test와 분기별 U06 포함 PostgreSQL restore drill을 자동 Evidence와 함께 수행한다

B) Scenario만 정의하고 실행은 Operations Phase까지 연기한다

C) 기능 Test만 수행하고 Failure Injection과 Restore Drill은 생략한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Planned Artifacts

- `aidlc-docs/construction/u06-engagement-and-operations/nfr-design/nfr-design-patterns.md`
- `aidlc-docs/construction/u06-engagement-and-operations/nfr-design/logical-components.md`

## Preliminary Extension Assessment

### Resiliency Baseline

- Question 1~4, 9~10, 13~14가 RESILIENCY-05~07, 09~10, 12~15의 구체적 Pattern과 Test Approach를 결정한다.
- RESILIENCY-08은 승인된 단일 서버 Prototype 예외이며 Question 13이 상용 확장 진입 순서를 정의한다.
- U07에서 선택한 월별 Failure Test와 분기별 Restore Drill은 Question 14에서 U06 범위로 확인한다.

### Property-Based Testing

- P-U06-01~12는 NFR Design의 codec, dedup, state machine, oracle, ordering과 privacy pattern에 연결한다.
- 실행·Shrinking·Seed·Integration 상세는 Code Generation 계획에서 PBT-02~08과 PBT-10으로 강제한다.

### Security Baseline

- 확장은 비활성화되어 N/A다. Question 7~8, 11~12는 핵심 감사 무결성, 인증, rate limit과 cache 안전 경계를 일반 NFR 설계로 확정한다.
