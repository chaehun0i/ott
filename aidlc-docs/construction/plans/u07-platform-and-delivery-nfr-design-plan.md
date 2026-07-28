# U07 Platform and Delivery NFR Design Plan

## Design Inputs

- U07-NFR-001~047
- API Boundary p95 Overhead 100ms
- Prototype Availability 99.0%, RTO 4시간, RPO 24시간
- 단일 API Process·단일 Worker와 PostgreSQL-backed Outbox
- FastAPI, Pydantic, SQLAlchemy, Alembic, psycopg, pytest, Hypothesis
- Reverse Proxy TLS, 외부 Secret 주입, Docker, GitHub Actions, GHCR
- 구조화 JSON Log, 중앙 Log, Metric, Health와 Trace Context
- 직접 배포, Version-pinned Rollback, Expand-and-contract Migration

## Mandatory Category Assessment

| NFR Design Category | Applicability | Open Design Decisions |
|---|---|---|
| Resilience Patterns | Applicable | Timeout, Retry, Circuit, Bulkhead와 DR Test 방식 |
| Scalability Patterns | Applicable | Trigger 이후 Stateless API·Worker 확장 구조 |
| Performance Patterns | Applicable | ASGI Execution, Pool, Compression과 Resource Bound |
| Security Patterns | Applicable | Rate Limit, Trust Boundary와 Secret 접근 |
| Logical Components | Applicable | Telemetry Pipeline, Health Aggregator, Recovery·Release Coordinator |

## NFR Design Questions

### Question 1 — External Timeout Profiles

외부 Dependency별 초기 Timeout Profile을 무엇으로 확정합니까?

A) 동기 AI는 전체 추천 10초 Budget 안에서 최대 8초, 일반 외부 HTTP는 연결 3초·응답 10초, Database Online Query는 Statement 3초를 기본으로 하고 Batch·Migration은 별도 Profile을 사용한다.

B) 모든 HTTP와 Database 호출에 공통 10초 Timeout을 사용한다.

C) Library 기본 Timeout을 사용하고 느린 호출만 개별 조정한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 2 — Retry, Circuit and Bulkhead

외부 장애 격리 Pattern을 무엇으로 확정합니까?

A) Idempotent·명시적 Retry-safe 호출만 최대 2회 지수 Backoff와 Jitter로 재시도하고, Dependency별 Circuit Breaker와 별도 Connection·Concurrency Limit을 둔다. 동기 AI는 10초 Budget을 넘는 재시도를 금지한다.

B) 모든 실패 호출을 최대 3회 재시도하고 Circuit Breaker는 사용하지 않는다.

C) API는 재시도하지 않고 Worker Job만 재시도한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 3 — Scale-out Evolution Pattern

확장 Trigger 도달 후 적용할 목표 Pattern은 무엇입니까?

A) API를 Stateless Replica로 확장하고 Worker를 Job Type별 Replica로 분리하며 PostgreSQL Connection Budget과 Outbox Claim을 중앙 조정한다.

B) 단일 Process의 Thread·Worker 수만 늘리고 여러 Host 확장은 고려하지 않는다.

C) 각 Business Unit을 즉시 독립 Microservice로 분리한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 4 — Performance Execution Pattern

FastAPI Runtime의 처리 Pattern을 무엇으로 확정합니까?

A) I/O 중심 Endpoint는 Async Boundary와 제한된 Connection Pool을 사용하고 CPU·장기 작업은 동기 요청에서 분리해 Worker Job으로 처리한다. Reverse Proxy에서 정적·대형 응답 Compression을 담당한다.

B) 모든 Endpoint와 작업을 동기 방식으로 처리한다.

C) 모든 요청을 먼저 Queue에 넣고 비동기 Polling으로 처리한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 5 — Rate Limiting and Trust Boundary

API 남용과 Resource 고갈 방지 Pattern은 무엇으로 확정합니까?

A) Reverse Proxy에서 IP 기반 기본 제한을 적용하고 Application에서 인증 Identity·Endpoint Cost 기반 제한을 추가한다. 관리자·인증·AI 추천 Endpoint는 별도 Bucket을 사용한다.

B) Reverse Proxy의 전역 IP 제한만 사용한다.

C) Prototype에서는 Rate Limit을 적용하지 않는다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 6 — Observability Logical Topology

단일 서버 Prototype의 관측성 논리 구성을 무엇으로 확정합니까?

A) Application JSON Log를 중앙 Log Collector로 수집하고 Prometheus-compatible Metric Endpoint와 Dashboard·Alert Engine을 사용한다. OpenTelemetry Trace Context는 전파하되 Trace Backend는 선택 사항으로 둔다.

B) Container 표준 출력 Log와 수동 Health 확인만 사용한다.

C) Log·Metric·Trace 전용 Backend를 모두 초기부터 필수 운영한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 7 — Health and Synthetic Monitoring

Health·외부 사용자 관점 점검을 어떻게 구성합니까?

A) Liveness와 Readiness를 분리하고 Deep Health는 운영자 전용으로 보호한다. 외부 Synthetic Check는 공개 Feed와 규칙 기반 Recommendation Fallback을 주기적으로 검사한다.

B) 하나의 `/health` Endpoint에서 모든 Dependency를 검사한다.

C) Process Liveness만 제공하고 Synthetic Check는 생략한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 8 — Resiliency Testing Approach

Failover, Backup·Restore와 장애 저하 Mechanism을 어떤 방식으로 검증합니까?

A) 기존 DR Test·Game Day·Chaos Engineering 절차를 사용한다. 선택 시 `[Answer]:` 뒤에 절차 Reference를 함께 적는다.

B) 기존 절차가 없으므로 월별 경량 Dependency Failure Test와 분기별 Backup Restore Drill을 포함한 계획을 제안한다.

C) Test Scenario만 지금 정의하고 실행은 Operations Phase로 연기한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: B

### Question 9 — Vulnerability Exception Policy

CI 취약점 Gate에서 즉시 수정할 수 없는 Finding은 어떻게 관리합니까?

A) Severity 기반 Gate를 적용하고 예외는 위험 근거, Owner, 보완 통제와 최대 30일 만료를 가진 Versioned Record로만 허용한다.

B) 모든 Finding은 Severity와 무관하게 Build를 차단한다.

C) 취약점 검사는 Report만 생성하고 Build를 차단하지 않는다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Execution Checklist

- [x] U07 NFR Requirements와 Tech Stack Decisions를 분석한다.
- [x] Resilience, Scalability, Performance, Security와 Logical Components 범주를 모두 평가한다.
- [x] 이전 사용자 결정과 미확정 Pattern을 분리한다.
- [x] RESILIENCY-14의 필수 사용자 결정 질문을 포함한다.
- [x] 9개 Context-specific Question을 작성한다.
- [x] 모든 답변의 완전성과 선택지 유효성을 검사한다.
- [x] 모호성, 결합 선택, 충돌과 NFR 위반을 분석한다.
- [x] 필요한 Follow-up Question을 추가하고 해소한다. 추가 질문 불필요.
- [x] `nfr-design-patterns.md`를 생성한다.
- [x] `logical-components.md`를 생성한다.
- [x] U07-NFR-001~047이 Design Pattern 또는 후속 Infrastructure Decision에 연결되는지 검증한다.
- [x] RESILIENCY-01~15의 적용·N/A·후속 상태를 검증한다.
- [x] PBT-01과 PBT-09 Handoff가 보존되는지 검증한다.
- [x] Markdown과 복잡 콘텐츠를 검증한다.
- [x] NFR Design 완료 승인 요청을 기록한다.

## Planned Pattern Coverage

- Timeout Budget and Deadline Propagation
- Retry with Exponential Backoff and Jitter
- Circuit Breaker and Bulkhead
- Graceful Degradation
- Stateless API and Worker Scale-out
- Bounded Pool and Async I/O
- Rate Limiting and Trust Boundary
- Health, Telemetry and Synthetic Monitoring
- Backup·Restore Verification and Version-pinned Rollback
- Vulnerability Gate and Time-bound Exception

## Planned Logical Components

- API Edge and Request Context
- Idempotency Store
- Dependency Policy Registry
- Connection and Concurrency Bulkheads
- PostgreSQL Outbox Job Store
- Health Aggregator
- Telemetry SDK, Log Collector, Metrics Store, Dashboard and Alert Router
- Release Compatibility Gate and Deployment Coordinator
- Backup Scheduler and Restore Verifier
- CI Quality and Vulnerability Gate

## Extension Compliance at Planning

- **RESILIENCY-14**: 필수 시험 방식 선택을 Question 8에 포함했으며 답변 전 상태는 진행 중이다.
- **RESILIENCY-01~13, 15**: 기존 결정과 NFR을 Pattern·Component 산출물로 연결할 계획이다.
- **PBT-01, PBT-09**: 식별 Property와 Hypothesis 선택을 유지하고 후속 Code Generation으로 전달한다.
- **Security Baseline**: 비활성화로 N/A. Rate Limit, Secret, TLS와 취약점 Gate는 일반 요구로 설계한다.
