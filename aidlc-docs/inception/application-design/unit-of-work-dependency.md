# Unit of Work Dependencies

## Dependency Convention

행 Unit이 열 Unit을 필요로 하면 `Required`로 표시한다. 모든 의존은 Versioned Contract, Service Port 또는 Read Model을 통하며 다른 Unit 소유 Table에 직접 쓰지 않는다.

## Dependency Matrix

| Consumer | U01 | U02 | U03 | U04 | U05 | U06 | U07 |
|---|---|---|---|---|---|---|---|
| U01 Web Experience | — | Required | Required | — | Required | Required | Required |
| U02 Identity and Personalization | — | — | — | — | — | — | Required |
| U03 Catalog and Discovery | — | — | — | — | — | — | Required |
| U04 Ingestion and Metadata Governance | — | — | Required | — | — | — | Required |
| U05 Recommendation and AI Grounding | — | Required | Required | Required | — | — | Required |
| U06 Engagement and Operations | — | Required | Required | — | Required | — | Required |
| U07 Platform and Delivery | — | — | — | — | — | — | — |

## Directed Dependency List

| Consumer | Provider | Contract | Reason |
|---|---|---|---|
| U01 | U02 | Identity, Profile, Consent API | 계정과 개인화 UI |
| U01 | U03 | Feed, Detail, Search API | 콘텐츠 탐색 UI |
| U01 | U05 | Recommendation and Conversation API | 자연어·대화형 추천 UI |
| U01 | U06 | Notification and Admin API | 알림 설정과 운영 UI |
| U01 | U07 | OpenAPI Client, Error and Session Contract | 모든 HTTP 통합 |
| U02 | U07 | Auth Runtime, Database and OAuth Adapter | 계정 실행 기반 |
| U03 | U07 | Database, Search Extension and API Boundary | Catalog 조회 기반 |
| U04 | U03 | ApprovedCatalogWritePort | 검증 통과 Metadata 승인 전환 |
| U04 | U07 | Worker Runtime, Provider Adapter and Job Store | 수집 작업 실행 |
| U05 | U02 | PersonalizationFeaturePort and ConsentPort | 비식별 개인화 Context |
| U05 | U03 | ApprovedCatalogReadPort and AvailabilityPort | 승인 후보와 하드 조건 검증 |
| U05 | U04 | Versioned ValidationRuleContract | 수집·추천 검증 규칙 정합성 |
| U05 | U07 | AI Adapter, Database, Timeout and API Runtime | 동기 추천 실행 기반 |
| U06 | U02 | IdentityRolePort and NotificationPreferencePort | 운영 권한과 알림 동의 |
| U06 | U03 | Catalog Administration Port | 운영자 수정과 알림 콘텐츠 |
| U06 | U05 | RecommendationTracePort | 추천·검증 추적 조회 |
| U06 | U07 | Notification Adapter and Observability Runtime | 비동기 전달과 운영 기반 |

## Topological Construction Sequence

| Wave | Units | Entry Condition | Parallelism |
|---|---|---|---|
| 1 | U07 Platform and Delivery foundation | 없음 | OpenAPI·Runtime Skeleton부터 시작 |
| 2 | U02 Identity and Personalization, U03 Catalog and Discovery | U07 공통 Contract 준비 | 두 Unit 병렬 가능 |
| 3 | U04 Ingestion and Metadata Governance | U03 ApprovedCatalogWritePort 준비 | U01 UI Shell과 병렬 가능 |
| 4 | U05 Recommendation and AI Grounding | U02 Feature Port, U03 Approved Catalog, U04 Validation Contract 준비 | 내부 C08~C11은 Contract-first 병렬 설계 가능 |
| 5 | U06 Engagement and Operations | U02 Role, U03 Catalog Admin, U05 Trace Port 준비 | 알림과 운영 화면 Backend는 부분 병렬 가능 |
| 6 | U01 Web Experience full integration | U02, U03, U05, U06 API 준비 | Wave 1부터 UI Shell·Mock Client 선행 가능 |
| 7 | U07 Delivery completion | 모든 Unit Build·Test 결과 준비 | CI/CD, Backup·Restore, Rollback 통합 검증 |

U07은 하나의 Unit이지만 Foundation Slice와 Delivery Completion Slice로 나누어 실행한다. 이는 순환 의존이 아니라 같은 Unit의 단계적 완료 조건이다.

## Acyclicity Proof

의존 Level을 다음과 같이 부여한다.

| Level | Units |
|---:|---|
| 0 | U07 |
| 1 | U02, U03 |
| 2 | U04 |
| 3 | U05 |
| 4 | U06 |
| 5 | U01 |

모든 Directed Dependency는 더 높은 Level의 Consumer에서 더 낮은 Level의 Provider로 향한다. 따라서 Unit Graph에는 Cycle이 없다.

## Failure Isolation and Fallback Handoff

| Failure | Primary Owner | Isolation Boundary | Required Fallback |
|---|---|---|---|
| AI Provider timeout | U05 | AIProviderPort | 승인 Metadata 기반 규칙 추천과 Template 설명 |
| Content Provider failure | U04 | ProviderPort and Job | 제한된 Retry, 격리, 마지막 정상 Catalog 유지 |
| Metadata validation failure | U04 | Quarantine | 승인 Catalog 전환 차단 |
| Recommendation output validation failure | U05 | Output Validation | 실패 항목 제거 또는 전체 규칙 기반 대체 |
| Notification channel failure | U06 | Delivery Job | 핵심 기능과 격리, Backoff 재시도 |
| PostgreSQL outage | U07 | Readiness and Write Guard | 요청 실패 표준화, 복구 절차 개시 |
| Deployment regression | U07 | Versioned Image and Migration Gate | 이전 호환 Version Rollback |

## Contract Change Rules

1. U07 OpenAPI와 공통 Schema 변경은 Consumer Contract Test를 먼저 갱신한다.
2. U04 ValidationRuleContract 변경은 U03 승인 전환과 U05 Output Validation 회귀 Test를 통과해야 한다.
3. U02 PersonalizationFeaturePort는 직접 식별자를 포함할 수 없다.
4. U03 ApprovedCatalog Contract는 승인 상태, Metadata Version, 출처와 지역·OTT 가용성을 보존한다.
5. Breaking Change는 Versioned Contract와 Migration 순서를 제공하고 U07 Rollback 호환성을 확인한다.

## Dependency Validation Result

- Unit 수: 7
- Directed Dependency 수: 17
- Cycle: 0
- Root Provider: U07
- Terminal Consumer: U01
- 다른 Unit Table에 대한 직접 Write Dependency: 0
- C06과 C11 사이의 규칙 복제: 0; Versioned Contract 공유

## Extension Compliance

- **Resiliency**: 외부·데이터·배포 장애의 격리 Owner와 Fallback을 Unit Dependency에 연결했다.
- **Property-Based Testing**: Contract Serialization 왕복, 승인 Catalog 폐쇄성, Validation Rule 일관성과 상태 전이는 후속 Functional Design·Code Generation 대상으로 전달한다.
- **Security Baseline**: 비활성화로 N/A. 다만 인증, Role과 비식별 Contract는 일반 요구사항에 따라 유지한다.

현재 Dependency 설계에서 차단 상태인 Extension Finding은 없다.
