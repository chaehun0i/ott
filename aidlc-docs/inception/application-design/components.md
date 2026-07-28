# Application Components

## Architecture Style

- Python backend는 하나의 배포 단위 안에서 Domain Module을 분리한 모듈형 Monolith로 구성한다.
- React 정적 Web과 Python API는 별도 Container로 배포한다.
- 수집과 알림은 같은 Codebase의 별도 Worker Entry Point로 실행한다.
- PostgreSQL이 관계형 데이터, JSON Metadata, 전문 검색과 Vector 확장의 기준 저장소이다.
- 외부 콘텐츠·OAuth·AI 공급자는 Port와 Adapter 뒤에 둔다.

## Component Summary

| ID | Component | Purpose | Deployment |
|---|---|---|---|
| C01 | Web Experience | 반응형·다국어 사용자 및 운영자 UI | Web Container |
| C02 | REST API Boundary | OpenAPI 기반 인증·검증·응답 경계 | API Container |
| C03 | Identity and Access | 이메일 인증, Session, Role, OAuth 연결 | API Module |
| C04 | Content Catalog | 승인 콘텐츠와 피드·상세 조회 | API Module |
| C05 | Content Ingestion | 외부 Metadata 수집·정규화 작업 | Worker Module |
| C06 | Metadata Validation | 승인·격리와 검증 결과 관리 | Shared Domain Module |
| C07 | Search | 제목·인물·Filter·의미 검색 | API Module |
| C08 | Recommendation Orchestrator | 동기 추천 Pipeline 조정과 Fallback | API Module |
| C09 | AI Interaction | 자연어 의도 및 근거 기반 문구 생성 | API Module plus Adapter |
| C10 | Recommendation Engine | 후보 필터, 점수, 개인화, 다양성, 최종 순위 | Domain Module |
| C11 | Recommendation Output Validation | 노출 전 적격성·Grounding 검증 | Domain Module |
| C12 | Personalization and Feedback | 선호·행동·동의·Feature 관리 | API Module |
| C13 | Notification | 검증된 공개 이벤트의 알림 생성 | Worker Module |
| C14 | Admin and Operations | 콘텐츠 수정, 추적, 상태, 장애 대응 | API Module |

## Component Definitions

### C01 Web Experience

- **Responsibilities**: 피드·검색·추천 대화·계정·개인정보·운영 UI, 한국어·영어, 접근성, API 상태 표시
- **Must Not**: 하드 조건 판정, 추천 순위 계산, Metadata 승인
- **Provides**: Browser UI
- **Requires**: C02 REST/OpenAPI Contract
- **State**: Browser Session과 비민감 UI 상태
- **Traceability**: FR-001~FR-035, US-001~US-019, US-027

### C02 REST API Boundary

- **Responsibilities**: Request Schema, 인증 Context, 권한 확인, Correlation ID, HTTP Error Contract
- **Must Not**: Domain Rule 또는 AI Prompt를 직접 구현
- **Provides**: Feed, Search, Recommendation, Account, Admin REST API
- **Requires**: C03, C04, C07, C08, C12, C14
- **State**: 없음
- **Traceability**: AC-001~AC-010, FR-042

### C03 Identity and Access

- **Responsibilities**: 이메일 자격 증명, Session·Token Lifecycle, 회원·운영자 Role, OAuth Adapter 조정
- **Must Not**: 개인화 Ranking 또는 콘텐츠 권한 밖의 데이터 처리
- **Provides**: IdentityPort, AuthorizationPort, OAuthPort
- **Requires**: CredentialRepository, SessionRepository, OAuthProviderAdapter
- **State**: 사용자 Identity, Credential, Session, Role
- **Traceability**: FR-023, NFR 7.3, US-014, US-027

### C04 Content Catalog

- **Responsibilities**: 승인 콘텐츠의 기준 저장·조회, 피드·상세 Projection, 출처·갱신 시각·가용성 제공
- **Must Not**: 원본 수집, 격리 판정, AI 문구 생성
- **Provides**: ApprovedCatalogPort, FeedQueryPort, ContentLookupPort
- **Requires**: CatalogRepository
- **State**: Approved Content, Provider Availability, Provenance, Projection
- **Traceability**: FR-001~FR-006, DR-003~DR-006, US-001~US-003

### C05 Content Ingestion

- **Responsibilities**: 공급자 Adapter 호출, Raw 보존, 정규화, 중복 후보 생성, C06 검증 요청
- **Must Not**: 검증 실패 데이터를 승인하거나 사용자 조회에 직접 게시
- **Provides**: IngestionJobPort
- **Requires**: ProviderAdapter, C06, JobRepository
- **State**: Job, Cursor, Attempt, Raw Record
- **Traceability**: DR-001~DR-005, US-020

### C06 Metadata Validation

- **Responsibilities**: Schema·출처·라이선스·최신성·식별자·지역·OTT 검증, 승인·격리 상태 전이, 실패 Code
- **Must Not**: 누락 데이터를 생성하거나 추천 순위를 변경
- **Provides**: MetadataValidationPort, QuarantinePort
- **Requires**: ValidationRuleRepository, C04 승인 저장 Port
- **State**: Normalized Record, Validation Result, Quarantine, Rule Version
- **Traceability**: FR-039~FR-041, DR-009~DR-012, AC-014, US-020

### C07 Search

- **Responsibilities**: 승인 콘텐츠의 제목·인물·Filter·전문·Vector 검색, 언어별 Query 정규화
- **Must Not**: 격리 콘텐츠 색인 또는 추천 Ranking 대체
- **Provides**: SearchPort
- **Requires**: C04, PostgreSQL Search·Vector Adapter
- **State**: Search Projection과 Embedding Reference
- **Traceability**: FR-007~FR-009, FR-033~FR-035, US-004~US-007

### C08 Recommendation Orchestrator

- **Responsibilities**: C09 의도 해석, C10 Ranking, C09 설명 생성, C11 최종 검증의 순서·Timeout·Fallback·응답 조립
- **Must Not**: 자체 점수 계산, 하드 조건 우회, 근거 없는 문구 승인
- **Provides**: RecommendationApplicationPort, ConversationPort
- **Requires**: C09, C10, C11, C12, C14 TracePort
- **State**: Recommendation Session과 Request Trace
- **Traceability**: FR-018~FR-022, FR-036~FR-042, US-008~US-013, US-022~US-024

### C09 AI Interaction

- **Responsibilities**: 한국어·영어 입력을 RecommendationIntent로 변환, 승인 Metadata에서 요약·이유 초안 생성
- **Must Not**: 후보 적격성, 최종 순위, 승인 상태, 콘텐츠 사실을 결정
- **Provides**: IntentInterpreterPort, ExplanationGeneratorPort
- **Requires**: Provider-neutral AIProviderPort의 초기 단일 Adapter
- **State**: Prompt·Schema Version과 비식별 Request Metadata
- **Traceability**: FR-008~FR-010, FR-014~FR-016, FR-036, FR-038, DR-008, DR-013

### C10 Recommendation Engine

- **Responsibilities**: 승인 후보 조회, 하드 Filter, Feature Scoring, 개인화, 다양성, 최종 순위와 규칙 기반 Fallback
- **Must Not**: 자연어 자유 해석 또는 줄거리·추천 이유 생성
- **Provides**: RecommendationRankingPort
- **Requires**: C04, C12
- **State**: Policy Version, Feature Definition, Scoring Configuration
- **Traceability**: FR-011~FR-013, FR-017, FR-037, AC-011~AC-012, US-010

### C11 Recommendation Output Validation

- **Responsibilities**: 승인 Catalog 소속, 지역·OTT·시간 조건, Claim Grounding, Rule Version 검증과 Fail-closed 결과
- **Must Not**: 실패 문구를 보완 생성하거나 Ranking을 임의 변경
- **Provides**: RecommendationValidationPort
- **Requires**: C04, C06 Rule Definition
- **State**: Validation Trace와 Failure Code
- **Traceability**: FR-039~FR-042, DR-014, AC-011~AC-014, US-011, US-022, US-023

### C12 Personalization and Feedback

- **Responsibilities**: 선호·구독 OTT·찜·평가·이력·동의, 행동 Event 정규화, Ranking Feature 제공, 데이터 권리 처리
- **Must Not**: 동의 없는 결합 또는 직접 식별자의 AI 전달
- **Provides**: ProfilePort, FeedbackPort, FeaturePort, DataRightsPort
- **Requires**: ProfileRepository, EventRepository, ConsentPolicy
- **State**: Profile, Consent, Interaction, Derived Feature
- **Traceability**: FR-012, FR-022, FR-024~FR-027, DR-007~DR-008, US-015~US-018

### C13 Notification

- **Responsibilities**: 검증된 공개 Event와 회원 설정을 사용한 알림 Job 처리
- **Must Not**: 격리·오래된 Metadata에서 알림 생성
- **Provides**: NotificationJobPort
- **Requires**: C04, C12, ChannelAdapter
- **State**: Subscription, Delivery Job, Delivery Result
- **Traceability**: FR-028~FR-029, US-019

### C14 Admin and Operations

- **Responsibilities**: 운영자 수정·노출 제어, 감사·추천 Trace 조회, Health·Metrics·Alert 연결, 복구·배포 상태 표면화
- **Must Not**: 권한 없는 사용자 데이터 조회 또는 검증 우회
- **Provides**: AdminContentPort, TraceQueryPort, HealthPort
- **Requires**: C03, C04, C06, C11, ObservabilityPort
- **State**: Override, Audit Record, Incident Reference
- **Traceability**: FR-030~FR-032, FR-042, US-021, US-023, US-025~US-028

## Cross-Cutting Ports and Adapters

- PostgreSQL Repository Adapters
- External Metadata Provider Adapters
- OAuth Provider Adapters
- AI Provider Adapter
- Notification Channel Adapters
- Clock, ID, Transaction, Scheduler, Job Queue, Observability and Secret Ports
- Prototype Job Queue는 PostgreSQL-backed Job·Outbox로 시작하며 Broker Adapter로 교체 가능하다.
