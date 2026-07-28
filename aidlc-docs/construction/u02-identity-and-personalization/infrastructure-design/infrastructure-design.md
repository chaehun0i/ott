# U02 Infrastructure Design

## Scope and Baseline

U02는 U07의 cloud-neutral prototype 기반을 공유한다. Remote Prototype 목표는 Linux host의 Docker Compose이지만, Local과 CI의 품질 gate는 Docker 자체가 아니라 실제 PostgreSQL에서 migration과 integration test가 skip 없이 성공하는지로 판정한다. 현재 검증된 native PostgreSQL 17.10 instance는 Local/Test 경로로 계속 사용할 수 있다.

## Infrastructure Decision Summary

| Category | Selected Design |
|---|---|
| Environments | Local native PostgreSQL 또는 container, CI 실제 PostgreSQL, Remote Linux Docker Compose |
| Compute | 같은 immutable image의 별도 API·worker process/service |
| Prototype budget | API 최대 1 vCPU·1 GiB, worker 최대 1 vCPU·1 GiB에서 시작 |
| Database | 공유 PostgreSQL instance/database의 `u02_identity` schema와 분리된 migration/API/worker role |
| Connections | U07 global limit 안에서 U02 API 10, worker 5 총 budget |
| Secrets | 분리된 versioned KEK, blind-index key, session HMAC pepper secret file |
| Export storage | backup과 분리된 private S3-compatible location, 24시간 lifecycle, public access 차단 |
| Messaging | 공유 PostgreSQL outbox/job table의 indexed high·normal·low lane |
| Email | Local mail sink, CI fake, Remote transactional email API 또는 SMTP adapter |
| Network | Caddy 80·443만 public, identity callback/API route만 노출, data·worker·deep health는 private |
| Monitoring | 공유 Prometheus·Loki·Grafana·OTel, U02 전용 dashboard·alert·label allow-list |
| Delivery | migration·key·PostgreSQL integration·PBT·failure gate를 통과한 immutable digest |

## Environment Mapping

| Environment | API and Worker | PostgreSQL | External Dependencies | Purpose |
|---|---|---|---|---|
| Local | 직접 Python process 또는 Compose service | 실제 native/container PostgreSQL; 현재 검증 instance는 17.10, port 55432 | mail sink, Google sandbox/test config, fake object adapter 가능 | 개발, migration, integration, PBT |
| CI Test | job process 또는 application image | ephemeral 실제 PostgreSQL service | fake email/object adapter, stubbed failure injection | repeatable quality gate |
| Remote Prototype | 별도 API·worker Compose service | private PostgreSQL container와 named volume | Google OAuth, transactional email, private S3-compatible storage | 사용자 검증 환경 |

Local/CI는 `TEST_DATABASE_URL`처럼 명시적 test connection을 사용한다. PostgreSQL이 없거나 연결되지 않아 integration test가 skip되면 gate는 미완료다. Docker 가용성은 gate 조건이 아니다.

## Compute Infrastructure

### Process Isolation

- API와 worker는 같은 source revision과 immutable image digest를 사용하지만 별도 process/service로 실행한다.
- API는 HTTP lifecycle, Argon2 bounded executor와 online transaction을 소유한다.
- worker는 outbox claim, feature, deletion, export와 key-rotation handler를 실행한다.
- API crash/restart가 committed job을 잃지 않고 worker backlog가 API process memory를 점유하지 않는다.

### Initial Resource Budget

| Service | CPU Limit | Memory Limit | Internal Concurrency |
|---|---:|---:|---|
| API | 1 vCPU | 1 GiB | Argon2 executor 최대 2, DB pool 총 10 |
| Worker | 1 vCPU | 1 GiB | high 2, normal 2, low 1, DB pool 총 5 |

이 값은 4 vCPU·8 GB U07 host의 상한 안에서 시작하는 budget이다. Argon2 64 MiB 이상과 p95 300ms single-hash 조건을 만족하지 못하거나 memory pressure가 발생하면 executor concurrency를 먼저 낮춘다. 보안 parameter를 성능 회피 목적으로 낮추지 않는다.

### Scale Trigger

- 동시 사용자 50명 또는 인증 burst 50 requests/second 예상
- API p95, pool checkout, Argon2 queue 또는 worker backlog가 정의된 threshold를 지속 초과
- feature oldest-event age 15분 초과
- deletion 72시간 또는 export 24시간 SLA 위험

증설 시 `replicas × pool_size`와 host CPU·memory budget을 다시 계산한다. 단일 host 한계를 넘으면 worker 분리 또는 managed compute/database 전환을 검토한다.

## Storage Infrastructure

### PostgreSQL Schema and Roles

| Principal | Access |
|---|---|
| `u02_migration_owner` | `u02_identity` DDL과 migration만 수행; runtime login 금지 |
| `u02_api_runtime` | online identity, session, profile, library, consent, feedback command에 필요한 최소 DML |
| `u02_worker_runtime` | outbox claim과 feature·data-rights·rotation job에 필요한 최소 DML |
| `backup_reader` | 암호화 backup에 필요한 일관된 read; application write 금지 |
| `monitor_reader` | bounded health/metric query만 허용 |

U02 table은 `u02_identity` schema에 둔다. shared outbox row의 lifecycle은 U07이 소유하고 U02 runtime에는 등록된 U02 job type의 producer/consumer 권한만 부여한다. 다른 unit은 U02 table을 직접 쓰지 않고 versioned port를 사용한다.

### Required Index and Constraint Families

- versioned email blind index와 provider-subject blind index의 unique constraint
- session HMAC unique index와 active expiry partial index
- current consent projection과 immutable ledger ordering index
- user/content별 profile·library unique composite index
- outbox lane/status/available-time claim partial index
- feature user/event contribution unique index와 monotonic feature version constraint
- deletion request/category unique index와 incomplete-step partial index

실제 index는 migration 후 `EXPLAIN (ANALYZE, BUFFERS)`와 write-amplification evidence로 확정한다. 평문 identifier는 index에 포함하지 않는다.

### Encryption Material

- `u02_kek_vN`, `u02_blind_index_key_vN`, `u02_session_pepper_vN`을 별도 read-only secret file로 주입한다.
- API와 worker에는 필요한 key만 service별 grant하며 migration, backup, monitoring service에는 decrypt key를 주지 않는다.
- database에는 wrapped DEK, ciphertext, nonce, algorithm과 key version reference만 저장한다.
- secret은 image, Compose YAML, shared `.env`, log, CI artifact와 database backup에 포함하지 않는다.
- Prototype key source는 host 권한 제한 file이며 Production 분류 전 managed KMS/HSM과 감사 가능한 key access가 필수다.

### Export Artifact Storage

- backup bucket과 다른 private bucket 또는 강하게 격리된 prefix, credential 및 encryption context를 사용한다.
- public access를 차단하고 application export role만 put/get/delete를 수행한다.
- object lifecycle은 24시간이며 versioning은 비활성화하거나 만료/소비 시 모든 version을 영구 삭제하도록 구성한다.
- database에는 opaque object reference, checksum, expiry와 consumed state만 저장한다.
- backup runner와 restore verifier에는 export object read 권한을 주지 않으며 PostgreSQL backup에서도 artifact body를 제외한다.

## Backup and Restore

U07의 일일 암호화 논리 backup과 30일 off-host retention에 `u02_identity` schema를 포함한다. export artifact는 backup 대상이 아니다.

Restore verification은 다음 invariant를 검사한다.

1. revoked session이 다시 active가 되지 않는다.
2. current consent projection이 immutable ledger의 최신 결정과 일치한다.
3. deletion-pending account와 category progress가 유지된다.
4. FeatureVersion과 contribution ledger가 역행하거나 중복되지 않는다.
5. ciphertext의 key-version reference가 복구 환경의 승인된 secret manifest와 일치한다.
6. plaintext identifier, token 또는 export body가 backup artifact에 없다.

복구 환경의 key는 backup과 분리된 승인 경로에서 제공한다. key가 없으면 silent data fallback 없이 restore verification이 실패한다.

## Messaging Infrastructure

### PostgreSQL Outbox Lanes

| Lane | Jobs | Worker Budget | Infrastructure Guard |
|---|---|---:|---|
| High | deletion, consent-withdrawal cleanup | 2 | reserved claim budget, Critical SLA alert |
| Normal | implicit feature update, recompute | 2 | 15-minute age alert |
| Low | export, re-encryption | 1 | batch/checkpoint, high-lane preemption |

동일 outbox/job table에 `lane`, `priority`, `status`, `available_at`, lease와 attempt를 저장하고 claimable row partial index를 둔다. lane별 semaphore와 independent retry budget으로 격리한다. 별도 Redis/RabbitMQ는 추가하지 않는다.

dead-letter 또는 retry exhaustion은 row를 삭제하지 않고 safe code와 terminal/operator state를 남긴다. deletion 실패는 account를 disabled로 유지한다.

## Email and OAuth Infrastructure

### Email

- Local은 browser로 확인 가능한 mail sink를 사용한다.
- CI는 network를 사용하지 않는 fake adapter로 verification/reset contract를 검증한다.
- Remote는 provider-neutral port 뒤 transactional email API 또는 SMTP provider를 사용한다.
- provider credential은 worker/email adapter에만 주입하고 link/token 원문을 log하지 않는다.
- 실패는 outbox retry와 bounded provider timeout을 사용하며 challenge lifetime을 임의로 연장하지 않는다.

### Google OAuth

- Local, CI callback test와 Remote domain마다 정확히 일치하는 redirect URI를 등록하고 wildcard를 사용하지 않는다.
- Remote callback은 `https://<prototype-domain>/api/v1/identity/oauth/google/callback` 형태의 Caddy route만 public에 노출한다.
- API outbound는 Google discovery/JWKS/token endpoint와 DNS/TLS에 필요한 경로로 제한한다.
- callback exchange는 자동 재시도하지 않고 discovery/JWKS만 bounded retry와 validated cache를 사용한다.

## Network Infrastructure

| Network | U02 Attachments | Exposure |
|---|---|---|
| `public_net` | Caddy, API | Caddy 80·443만 host 공개 |
| `private_net` | API, worker, PostgreSQL, backup runner | host port 없음; required egress만 허용 |
| `observability_net` | API, worker, OTel Collector, Prometheus, Grafana | Caddy의 인증된 operator route 외 비공개 |

Caddy가 `/api/v1/identity/*`와 OAuth callback을 API로 전달한다. PostgreSQL, worker, metrics endpoint, protected deep health, mail credential과 secret file은 public route가 없다. forwarded client headers는 Caddy trust boundary에서만 생성·수용한다.

## Monitoring Infrastructure

U07 OTel Collector, Prometheus, Loki와 Grafana를 공유하되 다음 U02 전용 구성을 provision한다.

- **Identity dashboard**: login outcome, Argon2 duration/queue, session revoke, authorization denial, OAuth circuit
- **Consent and feature dashboard**: fail-closed count, event acceptance/dedup, FeatureVersion conflict, oldest event age
- **Data-rights dashboard**: export age/failure, deletion category progress와 72-hour risk
- **Resource dashboard**: API/worker CPU·memory, pool checkout, lane concurrency, PostgreSQL query latency
- **Key dashboard**: key-version row count, rotation checkpoint, integrity failure와 old-version drain

label allow-list는 component, operation, provider=`google`, lane, bounded result/reason 및 key version만 허용한다. email, UserId, OAuth subject, session ID, content free text와 object reference는 금지한다.

public readiness는 traffic 처리 가능 여부만 반환한다. database, circuit, executor, queue와 key detail은 인증된 operator deep-health route에서만 제공한다.

## CI and Quality Infrastructure

필수 gate는 다음 순서로 실행한다.

1. format, lint, type 및 unit test
2. PostgreSQL migration apply와 downgrade/compatibility 검증
3. 실제 PostgreSQL integration test `pytest -m integration` — skip 0 필수
4. PBT-U02-01~11, seed 기록, shrinking 활성화와 counterexample artifact
5. Argon2 target-host benchmark와 bounded executor saturation
6. OAuth·database·session·feature·deletion·rotation failure injection
7. coverage 및 OpenAPI/consumer contract
8. dependency/image scan과 secret scanning

Docker 실행 성공은 별도 deployment rehearsal evidence이며 1~7의 대체물이 아니다.

## Deployment and Rollback

- source revision에서 검증된 API/worker image를 GHCR immutable digest로 게시한다.
- 배포 전 schema compatibility, required key-version secret 존재, OAuth/email config, PostgreSQL integration/PBT/failure evidence와 pre-deploy backup을 확인한다.
- expand migration을 먼저 적용하고 API·worker digest를 교체한 뒤 readiness와 identity smoke test를 수행한다.
- rollback은 이전 image가 새 schema를 읽을 수 있을 때만 수행한다.
- deletion·consent-withdrawal·key-rotation progress를 과거 database snapshot으로 되돌리지 않는다. 이 job은 idempotent forward recovery를 수행한다.
- destructive contract migration과 old key retirement는 compatibility window와 별도 승인 뒤 실행한다.

## Logical Component Mapping

| Logical Components | Infrastructure Resources |
|---|---|
| LC-U02-01~04 | Caddy route, API service, public/private network |
| LC-U02-05, 07, 11~14, 19, 21 | PostgreSQL `u02_identity` schema, API pool과 indexes |
| LC-U02-06, 15 | API CPU/memory limit, Argon2 executor와 provider circuit metric |
| LC-U02-08, 10 | Google egress, email adapter, provider-specific secrets |
| LC-U02-09 | versioned secret files, encrypted database fields, export encryption context |
| LC-U02-16~17 | SQLAlchemy transaction, shared PostgreSQL outbox |
| LC-U02-18, 20, 23~26 | worker service, lane semaphore, worker pool, export storage |
| LC-U02-22 | API internal route, request-scoped pseudonym boundary to U05 |
| LC-U02-27~28 | OTel Collector, Prometheus, Loki, Grafana, protected health route |

## Production Transition Gates

U07 gate에 더해 다음을 충족하지 않으면 U02를 Production으로 분류하지 않는다.

1. managed KMS/HSM과 audited key access·rotation·retirement
2. managed/HA PostgreSQL, multi-zone compute와 connection capacity evidence
3. transactional email domain 인증과 abuse/rate-limit 운영 절차
4. 개인정보 export/delete 법무 검토, access review와 evidence retention
5. independent synthetic login·consent·non-personalized fallback 검사
6. data deletion, key compromise와 OAuth outage incident runbook/실전 연습

## Requirements Traceability

| Requirement Range | Infrastructure Evidence |
|---|---|
| U02-NFR-001~013 | compute/pool budget, Argon2 executor, real PostgreSQL load gate |
| U02-NFR-014~021 | dependency isolation, outbox lanes, backup/restore and failure injection |
| U02-NFR-022~030 | secret files, cookie edge, OAuth callback/egress, email adapter |
| U02-NFR-031~039 | KEK/DEK/blind-index separation, private network and U05 boundary |
| U02-NFR-040~047 | retention, isolated export bucket, deletion worker and backup exclusion |
| U02-NFR-048~057 | feature lane, monitoring, alert and privacy-safe telemetry |
| U02-NFR-058~065 | migration/deployment gate, real PostgreSQL integration and PBT artifacts |
| U02-NFR-066~068 | versioned API route, safe errors and U01 contract |

## Extension Compliance

| Extension Rule | Status | Infrastructure Disposition |
|---|---|---|
| RESILIENCY-01~07 | Compliant | workload resource, SLO metric, health, alerts와 change evidence 매핑 |
| RESILIENCY-08~09 | N/A | 승인된 non-production single-host exception; Production gate 유지 |
| RESILIENCY-10 | Compliant | process/pool/lane/provider bulkhead와 backpressure |
| RESILIENCY-11~13 | Compliant | encrypted backup, isolated restore와 U02 re-entry invariant |
| RESILIENCY-14 | Compliant | automated failure injection과 quarterly restore evidence |
| RESILIENCY-15 | Compliant | U07 incident lifecycle과 privacy/key incident gate |
| PBT-01~10 | Compliant handoff | actual PostgreSQL CI/Local gate, seed/shrink/counterexample artifact 기반 |
| Security Baseline | N/A | extension disabled; secret/network/least-privilege는 core U02 design으로 적용 |

적용 가능한 활성 extension의 blocking finding은 없다.

