# U03 Catalog and Discovery Functional Design Plan

> **Single Source of Truth**: 이 파일은 U03 Functional Design의 계획, 사용자 결정과 체크박스 진행 상태를 관리한다. 모든 질문 답변과 모호성이 해소되기 전에는 설계 산출물을 생성하지 않는다.

## Unit Context

- **Goal**: 승인된 콘텐츠만 피드, 상세, 필터, 제목·인물 검색과 한국어·영어 의미 검색에 제공한다.
- **Owned Components**: C04 Content Catalog, C07 Search
- **Owned Services**: S01 FeedQueryService, S02 SearchService
- **Primary Stories**: US-001, US-002, US-003, US-004, US-005, US-006
- **Supporting Consumers**: U01 Web Experience, U05 Recommendation and AI Grounding, U06 Engagement and Operations
- **Provider Dependencies**: U04 ApprovedCatalogWritePort 호출, U07 API·PostgreSQL runtime, 외부 semantic embedding adapter slot
- **Owned Data**: approved_contents, content_localizations, availability, catalog_sources, feed_projections, search_projections
- **Hard Boundary**: 승인 상태가 아니거나 격리된 record는 피드, 상세, 검색, 추천 후보 조회에서 반환하지 않는다.

## Execution Plan

### Step 1 — Context and Traceability Analysis

- [x] U03 Unit Definition, Story Map과 data ownership 경계를 읽는다.
- [x] C04·C07 component method와 S01·S02 orchestration을 읽는다.
- [x] US-001~US-006과 FR-001~008, FR-013, FR-033~034, DR-003~004, DR-006, DR-009~012를 연결한다.
- [x] Resiliency와 Property-Based Testing extension의 활성 상태와 Functional Design 적용 범위를 확인한다.

### Step 2 — Functional Design Planning and Questions

- [x] U03 Functional Design 실행 계획을 작성한다.
- [x] 기존 요구사항에서 확정되지 않은 business logic 결정을 식별한다.
- [x] Question 1~12를 전용 계획 파일에 `[Answer]:` 형식으로 작성한다.
- [x] 모든 `[Answer]:`를 수집하고 선택지 유효성을 확인한다.
- [x] 답변 간 충돌과 모호성을 분석하고 필요하면 clarification question file을 작성한다. 추가 질문은 필요하지 않다.

### Step 3 — Business Logic Model

- [x] 승인 Catalog publish·replace·withdraw 흐름과 CatalogVersion 전이를 설계한다.
- [x] Feed category, filter, ordering, pagination과 freshness 상태 계산을 설계한다.
- [x] 상세 조회, 지역·OTT availability와 합법적 이동 link 선택을 설계한다.
- [x] 제목·인물 검색과 한국어·영어 semantic search, projection refresh와 fallback을 설계한다.
- [x] `business-logic-model.md`를 생성하고 story·requirement trace를 기록한다.

### Step 4 — Domain Entities

- [x] Aggregate, Entity, Value Object, identifier와 version 관계를 정의한다.
- [x] Approved Content와 source provenance, localization, availability의 불변 조건을 정의한다.
- [x] FeedProjection과 SearchProjection의 version, cursor와 freshness field를 정의한다.
- [x] `domain-entities.md`를 생성한다.

### Step 5 — Business Rules and Testable Properties

- [x] 승인 영역 폐쇄성, 지역·OTT·시간 filter와 localization fallback 규칙을 정의한다.
- [x] 정렬 안정성, 중복 제거, cursor pagination과 projection 재적용 규칙을 정의한다.
- [x] Search ranking, semantic fallback, stale data 표시와 장애 저하 규칙을 정의한다.
- [x] PBT-01에 따라 invariant, idempotence, oracle, stateful, easy-verification property를 식별한다.
- [x] `business-rules.md`를 생성한다.

### Step 6 — Validation and Completion

- [x] Story, FR·DR·AC와 domain rule traceability의 누락을 검증한다.
- [x] Resiliency와 PBT extension compliance를 rule별로 평가한다.
- [x] Markdown과 embedded content의 parsing compatibility를 검증한다.
- [x] U03 Functional Design 완료 메시지를 감사 로그에 기록하고 명시적 승인을 요청한다.

## Functional Design Questions

## Question 1
피드의 기본 구성과 category 중복 표시 정책은 무엇입니까?

A) 신작·공개 예정·인기·종료 예정 section을 각각 제공하며 한 작품이 여러 section에 중복 표시될 수 있다.

B) 네 category를 하나의 혼합 feed로 제공하고 작품마다 대표 category 하나만 선택한다.

C) 네 section을 제공하되 우선순위에 따라 작품을 한 section에만 배치한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
각 category의 판정 기준과 인기 순위 입력은 어떻게 관리합니까?

A) 공급자 상태·공개일·종료일과 공급자 인기 지표를 정규화하고, versioned rule로 category와 점수를 계산한다.

B) 공급자가 준 category와 순서를 그대로 사용하고 내부에서는 병합만 수행한다.

C) 날짜 기반 category는 내부 rule로 계산하고 인기는 사용자 행동만으로 계산한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
피드와 검색의 기본 정렬 및 pagination 안정성 정책은 무엇입니까?

A) category score 내림차순, 공개일 내림차순, content ID 오름차순의 결정적 순서와 opaque cursor를 사용한다.

B) 최신순을 기본으로 하고 page number pagination을 사용한다.

C) 인기와 최신성을 혼합한 versioned score 순서와 해당 snapshot version을 포함한 opaque cursor를 사용한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 4
복수 필터의 결합 의미는 무엇입니까?

A) 서로 다른 filter 종류는 AND, 같은 종류의 복수 값은 OR로 결합한다.

B) 모든 선택 값을 AND로 결합한다.

C) 모든 선택 값을 OR로 결합한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
지역과 OTT availability를 조회할 때 기본 지역과 미확인 상태는 어떻게 처리합니까?

A) 요청 region을 필수로 받고, 미확인 availability는 결과와 이동 link에서 제외한다.

B) 요청 region이 없으면 사용자 locale에서 추론하고, 미확인 항목은 경고와 함께 결과에 포함하되 link는 비활성화한다.

C) 요청 region이 없으면 전역 결과를 제공하고, availability 상태와 link 활성 여부만 별도로 표시한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 6
콘텐츠별 마지막 정상 갱신 이후 언제 stale 상태로 표시합니까?

A) 공급자별 계약 갱신 주기의 두 배를 초과하면 stale로 계산한다.

B) 모든 공급자에 공통 24시간 기준을 사용한다.

C) category와 공급자별 versioned freshness policy를 사용하고 기준이 없으면 24시간을 적용한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 7
한국어·영어 제목과 설명의 locale fallback 순서는 무엇입니까?

A) 요청 locale → 원문 locale → 영어 → 사용 가능한 첫 번역 순으로 선택하고 실제 반환 locale을 표시한다.

B) 요청 locale → 영어 순으로만 선택하고 없으면 해당 필드를 비운다.

C) 요청 locale이 없으면 항상 원문만 반환한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 8
동일 작품에 같은 OTT의 합법적 이동 link가 여러 개면 어떤 link를 선택합니까?

A) 요청 region과 일치하는 직접 시청 link를 우선하고, 없으면 공식 상세 link를 선택한다.

B) 공급자 priority가 가장 높은 link 하나만 선택한다.

C) 검증된 모든 link를 반환하고 client가 선택한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 9
제목·인물 text search의 match 및 ranking 정책은 무엇입니까?

A) 정확한 제목 → 제목 prefix → 제목 전문 검색 → 인물 일치 순으로 가중치를 적용하고 locale 및 인기도를 tie-breaker로 사용한다.

B) PostgreSQL 전문 검색 점수만 사용한다.

C) 제목과 인물 match를 동일 가중치로 계산하고 최신성을 tie-breaker로 사용한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 10
자연어·의미 검색에서 U03과 U05 AI 계층의 책임 경계는 무엇입니까?

A) U03은 검색 전용 한국어·영어 query parser와 embedding search를 소유하고, U05의 추천 intent parser와 contract만 공유한다.

B) U05 AI 계층이 검색 query도 구조화하고 U03은 구조화 filter와 embedding vector만 실행한다.

C) U03은 semantic similarity만 제공하고 자연어 조건 구조화는 초기 범위에서 제외한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 11
semantic search 또는 projection이 실패하거나 최신 CatalogVersion을 따라가지 못할 때 어떻게 저하 운용합니까?

A) 승인 Catalog를 재확인한 text search와 filter 결과로 자동 fallback하고 응답에 degraded 상태를 표시한다.

B) 마지막 정상 semantic projection을 사용하되 stale 상태를 표시한다.

C) semantic 결과를 반환하지 않고 재시도 가능한 오류만 응답한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 12
U04가 승인 콘텐츠를 재승인하거나 철회할 때 U03 projection 갱신 의미는 무엇입니까?

A) CatalogVersion별 outbox event로 비동기 갱신하며 같은 version 재적용은 idempotent이고 철회 record는 조회 시 즉시 차단한다.

B) 승인 transaction 안에서 feed와 search projection을 모두 동기 갱신한다.

C) 일정 주기 전체 rebuild만 수행하고 철회도 다음 rebuild에서 반영한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Planned Outputs

- `aidlc-docs/construction/u03-catalog-and-discovery/functional-design/business-logic-model.md`
- `aidlc-docs/construction/u03-catalog-and-discovery/functional-design/domain-entities.md`
- `aidlc-docs/construction/u03-catalog-and-discovery/functional-design/business-rules.md`

U03은 frontend를 소유하지 않으므로 `frontend-components.md`는 N/A이다. U01은 U03 REST/OpenAPI contract를 소비한다.

## Extension Applicability

- **Resiliency Baseline**: stale-while-revalidate, projection lag, semantic dependency failure, approved Catalog fallback과 장애 상태 전달을 후속 설계에 적용한다.
- **Property-Based Testing**: 승인 폐쇄성, filter 교집합, 중복 제거, 결정적 정렬, cursor 안정성, locale fallback, projection idempotence와 state transition을 PBT-01 대상으로 분석한다.
- **Security Baseline**: `aidlc-state.md`에서 disabled이므로 extension으로는 N/A이다. 지역·라이선스·승인 경계는 core data requirement로 계속 적용한다.
- **Frontend**: U03 소유 UI가 없으므로 N/A이며 접근성 presentation은 U01 handoff로 유지한다.
