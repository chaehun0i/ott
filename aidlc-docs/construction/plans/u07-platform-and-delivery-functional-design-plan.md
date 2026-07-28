# U07 Platform and Delivery Functional Design Plan

## Unit Context

- **Unit**: U07 Platform and Delivery
- **Owned Component**: C02 REST API Boundary
- **Primary Stories**: US-026 Backup·Restore, US-028 Reproducible Deployment·Rollback
- **Supporting Stories**: US-007, US-014, US-018~US-020, US-023~US-025, US-027
- **Design Depth**: Minimal Functional Design; Comprehensive NFR and Infrastructure Design follow later
- **Scope Boundary**: REST Contract, 공통 오류·Pagination, 멱등성, Migration·Outbox 상태와 Release·Recovery 검증 상태
- **Excluded Here**: Cloud·Container Product 선택, Timeout 수치, Backup Command, CI/CD 구현과 상세 배포 Topology

## Applicability Assessment

Functional Design을 실행한다. U07은 Business Ranking이나 Catalog Rule을 소유하지 않지만 모든 Unit이 공유하는 API Schema와 상태 전이를 정의하므로 Functional Contract 설계가 필요하다.

| Functional Design Category | Applicability | Treatment |
|---|---|---|
| Business Logic Modeling | Applicable | API Command, Idempotency, Release와 Recovery 상태 흐름 |
| Domain Model | Applicable | ContractVersion, IdempotencyRecord, OutboxJob, ReleaseArtifact, DeploymentRecord, BackupRecord |
| Business Rules | Applicable | 호환성, 중복 Command, Error 노출, Rollback Gate |
| Data Flow | Applicable | HTTP Request·Response, Outbox, Migration, Backup Verification |
| Integration Points | Applicable | 모든 Unit API, PostgreSQL, CI/CD, Adapter Bootstrap |
| Error Handling | Applicable | Validation, Conflict, Authorization, Dependency, Correlation |
| Business Scenarios | Applicable | 중복 요청, 부분 실패, 비호환 Migration, Restore 검증 실패 |
| Frontend Components | N/A | U07은 UI를 소유하지 않으며 U01이 OpenAPI Client를 소비한다. |

## Functional Design Questions

### Question 1 — API Versioning

REST API의 초기 Versioning 정책을 무엇으로 확정합니까?

A) Major Version을 URL Prefix인 `/api/v1`에 포함하고, 호환 변경은 같은 Version에서 확장한다.

B) Version을 Request Header로 전달하고 URL은 Version 없이 유지한다.

C) Prototype 동안 Version을 노출하지 않고 첫 Breaking Change 때 도입한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 2 — Success and Error Shape

공통 HTTP 응답 형태는 무엇으로 확정합니까?

A) 성공 응답은 Domain Schema를 직접 반환하고, 오류만 `code`, `message`, `details`, `correlationId`의 표준 구조를 사용한다.

B) 성공과 오류 모두 `data`, `error`, `meta`를 가진 공통 Envelope로 감싼다.

C) Endpoint마다 독립 응답을 정의하고 HTTP Status만 공통화한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 3 — Mutation Idempotency

중복 요청 방지를 위한 멱등성 Contract는 어디까지 적용합니까?

A) 재시도될 수 있는 생성·작업 시작 POST에 `Idempotency-Key`를 요구하고 동일 Key와 동일 Payload는 기존 결과를 반환한다.

B) 모든 POST·PUT·DELETE 요청에 `Idempotency-Key`를 요구한다.

C) API 멱등성 Key는 사용하지 않고 각 Domain Unit의 중복 방지 규칙에 맡긴다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 4 — Pagination Contract

Feed, Search, Admin 목록의 공통 Pagination은 무엇으로 확정합니까?

A) 불투명 Cursor와 `items`, `nextCursor`, `hasMore`를 사용한다.

B) Page Number와 Page Size, Total Count를 사용한다.

C) Feed·Search는 Cursor, Admin 목록은 Page Number를 사용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: C

### Question 5 — Outbox Job Lifecycle

Worker가 사용하는 공통 Job 상태 모델은 무엇으로 확정합니까?

A) `pending`, `processing`, `retry_wait`, `succeeded`, `dead_letter`, `cancelled` 상태와 명시적 재처리 Command를 사용한다.

B) `queued`, `running`, `done`, `failed`의 최소 상태만 사용하고 실패는 운영자가 직접 다시 생성한다.

C) 공통 상태 모델을 두지 않고 Ingestion과 Notification이 각자 정의한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 6 — Migration and Rollback Compatibility

Database 변경과 Application Rollback의 기능 규칙은 무엇으로 확정합니까?

A) Expand-and-contract를 기본으로 하며 이전 Application Version과 호환되지 않는 제거 변경은 별도 Release에서 수행한다.

B) 모든 Migration에 자동 Down Migration을 요구하고 Rollback 때 즉시 실행한다.

C) Prototype에서는 호환성을 보장하지 않고 실패 시 Backup Restore로만 복귀한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 7 — Restore Verification Decision

Backup Restore를 성공으로 판정하는 기능 절차는 무엇으로 확정합니까?

A) Restore 완료 후 무결성 검사와 핵심 사용자 흐름 Smoke Test가 모두 통과해야 `verified`로 전환한다.

B) Database가 기동되고 Row Count 검사만 통과하면 성공으로 판정한다.

C) Restore Command 종료 Code가 성공이면 별도 검증 없이 완료 처리한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Planning Checklist

- [x] U07 정의, Story Map, Component Method와 Dependency를 읽는다.
- [x] Functional Design 적용 필요성을 평가하고 Minimal 깊이로 확정한다.
- [x] 8개 질문 범주의 적용 여부를 모두 기록한다.
- [x] 적용 가능한 7개 결정 질문을 `[Answer]:` 형식으로 작성한다.
- [x] 모든 답변의 완전성과 선택지 유효성을 검사한다.
- [x] 답변의 모호성, 충돌과 결합 선택을 분석한다.
- [x] 필요한 Follow-up Question을 추가하고 해소한다. 추가 질문 불필요.
- [x] 승인된 답변에 따라 Functional Design 산출물을 생성한다.
- [x] `business-logic-model.md`를 생성하고 상태 흐름을 정의한다.
- [x] `business-rules.md`를 생성하고 Contract·멱등성·호환성 규칙을 정의한다.
- [x] `domain-entities.md`를 생성하고 Entity·Value Object·관계를 정의한다.
- [x] U07에 Frontend Component가 없음을 N/A로 검증한다.
- [x] PBT-01에 따라 모든 U07 Component의 Testable Properties를 식별한다.
- [x] 산출물의 Markdown과 복잡 콘텐츠를 검증한다.
- [x] Functional Design 완료 승인 요청을 기록한다.

## Planned PBT-01 Analysis

| Candidate | Property Category | Intended Assertion |
|---|---|---|
| OpenAPI DTO serialization | Round-trip | 유효 DTO의 Serialize·Deserialize가 의미상 동일하다. |
| Error mapping | Invariant | 내부 민감정보가 어떤 Error 입력에서도 외부 Payload에 나타나지 않는다. |
| Idempotency handling | Idempotence | 동일 Key와 동일 Payload의 반복 실행은 동일한 관찰 결과를 만든다. |
| Cursor handling | Round-trip and Invariant | 유효 Cursor Decode·Encode가 위치 의미를 보존한다. |
| Outbox lifecycle | Stateful | 임의 Command Sequence에서도 허용되지 않은 상태 전이가 없다. |
| Migration compatibility | Model-based | 호환 Release Sequence가 정의된 Compatibility Model을 위반하지 않는다. |
| Restore verification | Invariant | 무결성 또는 Smoke Test 실패 상태는 `verified`가 될 수 없다. |

공식 Property 목록과 N/A 근거는 답변 확정 후 생성되는 Functional Design에 기록한다.

## Extension Compliance at Planning

- **PBT-01**: 적용 대상과 후보 Property Category를 모든 U07 기능 Component에 대해 계획했다. 생성 산출물에서 공식 확정하기 전까지 진행 중이며 차단 Finding은 없다.
- **Resiliency**: US-026과 US-028의 Recovery·Rollback 결정이 질문 6~7과 산출물 계획에 포함되었다.
- **Security Baseline**: 비활성화로 건너뛴다. Error 비밀정보 비노출과 Secret 주입은 일반 NFR로 유지한다.
