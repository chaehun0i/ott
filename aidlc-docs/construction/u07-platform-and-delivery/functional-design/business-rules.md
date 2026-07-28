# U07 Business Rules

## API Contract Rules

- **BR-U07-001**: 모든 Public REST Endpoint는 `/api/v1` 아래에 있어야 한다.
- **BR-U07-002**: 같은 Major Version에서는 기존 Required Input 추가, Field 삭제와 의미 변경을 허용하지 않는다.
- **BR-U07-003**: 성공 응답은 Endpoint Domain Schema를 직접 반환하며 공통 성공 Envelope로 감싸지 않는다.
- **BR-U07-004**: 모든 오류 응답은 `code`, `message`, `details`, `correlationId`를 제공한다.
- **BR-U07-005**: 오류 `details`는 허용 목록 기반이며 Stack Trace, Secret, 내부 주소, 원본 Provider Payload와 모델 내부 추론을 포함할 수 없다.
- **BR-U07-006**: Client가 유효한 Correlation ID를 보내면 유지하고, 없거나 유효하지 않으면 Server가 새 값을 생성한다.

## Idempotency Rules

- **BR-U07-007**: 중복 Side Effect 위험이 있는 생성·작업 시작 POST는 `Idempotency-Key`를 필수로 선언한다.
- **BR-U07-008**: Idempotency Identity는 Actor 또는 Client, API Major Version, Method, Route Template과 Key를 포함한다.
- **BR-U07-009**: 동일 Identity와 동일 Canonical Payload의 완료 요청은 저장된 결과를 반환하고 Domain Command를 다시 실행하지 않는다.
- **BR-U07-010**: 동일 Identity에 다른 Payload가 오면 `idempotency_payload_conflict`로 거부한다.
- **BR-U07-011**: 처리 중인 동일 요청은 새 실행을 시작하지 않고 `idempotency_in_progress`를 반환한다.
- **BR-U07-012**: Idempotency Record 보존 만료는 NFR 정책을 따르며 만료 전 결과의 의미를 변경하지 않는다.

## Pagination Rules

- **BR-U07-013**: Feed와 Search는 불투명 Cursor Pagination을 사용한다.
- **BR-U07-014**: Cursor는 정렬 위치, Tie-breaker, Filter Fingerprint와 Contract Version을 보존해야 한다.
- **BR-U07-015**: 현재 Query와 Fingerprint가 다른 Cursor는 거부한다.
- **BR-U07-016**: Admin 목록은 1 기반 Page Number Pagination과 Total Metadata를 사용한다.
- **BR-U07-017**: 어떤 Pagination 응답도 요청 또는 정책 Page Size보다 많은 Item을 반환할 수 없다.

## Outbox Rules

- **BR-U07-018**: Outbox Job 상태는 `pending`, `processing`, `retry_wait`, `succeeded`, `dead_letter`, `cancelled`로 제한한다.
- **BR-U07-019**: Job Claim은 원자적이어야 하며 유효 Lease를 가진 Worker 하나만 `processing`으로 전환할 수 있다.
- **BR-U07-020**: Retry 가능한 실패는 원인 Code, Attempt와 다음 시도 시각을 기록한 뒤 `retry_wait`로 전환한다.
- **BR-U07-021**: 재시도 불가 또는 한도 도달 실패는 `dead_letter`로 전환한다.
- **BR-U07-022**: `dead_letter` 재처리는 권한 있는 명시적 Command, 사유와 새 Attempt Chain을 요구한다.
- **BR-U07-023**: `succeeded`와 `cancelled` 상태는 변경할 수 없다.
- **BR-U07-024**: 알림·수집 Job 실패는 동기 사용자 요청 Transaction을 Rollback시키지 않는다.

## Release and Migration Rules

- **BR-U07-025**: ReleaseArtifact는 Git Commit, Release Tag, Image Digest와 Contract Version을 추적해야 한다.
- **BR-U07-026**: Database 변경은 Expand-and-contract 순서를 기본으로 한다.
- **BR-U07-027**: Expand 단계는 현재 및 이전 Application Version이 모두 사용할 수 있어야 한다.
- **BR-U07-028**: 기존 Schema 제거와 비호환 변경은 Consumer 전환과 Backfill 검증 이후 별도 Contract Release에서 수행한다.
- **BR-U07-029**: Compatibility Gate를 통과하지 못한 Release는 Deployable로 전환할 수 없다.
- **BR-U07-030**: Application Rollback은 이전 불변 Image와 설정으로 수행하며 자동 Down Migration을 기본 경로로 사용하지 않는다.
- **BR-U07-031**: 이전 Application과 호환되지 않는 Database 상태에서는 Rollback을 시작하지 않고 승인된 복구 절차로 전환한다.

## Backup and Restore Rules

- **BR-U07-032**: 성공 Backup은 암호화된 Artifact, Manifest, 생성 시각과 보존 만료 정보를 가져야 한다.
- **BR-U07-033**: Backup 실행 또는 Artifact 검증 실패는 `failed`로 기록하고 운영 알림 입력을 생성한다.
- **BR-U07-034**: Restore는 원본 Backup과 격리된 Attempt Record를 가져야 한다.
- **BR-U07-035**: Restore는 Database Load 후 Manifest·Schema·Data Integrity 검사를 통과해야 Smoke Test로 진행할 수 있다.
- **BR-U07-036**: 필수 Smoke Test가 모두 통과해야 Restore Attempt를 `verified`로 전환한다.
- **BR-U07-037**: Integrity 또는 Smoke Test 하나라도 실패하면 `verified`를 허용하지 않는다.
- **BR-U07-038**: 실패 Restore Record는 수정하지 않고 새 Attempt가 이전 Attempt를 참조한다.

## Validation and Error Scenarios

| Scenario | Required Result | Rule References |
|---|---|---|
| 지원하지 않는 API Major Version | Version Error 반환 | BR-U07-001~002 |
| 동일 Idempotency Key와 다른 Payload | Conflict, 실행 없음 | BR-U07-008~010 |
| 이미 처리 중인 중복 요청 | In-progress Conflict | BR-U07-011 |
| 다른 Filter의 Cursor 재사용 | Invalid Cursor | BR-U07-014~015 |
| Worker Lease 경쟁 | 하나의 Claim만 성공 | BR-U07-019 |
| Retry 한도 도달 | Dead letter와 원인 보존 | BR-U07-020~022 |
| 비호환 Migration Release | Deployable 전환 차단 | BR-U07-026~031 |
| Restore Integrity 실패 | Failed, Smoke Test 진입 금지 | BR-U07-035~037 |
| Restore Smoke Test 실패 | Failed, Verified 금지 | BR-U07-036~037 |

## PBT Rule Linkage

| Business Rules | Property Category | Required Test |
|---|---|---|
| BR-U07-004~005 | Invariant | Error Payload 비밀정보 비노출 |
| BR-U07-007~012 | Idempotence and Stateful | 동일 Command 반복의 관찰 상태 동일성 |
| BR-U07-013~017 | Round-trip and Invariant | Cursor 왕복과 Page 범위 |
| BR-U07-018~024 | Stateful | Outbox Model과 임의 Command Sequence 비교 |
| BR-U07-025~031 | Oracle | Release Compatibility Reference Model 비교 |
| BR-U07-032~038 | Stateful and Invariant | Restore 상태 전이와 Verified Guard |

## Extension Compliance

- **PBT-01**: 모든 상태·변환 규칙을 Property Category와 연결했다. 식별 가능한 Property가 없는 Correlation ID 생성은 별도 근거와 예제·통계 Test 방식으로 기록했다.
- **Resiliency**: Release 호환성, Rollback, Backup 실패, Restore Gate와 불변 이력을 기능 규칙으로 정의했다.
- **Security Baseline**: 비활성화로 N/A. 오류 정보 최소화와 권한 있는 재처리는 일반 보안 요구로 유지한다.

차단 상태인 Functional Design Finding은 없다.
