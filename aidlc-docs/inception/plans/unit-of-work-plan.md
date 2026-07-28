# Unit of Work Generation Plan

## Purpose

OTT 통합 피드 및 AI 추천 서비스를 구현 가능한 Unit of Work로 분해한다. 각 Unit은 사용자 Story, Application Component, 데이터 책임과 검증 가능한 완료 경계를 함께 소유한다.

현재 설계는 Python 모듈러 Monolith API, 별도 React Web Container, 별도 Worker Process와 PostgreSQL 중심 저장소를 사용한다. 따라서 Unit은 Microservice 경계가 아니라 개발·설계·검증 순서를 관리하는 논리적 작업 단위이다.

## Context Reviewed

- [x] Requirements 42개, Data Requirements 14개, Acceptance Criteria 14개 검토
- [x] User Stories US-001~US-028과 Persona Mapping 검토
- [x] Application Components C01~C14와 Service S01~S10 검토
- [x] Component Dependency와 Recommendation·Ingestion Data Flow 검토
- [x] Workflow Planning의 Quality Gate와 Construction 단계 계획 검토
- [x] 활성화된 Resiliency Baseline과 Property-Based Testing 적용 시점 검토
- [x] Security Baseline 비활성화 상태 확인; 핵심 보안·개인정보 요구는 일반 요구사항으로 유지

## Decomposition Principles

- 사용자에게 전달되는 Business Capability를 중심으로 Story를 묶는다.
- AI Interaction, Recommendation Engine, Metadata Validation의 책임을 Unit 경계에서도 보존한다.
- 모든 Story는 정확히 하나의 Primary Unit에 할당하고, 필요한 경우 Supporting Unit을 별도 표시한다.
- Unit 간 의존은 방향을 명시하고 순환 의존을 허용하지 않는다.
- 공용 Contract는 Domain Port와 Versioned Schema로 표현한다.
- 단일 PostgreSQL을 사용하더라도 각 Unit의 소유 Table과 Write 책임을 명시한다.
- 복원력, 관측성, 개인정보, 접근성과 PBT 요구를 각 Unit의 후속 설계 입력으로 전달한다.

## Candidate Units

| Candidate | Capability | Primary Components | Likely Stories |
|---|---|---|---|
| U01 | Web Experience | C01, C02 Boundary | US-001~US-009, US-012~US-019, US-027 |
| U02 | Identity and Personalization | C03, C12 | US-014~US-018, US-027 |
| U03 | Catalog and Discovery | C04, C07 | US-001~US-006, US-020~US-021 |
| U04 | Ingestion and Metadata Governance | C05, C06 | US-003, US-020~US-022 |
| U05 | Recommendation and AI Grounding | C08~C11 | US-008~US-013, US-017, US-022~US-024 |
| U06 | Engagement and Operations | C13, C14 | US-019, US-021, US-023~US-028 |
| U07 | Platform and Delivery | Cross-cutting Ports and Adapters | US-024~US-028 |

이 표는 질문 답변을 돕기 위한 후보이며 승인 전 확정된 Unit Mapping이 아니다.

## Decomposition Questions

### Question 1 — Story Grouping

Unit을 어떤 기준으로 묶는 것이 가장 적합합니까?

A) 위 후보처럼 Business Capability별 7개 Unit으로 분해한다. 구현과 검증 순서가 명확해지는 권장안이다.

B) Web, Backend, Worker, Platform의 실행 Process별 4개 Unit으로 분해한다.

C) 모듈러 Monolith 전체를 하나의 Unit으로 두고 내부 Module만 구분한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 2 — Web Unit Boundary

별도 React Web Container를 Construction 과정에서 어떻게 다루어야 합니까?

A) Web Experience를 독립 Unit으로 두고 OpenAPI Contract 이후 병렬 구현 가능하게 한다.

B) 각 Business Capability Unit에 해당 UI Story를 함께 넣어 Vertical Slice로 구현한다.

C) Backend Unit을 모두 완료한 뒤 마지막 통합 UI Unit으로 구현한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:  A

### Question 3 — Metadata Validation Boundary

수집 Metadata 검증(C06)과 추천 결과 검증(C11)을 Unit 관점에서 어떻게 배치해야 합니까?

A) 서로 다른 Unit에 두되 승인 Catalog와 Validation Rule Contract를 공유한다. 책임 차이를 가장 명확히 유지하는 권장안이다.

B) 하나의 Metadata Governance Unit으로 묶어 모든 검증 규칙을 공동 소유한다.

C) Recommendation Unit이 C11을 소유하고 C06 규칙을 복제해 독립적으로 운영한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 4 — Dependencies and Shared Data

단일 PostgreSQL 환경에서 Unit 간 데이터 접근 원칙은 무엇으로 확정합니까?

A) 각 Unit이 소유 Table에만 쓰고, 다른 Unit은 Service Port 또는 Read Model을 통해 접근한다.

B) 모든 Backend Unit이 공용 Repository와 Table에 직접 접근한다.

C) 초기에는 직접 접근을 허용하되 상용화 전에 소유권 경계를 도입한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 5 — Team Alignment

Unit의 초기 소유와 협업 모델은 무엇입니까?

A) 1인 개발을 전제로 순차 소유하되, 향후 팀 분리를 위해 Unit별 책임과 Contract를 문서화한다.

B) Frontend, Backend, Data and AI, Platform의 4개 역할별 소유를 전제로 한다.

C) Business Capability별 독립 Team 소유를 전제로 한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 6 — Greenfield Code Organization

여러 논리 Unit을 수용할 Workspace Root의 코드 구조는 무엇으로 확정합니까?

A) Monorepo 구조로 `apps/web`, `apps/api`, `apps/worker`, `packages/contracts`, `infra`를 사용한다.

B) 단순 구조로 `frontend`, `backend`, `infra`를 사용하고 Backend 내부에 Domain Module을 둔다.

C) 각 Business Capability를 최상위 디렉터리로 두고 Unit별 독립 Package를 만든다.

D) Other (please describe after [Answer]: tag below)

[Answer]: B

## Answer Analysis

| Question | Answer | Confirmed Decision | Validation |
|---|---|---|---|
| Q1 Story Grouping | A | Business Capability 중심 7개 Unit | Valid |
| Q2 Web Boundary | A | Web Experience를 독립 Unit으로 구성 | Valid |
| Q3 Validation Boundary | A | C06과 C11을 별도 Unit에 두고 Contract 공유 | Valid |
| Q4 Shared Data | A | Unit 소유 Table만 쓰고 Port 또는 Read Model로 접근 | Valid |
| Q5 Team Alignment | A | 1인 순차 소유, 향후 분리를 위한 Contract 문서화 | Valid |
| Q6 Code Organization | B | `frontend`, `backend`, `infra` 구조와 Backend Domain Module | Valid |

- 누락되거나 허용되지 않은 선택지는 없다.
- 복수 선택이나 조건부·모호한 답변은 없다.
- 7개 논리 Unit과 단일 모듈러 Monolith, 별도 Web Container 결정은 양립한다.
- 독립 Web Unit은 OpenAPI Contract 이후 Backend Unit과 병렬 구현할 수 있다.
- 수집 검증과 추천 결과 검증은 분리하되 승인 Catalog 및 Versioned Validation Contract로 연결한다.
- 추가 Follow-up Question은 필요하지 않다.

## Part 1 — Planning Checklist

- [x] 이전 단계 Artifacts와 Extension Configuration을 로드한다.
- [x] Story Grouping, Dependencies, Team Alignment, Technical Considerations, Business Domain, Code Organization 범주를 모두 평가한다.
- [x] 단위 분해에 영향을 주는 질문과 선택지를 작성한다.
- [x] 모든 `[Answer]:`가 유효하게 작성되었는지 확인한다.
- [x] 답변의 모호성, 결합 선택, 충돌과 누락을 분석한다.
- [x] 필요한 경우 Follow-up Question을 추가하고 답변을 검증한다. 추가 질문 불필요.
- [x] Unit of Work Generation Plan 승인을 받는다.

## Part 2 — Generation Checklist

- [x] 승인된 분해 방식과 다음 미완료 Step을 확인한다.
- [x] `aidlc-docs/inception/application-design/unit-of-work.md`에 Unit 정의, 책임, 경계와 Greenfield 코드 구성 전략을 작성한다.
- [x] `aidlc-docs/inception/application-design/unit-of-work-dependency.md`에 의존 Matrix, 실행 순서와 병렬 가능성을 작성한다.
- [x] `aidlc-docs/inception/application-design/unit-of-work-story-map.md`에 US-001~US-028의 Primary·Supporting Unit Mapping을 작성한다.
- [x] 모든 Story가 정확히 하나의 Primary Unit에 할당되었는지 검증한다.
- [x] Component C01~C14와 Service S01~S10이 누락 없이 Unit에 귀속되는지 검증한다.
- [x] Unit 간 순환 의존, 중복 Write Ownership과 책임 충돌이 없는지 검증한다.
- [x] Requirements와 Quality Gate가 후속 Unit Design 입력으로 전달되는지 검증한다.
- [x] Resiliency 적용사항과 PBT 후속 적용사항의 Unit별 전달을 검증한다.
- [x] 모든 생성 Step 완료 즉시 해당 Checkbox를 `[x]`로 갱신한다.
- [x] Units Generation 완료 검증과 승인 요청을 기록한다.

## Planned Validation

- 모든 28개 Story ID가 누락·중복 없이 Primary Unit에 매핑되어야 한다.
- 모든 C01~C14와 S01~S10이 하나 이상의 Unit 책임에 연결되어야 한다.
- Dependency Graph는 순환이 없어야 하며 구현 순서를 계산할 수 있어야 한다.
- Unit 경계는 AI가 적격성·최종 순위를 변경하지 못한다는 설계 규칙을 보존해야 한다.
- 승인되지 않은 Metadata와 Grounding 실패 결과가 사용자 응답으로 유출되지 않는 검증 경계를 보존해야 한다.
- Markdown Table, Link, Identifier와 `[Answer]:` 형식이 파싱 가능해야 한다.

## Extension Compliance at Planning

### Resiliency Baseline

- Unit마다 중요도, 외부 의존성, Fallback, Recovery와 Observability 설계 입력을 전달한다.
- 단일 서버 예외를 유지하되 Platform and Delivery 경계에서 백업·복원·Rollback 책임을 누락하지 않는다.

### Property-Based Testing

- PBT-01의 공식 속성 식별은 Unit별 Functional Design에서 수행한다.
- Unit Mapping은 추천 하드 조건, 승인 Catalog 폐쇄성, Grounding, 격리, 정규화와 상태 전이 속성을 해당 Unit에 전달한다.
- PBT-02~PBT-10은 Units Generation의 직접 적용 단계가 아니므로 현재 N/A이며 차단 Finding이 아니다.

현재 Planning 단계에서 차단 상태인 Extension Finding은 없다.
