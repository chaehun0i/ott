# U02 Logical Components

## Component Model

U02는 domain과 application core가 framework, database, cryptography 및 provider SDK를 직접 의존하지 않는 port-and-adapter 구조를 사용한다. API는 stateless이고 PostgreSQL이 authoritative state를 소유한다. U07은 runtime, transaction, outbox, worker lease와 telemetry 기반을 제공한다.

## Logical Component Inventory

| ID | Component | Responsibility | Owned State | Key Dependencies |
|---|---|---|---|---|
| LC-U02-01 | Identity API Adapter | registration, login, OAuth callback, session·role command의 HTTP/OpenAPI 변환 | 없음 | LC-02, LC-03, U07 request context |
| LC-U02-02 | Identity Application Service | identity use case orchestration, transaction, idempotency, outbox handoff | 없음 | LC-05~10, LC-17 |
| LC-U02-03 | Session and Authorization Service | session 발급·회전·폐기, fresh-auth, current role policy 평가 | policy version | LC-05, LC-07, LC-09 |
| LC-U02-04 | Profile and Library Service | genre·OTT·save·rating·history mutation과 authoritative feature handoff | 없음 | LC-11, LC-12, LC-17, U03 |
| LC-U02-05 | Identity Repository | User, Credential, OAuthLink, RoleAssignment aggregate persistence | PostgreSQL rows | LC-16, U07 database |
| LC-U02-06 | Credential Hasher Adapter | Argon2id hash, verify, needs-rehash, bounded execution | parameter policy | Argon2 library, LC-15 |
| LC-U02-07 | Session Repository | HMAC lookup, expiry, revocation, authorization-version 검증 | Session rows | LC-09, U07 database |
| LC-U02-08 | Google Identity Adapter | OAuth/OIDC validation과 provider dependency isolation | validated discovery/JWKS cache만 | Google, HTTP client, LC-15 |
| LC-U02-09 | Secret and Cryptography Adapter | session HMAC, DEK/KEK wrapping, AES-GCM, blind index, key version | key handle/config only | secret provider, crypto library |
| LC-U02-10 | Challenge Service | email verification/reset purpose-bound single-use challenge | challenge rows | LC-05, LC-09, email port |
| LC-U02-11 | Profile Repository | UserProfile와 explicit preference persistence | PostgreSQL rows | U07 database |
| LC-U02-12 | Library Repository | WatchItem, Rating, WatchHistory persistence | PostgreSQL rows | U07 database |
| LC-U02-13 | Consent Policy Service | current decision, fail-closed eligibility, guest-link authorization | policy semantics | LC-14 |
| LC-U02-14 | Consent Repository | immutable ledger와 current projection persistence | PostgreSQL rows | U07 database |
| LC-U02-15 | Resource Limiters | Argon2 executor, provider circuit, request deadline, lane semaphore | in-process bounded state | U07 metrics/config |
| LC-U02-16 | Unit of Work | optimistic concurrency, transaction, isolation과 commit/rollback | transaction context | SQLAlchemy/psycopg |
| LC-U02-17 | Outbox Publisher | domain effect와 job payload의 atomic persistence | outbox rows | U07 outbox registry |
| LC-U02-18 | Feedback Intake Service | consent 확인, schema·content·dedup 검증, durable acceptance | 없음 | LC-13~14, LC-19, U03, LC-17 |
| LC-U02-19 | Behavior Event Repository | event와 idempotency/fingerprint persistence | PostgreSQL rows | U07 database |
| LC-U02-20 | Feature Projection Worker | explicit recompute, implicit aggregation, CAS/version/ledger 처리 | feature rows, contribution ledger | LC-14, LC-19, LC-21, U07 worker |
| LC-U02-21 | Feature Repository | feature set, snapshot eligibility와 version persistence | PostgreSQL rows | U07 database |
| LC-U02-22 | Feature Snapshot Service | consent-bound allow-list와 request pseudonym 생성 | request scope only | LC-13~14, LC-21, LC-09, U05 |
| LC-U02-23 | Data Rights Service | export/deletion authorization, lifecycle와 closure orchestration | request/step rows | LC-24~26, LC-17 |
| LC-U02-24 | Export Worker | encrypted artifact 생성, expiry, single-download 상태 | artifact metadata | LC-05, LC-11~14, LC-19, LC-21, LC-09 |
| LC-U02-25 | Deletion Worker | category별 idempotent 삭제와 terminal closure | deletion progress | 모든 U02 repository, U07 worker |
| LC-U02-26 | Key Rotation Worker | 500-row checkpointed re-encryption과 blind-index 전환 | rotation progress | LC-09, U02 repositories, U07 worker |
| LC-U02-27 | Telemetry and Safe Audit Adapter | redacted log, metric, trace, alert와 U06 audit event | bounded operational metadata | U07 telemetry, U06 audit |
| LC-U02-28 | Health Contributor | U02 readiness와 protected deep health 구성 | 없음 | database, LC-08, worker metrics |

## Dependency Rules

1. API adapter는 domain entity나 persistence model을 직접 반환하지 않고 versioned DTO와 safe error code만 반환한다.
2. application service는 repository, cryptography, provider, email, outbox 및 telemetry port에만 의존한다.
3. repository adapter가 SQLAlchemy model과 PostgreSQL query를 소유하며 domain layer에 ORM type을 노출하지 않는다.
4. Google SDK/HTTP type, Argon2 type 및 cryptography object는 각 adapter 경계를 넘지 않는다.
5. U02는 U03 content를 참조만 하고, U05에는 pseudonymous FeatureSnapshot만 제공하며, U06에는 최소 audit fact만 전송한다.
6. U07이 transaction, outbox row, worker lease와 telemetry transport를 소유하고 U02는 business payload와 outcome을 소유한다.
7. cross-request application cache는 없다. request-local 중복 조회 제거도 동일 transaction snapshot 안에서만 허용한다.

## Interaction Sequences

### Email Login and Session Authorization

1. LC-01이 request schema와 generic error contract를 검증한다.
2. LC-02가 LC-05에서 email blind index로 credential envelope를 조회한다.
3. LC-06이 LC-15 bounded executor에서 Argon2id를 검증한다.
4. 성공하면 LC-03이 LC-09로 256-bit token과 peppered HMAC lookup을 만들고 LC-07에 session을 저장한다.
5. state-changing 후속 요청은 LC-01에서 CSRF와 origin을 확인하고 LC-03이 매 요청 LC-07·LC-05의 current session/role/version을 검증한다.
6. LC-27은 safe outcome과 saturation만 기록한다.

**Failure behavior**: hash executor 포화는 bounded response가 되고 session insert가 commit되지 않으면 token 성공 응답을 보내지 않는다. account 존재 여부는 동일한 외부 오류로 감춘다.

### Google OAuth Login

1. LC-01과 LC-08이 state, nonce, callback binding을 확인한다.
2. LC-08은 LC-15의 provider timeout/circuit policy 아래 code exchange와 token validation을 수행한다.
3. LC-02는 provider subject blind index로 기존 OAuthLink를 조회한다.
4. 자동 email 병합 없이 기존 link만 인증하거나 fresh-authenticated explicit link command를 처리한다.
5. session 발급은 email login과 동일한 LC-03·LC-07·LC-09 경로를 사용한다.

**Failure behavior**: callback exchange를 자동 재시도하지 않는다. discovery/JWKS만 bounded retry가 가능하며 Google 장애가 email login 또는 기존 session 경로로 전파되지 않는다.

### Consent-Gated Feedback and Feature Update

1. LC-18이 인증 subject, typed event, U03 ContentId와 idempotency를 검증한다.
2. LC-13이 LC-14의 current ConsentDecision을 같은 요청에서 읽는다.
3. 미동의, 철회, 조회 실패 또는 deletion pending이면 durable event를 생성하지 않는다.
4. explicit mutation은 LC-04와 repository update, feature recompute 및 LC-17 outbox를 한 LC-16 transaction에서 처리한다.
5. implicit event는 LC-19와 LC-17에 원자적으로 저장한 뒤 LC-20이 normal lane에서 처리한다.
6. LC-20은 contribution ledger와 expected FeatureVersion으로 CAS하고 중복·역행 event를 무시한다.

**Failure behavior**: durable commit 전에는 acceptance를 반환하지 않는다. backlog가 15분을 넘으면 LC-27이 alert하며 ConsentVersion이 stale한 snapshot은 반환하지 않는다.

### FeatureSnapshot for U05

1. LC-22가 internal caller와 purpose를 검증한다.
2. LC-13이 current consent를 PostgreSQL에서 읽고 LC-21의 feature ConsentVersion과 비교한다.
3. eligible할 때만 LC-09가 request-scoped pseudonym을 만들고 allow-listed feature를 반환한다.
4. request context가 끝나면 pseudonym mapping을 폐기한다.

**Failure behavior**: consent가 없거나 읽기 실패·version 불일치·삭제 진행 중이면 non-personalized context를 반환하며 stale feature를 fallback하지 않는다.

### Account Deletion

1. LC-23이 fresh authentication 10분, idempotency와 owner를 확인한다.
2. LC-16 transaction에서 user를 `deletion_pending`으로 바꾸고 LC-07의 모든 session을 revoke하며 high-lane outbox job을 기록한다.
3. LC-25가 category별 DeletionStep을 idempotently 수행한다.
4. 모든 repository와 artifact에 closure query를 실행한 뒤에만 `deleted` terminal state로 바꾼다.
5. LC-27은 값이 아닌 category status와 SLA risk만 기록한다.

**Failure behavior**: retry exhaustion 뒤에도 account는 disabled이며 Critical alert와 retryable progress를 유지한다.

### Export and One-Time Download

1. LC-23이 fresh authentication과 request idempotency를 검증하고 low-lane export job을 만든다.
2. LC-24가 transactionally consistent 범위의 eligible data를 수집하고 LC-09의 artifact-specific key로 암호화한다.
3. artifact metadata에는 expiry와 consumed state만 저장한다.
4. download 시 LC-23이 fresh authentication을 다시 확인하고 atomic compare-and-set으로 미사용 reference를 소비한다.
5. 성공 download 또는 24시간 만료 뒤 encrypted artifact를 삭제한다.

### Key Rotation

1. LC-26이 from/to key version과 checkpoint를 가진 low-lane job을 claim한다.
2. 각 500-row batch에서 LC-09가 authenticated decrypt와 새 DEK encryption을 수행한다.
3. repository가 optimistic condition으로 ciphertext와 version을 갱신하고 checkpoint를 commit한다.
4. 중단 시 마지막 checkpoint부터 재개하며 완료 전에는 dual-read를 유지한다.
5. old-version count 0과 검증 표본 성공 뒤 이전 key retirement 승인을 요청한다.

## Data Ownership and Transaction Boundaries

| Boundary | Atomic Contents | Asynchronous Handoff |
|---|---|---|
| Identity | user/credential/link/role/session mutation and audit outbox | email delivery, audit transport |
| Profile/Library | authoritative row, version increment, feature-refresh outbox | feature recompute |
| Consent | immutable decision, current projection, invalidation/deletion outbox | feature invalidation, source cleanup |
| Feedback | behavior event, dedup record, processing outbox | feature aggregation |
| Feature | contribution ledger and monotonic feature CAS | optional metric/audit only |
| Data Rights | request status, step state, job outbox | export, category deletion, artifact cleanup |
| Key Rotation | row batch update and checkpoint | next batch scheduling |

Transaction은 외부 HTTP, email, object storage 또는 U05/U06 호출을 포함하지 않는다. 외부 effect는 commit된 outbox 이후 실행한다.

## Concurrency and Resource Model

- 모든 mutable aggregate는 positive `row_version`을 갖고 update/delete가 expected version을 조건으로 한다.
- conflict는 safe retry 가능 command에서만 bounded retry하며 사용자 결정이나 OAuth callback을 자동 재실행하지 않는다.
- API pool 10과 worker pool 5는 초기 전체 budget이다. replica 추가 시 총 connection 수를 다시 승인한다.
- Argon2 executor는 process당 2개, worker lane은 high 2·normal 2·low 1로 시작한다.
- long-running export와 re-encryption은 batch/checkpoint로 transaction 시간을 제한한다.
- Q12 결정에 따라 session·role·consent를 포함한 cross-request application cache는 사용하지 않는다.

## Error and Degradation Contract

| Condition | External Behavior | Internal Action |
|---|---|---|
| invalid credential/account state | 동일한 authentication failure | bounded reason metric, PII 없음 |
| CSRF/origin failure | forbidden safe code | security audit fact |
| PostgreSQL/pool timeout | retryable unavailable 또는 fail-closed | saturation/error alert |
| Google timeout/circuit open | provider unavailable | email/existing session 유지 |
| consent absent/stale/error | non-personalized 또는 collection denied | consent fail-closed metric |
| optimistic conflict | conflict/retryable safe code | bounded retry only where idempotent |
| feature backlog | eligible snapshot only; stale consent 금지 | 15분 alert and worker scale review |
| deletion partial failure | pending status, account disabled | high lane retry and SLA alert |
| export failure/expiry | safe failed/expired status | partial artifact cleanup |
| ciphertext authentication failure | integrity failure, no plaintext fallback | restricted incident signal |

## Observability Responsibilities

- LC-27은 correlation/job ID, component, operation, bounded result/reason, duration과 retry count만 log한다.
- metric label에 email, UserId, OAuth subject, session ID, content free text, raw payload 또는 artifact path를 넣지 않는다.
- LC-28 public readiness는 traffic 수용 가능 여부만 반환한다. protected deep health가 database, OAuth circuit, hash executor와 lane backlog를 제공한다.
- dashboard는 authentication, authorization, consent fail-closed, feature freshness, pool/hash saturation, export/deletion SLA와 key rotation progress를 표시한다.

## Verification Ownership

| Verification | Responsible Components | Stage |
|---|---|---|
| Argon2 benchmark and executor saturation | LC-06, LC-15, LC-27 | Code Generation, Build and Test |
| cookie, CSRF, rotation and fresh-auth | LC-01, LC-03, LC-07, LC-09 | Code Generation |
| encryption/blind-index round-trip and rotation restart | LC-09, LC-26, repositories | Code Generation, Infrastructure Design |
| pool, indexes and endpoint latency | LC-05, LC-07, LC-11~14, LC-16 | Build and Test |
| event idempotency, order and FeatureVersion monotonicity | LC-18~21 | Code Generation PBT/integration |
| deletion closure and export one-time use | LC-23~25 | Code Generation/integration |
| failure injection and alert evidence | LC-08, LC-15, LC-20, LC-25~28 | Build and Test |
| backup restore invariants | all repositories, U07 runtime | Build and Test |

## Requirement and Story Traceability

| Component Set | Requirements | Stories and Rules |
|---|---|---|
| LC-01~10 | U02-NFR-002~004, 007, 011, 013, 016, 022~035, 053~059, 066~068 | US-014, US-027; BR-U02 identity/session rules |
| LC-11~14 | U02-NFR-005, 008~009, 017~018, 036~046, 052 | US-015, US-016, US-018; profile/library/consent rules |
| LC-15~17 | U02-NFR-001~021, 048~057 | all U02 orchestration; U07 contracts |
| LC-18~22 | U02-NFR-009~010, 017~019, 036~042, 048~065 | US-017, US-018; PBT-U02 event/feature properties |
| LC-23~26 | U02-NFR-020~021, 031~035, 040~047, 053~059 | US-018, US-027; deletion/export/rotation rules |
| LC-27~28 | U02-NFR-011~016, 049~057, 063~068 | all operational and U01 handoff stories |

## Extension Compliance

- **Resiliency Baseline**: 모든 적용 항목이 dependency isolation, bulkhead, timeout, durable outbox, recovery, health, alert와 failure-injection component에 배정되었다. RESILIENCY-08·09는 승인된 prototype 예외로 N/A이며 production gate는 유지한다.
- **Property-Based Testing**: PBT-U02-01~11의 state transition, idempotency, monotonic version, consent eligibility, encryption round-trip 및 data-rights closure invariant를 LC-18~26의 verification ownership에 연결했다.
- **Security Baseline**: extension은 disabled이므로 N/A다. core 보안 요구사항은 LC-03·06~10·13·23~27에 명시되었다.

적용 가능한 활성 extension의 blocking finding은 없다.

