# U02 Tech Stack Decisions

## Decision Summary

| Area | Decision | Status |
|---|---|---|
| Runtime and API | Inherit Python 3.12.13, FastAPI and Pydantic | Selected |
| Persistence | Inherit PostgreSQL, SQLAlchemy 2, Alembic and psycopg | Selected |
| Password Hashing | Argon2id with versioned parameters | Selected |
| Browser Session | Opaque random token in secure cookie; server-side hashed session | Selected |
| OAuth | Google adapter through standards-based OAuth/OIDC client | Selected |
| Field Encryption | Application envelope encryption for direct identifiers | Selected |
| Equality Lookup | Domain-separated keyed blind index | Selected |
| Jobs | U07 PostgreSQL outbox and worker registry | Selected |
| Testing | pytest, Hypothesis and pytest-cov | Selected |
| Observability | U07 structured logs, metrics, health and trace context | Selected |

## ADR-U02-001 — Argon2id Password Hashing

- **Decision**: Argon2id를 기본 password hashing algorithm으로 사용한다.
- **Implementation direction**: Python의 maintained Argon2 binding을 CredentialHasher port 뒤에 둔다. hash envelope에 algorithm, memory, time, parallelism과 policy version을 저장한다.
- **Runtime tuning**: Code Generation 또는 NFR Design에서 target host benchmark를 수행해 p95 login 500ms와 bounded concurrency를 함께 만족하는 parameter를 고정한다.
- **Upgrade**: successful login에서 current policy보다 낮은 hash만 transaction-safe rehash한다.
- **Rejected**: bcrypt는 안정적이지만 새 greenfield baseline에서 memory-hard Argon2id보다 우선하지 않는다. 자체 cryptographic implementation은 금지한다.
- **Dependency**: 정확한 package와 version은 Code Generation에서 official release, Python 3.12 wheel과 resolver compatibility를 확인해 lock한다.

## ADR-U02-002 — Server-Side Opaque Sessions

- **Decision**: 최소 128-bit entropy의 opaque session token을 browser Secure·HttpOnly·SameSite cookie로 전달하고 PostgreSQL에는 cryptographic hash와 state만 저장한다.
- **Rationale**: 개별·전체 revocation, 30분 inactivity, 30일 absolute lifetime, authorization version과 deletion 즉시 차단을 server에서 일관되게 집행한다.
- **CSRF**: state-changing browser request는 SameSite policy와 별도의 CSRF token 또는 origin validation을 함께 요구한다. 세부 pattern은 NFR Design에서 확정한다.
- **Rejected**: fully self-contained JWT는 즉시 revocation과 deletion closure에 별도 deny-list를 요구하여 초기 모델을 복잡하게 한다.
- **Fresh authentication**: 민감 작업은 session creation이 아니라 최근 credential/OAuth reauthentication evidence 10분을 검사한다.

## ADR-U02-003 — Google OAuth/OIDC Adapter

- **Decision**: Google만 초기 활성 provider로 두고 provider-neutral OAuth port와 standards-based OAuth/OIDC client를 사용한다.
- **Validation**: state, nonce, issuer, audience, redirect binding, provider subject와 verified-email claim을 검증한다.
- **Account linking**: verified email 자동 병합을 금지하고 기존 session의 fresh reauthentication과 explicit link command를 요구한다.
- **Failure isolation**: Google 장애는 provider-specific dependency policy로 격리하며 email authentication과 기존 session authorization은 유지한다.
- **Deferred**: exact client library and version은 Code Generation resolver 검증에서 선택한다. Provider SDK에 domain entity가 의존할 수 없다.

## ADR-U02-004 — Envelope Encryption and Blind Indexes

- **Decision**: email과 저장 OAuth claim 같은 직접 식별 field에 authenticated application-level envelope encryption을 사용한다.
- **Key separation**: key-encryption key, per-record 또는 bounded-scope data key와 blind-index key를 분리한다. Database에는 ciphertext, nonce, algorithm과 key version reference만 저장한다.
- **Lookup**: normalized email equality lookup은 domain-separated keyed blind index를 사용한다. blind index는 authentication 또는 decryption key로 재사용하지 않는다.
- **Rotation**: 새 write는 current key version을 사용하고 background re-encryption job이 old rows를 idempotently 전환한다.
- **Library direction**: maintained Python cryptography library와 authenticated encryption primitive를 사용하며 custom crypto를 구현하지 않는다.
- **Rejected**: volume encryption만으로는 database dump 또는 과도한 database read 권한에서 direct identifier를 충분히 분리하지 못한다. 모든 field 암호화는 query·operation 비용 대비 필요성이 없다.

## ADR-U02-005 — PostgreSQL Aggregate Persistence

- **Decision**: U07 SQLAlchemy·Alembic·psycopg stack을 사용하고 U02 aggregate별 repository와 transaction boundary를 둔다.
- **Concurrency**: mutable aggregate는 row version을 이용한 optimistic concurrency를 기본으로 한다. idempotency, provider subject, current library record와 blind email index는 database unique constraint를 가져야 한다.
- **Consent**: immutable decision ledger와 current projection을 동일 transaction에서 갱신한다.
- **Deletion**: account disable·session revoke와 deletion outbox enqueue를 원자적으로 기록한다.
- **Migration**: expand-and-contract, encrypted-field dual read/write와 key-version compatibility를 지원해야 한다.

## ADR-U02-006 — U07 Outbox for Feedback and Data Rights

- **Decision**: 새 broker를 도입하지 않고 U07 PostgreSQL outbox와 worker handler registry를 사용한다.
- **Job types**: implicit feature update, consent withdrawal purge, export generation, account deletion, re-encryption과 retention cleanup을 분리한다.
- **Isolation**: deletion·withdrawal job은 일반 feature update보다 높은 business priority를 갖되 connection and concurrency bulkhead를 분리한다.
- **Idempotency**: job handler는 entity status/version과 job key를 함께 확인하고 retry·lease recovery에서 동일 결과를 유지해야 한다.
- **Scale trigger**: backlog 15분 또는 U07 saturation trigger 도달 시 worker replica 또는 broker adapter 전환을 재평가한다.

## ADR-U02-007 — Testing Stack

- **Decision**: U07의 pytest, Hypothesis와 pytest-cov를 그대로 사용한다.
- **Example tests**: BR-U02-001~051의 정상·거부·경계 branch와 US-014~US-018, US-027 acceptance criteria를 고정 사례로 검증한다.
- **Property tests**: PBT-U02-01~11에 domain-aware reusable strategy를 사용한다. random email/token이 log failure artifact에 직접 노출되지 않도록 safe representation을 제공한다.
- **Stateful tests**: session, consent, account deletion과 data-rights job transition은 rule-based state machine 후보이다.
- **CI**: shrinking 활성, explicit seed logging, replay artifact와 minimum counterexample regression promotion이 필수다.
- **Coverage**: line 80% 이상, 핵심 decision branch 100%를 별도 gate로 측정한다.

## ADR-U02-008 — Observability and Safe Audit

- **Decision**: U07 telemetry contract를 사용하며 metric label과 log field에 직접 식별자를 금지한다.
- **Metrics**: bounded status/reason enum, provider name과 job type만 사용한다. email, UserId, session ID, OAuth subject와 content-free-form 값을 label로 사용할 수 없다.
- **Logs**: correlation ID 또는 job ID와 safe error code를 기록한다. security event의 detailed personal context는 별도 최소권한 audit contract로 전달한다.
- **Health**: public readiness는 U02가 traffic을 처리할 수 있는지만 제공하고 deep health detail은 operator authorization 뒤에 둔다.

## Dependency and Version Policy

1. U07 `pyproject.toml`과 `uv.lock`이 단일 dependency source다.
2. Argon2, OAuth/OIDC와 cryptography dependency는 Code Generation Planning에서 official PyPI release, Python 3.12.13 support, wheel availability, yank와 resolver compatibility를 검증한다.
3. Cryptography 또는 auth library update는 credential, session, OAuth, encryption round-trip, migration, timing budget과 rollback tests를 통과해야 한다.
4. Critical vulnerability 예외는 U07의 owner·mitigation·30일 만료 record를 사용한다.
5. Algorithm·key·session policy 변경은 privacy/security review checklist와 versioned migration note가 필요하다.

## Deferred Decision Register

| Decision | Target Stage | Reason |
|---|---|---|
| Argon2id exact parameters and executor limit | NFR Design | target host benchmark and CPU budget required |
| Cookie SameSite mode and CSRF pattern | NFR Design | U01 origin and OAuth redirect flow interaction |
| Session hash and token byte length beyond minimum | NFR Design | rotation and storage format design |
| Envelope encryption key hierarchy and rotation batch | NFR Design and Infrastructure Design | secret provider and operational access depend on environment |
| Export artifact expiry and download count | NFR Design | user flow and storage risk tradeoff |
| OAuth, Argon2 and cryptography package versions | Code Generation Planning | actual resolver and official release validation required |
| PostgreSQL indexes, pool and worker concurrency | NFR Design | query and load budget required |

## Extension Compliance

- **Resiliency**: inherited U07 runtime patterns plus provider isolation, bounded hash resources, outbox retry, priority deletion and backlog trigger satisfy the applicable requirements direction.
- **Property-Based Testing**: pytest and Hypothesis, 11 formal properties, state machine candidates, shrinking, seed and regression promotion are mandatory.
- **Security Baseline**: disabled and therefore N/A as an extension. Argon2id, opaque session, envelope encryption, authorization and safe telemetry are core U02 requirements.
- **Frontend**: U02 has no UI. Cookie, CSRF, consent notice, status and safe message-key contracts are handed to U01.

No blocking enabled-extension finding remains at this stage.

