# U07 Domain Entities

## Modeling Principles

- U07 Entity는 Business 콘텐츠나 사용자 Profile을 소유하지 않는다.
- 식별자는 불투명 값이며 외부 Contract에서 내부 Database Key 의미를 노출하지 않는다.
- 시간, Version, Hash와 상태 값은 명시적 Value Object로 모델링한다.
- 상태 변경은 Entity Method를 통해서만 수행하고 감사 가능한 Domain Event를 생성한다.

## Aggregate Summary

| Aggregate | Root | Child or Value Objects | Primary Responsibility |
|---|---|---|---|
| API Contract | ApiContractVersion | EndpointContract, SchemaFingerprint | Major Version 호환성 |
| Idempotency | IdempotencyRecord | IdempotencyScope, PayloadHash, ResponseSnapshot | 중복 Side Effect 방지 |
| Outbox | OutboxJob | JobAttempt, Lease, FailureCode | 비동기 작업 상태 |
| Release | ReleaseArtifact | ImageDigest, GitRevision, CompatibilityDecision | 재현 가능한 배포 입력 |
| Deployment | DeploymentRecord | DeploymentTarget, DeploymentEvent | 배포·Rollback 이력 |
| Recovery | BackupRecord | BackupManifest, RetentionWindow | Backup Artifact 추적 |
| Recovery Verification | RestoreAttempt | IntegrityResult, SmokeTestResult | Restore 성공 판정 |

## ApiContractVersion

### Fields

| Field | Type | Constraint |
|---|---|---|
| major | PositiveInteger | URL Prefix와 일치 |
| schemaFingerprint | SchemaFingerprint | Canonical Schema Hash |
| publishedAt | Instant | 미래 시각 불가 |
| status | draft, active, deprecated, retired | 허용 전이만 사용 |

### Relationships

- 하나의 ApiContractVersion은 여러 EndpointContract를 포함한다.
- ReleaseArtifact는 정확히 하나의 활성 ApiContractVersion을 참조한다.

## IdempotencyRecord

### Fields

| Field | Type | Constraint |
|---|---|---|
| scope | IdempotencyScope | Actor·Client, Version, Method, Route, Key 포함 |
| payloadHash | PayloadHash | Canonical Payload에서 계산 |
| state | processing, completed, failed_retryable | 허용 값만 사용 |
| responseSnapshot | Optional ResponseSnapshot | completed일 때 필수 |
| operationReference | Optional OpaqueId | 생성된 Resource 또는 Job 참조 |
| createdAt, expiresAt | Instant | expiresAt은 createdAt 이후 |

### Invariants

- 같은 IdempotencyScope는 동시에 하나의 활성 Record만 가진다.
- completed 상태는 ResponseSnapshot을 가져야 한다.
- PayloadHash가 다른 요청은 기존 Record를 변경할 수 없다.

## Pagination Value Objects

### CursorToken

- **Fields**: contractVersion, sortPosition, tieBreakerId, filterFingerprint
- **Invariant**: Decode된 모든 Field가 현재 Endpoint Contract와 Query Context에 맞아야 한다.
- **Exposure**: 불투명하게 Encode하며 Client가 내부 Field를 조립하지 않는다.

### CursorPage

- **Fields**: items, nextCursor, hasMore
- **Invariant**: hasMore가 false이면 nextCursor가 없어야 한다.

### NumberedPage

- **Fields**: items, page, pageSize, totalItems, totalPages
- **Invariant**: page는 1 이상이고 모든 Count는 0 이상이며 items 수는 pageSize 이하이다.

## OutboxJob

### Fields

| Field | Type | Constraint |
|---|---|---|
| jobId | OpaqueId | 불변 |
| jobType | JobType | 등록된 Handler와 연결 |
| payload | VersionedPayload | Schema Version 필수 |
| state | JobState | pending, processing, retry_wait, succeeded, dead_letter, cancelled 중 하나 |
| attemptCount | NonNegativeInteger | Attempt 추가 시에만 증가 |
| nextAttemptAt | Optional Instant | retry_wait일 때 필수 |
| activeLease | Optional Lease | processing일 때 필수 |
| failureCode | Optional FailureCode | 실패 상태에서 필수 |
| parentJobId | Optional OpaqueId | 재처리 계보 |

### State Commands

- claim, complete, deferRetry, markDeadLetter, cancel, manualRequeue

### Invariants

- succeeded와 cancelled는 Terminal State다.
- processing은 만료되지 않은 Lease 하나를 가진다.
- retry_wait는 다음 시도 시각을 가진다.
- manualRequeue는 기존 이력을 수정하지 않고 새 Attempt Chain을 만든다.

## ReleaseArtifact

### Fields

| Field | Type | Constraint |
|---|---|---|
| releaseId | OpaqueId | 불변 |
| gitRevision | GitRevision | Commit과 연결 |
| releaseTag | ReleaseTag | Version 정책 준수 |
| imageDigest | ImageDigest | 변경 불가 Digest |
| apiContractVersion | ApiContractVersionRef | 활성 또는 승인 예정 Version |
| migrationSet | MigrationSetRef | 순서가 고정된 Migration 집합 |
| compatibility | CompatibilityDecision | 근거와 검사 결과 포함 |
| state | built, tested, published, deployable, blocked | Gate에 의한 전이 |

### Invariants

- deployable 상태는 Test와 Compatibility Gate를 모두 통과해야 한다.
- 동일 ReleaseArtifact의 ImageDigest는 변경할 수 없다.

## DeploymentRecord

### Fields

- deploymentId, releaseId, targetId, previousReleaseId
- action: deploy 또는 rollback
- state: requested, applying, verifying, succeeded, failed
- initiatedBy, startedAt, completedAt, failureCode

### Invariants

- Rollback은 previousReleaseId와 호환성 판정을 요구한다.
- succeeded는 Verification Result를 가져야 한다.
- 변경 이력은 Append-only다.

## BackupRecord

### Fields

- backupId, state, artifactReference, manifest, encryptionKeyReference
- startedAt, completedAt, retentionExpiresAt, failureCode

### Invariants

- succeeded Backup은 Artifact Reference와 검증된 Manifest를 가진다.
- Secret이나 실제 암호화 Key Material은 Entity에 저장하지 않고 Reference만 보관한다.
- retentionExpiresAt은 completedAt 이후이다.

## RestoreAttempt

### Fields

- restoreAttemptId, backupId, previousAttemptId
- state: requested, restoring, integrity_check, smoke_test, verified, failed
- integrityResult, smokeTestResult, startedAt, completedAt, failureCode

### Invariants

- integrity_check를 통과하기 전 smoke_test로 전환할 수 없다.
- verified는 IntegrityResult와 모든 필수 SmokeTestResult의 성공을 요구한다.
- failed Record는 수정하지 않으며 재시도는 새 RestoreAttempt다.

## Relationships

| Source | Relationship | Target |
|---|---|---|
| ApiContractVersion | referenced by | ReleaseArtifact |
| ReleaseArtifact | deployed through | DeploymentRecord |
| ReleaseArtifact | declares | MigrationSetRef |
| BackupRecord | verified through | RestoreAttempt |
| OutboxJob | may trigger | Backup, notification or ingestion operation |
| IdempotencyRecord | may reference | OutboxJob or Domain Resource |

## Domain Events

| Event | Emitted When | Required Fields |
|---|---|---|
| ApiRequestCompleted | API 결과가 확정됨 | correlationId, route, category, duration reference |
| IdempotentResultReplayed | 완료 결과가 재사용됨 | scope fingerprint, operation reference |
| OutboxJobDeadLettered | Job이 terminal failure에 도달 | jobId, jobType, attemptCount, failureCode |
| ReleaseBlocked | Compatibility Gate 실패 | releaseId, decision codes |
| DeploymentRolledBack | 이전 Release로 복귀 | deploymentId, fromRelease, toRelease |
| BackupFailed | Backup 생성·검증 실패 | backupId, failureCode |
| RestoreVerified | 이중 검증 완료 | restoreAttemptId, backupId, verification summary |
| RestoreFailed | Restore 또는 검증 실패 | restoreAttemptId, phase, failureCode |

Event에는 Secret, 직접 식별자, Provider Raw Payload와 모델 내부 추론을 포함하지 않는다.

## PBT Coverage by Entity

| Entity or Value Object | PBT Category | Required Property |
|---|---|---|
| ApiContract DTO | Round-trip | Schema-valid value serialization identity |
| IdempotencyRecord | Idempotence, Stateful | 반복 Command의 Side Effect 단일성 |
| CursorToken | Round-trip | Encode·Decode 의미 보존 |
| CursorPage, NumberedPage | Invariant | Cursor·Count·Size 제약 |
| OutboxJob | Stateful, Model-based | 모든 상태 전이가 Reference Model과 일치 |
| ReleaseArtifact | Oracle | Compatibility Gate와 Reference Decision 일치 |
| DeploymentRecord | Stateful | 검증 없는 성공과 비호환 Rollback 금지 |
| BackupRecord | Invariant | 성공 Artifact·Manifest와 Key 비노출 |
| RestoreAttempt | Stateful, Invariant | 검증 순서와 Verified Guard |

PBT-01 요구에 따라 식별 가능한 모든 Property를 기록했다. 구체 Generator, Shrinking, Seed와 Framework는 NFR Requirements 및 Code Generation에서 확정한다.

## Frontend Entity Assessment

N/A. U07에는 Frontend State Entity가 없다.
