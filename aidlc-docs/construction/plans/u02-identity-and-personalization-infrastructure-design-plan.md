    # U02 Identity and Personalization Infrastructure Design Plan

> **Single Source of Truth**: 이 파일은 U02 Infrastructure Design의 질문, 결정 및 실행 체크박스를 관리한다. 모든 답변을 검증하기 전에는 인프라 설계 산출물을 생성하지 않는다.

## Inputs and Inherited Decisions

- [x] U02 Functional Design, U02-NFR-001~068, NFR Design Patterns와 LC-U02-01~28을 확인했다.
- [x] U07의 Local·CI·Remote Prototype 환경, cloud-neutral Linux host, Caddy, PostgreSQL, PostgreSQL outbox, GHCR와 GitHub Actions 구성을 확인했다.
- [x] U07의 4 vCPU·8 GB RAM·100 GB SSD prototype budget, API 10·worker 5 U02 pool budget, backup·restore와 observability 기반을 확인했다.
- [x] 현재 Docker 오류와 별개로 실제 PostgreSQL 17.10 환경에서 U07 integration gate가 skip 없이 통과했음을 반영했다.
- [x] 활성화된 Resiliency Baseline과 Property-Based Testing 규칙 및 비활성 Security Baseline 상태를 확인했다.

## Category Assessment

| Mandatory Category | Applicability | Infrastructure Focus |
|---|---|---|
| Deployment Environment | Required | Docker 비의존 검증과 remote target의 관계, environment isolation |
| Compute Infrastructure | Required | API·worker 배치, Argon2 및 job lane resource limit |
| Storage Infrastructure | Required | U02 schema·role, encrypted export, key rotation, retention과 backup |
| Messaging Infrastructure | Required | PostgreSQL outbox lane, claim·retry·dead-letter 격리 |
| Networking Infrastructure | Required | public route, OAuth callback, egress와 private dependency exposure |
| Monitoring Infrastructure | Required | U02 dashboard, alerts, protected health와 failure exercise evidence |
| Shared Infrastructure | Required | U07 자원 공유 범위와 U02별 credential·pool·ownership 격리 |

## Execution Plan

### Step 1 - Infrastructure Decision Collection

- [x] Question 1~14의 `[Answer]:`를 모두 채운다.
- [x] 선택지 유효성, 상호 모순 및 U07·U02 설계와의 충돌을 검증한다.
- [x] 모호성이 있으면 follow-up 질문을 추가하고 해결한다. 모호성이 없어 추가 질문은 필요하지 않았다.

### Step 2 - Infrastructure Mapping

- [x] LC-U02-01~28을 compute, database, secret, object storage, network, messaging 및 observability resource에 매핑한다.
- [x] Local, CI Test와 Remote Prototype별 topology, configuration 및 isolation을 정의한다.
- [x] capacity, connection, Argon2, worker lane와 disk budget을 구체화한다.
- [x] `aidlc-docs/construction/u02-identity-and-personalization/infrastructure-design/infrastructure-design.md`를 생성한다.

### Step 3 - Deployment Architecture

- [x] public·private·observability network flow와 OAuth/email/object-storage egress를 정의한다.
- [x] secret/key injection, rotation, backup, restore, deployment 및 rollback 흐름을 정의한다.
- [x] Docker가 없어도 가능한 실제 PostgreSQL 검증 경로와 remote container target을 명확히 분리한다.
- [x] `aidlc-docs/construction/u02-identity-and-personalization/infrastructure-design/deployment-architecture.md`를 생성한다.

### Step 4 - Shared Infrastructure Assessment

- [x] U07 shared infrastructure 문서에 U02 공통 변경이 필요한지 판단했다. U02 전용 격리 계약이 공유 자원에 영향을 준다.
- [x] `aidlc-docs/construction/shared-infrastructure.md`를 U02 schema·role·secret·lane·quality gate로 갱신했다.

### Step 5 - Validation and Completion

- [x] 모든 mandatory infrastructure category와 U02-NFR-001~068의 mapping을 검증한다.
- [x] RESILIENCY-01~15와 PBT-01~10의 적용·N/A·후속 검증을 기록한다.
- [x] Mermaid 2개 diagram의 node·edge·quote syntax와 text alternative 및 Markdown compatibility를 확인했다.
- [x] Infrastructure Design 완료 메시지를 기록하고 표준 2개 선택지로 승인을 요청한다.

## Infrastructure Design Questions

## Question 1
현재 Docker 오류를 고려할 때 Local·CI·Remote Prototype의 실행 기준을 어떻게 정할까요?

A) Remote Prototype의 Linux Docker Compose 목표는 유지하되 Local·CI 검증은 native PostgreSQL 또는 container 중 사용 가능한 실제 PostgreSQL을 허용하며, Docker 실행 여부를 품질 gate로 삼지 않는다.

B) 모든 환경에서 Docker Compose만 허용하고 Docker가 복구될 때까지 U02 검증을 중단한다.

C) Remote Prototype도 Windows host의 native PostgreSQL과 직접 실행 Python process로 변경한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 2
U02 API와 background worker의 compute 배치는 어떻게 할까요?

A) 동일 immutable application image를 사용하되 API process와 worker process를 별도 container/service로 실행하고 독립 CPU·memory·restart·pool limit을 적용한다.

B) API process 안에서 background worker thread를 함께 실행한다.

C) U02를 별도 identity microservice image와 독립 host로 분리한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 3
4 vCPU·8 GB Remote Prototype에서 U02의 초기 compute resource 예약은 어떻게 할까요?

A) API 1 vCPU·1 GiB, worker 1 vCPU·1 GiB 상한 안에서 시작하고 Argon2 executor 2개와 high 2·normal 2·low 1 worker concurrency를 부하 시험으로 낮출 수 있게 한다.

B) API와 worker 각각 2 vCPU·2 GiB를 고정 예약해 다른 U07 service budget을 축소한다.

C) container resource limit을 두지 않고 host scheduler에 맡긴다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 4
U02 PostgreSQL 데이터와 권한을 어떻게 격리할까요?

A) 기존 PostgreSQL instance와 database를 공유하되 `u02_identity` schema, migration owner, API runtime role과 worker role을 분리하고 다른 unit에는 기본 write 권한을 주지 않는다.

B) 기존 database의 공용 schema와 공용 application role을 그대로 사용한다.

C) U02 전용 PostgreSQL instance와 volume을 별도로 운영한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 5
U02 direct identifier 암호화 key를 Prototype에서 어떻게 주입하고 관리할까요?

A) versioned KEK·blind-index key·session HMAC pepper를 서로 다른 read-only secret file로 service별 주입하고 database·image·backup과 분리하며, Production 전환 시 managed KMS/HSM을 필수 gate로 둔다.

B) 하나의 application master key를 `.env`로 API와 worker에 공통 주입한다.

C) key를 PostgreSQL configuration table에 저장하고 runtime role이 읽게 한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 6
개인정보 export artifact 저장소는 어떻게 구성할까요?

A) backup object와 분리된 private S3-compatible bucket 또는 강하게 격리된 prefix·credential을 사용하고, object lifecycle 24시간·versioning 비활성 또는 즉시 영구 삭제·public access 차단을 적용한다.

B) 30일 backup bucket에 export artifact도 저장하고 application에서만 24시간 만료로 표시한다.

C) Remote Prototype host의 local filesystem에만 저장하고 정기 cleanup한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 7
U02 table과 개인정보 상태를 U07 backup·restore에 어떻게 포함할까요?

A) 매일 암호화 논리 backup에 U02 schema를 포함하되 export artifact는 제외하고, restore drill에서 session revocation·current consent·deletion progress·FeatureVersion·key-version reference 무결성을 검증한다.

B) identity와 profile만 backup하고 behavior·feature·deletion progress는 복구 대상에서 제외한다.

C) U02 전용 시간별 backup을 새로 추가하고 U07 일일 backup과 별도로 관리한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 8
PostgreSQL outbox의 high·normal·low job lane을 물리적으로 어떻게 구현할까요?

A) 같은 outbox/job table에 lane·priority·available_at partial index를 두고 worker deployment의 lane별 semaphore와 claim budget으로 격리한다.

B) lane마다 별도 PostgreSQL database와 worker image를 만든다.

C) 하나의 FIFO claim query를 사용하고 application code에서 삭제 job을 먼저 확인한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 9
Email verification·password reset 전달 인프라는 어떤 방식으로 구성할까요?

A) provider-neutral email adapter를 두고 Local은 mail sink, CI는 fake adapter, Remote는 credential이 분리된 transactional email API 또는 SMTP provider를 사용한다.

B) 모든 환경에서 개발자 개인 SMTP account를 공용으로 사용한다.

C) Prototype에서는 verification/reset link를 API response와 log에 직접 출력한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 10
Google OAuth redirect와 outbound network 경계는 어떻게 구성할까요?

A) 환경별 고정 HTTPS redirect URI를 등록하고 Caddy 뒤 API callback만 public route로 노출하며, API egress는 Google OIDC와 email provider에 필요한 목적지로 제한한다.

B) wildcard redirect URI를 사용하고 container outbound traffic을 제한하지 않는다.

C) OAuth callback service를 별도 public host로 분리한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 11
U02 public·private network exposure는 어떻게 할까요?

A) 기존 Caddy 80·443만 public으로 유지하고 `/api/v1/identity/*`를 API로 route하며 PostgreSQL, worker, metrics, deep health와 secret provider는 private/observability network에만 둔다.

B) API container port와 PostgreSQL port도 host에 공개해 운영자가 직접 접근하게 한다.

C) U02 전용 public load balancer를 추가한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 12
U02 monitoring과 alerting은 어디에 배치할까요?

A) U07 Prometheus·Loki·Grafana·OTel Collector를 공유하되 U02 전용 dashboard와 auth·consent·feature·deletion·export·key-rotation alert rule 및 privacy-safe label allow-list를 둔다.

B) U02 전용 observability stack을 별도 배포한다.

C) 기존 service overview dashboard만 사용하고 U02 전용 alert는 만들지 않는다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 13
U07 shared infrastructure를 U02가 사용하는 격리 원칙은 무엇으로 할까요?

A) host·Caddy·PostgreSQL·outbox·observability·CI를 공유하되 schema, database role, connection pool, secret grant, job lane, dashboard와 storage credential은 U02 책임별로 격리한다.

B) 모든 resource와 credential을 U07 공용 설정으로 공유한다.

C) U02용 host, database, observability와 CI pipeline을 모두 별도로 만든다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 14
U02 infrastructure deployment와 rollback gate는 무엇으로 할까요?

A) migration compatibility, secret/key-version availability, PostgreSQL integration·PBT·failure-injection, pre-deploy backup을 통과한 digest만 배포하고 rollback 시 이전 image와 compatible schema를 사용하되 개인정보 삭제·key rotation job은 역행시키지 않는다.

B) application unit test만 통과하면 배포하고 실패 시 database snapshot 전체를 되돌린다.

C) schema와 key 변경은 rollback을 지원하지 않고 forward fix만 허용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Planned Outputs

- `aidlc-docs/construction/u02-identity-and-personalization/infrastructure-design/infrastructure-design.md`
- `aidlc-docs/construction/u02-identity-and-personalization/infrastructure-design/deployment-architecture.md`
- `aidlc-docs/construction/shared-infrastructure.md` only if shared-resource design changes are required

## Extension Planning Status

- **Resiliency Baseline**: compute isolation, outbox bulkhead, backup·restore, health·monitoring, deployment·rollback과 failure-injection infrastructure에 적용한다.
- **Property-Based Testing**: 실제 PostgreSQL이 있는 Local 또는 CI environment에서 seed·shrinking·counterexample artifact를 보존하는 gate로 연결한다.
- **Security Baseline**: extension은 disabled이므로 N/A이며, secret, network, TLS, least privilege와 privacy storage는 U02 core 요구사항으로 계속 적용한다.
