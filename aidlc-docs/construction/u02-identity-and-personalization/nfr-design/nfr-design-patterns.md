# U02 NFR Design Patterns

## Scope and Design Position

이 문서는 U02-NFR-001~068을 구현 가능한 resilience, scalability, performance 및 security pattern으로 변환한다. U07의 Python 3.12.13, FastAPI, PostgreSQL, SQLAlchemy, Alembic, psycopg, outbox worker, 관측성 및 복구 기반을 재사용한다. U02는 초기부터 별도 microservice나 외부 cache를 추가하지 않으며, stateless API와 PostgreSQL 중심 구조를 유지한다.

## Approved Design Decisions

| Area | Approved Pattern |
|---|---|
| Password hashing | target-host benchmark, Argon2id memory 64 MiB 이상, single-hash p95 300ms 이하, process당 bounded executor 2개 |
| Browser protection | Secure·HttpOnly·SameSite=Lax session cookie, signed double-submit CSRF, Origin/Referer 검증 |
| Session secret | CSPRNG 256-bit token, peppered HMAC-SHA-256 server lookup, security transition 시 rotation |
| Field encryption | versioned KEK, record별 DEK, AES-256-GCM, 분리된 versioned blind-index HMAC key |
| Key rotation | dual-read/new-write, 500-row idempotent re-encryption job, checkpoint와 pause/resume |
| PostgreSQL pool | U07 상한 내 API 10, worker 5 초기 budget과 saturation 기반 조정 |
| Concurrency | aggregate version 기반 optimistic concurrency와 목적별 unique/partial composite index |
| Job isolation | deletion·withdrawal high, feature normal, export·re-encryption low lane |
| Google dependency | connect 3초, overall 10초, callback exchange 무재시도, discovery/JWKS만 bounded retry·circuit breaker·cache |
| Export | 별도 key 암호화, 24시간 만료, fresh authentication 뒤 1회 download |
| Feature ordering | user별 monotonic version, compare-and-swap, replay 가능한 contribution ledger |
| Application cache | 없음; 모든 session·role·consent 검증을 PostgreSQL current state에서 수행 |
| Scale-out | stateless API, job-type/user-key partition 가능 worker, 측정 threshold 기반 증설 |
| Failure injection | OAuth, PostgreSQL, session, feature backlog, deletion exhaustion, key rotation 중단·재개 자동 검증 |

## Resilience Patterns

### RP-U02-01 — Consent Fail-Closed Gate

- 모든 personalization event 수집과 FeatureSnapshot 발급 전에 같은 요청에서 PostgreSQL의 current ConsentDecision을 조회한다.
- 조회 timeout, transaction 오류, version 불일치 또는 deletion-pending 상태는 모두 non-personalized 결과 또는 안전한 거절로 변환한다.
- consent를 추측하거나 이전 성공 결과로 대체하지 않는다. 승인된 Q12에 따라 cross-request cache도 사용하지 않는다.
- 실패는 bounded reason code로 계측하되 subject, UserId 또는 payload를 기록하지 않는다.
- **Trace**: U02-NFR-017, 036~039, 042, 046, 052~057.

### RP-U02-02 — Transactional Outbox and Idempotent Consumer

- library mutation, consent transition, deletion request 및 durable behavior acceptance는 authoritative row 변경과 outbox insert를 하나의 PostgreSQL transaction에서 commit한다.
- consumer는 job ID와 domain idempotency key로 이미 완료된 effect를 확인하고 재실행해도 동일한 terminal state를 만든다.
- lease expiry 뒤 재처리를 허용하되 attempt 증가와 safe failure code만 남긴다.
- poison job은 lane별 retry budget 이후 격리되며 삭제·동의 철회는 계정 비활성 상태를 유지한 채 운영 경보를 발생시킨다.
- **Trace**: U02-NFR-018~020, 042~051, 053~057.

### RP-U02-03 — Priority Lanes and Bulkheads

| Lane | Job Types | Initial Concurrency | Failure Policy |
|---|---|---:|---|
| High | account deletion, consent withdrawal cleanup | 2 | retry budget 소진 시 Critical alert; account/consent는 차단 상태 유지 |
| Normal | implicit feature update, feature recompute | 2 | 15분 backlog alert; eligible last snapshot만 허용 |
| Low | export generation, key re-encryption | 1 | checkpoint 후 pause/resume; high lane resource를 점유하지 않음 |

각 lane은 독립 semaphore, claim query 및 saturation metric을 갖는다. 실제 값은 동일 host에서 PostgreSQL connection budget과 CPU 사용량을 측정해 낮추거나 높일 수 있으나 high lane의 최소 처리 슬롯은 보존한다.

### RP-U02-04 — Google OAuth Dependency Isolation

- token/discovery/JWKS HTTP client는 connect timeout 3초, overall timeout 10초를 적용한다.
- authorization callback의 code exchange는 code 재사용과 중복 account mutation을 막기 위해 자동 재시도하지 않는다. 사용자는 새 OAuth flow를 시작한다.
- discovery와 JWKS의 idempotent GET만 exponential backoff와 jitter가 있는 bounded retry를 수행한다.
- provider별 circuit breaker는 연속 실패율과 최소 표본 기준으로 open되며 half-open probe로 회복을 확인한다. 정확한 threshold는 부하·장애 시험에서 조정하되 상태를 metric으로 공개한다.
- issuer·audience·signature·expiry를 통과한 discovery/JWKS만 TTL cache하며, cache 만료 뒤 provider 장애 시 Google login만 실패한다. email login과 기존 session authorization은 유지된다.
- **Trace**: U02-NFR-011, 014, 016, 029, 053~057.

### RP-U02-05 — Feature Version and Replay Safety

- 사용자별 FeatureVersion은 증가만 하며 update는 expected version을 조건으로 compare-and-swap한다.
- contribution ledger는 event ID, consent decision ID, source sequence 및 applied feature version을 저장한다.
- duplicate 또는 더 오래된 event는 contribution을 다시 적용하거나 현재 FeatureVersion을 낮출 수 없다.
- 충돌한 worker는 최신 state를 다시 읽고 결정론적으로 recompute한다. 사용자별 key partition을 지원하되 correctness가 broker ordering에 의존하지 않는다.
- ConsentVersion이 current granted version과 다르면 snapshot은 즉시 부적격이다.
- **Trace**: U02-NFR-019, 048~052, 062~065.

### RP-U02-06 — Data-Rights Saga with Closure Verification

- deletion은 즉시 user를 `deletion_pending`으로 바꾸고 모든 session을 revoke한 뒤 category별 DeletionStep을 high lane으로 처리한다.
- 단계별 effect는 idempotent하며 부분 실패가 account를 다시 활성화하지 못한다.
- terminal completion 전 credentials, OAuth link, session, profile, library, event, feature, export artifact와 임시 산출물 존재 여부를 closure query로 확인한다.
- export는 24시간 내 생성하며 artifact별 data key로 암호화한다. fresh authentication을 통과한 subject에게 1회용 signed reference를 발급하고 최초 성공 download 또는 24시간 경과 시 폐기한다.
- **Trace**: U02-NFR-020, 040~047, 053~059.

### RP-U02-07 — Recoverable Key Rotation

- current KEK·blind-index key version으로만 새 write를 생성하고 이전 version은 read-only decrypt/lookup 기간에만 유지한다.
- 500-row batch가 ciphertext authentication, decrypt, new-DEK encryption 및 version update를 한 transaction 경계 또는 재시작 가능한 checkpoint로 처리한다.
- job payload는 key material을 담지 않고 from-version, to-version, cursor와 job ID만 포함한다.
- 중단 후 마지막 committed checkpoint에서 재개하며, 실패 row는 safe code로 격리한다. rotation 완료는 old-version row count가 0이고 표본 decrypt 검증이 성공해야 한다.
- blind-index key rotation은 dual index column 또는 versioned index record로 검색 공백을 방지한 뒤 이전 index를 제거한다.
- **Trace**: U02-NFR-031~035, 046, 055, 058~059.

## Scalability and Capacity Patterns

### SP-U02-01 — Stateless API and Shared Database First

- API process에는 사용자 session state, consent state 또는 feature state를 보존하지 않는다.
- 모든 authoritative state는 PostgreSQL에 있고 secret provider와 Google adapter는 port 뒤에 둔다.
- scale-out은 10명/20 rps baseline을 먼저 검증하고, 50명/50 rps 예상 또는 p95·pool·CPU·backlog threshold의 지속 위반이 있을 때 수행한다.
- API replica는 동일 cookie/CSRF/key policy와 database schema version을 사용한다.

### SP-U02-02 — Connection Budget and Backpressure

- process 구성의 초기 `pool_size` 총합은 API 10, worker 5를 넘지 않으며 U07 global PostgreSQL connection 상한에서 migration, operator 및 recovery 여유를 제외한 뒤 배정한다.
- pool checkout timeout은 request deadline보다 짧게 두고 exhaustion 시 무제한 대기 대신 bounded unavailable response를 반환한다.
- hash executor가 가득 찬 login 요청과 worker lane이 포화된 job claim에는 명시적 backpressure를 적용한다.
- deployment replica 수 증가는 `replicas × pool_size`를 재계산한 capacity evidence 없이는 허용하지 않는다.
- **Trace**: U02-NFR-001~006, 012~013, 049~050.

### SP-U02-03 — Query Shape and Index Budget

| Access Path | Index or Constraint |
|---|---|
| email login | `(blind_index_version, email_blind_index)` unique for eligible identities |
| OAuth login | `(provider, provider_subject_blind_index)` unique for active links |
| session authorization | `session_token_hmac` unique plus partial active-session expiry lookup |
| current consent | `(subject_type, subject_id, purpose, sequence desc)` with one current projection |
| profile/library | `(user_id)` and `(user_id, content_id)` unique by entity type |
| outbox lane claim | `(lane, status, available_at, created_at)` partial for claimable jobs |
| feature contribution | `(user_id, event_id)` unique and `(user_id, feature_version)` |
| deletion closure | `(request_id, category)` unique plus incomplete-step partial index |

인덱스는 실제 `EXPLAIN (ANALYZE, BUFFERS)`와 write amplification evidence로 검증하며 개인 식별 평문을 포함하지 않는다.

## Performance Patterns

### PP-U02-01 — Bounded Argon2id Work

- startup 또는 release qualification에서 target host를 benchmark해 memory cost 64 MiB 이상을 유지하면서 single hash p95 300ms 이하인 Argon2id parameter set을 선택한다.
- hash/verify는 event loop 밖의 process-local bounded executor에서 실행하며 동시에 최대 2개만 허용한다.
- queue wait, execution time, rejection과 memory pressure를 metric으로 측정한다. login 전체 p95 500ms를 침해하면 보안 parameter를 임의로 낮추지 않고 replica·rate limit·capacity를 조정한다.
- credential envelope에 algorithm과 parameter version을 저장하고 성공 login에서만 current policy로 rehash한다.
- **Trace**: U02-NFR-002, 004, 007, 012~013, 022~023.

### PP-U02-02 — No Application Cache Baseline

- 승인된 Q12에 따라 session, role, consent, profile 및 FeatureSnapshot에 cross-request application cache를 두지 않는다.
- 한 request/transaction 안의 동일 row 재사용만 허용하며 request 종료 시 폐기한다.
- correctness는 cache invalidation에 의존하지 않는다. 300ms read와 500ms authorization 목표는 index, prepared query, bounded projection과 pool tuning으로 충족한다.
- 부하 시험에서 목표를 충족하지 못할 경우 cache 도입은 별도 change record와 revocation·consent stale-read proof를 요구한다.
- **Trace**: U02-NFR-005, 007~010, 017, 026, 030, 046, 052, 058.

### PP-U02-03 — Deadline Budgeting

- request deadline은 API validation, hash executor wait, database checkout/query 및 response serialization budget으로 분해한다.
- OAuth provider round-trip은 내부 latency histogram과 분리한다.
- background job은 작은 batch와 checkpoint를 사용해 long transaction과 lock retention을 제한한다.
- load evidence는 p50/p95/p99, throughput, error, pool wait, hash queue, lane backlog와 database query plan을 함께 보존한다.
- **Trace**: U02-NFR-007~013, 043~050.

## Security and Privacy Patterns

### SEC-U02-01 — Opaque Session and CSRF Binding

- browser에는 CSPRNG로 생성한 256-bit opaque token만 Secure·HttpOnly·SameSite=Lax cookie로 전달한다.
- PostgreSQL에는 domain-separated pepper를 사용한 HMAC-SHA-256 lookup 값, owner, issued/last-seen/absolute expiry, authorization version 및 revocation만 저장한다.
- login, privilege change, fresh authentication 성공 뒤 기존 token을 폐기하고 새 token으로 회전한다.
- state-changing browser 요청은 signed double-submit token과 Origin/Referer allow-list를 모두 통과해야 한다. OAuth callback은 state·nonce·redirect binding으로 별도 보호한다.
- inactivity 30분, absolute 30일, 민감 작업 fresh-auth 10분을 server clock으로 집행한다.
- **Trace**: U02-NFR-023~030, 066~068.

### SEC-U02-02 — Envelope Encryption and Blind Lookup

- record마다 CSPRNG DEK를 생성해 direct-identifier field를 AES-256-GCM으로 암호화하고 field name, record ID, schema version을 associated data로 결합한다.
- versioned KEK는 secret provider가 관리하며 database에는 wrapped DEK, nonce, ciphertext, algorithm과 key version만 저장한다.
- equality lookup은 별도 versioned HMAC key와 domain separator로 normalized value의 blind index를 생성한다. encryption, session 및 blind-index key는 상호 재사용하지 않는다.
- decrypt 실패는 plaintext fallback 없이 safe integrity error가 되며 secret과 PII는 log·metric·trace에 포함되지 않는다.
- **Trace**: U02-NFR-031~035, 055, 058~059.

### SEC-U02-03 — Least Privilege and Pseudonymous Boundary

- authorization은 현재 role assignment와 authorization version을 PostgreSQL에서 읽어 평가한다.
- U05에는 request마다 새 pseudonym을 생성하고 allow-listed feature, FeatureVersion, ConsentVersion 및 expiry만 전달한다.
- email, OAuth subject, stable UserId, session ID, raw behavior 및 export content는 AI/recommendation boundary와 일반 telemetry에 전달하지 않는다.
- U06 audit에는 actor category, action, result, safe reason, correlation과 policy version만 보내며 상세 개인정보는 최소권한 저장소로 분리한다.
- **Trace**: U02-NFR-030, 036~039, 045, 047, 053~057, 065.

## Failure-Injection Verification

| Scenario | Injection | Expected Invariant | Evidence |
|---|---|---|---|
| Google outage/latency | timeout, 5xx, invalid JWKS | Google login만 실패; email login과 기존 session 유지 | component plus integration test |
| Consent read failure | DB timeout/error | event 미수집, personalized snapshot 미발급 | integration test |
| Session store failure | insert/read/revoke failure | token 성공 응답 없음 또는 protected command 거절 | integration test |
| Feature backlog | normal lane 정지/지연 | 15분 경보, version 역행·중복 없음 | worker integration and PBT |
| Deletion retry exhaustion | category step 반복 실패 | account disabled 유지, Critical alert, 미완료 상태 | component plus integration test |
| Key rotation interruption | batch 중 process termination | committed checkpoint부터 재개, plaintext·손실 없음 | migration integration test |

월별 dependency failure exercise에는 OAuth, consent database 및 feature/deletion worker 중 회전 범위를 포함한다. 분기별 restore drill은 U07 기준과 함께 session revocation, consent current projection, deletion progress 및 feature version을 검증한다.

## Requirements Traceability

| Requirement Range | Primary Patterns |
|---|---|
| U02-NFR-001~006 | SP-U02-01~03, PP-U02-01 |
| U02-NFR-007~013 | PP-U02-01~03, RP-U02-04 |
| U02-NFR-014~021 | RP-U02-01~06, SP-U02-02 |
| U02-NFR-022~030 | SEC-U02-01, PP-U02-01, RP-U02-04 |
| U02-NFR-031~039 | SEC-U02-02~03, RP-U02-07 |
| U02-NFR-040~047 | RP-U02-03, RP-U02-06~07, SEC-U02-03 |
| U02-NFR-048~057 | RP-U02-01~06, PP-U02-02~03, SEC-U02-03 |
| U02-NFR-058~065 | all patterns plus change, migration and PBT gates |
| U02-NFR-066~068 | SEC-U02-01·03 and versioned U01 contract |

## Extension Compliance

| Rule | Status | Design Disposition |
|---|---|---|
| RESILIENCY-01 | Compliant | Critical/High workload별 pattern과 dependency가 연결됨 |
| RESILIENCY-02 | Compliant | U07 99.0%, RTO 4h, RPO 24h 상속 |
| RESILIENCY-03 | Compliant | privacy/security change record와 rotation checkpoint |
| RESILIENCY-04 | Compliant | stateless rollout, schema compatibility, version rollback 상속 |
| RESILIENCY-05 | Compliant | latency, pool, hash, lane, dependency metric 정의 |
| RESILIENCY-06 | Compliant | PostgreSQL, OAuth와 backlog health contribution 정의 |
| RESILIENCY-07 | Compliant | fail-closed, deletion, export와 backlog alert 정의 |
| RESILIENCY-08 | N/A | 승인된 비운영 single-server prototype; production multi-zone gate 유지 |
| RESILIENCY-09 | N/A | 초기 규모 예외와 50-user/포화 scale trigger가 명시됨 |
| RESILIENCY-10 | Compliant | bulkhead, timeout, bounded retry, circuit breaker, backpressure 적용 |
| RESILIENCY-11 | Compliant | U07 Backup and Restore 전략과 U02 re-entry 검증 연결 |
| RESILIENCY-12 | Compliant | 암호화된 persistent state와 key 분리 |
| RESILIENCY-13 | Compliant | restore 후 identity/consent/deletion/feature invariant 검증 |
| RESILIENCY-14 | Compliant | 월별 failure injection과 분기별 restore drill 범위 정의 |
| RESILIENCY-15 | Compliant | U07 incident lifecycle과 privacy impact 기록 상속 |
| PBT-01~10 | Compliant handoff | ordering, idempotency, consent, encryption round-trip 및 state transition invariant를 Code Generation test plan에 전달 |
| Security Baseline | N/A | extension disabled; core security/privacy pattern은 SEC-U02-01~03으로 충족 |

적용 가능한 활성 extension의 blocking finding은 없다.

