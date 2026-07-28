# U07 Business Logic Model

## Scope

U07은 Business Domain의 추천·Catalog 규칙을 소유하지 않는다. 모든 Unit이 동일하게 사용하는 REST Contract, 멱등성, Pagination, Outbox Job, Release Compatibility와 Restore Verification의 기능 상태를 소유한다.

## 1. REST Request Processing

### Input

- `/api/v1` 아래의 Versioned Endpoint
- HTTP Method, Route, Header, Query와 Body
- 선택적 인증 Context
- Client가 제공하거나 Server가 생성한 Correlation ID
- Endpoint가 멱등성을 요구할 때 `Idempotency-Key`

### Processing Sequence

1. 요청의 API Major Version과 Media Type을 검사한다.
2. Correlation ID를 정규화하거나 새로 생성한다.
3. 인증·권한이 필요한 Endpoint는 U02가 제공하는 Port를 호출한다.
4. Path, Query, Header와 Body를 Endpoint Schema로 검증한다.
5. 멱등 대상 POST이면 Idempotency Workflow를 실행한다.
6. C02가 해당 Application Service에 Typed Command 또는 Query를 전달한다.
7. 성공 결과는 Domain Response Schema로 직접 직렬화한다.
8. 실패 결과는 표준 ApiError로 매핑하고 내부 Payload·Stack·Secret을 제거한다.
9. Correlation ID와 결과 Category를 구조화된 운영 Event로 남긴다.

### Output

- 성공: Endpoint별 Domain Schema와 적절한 HTTP Status
- 실패: `code`, `message`, `details`, `correlationId`를 가진 ApiError
- 목록: Endpoint Category에 따른 CursorPage 또는 NumberedPage

## 2. API Version Compatibility

| Change | Same `/api/v1` Allowed | Rule |
|---|---|---|
| Optional Response Field 추가 | Yes | Consumer가 알 수 없는 Field를 무시할 수 있어야 한다. |
| Optional Request Field 추가 | Yes | Default 의미를 문서화한다. |
| Enum Value 추가 | Conditional | Unknown Value 처리 Contract가 선행되어야 한다. |
| Required Field 추가 | No | 새 Major Version 또는 명시적 Migration이 필요하다. |
| Field 삭제·의미 변경 | No | 새 Major Version이 필요하다. |
| Error Code 추가 | Yes | 공통 Category와 Retry 가능 여부를 문서화한다. |

Breaking Change는 `/api/v2` 같은 새 Major Prefix에서 병행 제공하고 U01 Client 전환 완료 후 이전 Version 종료를 계획한다.

## 3. Error Mapping

| Internal Category | External Category | Default HTTP Class | Details Policy |
|---|---|---|---|
| ValidationError | validation_error | Client error | 허용된 Field와 Rule Code만 포함 |
| AuthorizationError unauthenticated | unauthenticated | Authentication error | 인증 실패 원인의 민감한 세부정보 제외 |
| AuthorizationError forbidden | forbidden | Authorization error | 필요한 Permission 자체를 과도하게 노출하지 않음 |
| NotFoundError | not_found | Client error | 승인되지 않은 Resource 존재 여부를 누설하지 않음 |
| ConflictError | conflict | Client error | Version 또는 Idempotency 충돌 Code 포함 |
| DependencyError | dependency_unavailable | Server error | Provider Payload·Credential·내부 주소 제외 |
| UnexpectedError | internal_error | Server error | Correlation ID 외 내부 세부정보 제외 |

HTTP Status의 구체 값과 Retry Header 정책은 OpenAPI 및 NFR Design에서 확정하되 Category 의미는 본 설계를 따른다.

## 4. Idempotency Workflow

### Scope

재시도로 중복 Side Effect가 발생할 수 있는 생성·작업 시작 POST만 `Idempotency-Key`를 필수로 선언한다. Read Query와 Domain 자체가 자연 멱등인 수정·삭제 Command에는 일괄 강제하지 않는다.

### Identity

Idempotency Scope는 `actor-or-client`, API Major Version, HTTP Method, Route Template과 Key의 조합이다. Payload는 Canonical Form의 Hash로 비교한다.

### Decision Table

| Existing Record | Payload Hash | Decision |
|---|---|---|
| 없음 | Any | `processing` Record 생성 후 Domain Command 실행 |
| processing | Same | `idempotency_in_progress` 충돌 반환 |
| completed | Same | 저장된 Status와 Response를 그대로 재생 |
| failed_retryable | Same | 정책이 허용하면 동일 Operation을 재시도 |
| Any | Different | `idempotency_payload_conflict` 반환 |

보존 기간, 대기 시간과 Retry 횟수는 NFR Requirements에서 수치화한다.

## 5. Pagination Workflow

### Feed and Search

- CursorPage는 `items`, `nextCursor`, `hasMore`를 반환한다.
- Cursor는 정렬 Key, Tie-breaker ID, Filter Fingerprint와 Contract Version을 포함하는 불투명 값이다.
- 다른 Filter·Sort Context에서 Cursor를 재사용하면 `invalid_cursor`로 거부한다.
- 마지막 Page는 `nextCursor`가 없고 `hasMore`가 false이다.

### Admin Lists

- NumberedPage는 `items`, `page`, `pageSize`, `totalItems`, `totalPages`를 반환한다.
- Page는 1부터 시작하며 범위를 벗어난 Page는 빈 `items`와 유효한 Metadata를 반환한다.
- Page Size 허용 범위는 OpenAPI Constraint로 정의하며 구체 상한은 NFR Requirements에서 확정한다.

## 6. Outbox Job State Model

| Current State | Command or Result | Next State | Guard |
|---|---|---|---|
| pending | claim | processing | Lease를 원자적으로 획득 |
| processing | complete | succeeded | 결과 참조 저장 |
| processing | retryable failure | retry_wait | 다음 시도 시각과 원인 Code 저장 |
| processing | terminal failure | dead_letter | 재시도 불가 또는 한도 도달 |
| retry_wait | retry due | pending | 다음 시도 시각 도달 |
| pending | cancel | cancelled | 아직 Claim되지 않음 |
| retry_wait | cancel | cancelled | 재시도 전 취소 가능 |
| dead_letter | manual requeue | pending | 권한, 사유와 새 Attempt Chain 기록 |

`succeeded`와 `cancelled`는 Terminal State다. `dead_letter`는 운영자 재처리만 허용하며 원래 실패 이력을 지우지 않는다.

## 7. Release and Migration Compatibility

1. ReleaseArtifact는 Git Commit, Release Tag, 불변 Image Digest와 OpenAPI Major Version을 연결한다.
2. Database 변경은 Expand Release에서 새 구조를 추가하고 구·신 Application이 함께 동작하게 한다.
3. Application 전환과 Data Backfill이 검증될 때까지 기존 구조를 유지한다.
4. 비호환 제거는 별도 Contract Release에서만 수행한다.
5. Application Rollback은 이전 Image와 Deployment Configuration을 사용하고, Database는 호환 상태를 유지하므로 자동 Down Migration을 기본으로 실행하지 않는다.
6. Compatibility Gate 실패 시 Release는 Deployable 상태가 될 수 없다.

## 8. Backup and Restore Verification

### Backup State

| Current | Event | Next |
|---|---|---|
| requested | execution starts | running |
| running | encrypted artifact and manifest complete | succeeded |
| running | execution or verification error | failed |

### Restore State

| Current | Event | Next |
|---|---|---|
| requested | restore starts | restoring |
| restoring | database load complete | integrity_check |
| integrity_check | manifest, schema and integrity pass | smoke_test |
| integrity_check | any check fails | failed |
| smoke_test | all required user flows pass | verified |
| smoke_test | any required flow fails | failed |

`verified`는 무결성 검사와 핵심 사용자 흐름 Smoke Test가 모두 성공한 경우에만 도달한다. 실패한 Restore Attempt는 수정할 수 없으며 새 Attempt가 이전 Attempt를 참조한다.

## 9. Testable Properties — PBT-01

| Functional Component | Category | Property | Disposition |
|---|---|---|---|
| C02 DTO Codec | Round-trip | 모든 유효 DTO는 Serialize 후 Deserialize할 때 의미상 동일하다. | PBT required |
| C02 Error Mapper | Invariant | 어떤 내부 Error 입력에서도 Secret, Stack, Provider Payload가 외부 Error에 나타나지 않는다. | PBT required |
| Idempotency Registry | Idempotence | 같은 Scope·Key·Payload의 완료 요청 반복은 동일 Status와 Response를 반환하고 Side Effect를 추가하지 않는다. | PBT required |
| Cursor Codec | Round-trip | 유효 Cursor의 Encode·Decode가 위치, Filter Fingerprint와 Version을 보존한다. | PBT required |
| Cursor Validator | Invariant | Filter Fingerprint가 다른 Cursor는 항상 거부된다. | PBT required |
| Numbered Pagination | Invariant | Page Metadata는 음수가 아니며 `items` 수가 Page Size를 초과하지 않는다. | PBT required |
| Outbox Job | Stateful | 생성된 Command Sequence에서 허용 Transition만 발생하고 Terminal State는 임의로 벗어나지 않는다. | Stateful PBT required |
| Migration Compatibility Gate | Oracle | Release Sequence 판정이 단순 Compatibility Reference Model과 일치한다. | Model-based PBT required |
| Restore Verification | Invariant | Integrity 또는 Smoke Test가 실패하면 상태는 절대 `verified`가 아니다. | PBT required |
| Correlation ID 생성 | No PBT property identified | 고유성은 확률·운영 특성이며 고정 예제와 통계적 충돌 검사로 다룬다. | Example/NFR test |

이 Property들은 Code Generation Plan에 필수 Test 항목으로 전달한다. PBT는 US-026과 US-028의 명시적 예제 기반 Test를 대체하지 않는다.

## Traceability

| Design Area | Stories and Requirements |
|---|---|
| Restore state and verification | US-026, RESILIENCY-02, RESILIENCY-11~13 |
| Release and rollback compatibility | US-028, RESILIENCY-03~04 |
| Error and Correlation Contract | US-025, NFR 7.7 |
| Idempotency and Outbox | US-019~US-020, US-024 |
| Privacy-safe Error output | US-023, US-027, DR-008 |

## Frontend Components

N/A. U07은 Frontend Component를 소유하지 않는다. U01은 본 Unit의 OpenAPI와 Error·Pagination Contract를 소비한다.
