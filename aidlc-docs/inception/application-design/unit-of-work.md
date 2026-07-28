# Unit of Work Definitions

## Decomposition Decision

시스템을 Business Capability 중심의 7개 논리 Unit으로 분해한다. Unit은 독립 Microservice가 아니라 모듈러 Monolith와 별도 React Web·Worker Process를 단계적으로 설계하고 구현하기 위한 작업·검증 경계이다.

## Unit Summary

| Unit | Name | Primary Components | Primary Services | Primary Story Count |
|---|---|---|---|---:|
| U01 | Web Experience | C01 | 없음; Backend Service Client | 1 |
| U02 | Identity and Personalization | C03, C12 | S05, S06 | 6 |
| U03 | Catalog and Discovery | C04, C07 | S01, S02 | 6 |
| U04 | Ingestion and Metadata Governance | C05, C06 | S07 | 1 |
| U05 | Recommendation and AI Grounding | C08, C09, C10, C11 | S03, S04 | 8 |
| U06 | Engagement and Operations | C13, C14 | S08, S09, S10 | 4 |
| U07 | Platform and Delivery | C02, Cross-cutting Adapters | 공통 API·Runtime 지원 | 2 |

Primary Story 총계는 28개이다. Supporting 관계는 `unit-of-work-story-map.md`에서 별도로 관리한다.

## U01 — Web Experience

- **목표**: 한국어·영어 반응형 UI에서 피드, 검색, 추천 대화, 계정, 알림과 운영 기능을 일관되고 접근 가능하게 제공한다.
- **소유 구성요소**: C01 Web Experience
- **포함 책임**: Route와 화면 상태, 국제화, 접근성, 추천 처리 중 상태, 오류·Fallback 표시, OpenAPI Client 통합
- **제외 책임**: 추천 점수 계산, Metadata 검증, 권한 판정과 개인정보 정책의 서버 측 집행
- **입력 Contract**: U07 OpenAPI Schema와 인증 Session Contract
- **출력 Contract**: 사용자 Command, 검색·추천 Query, 동의된 행동 Event
- **데이터 소유**: 영속 Business Table 없음; 비민감 UI 상태와 Session 참조만 Client에서 관리
- **완료 경계**: 핵심 사용자 Journey가 한국어·영어와 목표 접근성 수준에서 API Contract Test를 통과한다.
- **후속 설계 깊이**: Functional Standard, NFR Comprehensive for accessibility and perceived performance

## U02 — Identity and Personalization

- **목표**: 계정, 인증, 사용자 선호, 구독 OTT, 찜·평가·시청 이력, 동의와 행동 Feature를 관리한다.
- **소유 구성요소**: C03 Identity and Access, C12 Personalization and Feedback
- **소유 서비스**: S05 AccountAndPrivacyService, S06 FeedbackService
- **포함 책임**: 이메일 인증, OAuth Adapter 경계, Role, Profile, Consent, Data Export·Deletion, 비식별 추천 Context
- **제외 책임**: 추천 최종 순위와 AI 문구 생성, 콘텐츠 Metadata 수정
- **소유 데이터**: users, credentials, oauth_links, roles, preferences, subscriptions, watch_items, ratings, watch_history, consents, behavior_events, personalization_features
- **제공 Port**: IdentityPort, ConsentPort, PersonalizationFeaturePort, FeedbackEventPort
- **완료 경계**: 동의 범위와 권한이 서버에서 집행되고 직접 식별자가 추천·AI Context로 유출되지 않는다.
- **후속 설계 깊이**: Functional and NFR Comprehensive

## U03 — Catalog and Discovery

- **목표**: 승인된 콘텐츠만 피드, 상세, Filter, 제목·인물·의미 검색에 제공한다.
- **소유 구성요소**: C04 Content Catalog, C07 Search
- **소유 서비스**: S01 FeedQueryService, S02 SearchService
- **포함 책임**: Approved Catalog 조회, Feed Projection, 지역·OTT 가용성, 다국어 제목 대체, Search Projection과 의미 검색
- **제외 책임**: Raw 수집, 승인·격리 결정, 자유 형식 AI 설명, 사용자 Profile 쓰기
- **소유 데이터**: approved_contents, content_localizations, availability, catalog_sources, feed_projections, search_projections
- **제공 Port**: ApprovedCatalogReadPort, ApprovedCatalogWritePort, SearchPort, AvailabilityPort
- **완료 경계**: 사용자 Query와 추천 후보 조회가 승인 영역 밖의 Record를 반환하지 않는다.
- **후속 설계 깊이**: Functional Comprehensive for query and availability rules; NFR Comprehensive

## U04 — Ingestion and Metadata Governance

- **목표**: 외부 Metadata를 합법적이고 재현 가능한 방식으로 수집·정규화·중복 제거·검증하여 승인 또는 격리한다.
- **소유 구성요소**: C05 Content Ingestion, C06 Metadata Validation
- **소유 서비스**: S07 ContentIngestionService
- **포함 책임**: Provider Adapter, Rate Limit, Raw 보존, Normalization, Deduplication, Validation Rule Version, Quarantine, 재처리
- **제외 책임**: 사용자 노출 Query, 추천 최종 순위, 추천 문구 Claim 검증
- **소유 데이터**: provider_records, raw_metadata, normalized_metadata, validation_runs, validation_failures, quarantine_records, ingestion_jobs
- **제공 Port**: ProviderPort, MetadataValidationPort, ValidationRuleContract, 승인 전환 시 U03의 ApprovedCatalogWritePort 호출
- **완료 경계**: 필수·출처·라이선스·최신성·지역·식별자 검증을 통과한 Record만 U03 승인 Catalog로 전달된다.
- **후속 설계 깊이**: Functional, NFR and Resiliency Comprehensive

## U05 — Recommendation and AI Grounding

- **목표**: 자연어 의도를 구조화하고 승인 후보를 하드 조건·개인화·다양성으로 순위화한 뒤 근거가 검증된 설명만 반환한다.
- **소유 구성요소**: C08 Recommendation Orchestrator, C09 AI Interaction, C10 Recommendation Engine, C11 Recommendation Output Validation
- **소유 서비스**: S03 RecommendationApplicationService, S04 RecommendationConversationService
- **포함 책임**: Intent Schema, Session 조건 변경, 후보 Filter·Score·Diversity·Final Rank, GroundedTextDraft, 노출 전 Eligibility·Claim 검증, Timeout과 규칙 기반 Fallback
- **제외 책임**: AI에 후보 적격성·최종 순위 권한 부여, 승인되지 않은 Metadata 보완 생성, 사용자 직접 식별자 전달
- **소유 데이터**: recommendation_sessions, recommendation_requests, recommendation_candidates, ranking_runs, explanation_drafts, output_validation_results, recommendation_traces
- **제공 Port**: RecommendationPort, ConversationPort, AIProviderPort, RecommendationTracePort
- **완료 경계**: 모든 노출 항목은 승인 Catalog 소속, 하드 조건 충족, 유효 Evidence Reference와 검증 통과 상태를 가진다.
- **후속 설계 깊이**: Functional, NFR, PBT and Resiliency Comprehensive

## U06 — Engagement and Operations

- **목표**: 알림, 운영자 콘텐츠 관리, 감사 추적, 상태 점검, 장애 대응과 품질 운영 화면을 제공한다.
- **소유 구성요소**: C13 Notification, C14 Admin and Operations
- **소유 서비스**: S08 NotificationService, S09 AdminContentService, S10 OperationsService
- **포함 책임**: 관심 콘텐츠 알림, Channel Adapter, 운영자 Override, 변경 감사, 추천·검증 Trace 조회, Health·Metrics·Incident Reference
- **제외 책임**: 사용자 추천 Ranking 변경, 검증 실패 콘텐츠의 승인 우회, Platform 배포·Backup 실행
- **소유 데이터**: notification_preferences, notification_jobs, notification_deliveries, admin_overrides, audit_events, incident_records
- **제공 Port**: NotificationPort, AdminAuditPort, ObservabilityPort, IncidentPort
- **완료 경계**: 운영 작업이 Role로 제한되고 모든 변경이 감사되며 알림 실패가 핵심 피드·추천 흐름과 격리된다.
- **후속 설계 깊이**: Functional Standard; NFR and Resiliency Comprehensive

## U07 — Platform and Delivery

- **목표**: 모든 Unit이 재현 가능한 Contract, Runtime, 저장소 Migration, CI/CD, 관측성·Backup·Rollback 기반 위에서 실행되게 한다.
- **소유 구성요소**: C02 REST API Boundary와 공통 PostgreSQL·OAuth·AI·Provider·Notification Adapter Bootstrap
- **포함 책임**: REST/OpenAPI Versioning, Error Envelope, Correlation ID, Configuration·Secret 주입, Database Migration, Docker, CI/CD, GHCR, Backup·Restore, Release·Rollback
- **제외 책임**: Business Rule, 콘텐츠 승인 결정, 추천 점수와 사용자 동의 결정
- **소유 데이터**: schema_migrations, outbox_jobs의 공통 Runtime Schema, 운영 Metadata; 각 Business Table의 Write 권한은 해당 Unit에 유지
- **제공 Contract**: OpenAPI, 공통 Error·Pagination Schema, Runtime Port 구현, Health Endpoint Wiring
- **완료 경계**: Local·CI 환경에서 Build와 Test가 재현되고 Versioned 배포·Backup·Restore·Rollback 절차를 실행할 수 있다.
- **후속 설계 깊이**: Functional Minimal; NFR and Infrastructure Comprehensive

## Component and Service Ownership

| Unit | Owned Components | Owned Services |
|---|---|---|
| U01 | C01 | Backend Service Client only |
| U02 | C03, C12 | S05, S06 |
| U03 | C04, C07 | S01, S02 |
| U04 | C05, C06 | S07 |
| U05 | C08, C09, C10, C11 | S03, S04 |
| U06 | C13, C14 | S08, S09, S10 |
| U07 | C02 | Shared REST and Runtime support |

모든 C01~C14와 S01~S10은 정확히 하나의 Primary Owner를 가진다.

## Data Ownership Rules

1. Unit은 자신의 소유 Table에만 직접 쓴다.
2. 다른 Unit의 데이터는 Application Service Port, 명시적 Read Model 또는 Versioned Event Contract를 사용한다.
3. U04는 검증 결과를 직접 승인 Table에 쓰지 않고 U03의 ApprovedCatalogWritePort를 호출한다.
4. U05는 U03의 승인 Read Port와 U02의 비식별 Feature Port만 사용한다.
5. U06의 운영자 Override는 U03 Service를 통해 적용하고 변경 전후 값은 U06 Audit에 기록한다.
6. PostgreSQL Transaction이 여러 Unit에 걸치면 Orchestrator가 순서를 관리하고 Outbox로 후속 작업을 연결한다.

## Greenfield Code Organization

- `frontend/src/features/`: 사용자 Capability별 React Feature
- `frontend/src/shared/`: 공통 UI, 국제화, OpenAPI Client
- `frontend/tests/`: Component, Accessibility, Contract와 사용자 흐름 Test
- `backend/app/api/`: C02 REST API Boundary
- `backend/app/modules/identity/`: C03 Identity
- `backend/app/modules/personalization/`: C12 Personalization and Feedback
- `backend/app/modules/catalog/`: C04 Content Catalog
- `backend/app/modules/search/`: C07 Search
- `backend/app/modules/ingestion/`: C05 Content Ingestion
- `backend/app/modules/metadata_validation/`: C06 Metadata Validation
- `backend/app/modules/recommendation/`: C08 Orchestrator와 C10 Engine
- `backend/app/modules/ai_interaction/`: C09 AI Interaction
- `backend/app/modules/recommendation_validation/`: C11 Output Validation
- `backend/app/modules/notification/`: C13 Notification
- `backend/app/modules/admin/` 및 `backend/app/modules/operations/`: C14 Admin and Operations
- `backend/app/shared/`: 공통 Domain Primitive와 Port 지원
- `backend/worker/`: Ingestion·Notification Worker Entry Point
- `backend/tests/`: Unit, Integration, Contract와 Property-Based Test
- `infra/`: Docker Compose, 배포, Backup·Restore와 Observability 설정
- `scripts/`: 개발·검증 Automation
- `aidlc-docs/`: AI-DLC 문서 전용

이 구조는 선택된 `frontend`, `backend`, `infra` 최상위 구성을 따르며 Application Code는 `aidlc-docs/` 밖에 둔다.

## Cross-Cutting Quality Handoff

| Concern | Owning Unit | Supporting Units | Construction Handoff |
|---|---|---|---|
| Approved Metadata closure | U03 | U04, U05 | Functional invariant and PBT |
| Grounded recommendation text | U05 | U03, U04 | Functional rule, Evidence Contract and PBT |
| Consent and de-identification | U02 | U05, U06 | Functional rule and security/privacy tests |
| External dependency fallback | U05 | U03, U04, U06, U07 | NFR timeout, retry, circuit and degradation design |
| Backup, restore and rollback | U07 | U02~U06 | Infrastructure design and recovery test |
| Accessibility and localization | U01 | U02~U06 | UI NFR and end-to-end tests |
| Audit and incident learning | U06 | U02~U05, U07 | Observability and incident workflow design |

## Extension Compliance

- **Resiliency**: Unit별 중요도, 장애 격리, Fallback, Health, Backup·Restore와 Rollback 책임을 명시했다. 단일 서버와 수평 확장 제외는 승인된 Prototype 예외를 유지한다.
- **Property-Based Testing**: U03, U04, U05와 U02의 상태·변환·불변 조건을 Functional Design에 전달한다. PBT-01의 공식 분석은 해당 후속 단계에서 수행한다.
- **Security Baseline**: Extension은 비활성화되어 건너뛴다. U02, U06, U07의 핵심 인증·권한·비밀정보·개인정보 요구는 일반 NFR로 유지한다.

Units Generation 단계에서 차단 상태인 Extension Finding은 없다.
