# Unit of Work Story Map

## Mapping Rules

- 각 Story는 정확히 하나의 Primary Unit에 할당한다.
- Supporting Unit은 UI, Contract, 데이터 또는 운영 지원 책임만 가지며 Story의 최종 인수 책임을 중복 소유하지 않는다.
- Story의 기존 Requirements·Data Requirements·Acceptance Criteria Traceability는 `stories.md`를 기준으로 유지한다.

## Story Mapping

| Story | Title | Primary Unit | Supporting Units | Primary Acceptance Boundary |
|---|---|---|---|---|
| US-001 | 최신 콘텐츠 통합 피드 탐색 | U03 | U01, U07 | 승인 Catalog 기반 통합 Feed Query |
| US-002 | 피드 필터링과 작품 상세 확인 | U03 | U01 | Filter·Detail Data 정확성 |
| US-003 | 데이터 최신성과 상태 확인 | U03 | U01, U04 | Last Updated와 상태 표시 Data 제공 |
| US-004 | 제목·인물 및 필터 검색 | U03 | U01 | 구조 검색 결과 정확성 |
| US-005 | 한국어 자연어·의미 검색 | U03 | U01, U05 | 한국어 의미 Query와 결과 |
| US-006 | 영어 자연어·의미 검색 | U03 | U01, U05 | 영어 의미 Query와 결과 |
| US-007 | 다국어·접근 가능한 공통 UI | U01 | U07 | 한국어·영어와 접근성 UI |
| US-008 | 한국어 상황 기반 추천 요청 | U05 | U01, U02, U03 | 한국어 Intent와 검증 추천 |
| US-009 | 영어 상황 기반 추천 요청 | U05 | U01, U02, U03 | 영어 Intent와 검증 추천 |
| US-010 | 하드 조건을 지키는 개인화 순위 | U05 | U02, U03, U04 | Filter 우선 Ranking과 다양성 |
| US-011 | 메타데이터 근거 기반 추천 이유와 요약 | U05 | U03, U04 | Evidence 연결과 Claim 검증 |
| US-012 | 대화형 추천 조정과 초기화 | U05 | U01, U02 | Session 조건 전이 |
| US-013 | 모호하거나 충돌하는 추천 조건 조정 | U05 | U01 | 충돌 설명과 사용자 조정 |
| US-014 | 이메일·소셜 로그인과 계정 접근 | U02 | U01, U07 | 인증·Session·OAuth Contract |
| US-015 | 선호 장르와 구독 OTT 설정 | U02 | U01 | Profile Preference 관리 |
| US-016 | 찜·평가·시청 이력 관리 | U02 | U01, U03 | 회원 Library 상태 관리 |
| US-017 | 행동 피드백 기반 추천 피드 개선 | U02 | U01, U03, U05 | 동의 Event와 Feature 갱신 |
| US-018 | 개인화 데이터 동의·조회·내보내기·삭제 | U02 | U01, U07 | Consent와 Data Rights 수행 |
| US-019 | 관심 콘텐츠 알림 관리 | U06 | U01, U02, U03, U07 | Preference 기반 알림 전달 |
| US-020 | 메타데이터 수집·정규화·검증·격리 | U04 | U03, U06, U07 | 상태 Pipeline과 Quarantine |
| US-021 | 작품 정보와 노출 상태 운영 | U06 | U01, U03, U04 | 권한 기반 Override와 Audit |
| US-022 | 추천 결과 Metadata 검증과 안전한 대체 | U05 | U03, U04, U06 | Fail-closed Validation과 Fallback |
| US-023 | 추천 결정과 검증 추적 | U06 | U02, U05, U07 | 비식별 Trace 조회와 감사 |
| US-024 | 외부 서비스 장애 시 저하 운용 | U05 | U03, U04, U06, U07 | Timeout·Fallback 결과 제공 |
| US-025 | 상태 점검·관측·장애 대응 | U06 | U07 | Health·Metrics·Alert·Incident 흐름 |
| US-026 | 백업·복원과 복구 검증 | U07 | U06 | RTO·RPO 내 Restore 검증 |
| US-027 | 안전한 계정·개인정보·접근성 운영 | U02 | U01, U06, U07 | 권한·Privacy·접근성 통합 기준 |
| US-028 | 재현 가능한 배포와 버전 롤백 | U07 | U06 | CI/CD와 Version Rollback |

## Primary Story Totals

| Unit | Primary Stories | Count |
|---|---|---:|
| U01 | US-007 | 1 |
| U02 | US-014, US-015, US-016, US-017, US-018, US-027 | 6 |
| U03 | US-001, US-002, US-003, US-004, US-005, US-006 | 6 |
| U04 | US-020 | 1 |
| U05 | US-008, US-009, US-010, US-011, US-012, US-013, US-022, US-024 | 8 |
| U06 | US-019, US-021, US-023, US-025 | 4 |
| U07 | US-026, US-028 | 2 |
| **Total** | **US-001~US-028** | **28** |

## Requirements and Quality Handoff by Unit

| Unit | Main Functional Scope | Data and NFR Focus | Mandatory Quality Gates |
|---|---|---|---|
| U01 | Feed·Search·Recommendation·Account UI, FR-033~035 presentation | Localization, accessibility, perceived performance | Accessibility, Contract and end-to-end Gate |
| U02 | FR-011~012, FR-022~027 | DR-007~008, privacy, auth, consent | Privacy and authorization Gate |
| U03 | FR-001~008, FR-013, FR-033~034 | DR-003~004, DR-006, DR-009~012 | Approved Metadata closure Gate |
| U04 | FR-006, FR-030~032 support, FR-039~041 rule source | DR-001~006, DR-009~011 | Data provenance, quarantine and resiliency Gate |
| U05 | FR-009~022, FR-036~042 | DR-008, DR-012~014, AI quality and latency | Recommendation, Grounding and PBT Gate |
| U06 | FR-028~032, FR-042 operations | Audit, observability, notification isolation | Operations and incident Gate |
| U07 | Cross-cutting API and runtime, deployment support | Security NFR, backup, restore, CI/CD, portability | Build, recovery and rollback Gate |

US-023은 기존 Traceability에 따라 DR-008을 포함하며, U06이 비식별 Trace의 인수 책임을 가지고 U02와 U05가 직접 식별자 제거 및 추천 Trace Contract를 지원한다.

## Mapping Validation

- Expected Story IDs: US-001~US-028
- Primary Mapping Rows: 28
- Unique Primary Story IDs: 28
- Missing Story IDs: 0
- Duplicate Primary Assignments: 0
- Unassigned Stories: 0
- Persona/Story Mapping 변경: 없음
- Requirements Traceability 변경: 없음; 기존 Story Trace를 Unit에 전달

## Construction Handoff

각 Unit의 Functional Design은 Primary Story의 Acceptance Criteria와 Supporting Contract를 함께 읽어야 한다. U03, U04, U05는 승인 Metadata·격리·Grounding 불변 조건을, U02는 Consent와 상태 전이를, U07은 Serialization·Migration·복구 속성을 PBT 후보로 분석한다.

## Extension Compliance

- **Resiliency**: US-024~US-026과 US-028의 Primary Owner와 모든 Supporting Owner가 명시되어 장애 저하·관측·복구·Rollback 요구가 누락되지 않았다.
- **Property-Based Testing**: PBT-01은 다음 Functional Design 단계에서 Unit별로 적용한다. 현재 Story Map은 속성 후보와 책임 Unit을 명시하므로 Compliant이다. PBT-02~PBT-10은 현재 단계 N/A이다.
- **Security Baseline**: 비활성화로 N/A. US-014, US-018, US-023, US-027의 핵심 보안·개인정보 요구는 U02·U06·U07에 유지된다.

현재 Story Mapping에서 차단 상태인 Extension Finding은 없다.
