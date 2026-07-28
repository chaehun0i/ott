# U02 Identity and Personalization NFR Design Plan

> **Single Source of Truth**: 이 파일은 U02 NFR Design의 결정, 질문 답변 및 실행 체크박스를 관리한다. 모든 필수 답변을 검증하기 전에는 설계 산출물을 생성하지 않는다.

## Inputs and Inherited Decisions

- [x] U02 Functional Design의 BR-U02-001~051 및 PBT-U02-01~11을 확인했다.
- [x] U02-NFR-001~068과 기술 스택 결정을 확인했다.
- [x] U07의 PostgreSQL, outbox worker, 구조화 로그·메트릭·health, 복구 및 배포 기준을 상속했다.
- [x] 활성화된 Resiliency Baseline 및 Property-Based Testing 규칙을 설계 입력으로 반영했다.
- [x] Security Baseline 확장은 비활성 상태임을 확인했으며, 인증·인가·개인정보 보호의 core 요구사항은 계속 적용한다.

## Category Assessment

| Category | Assessment | Design Focus |
|---|---|---|
| Resilience patterns | Required | 외부 OAuth 장애 격리, 작업 우선순위, 재시도·멱등성, 삭제 SLA 보호 |
| Scalability patterns | Required | stateless API, PostgreSQL 연결 예산, worker lane과 사용자 단위 순서 보장 |
| Performance patterns | Required | Argon2 자원 격리, 인덱스, 제한적 캐시, latency budget 보호 |
| Security patterns | Required | opaque session, CSRF, 암호화 키 계층, blind index, export 보호 |
| Logical components | Required | port·adapter 경계, 정책 서비스, 저장소, job handler, 관측 구성요소 |

## Execution Plan

### Step 1 - NFR Design Decision Collection

- [x] Question 1~14의 `[Answer]:`를 모두 채운다.
- [x] 선택지 유효성, 상호 모순, U02 NFR 및 U07 상속 결정과의 충돌을 검증한다.
- [x] 모호성이 있으면 follow-up 질문을 추가하고 해결한다. 모호성이 없어 추가 질문은 필요하지 않았다.

### Step 2 - NFR Design Patterns

- [x] resilience, scalability, performance 및 security pattern을 요구사항 ID와 연결한다.
- [x] timeout, retry, circuit breaker, bulkhead, idempotency, concurrency 및 degradation 동작을 정의한다.
- [x] 암호화 키 회전, session/CSRF, export artifact 및 개인정보 삭제 보호 설계를 정의한다.
- [x] `aidlc-docs/construction/u02-identity-and-personalization/nfr-design/nfr-design-patterns.md`를 생성한다.

### Step 3 - Logical Components

- [x] API, application service, domain policy, repository, cryptography, identity provider 및 worker 경계를 정의한다.
- [x] 동기·비동기 호출, 데이터 소유권, 오류 전파와 관측 책임을 명시한다.
- [x] U01, U05, U06 및 U07 contract 연결을 표시한다.
- [x] `aidlc-docs/construction/u02-identity-and-personalization/nfr-design/logical-components.md`를 생성한다.

### Step 4 - Validation and Completion

- [x] U02-NFR-001~068과 설계 패턴·논리 구성요소 간 traceability를 검증한다.
- [x] RESILIENCY-01~15와 PBT-01~10의 적용·N/A·후속 단계 처리를 검증한다.
- [x] Mermaid를 사용하지 않았으며 Markdown parsing compatibility를 확인한다.
- [x] NFR Design 완료 메시지를 기록하고 표준 2개 선택지로 명시적 승인을 요청한다.

## NFR Design Questions

## Question 1
Argon2id의 초기 자원 프로파일과 API process별 동시 실행 제한을 어떻게 설계할까요?

A) 실제 배포 host benchmark로 단일 hash p95 300ms 이하를 맞추되 memory 64 MiB 이상을 보장하고, 별도 bounded executor에서 process당 최대 2개만 동시에 실행한다.

B) benchmark 없이 memory 64 MiB, time cost 3, parallelism 1로 고정하고 동시 실행 제한을 두지 않는다.

C) memory 128 MiB, time cost 2, parallelism 1로 고정하고 process당 최대 1개만 실행한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 2
브라우저 session cookie와 CSRF 방어 조합은 무엇으로 할까요?

A) Secure·HttpOnly·SameSite=Lax cookie, signed double-submit CSRF token, Origin/Referer 검증을 함께 적용하고 state-changing 요청에 모두 요구한다.

B) SameSite=Strict cookie와 Origin 검증만 사용한다.

C) SameSite=Lax cookie와 CSRF token만 사용하고 Origin/Referer는 검증하지 않는다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 3
불투명 session token의 생성·저장·회전 패턴은 무엇으로 할까요?

A) CSPRNG 256-bit token을 발급하고 server에는 별도 pepper를 사용한 HMAC-SHA-256 값만 저장하며, 로그인·권한 변경·fresh authentication 후 token을 회전한다.

B) CSPRNG 128-bit token을 발급하고 단순 SHA-256 hash만 저장하며 로그인 때만 회전한다.

C) CSPRNG 256-bit token을 발급하고 단순 SHA-256 hash만 저장하며 만료 전에는 회전하지 않는다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 4
직접 식별자 field encryption과 검색용 blind index의 키 계층은 어떻게 구성할까요?

A) versioned KEK가 record별 DEK를 감싸고 DEK로 AES-256-GCM 암호화하며, blind index에는 암호화 키와 분리된 versioned HMAC key를 사용한다.

B) table별 단일 DEK로 모든 record를 AES-256-GCM 암호화하고 같은 key에서 blind index key를 파생한다.

C) application 전체에 단일 AES key를 사용하고 blind index도 동일 key로 생성한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 5
암호화 키 회전과 기존 데이터 재암호화는 어떤 패턴으로 처리할까요?

A) dual-read/new-write를 적용하고 500건 단위의 멱등 outbox job으로 재암호화하며, checkpoint·pause/resume·실패 격리를 지원한다.

B) maintenance window에서 전체 table을 한 번에 재암호화한다.

C) 새 key로 쓰고 기존 record는 읽힐 때만 lazy re-encryption한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 6
U02가 공유 PostgreSQL 연결 예산을 사용하는 방식은 무엇으로 할까요?

A) API와 worker에 별도 pool budget을 두고 U07 전체 연결 상한 안에서 시작값을 API 10·worker 5로 제한하며, timeout과 saturation metric으로 조정한다.

B) API와 worker가 하나의 pool을 공유하고 기본 크기 20으로 시작한다.

C) 연결 상한 없이 요청량에 따라 각 process가 독립적으로 pool을 확장한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 7
동시 수정 충돌과 주요 조회의 PostgreSQL index 패턴은 무엇으로 할까요?

A) aggregate에 version column을 둔 optimistic concurrency를 사용하고, email blind index·OAuth provider subject·session hash·활성 consent·library user/content lookup에 unique 또는 partial composite index를 둔다.

B) 모든 쓰기에서 pessimistic row lock을 사용하고 기본 key index 외에는 부하 시험 후 추가한다.

C) last-write-wins를 사용하고 자주 조회되는 field마다 단일-column index를 둔다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 8
개인정보 관련 background job의 우선순위와 bulkhead는 어떻게 구성할까요?

A) 삭제·동의 철회 high-priority lane, feature 갱신 normal lane, export·재암호화 low-priority lane을 분리하고 각 lane에 독립 concurrency·retry budget을 둔다.

B) 모든 job을 하나의 FIFO queue와 동일 retry policy로 처리한다.

C) 삭제·동의 철회만 별도 queue로 두고 나머지는 하나의 shared lane에서 처리한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 9
Google OAuth/OIDC 의존성의 timeout·retry·circuit breaker 패턴은 무엇으로 할까요?

A) connect 3초·overall 10초 timeout을 적용하고 사용자 callback 교환은 자동 재시도하지 않으며, discovery/JWKS 조회만 bounded retry·circuit breaker·검증된 cache를 사용한다.

B) token 교환을 포함한 모든 호출을 최대 2회 자동 재시도하고 circuit breaker를 사용한다.

C) 공통 30초 timeout만 적용하고 retry와 circuit breaker는 사용하지 않는다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 10
개인정보 export artifact의 보호와 만료 정책은 무엇으로 할까요?

A) artifact를 별도 key로 암호화하고 24시간 후 만료하며, fresh authentication 뒤 1회만 다운로드할 수 있는 signed reference를 제공한다.

B) artifact를 7일간 보관하고 최대 3회 다운로드를 허용한다.

C) artifact를 72시간 보관하고 만료 전 다운로드 횟수를 제한하지 않는다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 11
명시적·암시적 행동 event와 FeatureSnapshot의 순서 및 정합성을 어떻게 보장할까요?

A) 사용자별 monotonic feature version과 compare-and-swap을 사용하고, 오래된 event가 최신 상태를 되돌리지 못하게 하며 replay 가능한 집계 ledger를 유지한다.

B) worker 도착 순서대로 적용하고 최신 update timestamp만 기록한다.

C) 사용자별 distributed lock으로 모든 event를 직렬 처리한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 12
초기 U02 cache 전략은 무엇으로 할까요?

A) 외부 cache는 도입하지 않고 request-local cache를 기본으로 하며, session·role만 auth-version 기반 process-local 30초 cache를 허용하고 consent·deletion state는 cross-request cache하지 않는다.

B) Redis를 즉시 도입해 session, role, consent 및 FeatureSnapshot을 모두 cache한다.

C) cache를 전혀 사용하지 않고 모든 검증을 매 요청 PostgreSQL에서 조회한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:C

## Question 13
초기 확장 구조와 scale-out trigger는 어떻게 설계할까요?

A) stateless API와 job-type/user-key partition 가능한 worker를 유지하고 PostgreSQL 중심으로 시작하며, latency·pool saturation·backlog threshold가 지속될 때 replica 또는 worker를 증설한다.

B) 단일 API process와 단일 worker를 유지하고 vertical scaling만 사용한다.

C) 초기부터 별도 identity microservice와 Redis broker cluster로 분리한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 14
U02 resilience 설계의 필수 failure-injection 검증 범위는 무엇으로 할까요?

A) Google OAuth 장애·지연, PostgreSQL consent read 실패, session 저장 실패, feature backlog, 삭제 job retry exhaustion, key rotation 중단·재개를 자동화된 component/integration test로 검증한다.

B) Google OAuth 장애와 PostgreSQL 연결 실패만 자동화하고 나머지는 운영 runbook으로 검증한다.

C) 기능 test만 수행하고 failure injection은 운영 전 수동 점검으로 대체한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Planned Outputs

- `aidlc-docs/construction/u02-identity-and-personalization/nfr-design/nfr-design-patterns.md`
- `aidlc-docs/construction/u02-identity-and-personalization/nfr-design/logical-components.md`

## Extension Planning Status

- **RESILIENCY-01~15**: OAuth dependency, PostgreSQL, worker lane, deletion SLA, recovery and failure-injection 설계로 구체화한다.
- **PBT-01~10**: PBT-U02-01~11의 invariant와 generator 경계는 logical component 및 Code Generation handoff에 보존한다.
- **Security Baseline**: extension은 disabled이므로 N/A이며, U02 core security/privacy 요구사항은 Question 1~12에서 독립적으로 설계한다.
