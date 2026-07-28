# OTT 통합 피드 및 AI 추천 서비스 Application Design Plan

## 1. Planning Status

- [x] 승인된 Execution Plan 로드
- [x] Requirements, User Stories, Personas 로드
- [x] 내부 책임 경계와 확장 설정 로드
- [x] Application Design 질문 답변 수집
- [x] 답변의 누락·모호성·상충 검증
- [x] Component 경계와 Interface 설계
- [x] Service orchestration과 dependency 설계
- [x] Application Design 산출물 생성 및 검증

## 2. Design Scope

### Business Capabilities

- OTT 최신 콘텐츠 수집·정규화·승인·격리
- 통합 피드, 필터, 검색, 다국어 탐색
- 한국어·영어 자연어 의도 구조화
- 하드 조건 기반 후보 생성과 개인화·다양성 순위
- Metadata 근거 기반 AI 요약·추천 이유
- 추천 결과 사후 검증과 안전한 Fallback
- 계정, 선호, 행동 피드백, 개인정보 통제
- 콘텐츠 운영, 추적, 관측, 백업과 배포

### Required Responsibility Boundaries

- AI 계층은 자유 형식 언어 해석과 근거 기반 문구 생성을 담당한다.
- Recommendation Engine은 후보 적격성, 하드 조건, 점수, 개인화, 다양성, 최종 순위를 담당한다.
- Metadata Validation Pipeline은 승인·격리 상태와 사용자 노출 전 검증을 담당한다.
- Recommendation Orchestrator는 호출 순서, 제한 시간, 실패 처리와 응답 조립을 담당한다.
- 내부 구성요소는 사용자·외부 Actor와 분리한다.

## 3. Design Decision Questions

아래 각 `[Answer]:` 뒤에 선택한 알파벳을 입력해 주세요. `X) 기타`를 선택하면 알파벳 뒤에 구체적인 내용을 적어 주세요.

### Question 1
초기 백엔드의 Application Architecture는 무엇으로 할까요?

A) 모듈형 Monolith — 하나의 Python 배포 단위 안에서 도메인별 모듈과 Interface를 엄격히 분리

B) Microservices — 콘텐츠, 추천, 계정, 운영을 독립 서비스로 배포

C) Hybrid — 핵심 API는 모듈형 Monolith, 수집·AI 작업만 별도 Worker로 분리

X) 기타 (아래 `[Answer]:` 뒤에 설명)

[Answer]: A

### Question 2
프론트엔드와 백엔드의 배포 경계는 어떻게 할까요?

A) React 정적 Web과 Python API를 별도 Container로 배포

B) Python Backend가 빌드된 React 정적 파일도 함께 제공

C) React SSR Application과 Python API를 별도 Container로 배포

X) 기타 (아래 `[Answer]:` 뒤에 설명)

[Answer]: A

### Question 3
콘텐츠·계정·추천 추적의 기본 Data Store 구성은 무엇으로 할까요?

A) PostgreSQL 중심 — 관계형 데이터, JSON Metadata, 기본 검색과 Vector 확장을 한 저장소에서 운영

B) PostgreSQL과 별도 검색 Engine — 정합성 데이터와 전문·의미 검색을 분리

C) PostgreSQL과 별도 Vector Store — 관계형 데이터와 의미 검색 Vector를 분리

D) 요구사항에 맞는 구성을 Application Design이 제안하되 Prototype 단순성을 우선

X) 기타 (아래 `[Answer]:` 뒤에 설명)

[Answer]: A

### Question 4
콘텐츠 수집, 알림, 장시간 AI 작업의 비동기 처리는 어떻게 할까요?

A) 동일 Backend Process의 Scheduler와 Background Task로 시작

B) 별도 Worker와 Message Broker를 사용

C) 수집·알림은 별도 Worker, 사용자 추천 요청은 동기 처리

D) 요구사항에 맞게 제안하되 추후 Broker로 교체 가능한 Interface를 유지

X) 기타 (아래 `[Answer]:` 뒤에 설명)

[Answer]: C

### Question 5
AI Provider 경계와 장애 대응은 어떻게 설계할까요?

A) Provider-neutral Adapter를 두고 초기에는 한 Provider만 연결

B) 두 개 이상의 AI Provider를 연결하고 즉시 Fallback 지원

C) 자체 Hosting Model 중심으로 설계

D) AI 없이 규칙 기반 Prototype을 먼저 만들고 AI Adapter는 후속 구현

X) 기타 (아래 `[Answer]:` 뒤에 설명)

[Answer]: A

### Question 6
사용자 추천 요청의 응답 방식은 무엇으로 할까요?

A) 단일 동기 HTTP 응답 — 제한 시간 안에 전체 추천 반환

B) 비동기 Job — 요청 ID 반환 후 Polling으로 결과 조회

C) 동기 기본 결과 후 Server-Sent Events로 AI 설명을 점진 전달

D) 빠른 규칙 기반 결과를 즉시 반환하고 AI 보강 결과는 별도 갱신

X) 기타 (아래 `[Answer]:` 뒤에 설명)

[Answer]: A

### Question 7
회원 인증 Component 경계는 어떻게 할까요?

A) Application이 이메일 인증을 관리하고 OAuth Provider Adapter로 소셜 로그인 연결

B) 외부 Identity Provider가 이메일·소셜 인증을 모두 담당

C) Prototype은 이메일 인증만 구현하고 소셜 로그인은 Interface만 정의

X) 기타 (아래 `[Answer]:` 뒤에 설명)

[Answer]: A

### Question 8
Web Client API Contract는 무엇으로 할까요?

A) REST JSON API와 OpenAPI Contract

B) GraphQL API

C) REST JSON API를 기본으로 하고 추천 진행 상태에만 Server-Sent Events 추가

D) REST JSON API를 기본으로 하고 양방향 추천 대화에 WebSocket 추가

X) 기타 (아래 `[Answer]:` 뒤에 설명)

[Answer]: A

## 4. Approved-Decision Execution Checklist

답변 검증 후 아래 순서로 설계를 실행하며 각 단계 완료 즉시 `[x]`로 갱신한다.

- [x] **Step 1 - Component Identification**
  - [x] Component 이름, 목적, 책임, 금지 책임을 정의한다.
  - [x] Port·Adapter와 내부 Domain 경계를 정의한다.
- [x] **Step 2 - Component Interfaces**
  - [x] 공개 Interface와 주요 입력·출력 Type을 정의한다.
  - [x] 상세 Business Rule은 Functional Design으로 연기한다.
- [x] **Step 3 - Service Layer Design**
  - [x] 사용자 요청, 수집, 추천, 검증, 운영 흐름의 Orchestration을 정의한다.
  - [x] Transaction·Idempotency·Fallback 경계를 고수준으로 정의한다.
- [x] **Step 4 - Dependency and Communication Design**
  - [x] 허용 Dependency 방향과 금지 Dependency를 정의한다.
  - [x] 동기·비동기 통신 Pattern과 Failure 경계를 정의한다.
  - [x] Data Flow를 Mermaid와 Text Alternative로 문서화한다.
- [x] **Step 5 - Mandatory Artifacts**
  - [x] `aidlc-docs/inception/application-design/components.md`
  - [x] `aidlc-docs/inception/application-design/component-methods.md`
  - [x] `aidlc-docs/inception/application-design/services.md`
  - [x] `aidlc-docs/inception/application-design/component-dependency.md`
  - [x] `aidlc-docs/inception/application-design/application-design.md`
- [x] **Step 6 - Design Validation**
  - [x] Requirements와 Story가 하나 이상의 Component·Service에 연결되는지 확인한다.
  - [x] AI, Recommendation Engine, Metadata Validation 책임 경계 위반이 없는지 확인한다.
  - [x] Resiliency와 PBT 적용 지점이 후속 단계에 전달되는지 확인한다.
  - [x] Markdown, Mermaid와 Text Alternative를 검증한다.

## 5. Mandatory Artifact Content

### components.md

- Component 이름, 목적, 책임, 금지 책임
- 제공·요구 Interface
- 소유 데이터와 상태
- Requirements·Story 연결

### component-methods.md

- Component별 고수준 Method Signature
- Input·Output·Error Contract
- Side Effect와 Idempotency 기대
- 상세 Business Rule은 Functional Design 대상임을 명시

### services.md

- Application Service와 Orchestration 흐름
- Transaction, Retry, Timeout, Fallback 경계
- 사용자·운영자 관찰 결과

### component-dependency.md

- Dependency Matrix
- 동기·비동기 Communication Pattern
- 추천·수집·개인화 Data Flow
- Mermaid Diagram과 Text Alternative

### application-design.md

- 위 산출물의 통합 요약
- 핵심 Architecture Decision과 Trade-off
- 후속 Units Generation 입력

## 6. Constraints

- Prototype 단순성을 우선하되 Port·Adapter 경계로 교체 가능성을 유지한다.
- AI 계층은 후보 적격성이나 최종 순위를 결정하지 않는다.
- 승인되지 않은 Metadata는 검색·피드·추천 입력에 사용할 수 없다.
- 사용자 노출 전 Metadata Grounding 검증을 우회할 수 없다.
- 상세 Algorithm, 점수 공식, Schema Field는 Functional Design에서 확정한다.
- 배포 Resource와 Provider 선택의 상세는 Infrastructure Design에서 확정한다.
