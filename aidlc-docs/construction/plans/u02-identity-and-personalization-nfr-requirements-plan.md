# U02 Identity and Personalization NFR Requirements Plan

> **Single Source of Truth**: 이 파일은 U02 NFR Requirements의 계획, 사용자 결정과 체크박스 진행 상태를 관리한다. 답변과 모호성 검증 전에는 NFR 산출물을 생성하지 않는다.

## Inputs and Inherited Decisions

- [x] U02 Functional Design 3개 산출물과 BR-U02-001~051을 읽었다.
- [x] US-014~US-018, US-027과 U02의 U01·U05·U06 contract를 확인했다.
- [x] U07의 FastAPI, Pydantic, SQLAlchemy, Alembic, psycopg, PostgreSQL, pytest, Hypothesis와 Python 3.12.13 baseline을 상속한다.
- [x] U07의 Prototype SLO 99.0%, RTO 4시간, RPO 24시간, Backup and Restore DR를 상속한다.
- [x] GitHub Actions, 직접 배포, version-pinned rollback, 구조화 log·metric·health와 월별 dependency failure test·분기 restore drill을 상속한다.
- [x] Security Baseline extension은 disabled이나 core authentication, authorization, secret과 privacy requirement는 필수다.

## Execution Plan

### Step 1 — NFR Decision Collection

- [x] Question 1~15의 `[Answer]:`를 모두 채운다.
- [x] 선택지 유효성, 상호 모순, Functional Rule과 U07 inherited decision 충돌을 검사한다.
- [x] 모호성이 있으면 follow-up 질문을 추가하고 해소한다. 추가 질문은 필요하지 않았다.

### Step 2 — NFR Requirements

- [x] Workload criticality, capacity, latency, availability와 recovery requirement를 정의한다.
- [x] Authentication, session, encryption, privacy, retention과 data-rights requirement를 정의한다.
- [x] Reliability, observability, maintainability, testing과 U01 usability handoff를 정의한다.
- [x] `aidlc-docs/construction/u02-identity-and-personalization/nfr-requirements/nfr-requirements.md`를 생성한다.

### Step 3 — Tech Stack Decisions

- [x] Password hashing, session/token, encryption, OAuth와 job integration stack을 결정한다.
- [x] U07 stack과의 compatibility, rejected alternative와 deferred tuning을 기록한다.
- [x] pytest·Hypothesis PBT 적용과 dependency requirement를 기록한다.
- [x] `aidlc-docs/construction/u02-identity-and-personalization/nfr-requirements/tech-stack-decisions.md`를 생성한다.

### Step 4 — Compliance and Completion

- [x] U02-NFR ID와 verification matrix의 완전성을 검사한다.
- [x] RESILIENCY-01~15와 PBT-01~10의 적용·N/A·handoff를 평가한다.
- [x] Markdown parsing과 traceability를 검증한다.
- [x] NFR Requirements 완료 메시지를 기록하고 명시적 승인을 요청한다.

## NFR Requirements Questions

## Question 1
U02 하위 workload의 중요도를 어떻게 분류합니까?

A) 인증·권한·동의·삭제는 Critical, Profile·Library·Feature는 High로 분류한다.

B) 인증·권한은 Critical, 나머지는 Medium으로 분류한다.

C) Prototype 전체를 High로 동일 분류하고 상용 전환 때 세분화한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
정상 부하에서 U02 API의 초기 p95 latency 목표는 무엇입니까?

A) Login·권한 500ms, Profile·Library write 500ms, read·FeatureSnapshot 300ms, event 접수 200ms 이하로 한다. 외부 OAuth 시간은 별도 측정한다.

B) 모든 U02 API를 p95 1초 이하로 통일한다.

C) Login 1초, 나머지 API 500ms 이하로 한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
U02 용량 검증 기준은 무엇입니까?

A) U07과 같은 동시 사용자 10명을 검증하고 인증 burst 20 requests/second를 별도 시험한다.

B) 동시 사용자 50명과 인증 burst 50 requests/second를 초기부터 검증한다.

C) 기능 검증만 수행하고 용량 시험은 상용 전환까지 연기한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4
비밀번호 해싱 알고리즘 기준은 무엇입니까?

A) Argon2id를 기본으로 하고 parameter version을 저장하여 로그인 시 점진적으로 rehash한다.

B) bcrypt를 기본으로 하고 cost version을 저장한다.

C) 표준 library 추상화를 두고 Code Generation 시 최신 권고 알고리즘을 선택한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
웹 세션 전달과 저장 방식은 무엇입니까?

A) 불투명 session token은 Secure·HttpOnly·SameSite cookie로 전달하고 서버에는 hash와 상태만 저장한다.

B) 짧은 JWT access token과 server-side refresh session을 사용한다.

C) access와 refresh 모두 self-contained JWT로 사용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 6
세션 수명과 재인증 기준은 무엇입니까?

A) 30분 inactivity, 30일 absolute lifetime, 민감 작업은 10분 이내 fresh authentication을 요구한다.

B) 24시간 absolute session만 사용하고 민감 작업마다 비밀번호를 다시 확인한다.

C) 7일 inactivity, 90일 absolute lifetime, 민감 작업은 30분 이내 fresh authentication을 요구한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 7
이메일 verification과 password reset challenge의 유효시간은 무엇입니까?

A) 이메일 verification 24시간, password reset 30분으로 하고 single-use 처리한다.

B) 둘 다 1시간으로 통일한다.

C) 이메일 verification 7일, password reset 1시간으로 한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 8
저장 개인정보의 암호화 범위는 무엇입니까?

A) PostgreSQL volume encryption에 더해 이메일과 OAuth claim 같은 직접 식별 field를 application-level envelope encryption한다.

B) PostgreSQL volume·backup encryption만 사용하고 field-level encryption은 상용 전환 때 추가한다.

C) 모든 U02 field를 application-level encryption한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 9
초기 서비스 대상 지역과 개인정보 기준은 무엇입니까?

A) 대한민국 사용자를 우선 대상으로 하고 국내 법무 검토를 상용 전환 gate로 둔다.

B) 대한민국과 미국 사용자를 대상으로 하고 두 지역 요구를 설계 기준으로 둔다.

C) 대한민국과 EU 사용자를 대상으로 하며 GDPR 수준의 data-rights 기준을 초기부터 적용한다.

D) 국가 비종속의 엄격한 privacy baseline을 적용하되 출시 지역은 나중에 정한다.

E) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 10
개인화 행동 데이터의 기본 보존 기간은 얼마입니까?

A) 원본 행동 이벤트 180일, 집계 feature 365일이며 동의 철회·삭제가 먼저 발생하면 즉시 제거한다.

B) 원본 이벤트와 feature 모두 90일로 한다.

C) 원본 이벤트 30일, 집계 feature 365일로 한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 11
내보내기·삭제 작업의 사용자 대상 완료 목표는 무엇입니까?

A) Export 24시간 이내, 계정·개인화 삭제 72시간 이내 완료한다.

B) Export와 삭제 모두 24시간 이내 완료한다.

C) Export 72시간, 삭제 7일 이내 완료한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 12
암시적 행동 이벤트의 feature 반영 SLA는 무엇입니까?

A) 정상 상태에서 p95 5분 이내, 15분 초과 backlog에 경보를 발생시킨다.

B) 정상 상태에서 p95 1분 이내, 5분 초과 backlog에 경보를 발생시킨다.

C) 일 단위 batch로 반영한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 13
인증과 개인정보 운영 경보 기준은 무엇입니까?

A) 인증 실패율 급증, rate-limit 증가, OAuth 오류, consent fail-closed, deletion SLA 위험과 export 실패를 모두 경보 대상으로 한다.

B) 로그인과 OAuth 오류만 경보 대상으로 하고 개인정보 job은 dashboard에서 수동 확인한다.

C) U07 공통 API error alert만 사용하고 U02 전용 경보를 두지 않는다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 14
U02 핵심 Business Rule의 test quality gate는 무엇입니까?

A) 전체 line coverage 80% 이상, BR-U02-001~051 핵심 branch 100%, example test와 11개 PBT 후보를 함께 요구한다.

B) 전체 line coverage 80%만 요구하고 branch·PBT 목표는 권고로 둔다.

C) 전체 line coverage 90% 이상을 요구하고 PBT는 상태 전이에만 적용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 15
인증·개인정보 NFR 변경의 운영 승인 방식은 무엇입니까?

A) U07의 경량 change record를 사용하되 schema, consent notice, encryption 또는 session 정책 변경에는 privacy/security review checklist를 추가한다.

B) U07의 일반 change record만 사용한다.

C) 모든 U02 변경에 별도 수동 승인과 유지보수 시간을 요구한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Planned Outputs

- `aidlc-docs/construction/u02-identity-and-personalization/nfr-requirements/nfr-requirements.md`
- `aidlc-docs/construction/u02-identity-and-personalization/nfr-requirements/tech-stack-decisions.md`

## Extension Planning Status

- **RESILIENCY-01~15**: U07 공통 결정은 상속하고 U02 criticality, feature backlog, privacy job과 dependency failure 지표를 구체화한다.
- **PBT-01**: Functional Design의 PBT-U02-01~11을 formal property inventory로 사용한다.
- **PBT-09**: pytest와 Hypothesis를 상속한다. Code Generation에서 dependency·seed·shrinking을 검증한다.
- **Security Baseline**: disabled이므로 extension으로는 N/A. U02 core NFR은 질문 4~11과 13~15에서 별도로 강화한다.
- **Frontend**: U02는 UI를 소유하지 않는다. session cookie contract, consent notice data와 accessibility 상태를 U01에 전달한다.
