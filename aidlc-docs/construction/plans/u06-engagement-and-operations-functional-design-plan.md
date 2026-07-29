# U06 Engagement and Operations Functional Design Plan

> **Single Source of Truth**: 이 파일은 U06 Functional Design의 계획, 사용자 결정 및 완료 체크박스를 관리한다. 모든 답변이 유효하고 모호하지 않을 때까지 최종 설계 산출물을 생성하지 않는다.

## Unit Context

- **Goal**: 승인된 콘텐츠 이벤트에 대한 사용자 알림, 권한 기반 콘텐츠 운영 변경, 비식별 추천 추적 조회, 상태·경보·Incident 대응 흐름을 제공한다.
- **Owned Components**: C13 Notification, C14 Admin and Operations.
- **Owned Services**: S08 NotificationService, S09 AdminContentService, S10 OperationsService.
- **Primary Stories**: US-019, US-021, US-023, US-025.
- **Supporting Stories**: US-020, US-022, US-024, US-026, US-027, US-028.
- **Required Dependencies**: U02 역할·알림 설정·비식별 주체 참조, U03 승인 콘텐츠·운영 변경 Port, U04 검증·격리 상태, U05 RecommendationTracePort, U07 관측·작업·백업·배포 상태 Contract.
- **Owned Data**: notification preferences/jobs/deliveries, admin overrides, audit events, incident records.
- **Hard Boundary**: U06은 알림 전달과 운영 조정을 담당하지만 콘텐츠 승인, 추천 순위, Metadata 검증, 배포·백업 실행을 우회하지 않는다.
- **Frontend Ownership**: U06은 UI를 소유하지 않는다. U01이 U06 API Contract를 사용해 알림 설정과 운영 화면을 구성한다.
- **Enabled Extensions**: Resiliency Baseline (Full), Property-Based Testing (Full).
- **Disabled Extension**: Security Baseline. 단, 역할 검증, 감사 불변성, 비식별 추적, 최소정보 노출은 핵심 요구사항으로 유지한다.

## Execution Plan

### Step 1 - Context and Traceability

- [x] U06 단위 정의, 구성요소, 서비스, 데이터 소유권과 Primary/Supporting Story Map을 확인한다.
- [x] US-019, US-021, US-023, US-025와 FR-028~032, FR-042, DR-008의 인수 경계를 확인한다.
- [x] U02~U05와 U07의 현재 공개 Contract 및 U06 소비 경계를 확인한다.
- [x] U06이 콘텐츠 승인, 추천 결정, 검증 규칙 변경, 배포·백업 실행을 소유하지 않음을 확인한다.

### Step 2 - Planning and Questions

- [x] 알림, 운영 Override, 감사, 추적 조회, 경보와 Incident 흐름에 영향을 주는 미결 비즈니스 결정을 식별한다.
- [x] 상호 배타적 선택지와 마지막 `X) Other` 선택지를 포함한 Question 1~12를 작성한다.
- [ ] 모든 `[Answer]:` 값을 수집하고 제공된 선택지와 일치하는지 검증한다.
- [ ] 답변 간 모순과 모호성을 분석하고 필요한 경우 별도 clarification 파일을 작성한다.

### Step 3 - Business Logic Model

- [ ] 승인 이벤트부터 대상 선정, 중복 제거, 예약, 전달, 재시도, 취소까지 알림 흐름을 설계한다.
- [ ] 권한 검증, 충돌 확인, Override 적용, U03 반영, 감사 기록과 종료까지 운영 변경 흐름을 설계한다.
- [ ] U05 비식별 Trace 조회와 U07 Health·Metrics·Alert를 Incident로 연결하는 흐름을 설계한다.
- [ ] Primary Story와 Supporting Contract traceability를 포함한 `business-logic-model.md`를 생성한다.

### Step 4 - Domain Entities

- [ ] Notification Preference, Interest Subscription, Notification Event, Job, Delivery Attempt와 상태 전이를 정의한다.
- [ ] Admin Override, Audit Event, Trace Query, Health Snapshot, Alert Signal, Incident와 관계를 정의한다.
- [ ] 식별자, 불변 버전, 소유권, 보존 경계와 외부 참조를 정의한다.
- [ ] `domain-entities.md`를 생성한다.

### Step 5 - Business Rules and Testable Properties

- [ ] 알림 적격성, 중복 방지, 취소, 빈도 제한, 재시도 및 실패 격리 규칙을 정의한다.
- [ ] 역할 분리, Override 우선순위·만료·충돌, 감사 불변성과 Trace 최소화 규칙을 정의한다.
- [ ] Health 집계, 경보 상관관계, Incident 상태 전이·에스컬레이션·종료 규칙을 정의한다.
- [ ] PBT-01에 따라 round-trip, invariant, idempotence, commutativity, oracle, stateful, easy-verification 속성을 분류하고 `business-rules.md`를 생성한다.

### Step 6 - Validation and Completion

- [ ] Story/FR/DR/NFR traceability와 U02~U05/U07 Contract 정합성을 검증한다.
- [ ] RESILIENCY-01~15와 PBT-01의 적용 여부 및 준수 근거를 검증한다.
- [ ] Markdown 문법, 특수문자, 표와 코드 표기 호환성을 검증한다.
- [ ] 계획·상태·감사 기록을 갱신하고 표준 Functional Design 승인 지점을 제시한다.

## Functional Design Questions

각 `[Answer]:` 뒤에 선택한 문자 하나를 입력한다. 적합한 정책이 없으면 `X`를 선택하고 원하는 내용을 함께 작성한다.

## Question 1
어떤 이벤트가 관심 콘텐츠 알림을 생성할 수 있어야 합니까?

A) U03의 승인된 공개·공개예정·가용성 변경 이벤트만 허용하고 격리·만료·미승인 콘텐츠는 차단한다

B) U03 승인 이벤트와 U04 격리 이벤트를 모두 허용하되 상태를 알림에 표시한다

C) 공급자 원본 이벤트를 즉시 알림으로 보내고 이후 검증 결과로 정정한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 2
프로토타입에서 지원할 사용자 알림 채널 범위는 무엇입니까?

A) 인앱 알림과 이메일을 지원하고 사용자가 유형별·채널별로 각각 켜거나 끈다

B) 이메일만 지원하고 전체 알림을 하나의 설정으로 켜거나 끈다

C) 인앱 알림만 지원하며 외부 채널은 상용 전환 때 추가한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 3
동일 작품·이벤트가 반복 수신될 때 중복 알림과 예약 알림을 어떻게 처리해야 합니까?

A) 사용자·작품·이벤트 유형·공개 시각 기준의 안정된 중복 키를 사용하고, 설정 해제나 승인 상태 철회 시 미전송 Job을 취소한다

B) 공급자 이벤트 ID가 다르면 모두 별도 알림으로 전달한다

C) 하루 단위로 모든 알림을 하나의 요약 알림으로만 합친다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 4
알림 전달 실패의 재시도와 사용자 영향은 어떻게 격리해야 합니까?

A) 채널별 제한된 재시도와 만료 시각을 적용하고 최종 실패를 기록하되 Feed·Search·Recommendation 요청은 실패시키지 않는다

B) 성공할 때까지 무기한 재시도하고 다른 알림도 동일 순서로 대기시킨다

C) 첫 전달 실패 즉시 Job을 삭제하고 별도 실패 기록을 남기지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 5
운영자가 변경할 수 있는 콘텐츠 범위와 적용 방식은 무엇입니까?

A) 허용된 설명·가용성 보정·노출 상태만 버전 조건부 Command로 U03/U04 Port에 요청하며 승인·검증 규칙 자체는 우회하지 않는다

B) U06이 U03/U04 테이블을 직접 수정하고 사후 감사만 남긴다

C) 운영자는 노출 상태만 변경할 수 있고 콘텐츠 필드 보정은 허용하지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 6
자동 수집 값과 운영자 Override가 충돌할 때 우선순위와 수명은 어떻게 관리해야 합니까?

A) 활성 Override가 지정 필드에만 우선하며 이유·작성자·시작·만료·기준 버전을 가진다. 만료 후 최신 승인 자동 값으로 복귀하고 충돌은 운영자에게 표시한다

B) 운영자 값은 영구적으로 우선하며 자동 값과의 충돌을 다시 평가하지 않는다

C) 최신 변경 시각만 비교해 자동 값과 운영자 값 중 더 최근 값을 사용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 7
운영 변경의 역할 분리와 승인 수준은 어떻게 해야 합니까?

A) 조회 역할과 변경 역할을 분리하고, 노출 중지·복구 같은 고영향 Command는 명시적 이유와 최신 버전 확인을 요구하며 모든 결과를 감사한다

B) 단일 운영자 역할이 조회와 모든 변경을 수행하고 이유 입력은 선택 사항으로 둔다

C) 모든 변경에 두 명의 운영자 승인을 필수로 한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 8
감사 기록은 어떤 내용을 보존하고 어떤 내용을 제외해야 합니까?

A) 행위자 역할·비식별 참조, Command, 대상, 이유, 상관관계 ID, 전후 버전·허용된 필드, 결과를 불변 기록하고 비밀정보·직접 식별자·원문 Prompt는 제외한다

B) 문제 재현을 위해 요청·응답 본문과 사용자 프로필을 모두 보존한다

C) 변경자와 시각만 기록하고 전후 값과 결과는 보존하지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 9
US-023 추천 Trace 조회에서 운영자에게 공개할 범위는 무엇입니까?

A) 허용된 Trace ID로 버전·후보 수·필터·점수 구성·검증 코드·대체 경로를 조회하되 직접 식별자, 원문 입력, AI 응답과 내부 추론은 공개하지 않는다

B) 재현성을 위해 원문 요청과 전체 AI Provider 응답까지 공개한다

C) 최종 콘텐츠 ID와 성공·실패 여부만 공개한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 10
여러 Unit의 상태를 U06 운영 상태로 어떻게 집계해야 합니까?

A) process liveness와 필수 의존성 readiness를 분리하고, 비필수 의존성 실패는 degraded로 표시하며 근거·측정 시각·신선도와 함께 집계한다

B) 하나의 의존성이라도 실패하면 전체 시스템을 unhealthy로 표시한다

C) 프로세스 실행 여부만 확인하고 하위 의존성 상태는 표시하지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 11
경보를 Incident로 승격하고 중복을 억제하는 정책은 무엇입니까?

A) 서비스·증상·영향 범위의 상관관계 키로 반복 경보를 묶고 지속 시간·심각도 기준 충족 시 Incident를 생성하거나 갱신한다

B) 모든 개별 경보마다 새로운 Incident를 생성한다

C) Incident는 운영자가 수동으로만 생성하며 경보와 연결하지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 12
Incident의 표준 수명주기와 사후 조치는 무엇입니까?

A) detected, acknowledged, mitigating, monitoring, resolved 상태를 사용하고 소유자·영향·조치·복구 증거를 기록하며 해결 후 경량 COE와 후속 작업을 연결한다

B) open과 closed 두 상태만 사용하고 세부 대응 기록은 외부 메모에 남긴다

C) 경보가 정상화되면 검토 없이 Incident를 자동 삭제한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Planned Artifacts

- `aidlc-docs/construction/u06-engagement-and-operations/functional-design/business-logic-model.md`
- `aidlc-docs/construction/u06-engagement-and-operations/functional-design/business-rules.md`
- `aidlc-docs/construction/u06-engagement-and-operations/functional-design/domain-entities.md`

U06은 사용자 인터페이스를 소유하지 않으므로 `frontend-components.md`는 N/A다. U01이 이후 U06의 알림 설정, 운영, Trace와 Incident API Contract를 소비한다.

## Preliminary Extension Assessment

### Resiliency Baseline

- RESILIENCY-01, 05~07, 10, 15는 알림 격리, 상태 집계, 경보와 Incident 흐름에 직접 적용한다.
- RESILIENCY-02~04와 11~14는 승인된 U07 복구·배포 결정의 상태를 조회하고 Incident에 참조하는 Supporting Contract로 유지한다.
- RESILIENCY-08~09는 승인된 단일 서버·고정 용량 프로토타입 예외이며 상용 전환 전에 재평가한다.

### Property-Based Testing

- PBT-01 후보는 알림 중복 제거·취소의 멱등성, Preference 직렬화 round-trip, Override 필드 격리와 만료 불변식, 감사 추가 전용성, Trace 비식별성, Health 집계 oracle, 경보 상관관계의 순서 독립성, Incident 상태 머신이다.
- PBT-02~10 구현 책임은 승인된 속성 목록을 NFR Requirements와 Code Generation에 전달해 수행한다.

### Security Baseline

- 확장은 비활성화되어 N/A다. 핵심 역할 검증, 감사 불변성, 개인정보 최소화, 비밀정보와 AI 내부 내용 비노출은 일반 요구사항으로 강제한다.
