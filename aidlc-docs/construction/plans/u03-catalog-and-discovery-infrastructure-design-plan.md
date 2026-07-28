# U03 Catalog and Discovery Infrastructure Design Plan

> **Single Source of Truth**: 이 파일은 U03 Infrastructure Design의 질문, 결정과 체크박스 진행 상태를 관리한다. 모든 답변이 검증되기 전에는 인프라 산출물을 생성하지 않는다.

## Inputs and Inherited Decisions

- [x] U03 Functional Design, U03-NFR-001~057, 20개 NFR pattern과 30개 logical component를 읽는다.
- [x] U07 Local Compose·GitHub Actions·Remote Linux Compose, Caddy, PostgreSQL, outbox, GHCR와 observability topology를 상속한다.
- [x] U07의 4 vCPU·8 GiB·100 GB SSD, PostgreSQL 40 GB budget, daily encrypted backup, RTO 4시간과 RPO 24시간을 상속한다.
- [x] Docker 장애가 Local/CI 검증을 막지 않으며 실제 PostgreSQL 환경에서 integration skip=0을 충족하는 기존 결정을 상속한다.
- [x] Resiliency·PBT extension 활성화와 Security Baseline 비활성화 상태를 확인한다.

## Mandatory Category Assessment

| Category | Applicability | U03 infrastructure focus |
|---|---|---|
| Deployment Environment | Required | Docker-optional local/CI verification and remote Compose target |
| Compute Infrastructure | Required | Shared API plus projection worker resource/concurrency isolation |
| Storage Infrastructure | Required | Catalog schema, PostgreSQL search extensions, vector/index disk and backup scope |
| Messaging Infrastructure | Required | PostgreSQL outbox claims, U03 lane, retry/gap/rebuild jobs |
| Networking Infrastructure | Required | Public discovery routes, private PostgreSQL/worker and restricted embedding egress |
| Monitoring Infrastructure | Required | Discovery dashboard, alerts, health and quality evidence |
| Shared Infrastructure | Required | U07 host/database/worker/CI sharing with U03 roles, secrets and extension image |

## Execution Plan

### Step 1 — Infrastructure Decision Collection

- [x] 모든 mandatory category에서 미결정 인프라 항목을 식별한다.
- [x] Question 1~14를 `[Answer]:` 형식으로 작성한다.
- [x] 모든 답변의 누락과 선택지 유효성을 확인한다.
- [x] 답변 간 모순과 U07/U03 design 충돌을 검사하고 clarification을 완료한다. 추가 질문은 필요하지 않다.

### Step 2 — Infrastructure Mapping

- [x] LC-U03-01~30을 compute, database, extension, secret, network, messaging와 observability resource에 매핑한다.
- [x] Local, CI Test와 Remote Prototype topology와 configuration isolation을 정의한다.
- [x] Resource, connection, disk, vector index, worker concurrency와 scale gate를 구체화한다.
- [x] `aidlc-docs/construction/u03-catalog-and-discovery/infrastructure-design/infrastructure-design.md`를 생성한다.

### Step 3 — Deployment Architecture

- [x] Public/private/observability network flow와 embedding egress를 정의한다.
- [x] Extension preflight, migration, online generation build/swap, backup·restore와 rollback 흐름을 정의한다.
- [x] Docker 없이 가능한 실제 PostgreSQL verification path와 remote container target을 분리한다.
- [x] `aidlc-docs/construction/u03-catalog-and-discovery/infrastructure-design/deployment-architecture.md`를 생성한다.

### Step 4 — Shared Infrastructure Assessment

- [x] PostgreSQL extension image, U03 schema/roles, secrets, worker lane, observability와 CI 변경의 shared impact를 평가한다.
- [x] 변경이 필요하면 `aidlc-docs/construction/shared-infrastructure.md`를 U03 격리 계약과 gate로 갱신한다.

### Step 5 — Validation and Completion

- [x] 모든 mandatory category, U03-NFR-001~057과 LC-U03-01~30 mapping을 검증한다.
- [x] RESILIENCY-01~15와 PBT-01~10의 적용·N/A·handoff를 검증한다.
- [x] Mermaid 또는 Markdown parsing compatibility를 검증한다.
- [x] Infrastructure Design 완료 메시지를 기록하고 표준 2개 선택지로 명시적 승인을 요청한다.

## Infrastructure Design Questions

## Question 1
Local·CI·Remote Prototype에서 U03 PostgreSQL 검색 확장 검증 경로를 어떻게 구성합니까?

A) Remote는 Docker Compose를 유지하되 Local·CI는 container 또는 native 실제 PostgreSQL 중 사용 가능한 경로를 허용하고 `pg_trgm`, `unaccent`, `vector` preflight와 integration skip=0을 동일하게 적용한다.

B) 모든 환경에서 Docker Compose만 허용하고 Docker 장애 시 U03 검증을 중단한다.

C) 모든 환경을 native PostgreSQL로 변경하고 Remote Compose를 제거한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
U03 API와 Projection/Embedding/Rebuild 작업의 compute 배치는 무엇입니까?

A) 기존 immutable application image를 공유하되 API와 worker를 별도 service/process로 실행하고 worker 내부에 incremental·embedding·rebuild concurrency budget을 분리한다.

B) API process 내부 background thread에서 모든 projection 작업을 수행한다.

C) U03 전용 microservice image와 별도 host를 즉시 추가한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
4 vCPU·8 GiB Remote Prototype에서 U03 resource budget을 어떻게 적용합니까?

A) 공유 API/worker limit 안에서 U03 online DB concurrency 4, embedding concurrency 4, incremental worker 2, rebuild worker 1로 시작하고 rebuild 중 online SLO가 악화되면 자동 pause한다.

B) U03 worker에 2 vCPU·4 GiB를 전용 예약하여 다른 Unit budget을 축소한다.

C) Resource와 concurrency limit 없이 host scheduler에 맡긴다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4
PostgreSQL 검색 확장은 어떻게 공급하고 고정합니까?

A) PostgreSQL 17 기반의 version-pinned image/build manifest에 `vector` extension을 포함하고 내장 `pg_trgm`·`unaccent`와 함께 startup·migration preflight에서 exact version을 검증한다.

B) Container 시작마다 package manager로 latest extension을 설치한다.

C) Remote host의 PostgreSQL에 운영자가 수동 설치하고 version을 기록하지 않는다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
U03 PostgreSQL schema와 role isolation은 무엇입니까?

A) 공유 database에 `u03_catalog` schema를 만들고 migration owner, API read/runtime role과 projection worker role을 분리하며 다른 Unit은 U03 Port를 통해서만 접근한다.

B) 공용 schema와 하나의 application role을 모든 Unit이 공유한다.

C) U03 전용 PostgreSQL instance와 volume을 별도로 운영한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 6
100,000개 Catalog·Locale·Availability·Vector를 위한 초기 disk budget은 무엇입니까?

A) 기존 PostgreSQL 40 GB allocation 안에서 U03 table/index 15 GB soft budget과 70% warning·80% critical threshold를 두고 실제 fixture 측정으로 조정한다.

B) U03 전용 100 GB volume을 즉시 추가한다.

C) Disk budget과 threshold를 정하지 않고 공간 부족 시 수동 확장한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 7
U03 backup과 projection data의 복구 범위는 무엇입니까?

A) 승인 Catalog, provenance, availability, CatalogVersion, outbox receipt와 generation registry는 backup하고 재생성 가능한 FTS/vector index·candidate generation은 rebuild 대상으로 취급한다.

B) 모든 FTS/vector index와 중간 candidate generation까지 backup하고 그대로 복원한다.

C) U03 전체를 backup에서 제외하고 외부 provider에서 다시 수집한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 8
PostgreSQL outbox에서 U03 job을 어떻게 격리합니까?

A) 공용 job table에 unit/job_type/priority/available_at partial index와 U03 claim budget을 두고 incremental·embedding·rebuild lane별 semaphore를 적용한다.

B) U03 job type마다 별도 database와 worker image를 만든다.

C) 모든 Unit job을 하나의 FIFO claim query와 동일 concurrency로 처리한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 9
Embedding provider credential과 U03 HMAC key는 어떻게 주입합니까?

A) Embedding credential, cursor HMAC current/previous와 query-fingerprint HMAC current/previous를 용도별 read-only secret file로 API/worker에 최소 grant하고 image·database·backup과 분리한다.

B) 하나의 application master key와 embedding credential을 공통 `.env`에 둔다.

C) Secret을 PostgreSQL configuration table에 저장하고 runtime role이 읽게 한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 10
U03 network exposure와 embedding egress는 어떻게 제한합니까?

A) Caddy의 `/api/v1/feed*`, `/api/v1/contents*`, `/api/v1/search*`만 public route로 제공하고 PostgreSQL·worker·metrics·deep health는 private/observability network에 두며 API/worker egress를 configured embedding endpoint와 필수 DNS/TLS로 제한한다.

B) API, PostgreSQL과 metrics port를 host에 공개하고 outbound는 제한하지 않는다.

C) Embedding 전용 public proxy host를 추가하고 모든 search traffic을 통과시킨다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 11
U03 monitoring infrastructure는 어디에 배치합니까?

A) U07 Prometheus·Loki·Grafana·OTel Collector를 공유하되 U03 전용 dashboard, alert rules, privacy label allowlist와 golden-set/rebuild evidence artifact를 추가한다.

B) U03 전용 observability stack을 별도 배포한다.

C) U07 service overview만 사용하고 U03 전용 signal은 수집하지 않는다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 12
CI에서 실제 PostgreSQL 확장 Integration Gate를 어떻게 구성합니까?

A) Version-pinned PostgreSQL 17+vector service 또는 동등한 native PostgreSQL을 사용해 clean/upgrade migration, extension version, FTS/HNSW, outbox/rebuild/failure-injection과 `pytest -m integration` skip=0을 필수 gate로 둔다.

B) SQLite와 mocked vector repository로 CI를 통과시키고 PostgreSQL test는 선택 사항으로 둔다.

C) Unit test만 CI에서 실행하고 integration은 Remote 배포 후 수동 실행한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 13
U03 deployment와 rollback 순서는 무엇입니까?

A) Extension preflight와 backup 후 expand migration, new image 배포, candidate generation build·quality/closure validation, atomic pointer swap을 수행하고 이전 image·schema·generation을 rollback window 동안 유지한다.

B) 기존 projection을 먼저 삭제한 뒤 migration과 rebuild를 수행하고 실패하면 backup 전체를 복원한다.

C) Application image만 교체하고 extension·migration·generation compatibility는 확인하지 않는다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 14
U07 shared infrastructure에 반영할 U03 격리 원칙은 무엇입니까?

A) Host·Caddy·PostgreSQL·outbox·observability·CI를 공유하되 schema/role, pool, disk budget, extension version, secret grant, job lane, dashboard와 deployment gate를 U03 책임 범위로 격리한다.

B) 모든 resource와 credential을 U07 공통 설정으로 공유한다.

C) U03 host, database, observability와 CI를 모두 별도로 만든다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Planned Outputs

- `aidlc-docs/construction/u03-catalog-and-discovery/infrastructure-design/infrastructure-design.md`
- `aidlc-docs/construction/u03-catalog-and-discovery/infrastructure-design/deployment-architecture.md`
- `aidlc-docs/construction/shared-infrastructure.md` only for confirmed shared-resource changes

## Extension Planning Status

- **Resiliency Baseline**: Compute/pool isolation, PostgreSQL extension pinning, outbox lanes, online generation rollback, backup/rebuild, health/alert와 failure-injection environment에 적용한다.
- **Property-Based Testing**: 실제 PostgreSQL 17+extension 환경에서 seed·shrinking·counterexample artifact와 integration skip=0을 보존하는 gate로 연결한다.
- **Security Baseline**: disabled이므로 N/A이다. Secret, network, TLS, least privilege, query privacy와 integrity는 core requirement로 적용한다.
