# U01 Web Experience Functional Design Plan

> **Single Source of Truth**: 이 파일은 U01 Functional Design의 계획, 사용자 결정 및 완료 체크박스를 관리한다. 모든 답변이 유효하고 모호하지 않을 때만 설계 산출물을 생성한다.

## Unit Context

- **Goal**: 한국어·영어 반응형 UI에서 통합 피드, 검색, 추천 대화, 계정·개인정보, 알림 및 운영 기능을 일관되고 접근 가능하게 제공한다.
- **Owned Component**: C01 Web Experience.
- **Primary Story**: US-007.
- **Supporting Stories**: US-001~US-006, US-008~US-019, US-021, US-027.
- **Required Dependencies**: U02 Identity/Profile/Consent, U03 Feed/Detail/Search, U05 Recommendation/Conversation, U06 Notification/Admin, U07 OpenAPI/Error/Session 계약.
- **Data Ownership**: 영속 비즈니스 테이블 없음. 비민감 화면 상태와 허용된 세션 참조만 클라이언트에서 관리한다.
- **Hard Boundary**: U01은 추천 순위, 메타데이터 승인, 권한 또는 개인정보 정책을 결정하지 않고 서버 계약의 결과를 표시하고 사용자 명령을 전달한다.
- **Enabled Extensions**: Resiliency Baseline (Full), Property-Based Testing (Full).
- **Disabled Extension**: Security Baseline. 인증정보 비노출, 서버 권한 검증, 동의 범위 준수는 핵심 요구사항으로 유지한다.

## Execution Plan

### Step 1 - Context and Traceability

- [x] U01 정의, C01 책임, Primary/Supporting Story 및 의존 계약을 확인했다.
- [x] U01이 영속 비즈니스 데이터나 서버 도메인 결정을 소유하지 않음을 확인했다.
- [x] 기존 작업공간에 U01 프런트엔드 구현이 아직 없음을 확인했다.

### Step 2 - Planning and Questions

- [x] 화면 구조, 탐색 상태, 추천 대화, 인증 경계, 오류·저하 상태 및 접근성의 미결정을 식별했다.
- [x] 각 질문에 상호 배타적인 선택지와 마지막 `X) Other` 선택지를 작성했다.
- [ ] Question 1~12의 모든 `[Answer]:` 값을 수집한다.
- [ ] 답변의 유효성·일관성·모호성을 검토하고 필요한 경우 clarification 질문을 작성한다.

### Step 3 - Business Logic Model

- [ ] 방문자·회원·운영자 여정과 라우트 전이를 정의한다.
- [ ] Feed·Search·Recommendation의 query, pagination, refinement 및 reset 흐름을 정의한다.
- [ ] 인증 만료, 권한 거부, 부분 장애, stale data 및 재시도 흐름을 정의한다.
- [ ] `business-logic-model.md`를 생성하고 Story/API 계약 추적성을 연결한다.

### Step 4 - Domain Entities

- [ ] UI Route, View State, Query State, Recommendation Conversation 및 Session Reference를 정의한다.
- [ ] Content Card, Evidence, Availability, Freshness, Consent 및 Feedback 표현 모델을 정의한다.
- [ ] 로컬 상태와 서버 원본 상태의 소유권·수명·초기화 규칙을 정의한다.
- [ ] `domain-entities.md`를 생성한다.

### Step 5 - Business Rules and Frontend Components

- [ ] 로딩·빈 결과·오류·저하·오래된 데이터 표시 규칙과 복구 동작을 정의한다.
- [ ] 인증·동의·운영자 권한·외부 OTT 이동·행동 이벤트 규칙을 정의한다.
- [ ] 한국어·영어, 키보드, 초점, 라이브 영역, 대체 텍스트 및 오류 연결 규칙을 정의한다.
- [ ] 컴포넌트 계층, props/state, 상호작용, validation 및 API 연계를 정의한다.
- [ ] PBT 대상 UI 상태 전이와 불변조건을 분류한다.
- [ ] `business-rules.md`와 `frontend-components.md`를 생성한다.

### Step 6 - Validation and Completion

- [ ] Story/FR/DR/NFR 및 U02~U07 API 계약 추적성을 검증한다.
- [ ] Resiliency와 Property-Based Testing 확장 규칙 준수를 검증한다.
- [ ] Markdown 구조와 질문·답변 파싱 호환성을 검증한다.
- [ ] 계획, 상태 및 감사 로그를 갱신하고 Functional Design 검토를 요청한다.

## Functional Design Questions

각 `[Answer]:` 뒤에 선택한 문자 하나를 입력한다. 선택지에 없는 정책이면 `X`를 쓰고 같은 줄에 원하는 내용을 설명한다.

## Question 1
최상위 사용자 탐색 구조는 무엇으로 확정할까요?

A) Feed, Search, Recommend, Library를 주 탐색으로 두고 Account/Notification을 프로필 메뉴에 둔다

B) Feed와 Recommend만 주 탐색으로 두고 나머지는 통합 메뉴에 둔다

C) 모든 기능을 단일 대시보드 화면의 섹션으로 제공한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 2
방문자가 회원 전용 동작(찜, 평가, 추천 저장 등)을 선택하면 어떻게 처리할까요?

A) 현재 화면과 의도를 보존한 채 로그인으로 이동하고 성공 후 원래 동작을 한 번 재개한다

B) 로그인 안내만 표시하고 사용자가 로그인 후 직접 다시 동작하게 한다

C) 방문자 로컬 상태로 저장하고 가입 시 일괄 병합한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 3
피드 필터와 정렬 상태를 어디까지 유지할까요?

A) URL query를 기준으로 뒤로가기·새로고침·공유 시 재현하고, 새 세션 기본값은 초기화한다

B) 현재 탭 메모리에만 유지하고 새로고침 시 초기화한다

C) 회원 프로필에 마지막 상태를 영구 저장한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 4
목록에서 작품 상세를 여는 기본 상호작용은 무엇인가요?

A) 독립 상세 라우트로 이동하며 뒤로가기로 목록 위치와 query 상태를 복원한다

B) 데스크톱 modal·모바일 전체 화면 sheet를 사용하고 URL은 바꾸지 않는다

C) 카드 안에서 상세 내용을 확장한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 5
검색 입력은 구조 검색과 자연어 검색을 어떻게 구분할까요?

A) 하나의 입력을 사용하고 서버 해석 결과·추출 조건을 표시해 사용자가 수정하게 한다

B) 제목·인물 검색과 자연어 검색을 별도 탭으로 분리한다

C) 검색은 구조 검색만 제공하고 자연어 입력은 추천 화면에서만 제공한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 6
추천 대화 결과와 조건 변경을 어떤 화면 모델로 제공할까요?

A) 대화 이력, 현재 적용 조건, 추천 카드 목록을 함께 표시하고 조건별 제거·초기화를 제공한다

B) 최근 요청과 결과만 표시하고 이전 대화는 별도 이력 화면에서 연다

C) 대화 없이 매 요청마다 새 추천 폼과 결과로 교체한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 7
추천 카드의 이유·요약·근거는 기본적으로 어떻게 노출할까요?

A) 짧은 요약과 추천 이유를 기본 표시하고 근거·메타데이터는 확장 영역에서 제공한다

B) 제목과 포스터만 기본 표시하고 모든 설명은 상세 화면에서 제공한다

C) 요약, 이유, 근거 필드를 모두 카드에 항상 표시한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 8
API 일부가 실패하거나 stale 상태일 때 화면 정책은 무엇인가요?

A) 성공한 영역은 유지하고 영향 범위에 stale/degraded 표시, 마지막 갱신 시각 및 국소 재시도를 제공한다

B) 하나의 핵심 API라도 실패하면 전체 화면 오류로 전환한다

C) 오류를 표시하지 않고 마지막 성공 데이터를 계속 보여준다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 9
언어 선택과 콘텐츠 번역 fallback은 어떻게 동작해야 하나요?

A) UI 언어는 즉시 전환하고, 콘텐츠는 선택 언어→원제/정의된 대체 언어 순으로 표시하며 fallback임을 표시한다

B) UI와 콘텐츠 번역이 모두 준비된 경우에만 언어를 전환한다

C) 브라우저 언어로만 자동 결정하고 수동 선택을 제공하지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 10
개인화 동의 철회 후 현재 화면 상태는 어떻게 처리할까요?

A) 개인화 결과·임시 개인화 상태를 즉시 제거하고 비개인화 feed/recommendation으로 전환한다

B) 현재 세션 결과는 유지하고 다음 로그인부터 비개인화한다

C) 현재 결과는 유지하되 경고 문구만 표시한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 11
OTT 외부 이동은 어떤 확인과 추적 규칙을 적용할까요?

A) 지원·검증된 링크만 활성화하고 외부 이동을 명시하며 동의 범위 내 이벤트를 기록한 후 새 탭으로 연다

B) 링크가 있으면 검증 상태와 무관하게 같은 탭으로 즉시 이동한다

C) 실제 이동 없이 OTT 이름과 이용 가능 여부만 표시한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 12
운영자 UI는 일반 사용자 UI와 어떤 경계로 제공할까요?

A) 별도 `/admin` 라우트와 layout을 사용하고 서버 권한 확인 실패 시 일반 화면으로 자동 노출하지 않는다

B) 일반 콘텐츠 상세 화면에 권한이 있을 때만 편집 control을 추가한다

C) 운영자 UI를 U01 초기 범위에서 제외한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Planned Artifacts

- `aidlc-docs/construction/u01-web-experience/functional-design/business-logic-model.md`
- `aidlc-docs/construction/u01-web-experience/functional-design/business-rules.md`
- `aidlc-docs/construction/u01-web-experience/functional-design/domain-entities.md`
- `aidlc-docs/construction/u01-web-experience/functional-design/frontend-components.md`

## Preliminary Extension Assessment

### Resiliency Baseline

- 부분 장애, stale 상태, 국소 재시도, 세션 복원과 외부 의존성 저하 표현에 직접 적용한다.
- 배포·백업·복원 소유권은 U07이며 U01은 사용자에게 필요한 상태와 복구 동작만 표시한다.

### Property-Based Testing

- query round-trip, 필터 순서 독립성, locale fallback, 접근성 ID 연결, 추천 조건 상태 전이, 동의 철회 후 개인화 상태 제거를 후보 속성으로 유지한다.
- 구체적 generator와 실행 예산은 NFR Requirements 및 Code Generation에서 확정한다.

### Security Baseline

- 비활성화로 N/A이다. 인증정보 비노출, 서버 권한의 최종성, 동의 범위 준수 및 민감 상태 비영속화는 핵심 요구사항으로 적용한다.
