# Shared Infrastructure

> **Status: U03 Extension Applied** — U07 기반에 U02 identity 격리와 U03 catalog/search extension·role·secret·job lane·monitoring 및 Docker-independent PostgreSQL quality gate를 추가했다.

## Scope

U01~U07은 하나의 Docker Compose Project와 단일 PostgreSQL Cluster, Caddy Edge와 관측성 Stack을 공유한다. 이 문서는 공유 비용을 줄이면서 Unit 책임·Credential·Network·Data Write 경계를 유지하는 규칙을 정의한다.

## Shared Resource Ownership

| Shared Resource | Platform Owner | Consumers | Ownership Rule |
|---|---|---|---|
| Caddy and public_net | U07 | U01~U06 | Route는 OpenAPI·운영 Contract와 함께 Version 관리 |
| API Runtime | U07 | U02~U06 Modules | Framework Lifecycle만 U07 소유, Business Rule은 각 Unit 소유 |
| PostgreSQL Cluster | U07 Runtime | U02~U06 | Table Write Owner는 Unit별로 고정 |
| Outbox Runtime | U07 | U02, U04, U06 and other async producers | 상태 Machine은 U07, lane·Job Payload·Outcome은 Producer Unit 소유 |
| OTel Collector | U07 | API and Workers | 공통 Attribute와 Redaction Policy 적용 |
| Prometheus·Loki·Grafana | U07 | All Units | Unit별 Dashboard·Alert Owner 지정 |
| GitHub Actions and GHCR | U07 | Web, API, Worker | 공통 Gate, Artifact별 Owner 유지 |
| Backup and Restore | U07 | All persistent Units | U07 실행, 각 Unit이 Integrity·Smoke Assertion 제공 |

## Database Ownership

| Logical Schema or Table Group | Write Owner | Read Consumers |
|---|---|---|
| `u02_identity`: identity, personalization, data rights | U02 | U05 through Feature Port, U06 through authorized Port |
| `u03_catalog`: approved catalog, feed/search/vector generations | U03 | U01 API, U04 approval Port, U05 approved read, U06 admin Port |
| ingestion, metadata_validation, quarantine | U04 | U03 approval process, U05 rule contract, U06 operations |
| recommendation, explanation, output_validation | U05 | U06 trace view |
| notification, admin_audit, incident | U06 | Authorized operations only |
| platform_idempotency, outbox, release, recovery | U07 | Producing and operating Units through shared Port |

Cross-Unit Read는 Service Port 또는 승인된 Read Model을 사용한다. 다른 Unit Table에 직접 Write하는 Repository를 만들 수 없다.

## Database Roles

| Role | Intended Access |
|---|---|
| migration_owner | Schema 변경 전용; Runtime 사용 금지 |
| api_runtime | U02, U03, U05, U06 API Module에 필요한 최소 Runtime Grant |
| ingestion_worker | U04 Ingestion·Validation과 U03 ApprovedCatalogWritePort 실행 |
| notification_worker | U06 Notification Job과 필요한 Read Model |
| backup_reader | Backup에 필요한 Read와 Global Metadata; Application Write 금지 |
| monitor_reader | Health·Metric용 제한된 System View |
| u02_migration_owner | `u02_identity` DDL 전용; Runtime 사용 금지 |
| u02_api_runtime | U02 online command·query 최소 DML; 다른 Unit write 금지 |
| u02_worker_runtime | U02 feature·data-rights·rotation job과 허용된 outbox claim 최소 DML |
| u03_migration_owner | `u03_catalog` DDL과 search extension-dependent object 관리; Runtime 사용 금지 |
| u03_api_runtime | U03 approved catalog/projection read와 허용된 routine; projection mutation 금지 |
| u03_worker_runtime | U03 publication, outbox receipt, projection/generation mutation; 다른 Unit write 금지 |

모듈러 Monolith의 `api_runtime`이 여러 Schema를 사용하더라도 Repository Boundary Test와 Migration Grant Review로 Unit Write Ownership을 검증한다. Unit이 독립 Service로 분리될 때 Role도 분리한다.

## Network Isolation

- `public_net`: Caddy, Web, API만 연결한다.
- `private_net`: API, Workers, PostgreSQL과 Backup Runner를 연결하고 Host Port를 게시하지 않는다.
- `observability_net`: Telemetry Source, Collector, Prometheus, Loki, Grafana와 Caddy 보호 Route만 연결한다.
- PostgreSQL은 public_net과 observability_net에 연결하지 않는다.
- Grafana, Prometheus와 Loki는 Caddy 외부에 직접 Port를 공개하지 않는다.
- Service 이름으로 연결하며 Container IP를 Configuration에 고정하지 않는다.
- Public Domain DNS와 80·443 Inbound를 Caddy 자동 HTTPS의 배포 전제조건으로 검사한다.
- 비표준 Caddy Plugin 없이 Host 연결 제한과 FastAPI의 IP·Identity·Endpoint Rate Limit을 계층화한다.

## Secret Isolation

| Secret | Granted Services |
|---|---|
| database_api | api |
| database_ingestion | worker-ingestion |
| database_notification | worker-notification |
| database_backup | backup-runner, restore-verifier |
| ai_provider | api only |
| content_provider | worker-ingestion only |
| oauth_provider | api only |
| notification_channel | worker-notification only |
| object_storage | backup-runner, restore-verifier |
| alert_email_webhook | grafana only |
| u02_kek_versions | api, worker only; backup과 monitoring 제외 |
| u02_blind_index_keys | api, worker only; KEK·session key와 분리 |
| u02_session_peppers | api and explicitly required session worker only |
| u02_email_provider | U02 email worker/adapter only |
| u02_export_storage | U02 export worker only; backup runner 제외 |
| u03_embedding_credential | U03 API와 worker only; allowlisted provider 호출 최소 scope |
| u03_cursor_hmac_current_previous | U03 API only; query fingerprint key와 분리 |
| u03_query_hmac_current_previous | U03 API only; cursor key와 분리 |

Secret은 Compose에서 Service별로 명시하고 `/run/secrets/` File로 Mount한다. Secret 값은 공유 Environment File에 모으지 않는다.

## Volume and Retention Isolation

| Volume | Failure Risk | Guard |
|---|---|---|
| postgres_data | 손실 시 Stateful 기능 중단 | Off-host Backup, Disk Alert, 직접 삭제 금지 |
| loki_data | 폭증 시 Host Disk 고갈 | 7일·7GB 초기 Limit과 Drop Alert |
| prometheus_data | 시계열 증가 | 15일·5GB 초기 Limit |
| grafana_data | Dashboard·Alert 설정 손실 | 설정 Export 또는 Provisioning을 Version 관리 |
| caddy_data | 인증서 상태 손실 | 권한 제한 Volume과 재발급 Runbook |
| restore_test_data | Drill 잔여 Data | Drill 후 검증된 Cleanup |

Business Data Volume과 Observability Volume은 분리한다. Disk 80% Alert는 Retention 조정 또는 Scale Review를 유발한다.

## Shared Configuration

- Compose Base File은 공통 Service·Network·Volume·Health를 정의한다.
- Local Override는 개발 Port와 Mock Provider만 추가한다.
- Remote Override는 Immutable Image Digest, Domain, Resource Limit과 Production-like Secret Reference를 정의한다.
- Observability와 Restore는 Profile로 분리하되 Remote 핵심 Monitoring은 항상 활성화한다.
- Configuration Schema와 Example은 Version 관리하고 실제 Secret은 제외한다.

## U02 Shared Resource Contract

- Local과 CI는 native 또는 container 방식과 무관하게 실제 PostgreSQL을 사용할 수 있다. marker-selected integration test의 skip은 성공으로 간주하지 않는다.
- Remote Prototype의 Linux Docker Compose 목표는 유지하며 Local Docker 장애가 schema·integration·PBT gate를 차단하지 않는다.
- U02 connection pool 총 budget은 API 10, worker 5로 시작하고 replica 수를 곱한 값이 PostgreSQL global headroom을 침해할 수 없다.
- shared outbox는 high deletion/withdrawal, normal feature, low export/rotation lane과 claim partial index를 지원한다.
- backup은 `u02_identity` schema를 포함하지만 24시간·1회용 export artifact body와 U02 decrypt key를 포함하지 않는다.
- shared observability는 U02 dashboard와 alert를 제공하되 label allow-list가 email, UserId, OAuth subject, session ID와 object reference를 거부한다.

## U03 Shared Resource Contract

- Local과 CI는 container 또는 native 방식의 실제 PostgreSQL 17을 사용할 수 있다. `pg_trgm`, `unaccent`, `vector` preflight와 marker-selected integration `skip=0`은 두 경로 모두 필수이다.
- Remote Prototype은 version-pinned PostgreSQL 17+vector image/build manifest를 사용하고 extension exact version을 release artifact와 deployment preflight에 기록한다.
- `u03_catalog` schema는 U03가 write-owner이며 migration, API와 worker role을 분리한다. U01·U04·U05·U06은 U03 Port를 통해 접근한다.
- 공유 PostgreSQL 40 GB allocation 안에서 U03 table/index soft budget은 15 GB이며 70% warning과 80% critical threshold를 적용한다.
- API/worker는 전체 PostgreSQL headroom 안에서 별도 pool budget을 사용한다. U03 online DB concurrency 4, embedding concurrency 4, incremental worker 2와 rebuild worker 1로 시작한다.
- Shared outbox는 U03 incremental·embedding·rebuild lane과 unit/job_type/priority/available_at partial index, claim lease, retry, dead-letter와 CatalogVersion gap state를 지원한다.
- Backup은 approved Catalog, provenance, availability, CatalogVersion, durable outbox/receipt와 generation registry를 포함한다. 재생성 가능한 FTS/vector index와 incomplete candidate generation은 restore 후 rebuild한다.
- Shared observability는 U03 dashboard와 gap·lag·closure drop·fallback·zero-result·stale ratio·disk·rebuild alert를 제공하며 raw query, vector와 provider payload를 label/log에서 거부한다.
- Caddy는 discovery API route만 public으로 제공한다. PostgreSQL, worker, metric과 deep health는 private/observability network에 유지하고 embedding egress는 configured endpoint로 제한한다.
- U03 배포는 extension preflight, real-PostgreSQL migration/integration/PBT/failure-injection, pre-deploy backup, candidate quality/closure validation과 atomic generation swap을 통과한 digest만 허용한다.

## U04 Shared Resource Contract

- 동일 Backend Image에서 전용 `worker-ingestion` Service를 실행하고 Public Port를 게시하지 않는다.
- `u04_ingestion` Schema와 `u04_migration_owner`, `u04_worker_runtime`, `u04_api_runtime` Role을 추가한다. U04는 U03 Table에 직접 Write하지 않는다.
- 공유 PostgreSQL Pool에서 U04 Worker 5, API 기여 2 Connection으로 시작하며 전체 Headroom을 침해할 수 없다.
- U04는 withdrawal, publication, incremental, revalidation, full-sync, retention Job Lane과 Provider별 공정 Claim·Fencing을 사용한다.
- U04 Table·Index Soft Budget은 10 GB이며 70% Warning, 80% Critical Alert와 1,000,000-row Query-plan Gate를 적용한다.
- `worker-ingestion`은 `private_net`, `observability_net`, outbound-only `provider_egress_net`만 사용한다. Provider Origin은 Scheme·Host·Port Allowlist를 적용한다.
- Provider Credential은 `u04_provider_<id>` 별도 Read-only Secret으로 주입하며 공유 Environment File, Image, Database, Backup과 Telemetry에 포함하지 않는다.
- Backup은 허용된 Raw State, Policy, Cursor, Validation, Quarantine, Pending Publication과 Receipt를 포함한다. Provider Retention으로 만료된 Body는 복원 후 노출하지 않는다.
- Shared Observability는 Cursor·Publication Age, Freshness, Quarantine, Retry·Circuit, Retention, Disk·Pool과 Invariant Alert를 제공한다.
- Local/CI는 Docker 여부와 무관하게 실제 PostgreSQL 17, Migration, U03/U05 Contract, PBT-U04-01~12와 Integration `skip=0`을 통과해야 한다.

## Shared Failure Impact

| Shared Failure | Affected Units | Mitigation |
|---|---|---|
| PostgreSQL | U02~U07 | Pool Bulkhead, Readiness, Backup Restore |
| Host Disk | All | 80% Alert, Retention Limit, Off-host Backup |
| Caddy | U01~U06 external access | Config Validation, Restart, Previous Config Rollback |
| OTel·Loki·Prometheus | Operational visibility | Business Path non-blocking, Buffer, Recovery Alert |
| GitHub Actions | New Release | Current Version continues, Local Emergency Runbook documented later |
| GHCR | New Host·Deploy Pull | Current local Image retained; Digest and Restore Procedure |

## Shared Change Rules

1. PostgreSQL Major, Compose Network, Caddy Route와 Telemetry Schema 변경은 모든 Consumer Contract Test를 실행한다.
2. Shared Migration은 Expand-and-contract와 이전 Image Compatibility를 통과해야 한다.
3. 공통 Resource Limit 변경은 API, Worker, Database와 Monitoring 전체 부하 시험 결과를 기록한다.
4. Shared Secret Rotation은 영향 Service만 재시작하고 다른 Secret을 함께 교체하지 않는다.
5. Shared 장애 수정은 경량 Incident·COE와 Corrective Action을 남긴다.
6. U02 secret/key rotation은 old-version row drain, restore sample과 rollback window 종료 전 key를 폐기할 수 없다.
7. 삭제·동의 철회·key rotation progress는 application rollback을 이유로 database snapshot에서 역행시킬 수 없다.

## Cost and Capacity Guardrails

- 단일 4 vCPU·8GB·100GB Host와 S3-compatible Backup Storage가 초기 Cost Boundary다.
- Metric·Log Retention보다 Business Data와 Restore 가능성을 우선한다.
- Host Upgrade 또는 Resource 분리는 SLO 침해, Disk·Pool 포화, 50명 예상 또는 Queue Backlog로 결정한다.
- 상용 전환 Cost 추정에는 Multi-zone Database, Load Balancer, 독립 Monitoring과 On-call을 포함한다.

## Compliance

- **Resiliency**: 공유 장애 영향, Isolation, Off-host Backup, Recovery와 Production Gate를 명시했다.
- **PBT**: 공통 CI와 Database·Contract Test 환경이 Unit별 Hypothesis Test를 실행한다.
- **Security Baseline**: 비활성화로 N/A. Service별 Secret, Network와 Role 최소 권한은 일반 요구로 유지한다.

현재 Shared Infrastructure에서 차단 상태인 Extension Finding은 없다.
