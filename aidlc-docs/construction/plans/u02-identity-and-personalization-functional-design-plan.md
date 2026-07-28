# U02 Identity and Personalization Functional Design Plan

> **Single Source of Truth**: 이 파일은 U02 Functional Design의 계획, 사용자 결정과 체크박스 진행 상태를 관리한다. 질문 답변과 모호성 해소가 끝나기 전에는 설계 산출물을 생성하지 않는다.

## Unit Context

- **Goal**: 계정, 인증, 역할, 사용자 선호, 구독 OTT, 찜·평가·시청 이력, 동의, 행동 이벤트와 비식별 개인화 feature를 관리한다.
- **Owned Components**: C03 Identity and Access, C12 Personalization and Feedback
- **Owned Services**: S05 AccountAndPrivacyService, S06 FeedbackService
- **Primary Stories**: US-014, US-015, US-016, US-017, US-018, US-027
- **Supporting Consumers**: U01 계정 UI, U05 Consent·PersonalizationFeature Port, U06 Role·Notification Preference Port
- **Provider Dependency**: U07 API context, rate limit, idempotency, PostgreSQL runtime, OAuth adapter slot과 outbox
- **Owned Data**: users, credentials, oauth_links, roles, preferences, subscriptions, watch_items, ratings, watch_history, consents, behavior_events, personalization_features
- **Hard Boundary**: 추천 최종 순위·AI 문구·콘텐츠 metadata를 소유하지 않으며 직접 식별자를 추천·AI context에 전달하지 않는다.

## Execution Plan

### Step 1 — Context and Traceability Analysis

- [x] U02 Unit Definition, Story Map과 Dependency Graph를 읽는다.
- [x] C03·C12 Component 책임, Method와 S05·S06 Orchestration을 읽는다.
- [x] US-014~US-018, US-027 Acceptance Criteria와 FR-011~012, FR-022~027, DR-007~008, AC-005, AC-007을 연결한다.
- [x] Security extension은 disabled이지만 인증·권한·개인정보 core requirement는 필수임을 확인한다.

### Step 2 — Functional Decisions

- [x] 아래 Question 1~14의 `[Answer]:`를 모두 채운다.
- [x] 답변의 누락, 충돌과 모호성을 검증한다.
- [x] 필요한 경우 follow-up 질문을 같은 파일에 추가하고 모든 모호성을 해소한다. 추가 질문은 필요하지 않았다.

### Step 3 — Business Logic Model

- [x] 회원 등록·인증·세션·OAuth 연결·해제·계정 복구 흐름을 설계한다.
- [x] Preference, Subscription, Library와 Feedback Event 상태 전이를 설계한다.
- [x] Consent 변경, Feature Snapshot, Data Export·Deletion 흐름과 비식별 경계를 설계한다.
- [x] `business-logic-model.md`를 생성하고 story·requirement trace를 기록한다.

### Step 4 — Domain Entities

- [x] Aggregate, Entity, Value Object, Identifier와 관계를 정의한다.
- [x] 동시 수정 version, idempotency key, consent snapshot과 provenance field를 정의한다.
- [x] 직접 식별 데이터와 추천용 pseudonymous feature의 저장 경계를 정의한다.
- [x] `domain-entities.md`를 생성한다.

### Step 5 — Business Rules and Properties

- [x] 인증·권한·account-linking·session lifecycle 규칙을 정의한다.
- [x] 선호·구독·찜·평가·시청 이력의 validation과 state transition을 정의한다.
- [x] 동의 목적·철회·guest linking·export·deletion 규칙을 정의한다.
- [x] 저장 멱등성, rating range, consent non-bypass, deletion closure와 pseudonymization property를 식별한다.
- [x] `business-rules.md`를 생성한다.

### Step 6 — Validation and Completion

- [x] Story, FR·DR·AC와 Domain Rule traceability의 누락을 검사한다.
- [x] Resiliency와 Property-Based Testing extension compliance를 평가한다.
- [x] Markdown과 embedded content parsing을 검증한다.
- [x] U02 Functional Design 완료 메시지를 기록하고 명시적 승인을 요청한다.

## Functional Design Questions

## Question 1
초기 이메일 인증 방식은 무엇으로 설계합니까?

A) 이메일·비밀번호와 이메일 소유 확인을 사용한다.

B) 비밀번호 없이 이메일 magic link 또는 일회용 code를 사용한다.

C) 이메일·비밀번호와 passwordless 방식을 모두 제공한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
초기 소셜 로그인 공급자 범위는 무엇입니까?

A) Google만 제공하고 adapter contract로 확장한다.

B) Google과 Apple을 제공한다.

C) Google, Apple, Kakao와 Naver를 제공한다.

D) 소셜 로그인 contract만 설계하고 초기 구현에서는 비활성화한다.

E) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
동일한 검증 이메일을 가진 이메일 계정과 OAuth 계정은 어떻게 연결합니까?

A) 사용자가 기존 계정으로 재인증하고 명시적으로 연결할 때만 합친다.

B) 공급자가 verified email을 제공하면 자동 연결한다.

C) 자동 연결하지 않고 항상 별도 계정으로 유지한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4
세션과 기기 관리 정책은 무엇입니까?

A) 여러 기기 세션을 허용하고 사용자가 개별 세션 또는 전체 세션을 폐기할 수 있다.

B) 계정당 하나의 활성 세션만 허용한다.

C) 여러 세션을 허용하지만 비밀번호 변경·계정 위험 이벤트에서 모두 폐기한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
초기 역할 모델은 무엇입니까?

A) Member와 Operator 두 역할만 사용한다.

B) Member, Content Operator와 System Administrator를 분리한다.

C) Role에 세부 Permission 집합을 연결하는 일반 RBAC로 설계한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 6
선호 장르와 구독 OTT는 어떤 의미로 저장합니까?

A) 선호 장르는 선택 집합, OTT는 현재 구독 여부만 저장한다.

B) 장르 선호 강도와 OTT별 구독·비구독·미지정 상태를 저장한다.

C) 좋아함·싫어함 장르와 OTT별 구독 상태를 저장한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 7
평가와 시청 이력의 초기 모델은 무엇입니까?

A) 1~5 정수 별점, 찜 여부, 시청 완료 여부와 최근 시청 시각을 저장한다.

B) 좋아요·싫어요, 찜과 시청 완료만 저장한다.

C) 0.5 단위 1~5 별점, 진행률, 완료·중단 상태와 반복 시청 횟수를 저장한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 8
개인화 관련 동의는 어느 수준으로 분리합니까?

A) 개인화 목적의 단일 동의로 관리한다.

B) 개인화, 서비스 분석과 외부 AI 전송을 각각 독립 동의로 관리한다.

C) 필수 서비스 처리와 선택 개인화만 분리하고 외부 AI에는 직접 식별 데이터를 보내지 않는다.

D) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 9
개인화 동의를 철회했을 때 기존 행동 데이터는 어떻게 처리합니까?

A) 신규 feature 사용을 즉시 중단하고 기존 원본 이벤트는 보존 기간까지 격리한다.

B) 신규 사용을 중단하고 개인화 원본 이벤트와 파생 feature를 삭제한다.

C) 파생 feature만 즉시 삭제하고 원본 이벤트는 비식별 통계로만 유지한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 10
비회원 행동을 회원 계정과 연결하는 정책은 무엇입니까?

A) 회원 전환 시 별도 명시적 동의를 받은 경우에만 기존 guest 행동을 연결한다.

B) guest 행동은 어떤 경우에도 회원 profile과 연결하지 않는다.

C) 로그인 시 고지 후 사용자가 거부하지 않으면 연결한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 11
클릭·저장·다시 추천·무시·OTT 이동 이벤트가 개인화 feature에 반영되는 시점은 언제입니까?

A) event를 durable하게 기록한 뒤 비동기 worker가 수 분 내 feature를 갱신한다.

B) 요청 transaction에서 event와 feature를 즉시 함께 갱신한다.

C) 저장·평가처럼 명시적 행동은 즉시, 클릭·OTT 이동 등 암시적 행동은 비동기로 처리한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 12
중복 행동 이벤트는 어떻게 판정합니까?

A) client가 제공하는 idempotency key를 사용자·event type scope에서 적용한다.

B) 서버가 user, content, event type과 짧은 time window로 중복을 판정한다.

C) idempotency key를 우선 사용하고 없는 경우 제한된 time-window 규칙을 적용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 13
사용자 데이터 삭제 요청의 초기 정책은 무엇입니까?

A) 재인증 후 즉시 비활성화하고 비동기 삭제하며 법적·운영상 필수 tombstone만 분리 보존한다.

B) 재인증 후 복구 가능한 유예 기간을 두고 이후 비동기 삭제한다.

C) 계정은 익명화하고 행동 이벤트는 통계 목적으로 계속 보존한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 14
U05에 제공하는 개인화 Feature Snapshot의 식별 경계는 무엇입니까?

A) 요청 범위의 pseudonymous subject ID와 동의된 feature 값·버전만 제공한다.

B) subject ID 없이 feature 값·버전만 제공하고 U02 내부에서 사용자와 연결한다.

C) 장기 pseudonymous ID를 제공하되 이메일·OAuth ID·원본 행동 payload는 제외한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Planned Outputs

- `aidlc-docs/construction/u02-identity-and-personalization/functional-design/business-logic-model.md`
- `aidlc-docs/construction/u02-identity-and-personalization/functional-design/domain-entities.md`
- `aidlc-docs/construction/u02-identity-and-personalization/functional-design/business-rules.md`

U02는 frontend를 소유하지 않으므로 `frontend-components.md`는 N/A이다. U01이 U02의 REST/OpenAPI contract를 소비한다.

## Extension Applicability

- **Resiliency Baseline**: session revocation, OAuth failure isolation, export·deletion job 재처리와 consent fail-closed 흐름에 적용한다.
- **Property-Based Testing**: 저장 멱등성, rating range, state transition, consent non-bypass, deletion closure와 serialization round-trip property를 식별한다.
- **Security Baseline**: aidlc-state에서 disabled이므로 extension으로는 N/A. 인증·권한·privacy는 core requirement로 적용한다.
- **Frontend**: U02 소유 UI가 없으므로 N/A. 접근성 UI 구현은 U01 handoff로 유지한다.
