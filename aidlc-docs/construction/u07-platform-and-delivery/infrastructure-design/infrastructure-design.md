# U07 Infrastructure Design

> **Status: Ready for Review** — Follow-up 10~11의 A 답변을 반영하고 Infrastructure 검증을 완료했다.

## Infrastructure Decision Summary

| Category | Selected Infrastructure |
|---|---|
| Environments | Local Compose, GitHub Actions ephemeral Test, one Remote Prototype Host |
| Compute | Linux Host, 4 vCPU, 8GB RAM, 100GB SSD |
| Runtime | Docker Engine and Docker Compose Plugin |
| Edge | Official Caddy image with automatic HTTPS, Routing and Compression; Host connection controls plus FastAPI request rate limits |
| Database | Same-host PostgreSQL Container with dedicated Named Volume |
| Jobs | PostgreSQL-backed Outbox and Job Tables |
| Backup | Daily encrypted export to versioned S3-compatible Object Storage, 30 days |
| Metrics | Prometheus-compatible collection |
| Logs | OpenTelemetry Collector to Loki-compatible central store |
| Dashboard and Alerts | Grafana with Email and optional Webhook |
| Image Registry | GHCR immutable image digest |
| Delivery | GitHub Actions build·test·publish, operator-driven direct deployment |

## Environment Architecture

### Local

- Docker Compose로 Web, API, Worker, PostgreSQL와 선택적 Observability Profile을 실행한다.
- 개발 Secret은 Git에서 제외된 Local File로 제공하고 값 없는 Example만 Version 관리한다.
- Local Database와 Volume은 Remote Prototype과 공유하지 않는다.
- Mock 또는 명시적으로 허용된 Sandbox Provider를 기본으로 사용한다.

### CI Test

- GitHub Actions Job마다 임시 PostgreSQL과 Application Container를 생성한다.
- Format, Lint, Type, Unit, Contract, Integration, PBT, Coverage, Dependency·Image Scan을 실행한다.
- PBT Seed, Shrunk 반례, Coverage, OpenAPI와 Scan 결과를 Artifact로 보존한다.
- Test 종료 시 임시 Resource를 폐기하고 실제 운영 Secret은 제공하지 않는다.

### Remote Prototype

- 하나의 Cloud-neutral Linux Host에서 Docker Compose Project 하나를 실행한다.
- Public Domain과 DNS Record를 Host에 연결하고 외부에서 80·443에 도달할 수 있게 한 뒤 Caddy 자동 HTTPS를 사용한다.
- Public Port는 Caddy의 80과 443만 허용한다. SSH 또는 관리 Port는 Host Firewall의 관리 Source 범위로 제한한다.
- PostgreSQL, Worker, Prometheus, Loki와 OpenTelemetry Collector Port는 Host에 게시하지 않는다.
- 별도 Staging Host는 없으므로 Release 전 CI와 Local Restore·Migration Rehearsal을 강화한다.

## Compute Design

### Initial Capacity

| Resource | Baseline | Allocation Intent |
|---|---:|---|
| CPU | 4 vCPU | API·Worker와 관측성 Peak 분리 |
| Memory | 8GB | OS 1.5GB, PostgreSQL 2.5GB, API 1GB, Workers 1GB, Observability 1.5GB, Edge·Web 0.5GB 기준 |
| SSD | 100GB | PostgreSQL 40GB, Logs 7GB, Metrics 5GB, Images·Build 15GB, OS·Config 13GB, Free Headroom 20GB 기준 |

Resource 값은 초기 Budget이며 Compose Limit, PostgreSQL 설정과 Retention은 실제 부하 시험으로 조정한다. Disk 80% 도달, 지속적 CPU·Memory·Pool 포화 또는 동시 사용자 50명 예상은 Scale Review Trigger다.

### Container Resource Rules

- API와 Worker에 별도 CPU·Memory Limit을 설정한다.
- PostgreSQL은 API와 Worker Connection Budget을 합산해 `max_connections`보다 낮게 제한한다.
- Observability Container는 Retention·Disk Limit을 적용해 Business Data Volume을 잠식하지 않게 한다.
- Restart Policy는 Process Crash를 복구하되 영구 설정 오류의 무한 재시작을 Alert로 노출한다.
- Privileged Mode, Host PID·Network와 불필요한 Capability를 금지한다.

## Storage Infrastructure

### PostgreSQL

- 전용 PostgreSQL Container와 `postgres_data` Named Volume을 사용한다.
- Database Port는 Private Network에만 노출하고 Host Port를 게시하지 않는다.
- Migration Owner와 Runtime Role을 분리한다.
- U02~U06의 Unit Write Ownership은 Module Repository와 Database Grant로 집행한다.
- Online Query와 Worker Connection Pool을 분리하고 API 요청에 3초 Statement Timeout 기본 Profile을 적용한다.

### Persistent Volumes

| Volume | Owner | Retention and Protection |
|---|---|---|
| postgres_data | PostgreSQL | 일일 Off-host Backup, 직접 삭제 금지 |
| caddy_data | Caddy | 인증서·자동화 상태, 권한 제한 |
| prometheus_data | Prometheus | 초기 15일 또는 5GB 이내 |
| loki_data | Loki | 초기 7일 또는 7GB 이내 |
| grafana_data | Grafana | Dashboard·Alert 설정 Backup 대상 |
| otel_buffer | OTel Collector | 제한된 장애 Buffer, Business 영속성 없음 |

### Backup and Restore

Prototype Backup Runner는 PostgreSQL의 일관된 논리 Export와 Global Object Export를 생성하고, Manifest·Checksum을 만든 뒤 외부 S3-compatible Storage로 암호화 Upload한다.

- Schedule: 최소 일 1회
- Retention: 30일
- Object Storage: Versioning과 Lifecycle 활성화
- Encryption: 전송 중과 저장 시 적용; Key Material은 Backup과 분리
- Local Staging: Upload·Checksum 확인 후 제거
- Failure: Grafana Alert를 Email로 전달하고 선택적 Webhook 사용
- Restore: 일치하는 PostgreSQL Major Version의 격리 Container에서 실행
- Verification: Manifest, Schema, Integrity, 핵심 Feed·Recommendation Fallback Smoke Test

논리 Export는 단순 Prototype 복구에 한정한다. 상용 Production 전환 전 Managed Backup, Physical Backup 또는 WAL 기반 Point-in-time Recovery를 RPO와 데이터 규모에 맞게 재평가한다.

## Messaging Infrastructure

- 별도 Redis·RabbitMQ를 도입하지 않고 PostgreSQL Outbox와 Job Table을 사용한다.
- Ingestion과 Notification Worker는 Job Type별 Claim Query와 Lease를 사용한다.
- API Transaction은 Outbox Record까지만 원자적으로 Commit하고 외부 전달은 Worker가 수행한다.
- Retry, Dead Letter와 Manual Requeue 상태는 PostgreSQL에 영속화한다.
- Queue Depth, Claim Latency, Retry와 Dead Letter를 Prometheus Metric으로 노출한다.
- 전용 Broker 도입 Trigger는 지속적 Queue 포화, 다중 Host Worker 또는 PostgreSQL Job 부하가 Online Query SLO를 침해하는 경우다.

## Network Infrastructure

### Networks

| Network | Attached Services | Exposure |
|---|---|---|
| public_net | Caddy, Web, API | Caddy 80·443만 Host 공개 |
| private_net | API, Workers, PostgreSQL, Backup Runner | Host Port 없음; 필요한 Outbound NAT만 허용 |
| observability_net | Caddy, API, Workers, OTel Collector, Prometheus, Loki, Grafana | Internal Network; Grafana는 Caddy의 인증된 Route로만 접근 |

Caddy가 Client IP Header의 신뢰 경계를 소유한다. 외부에서 전달된 Forwarding Header를 무조건 신뢰하지 않으며 알려진 Upstream Proxy가 생길 때만 Trusted Proxy 범위를 명시한다.

### Caddy Edge

- Public Domain의 DNS가 Prototype Host를 가리키고 80·443 Inbound가 도달 가능한 상태에서 자동 HTTPS와 HTTP-to-HTTPS Redirect를 사용한다.
- `/api/*`는 API, Web Route는 Web Container, 보호된 운영 Route는 Grafana 또는 Admin API로 전달한다.
- Version을 고정한 공식 Caddy Image를 사용하며 비표준 Rate Limit Plugin이나 Custom Build를 사용하지 않는다.
- Host Firewall·Kernel의 연결 수준 제한과 FastAPI의 IP·인증 Identity·Endpoint별 HTTP Rate Limit을 결합한다. 제한 초과는 일관된 `429` 응답과 `Retry-After`를 반환하고 Metric·Log에 기록한다.
- Request Body Size, Header Size, Compression과 Upstream Timeout을 명시적으로 구성한다.
- API·Grafana의 Readiness 실패 시 Traffic을 전달하지 않는다.
- Caddy Configuration은 CI에서 구문 검증 후 배포한다.

## Monitoring Infrastructure

### Telemetry Flow

1. API와 Worker가 JSON Log, Prometheus-compatible Metric과 OpenTelemetry Trace Context를 생성한다.
2. OpenTelemetry Collector가 Log를 수집·Redact·Batch하여 Loki의 OTLP Endpoint로 전송한다.
3. Prometheus가 API, Worker, Collector와 Host Metric Endpoint를 Scrape한다.
4. Grafana가 Prometheus와 Loki를 Data Source로 사용한다.
5. Grafana Alerting이 Email을 기본 채널로 사용하고 선택적 Webhook을 호출한다.

### Required Dashboards

- Service Overview: Availability, Request Latency, Error와 Throughput
- Resource: CPU, Memory, Disk, Container Restart와 PostgreSQL Pool
- Jobs: Queue Depth, Age, Attempt, Retry와 Dead Letter
- Dependencies: Timeout, Circuit State, Fallback과 Provider Rate Limit
- Data and Recovery: Freshness, Backup Success, Last Verified Restore와 RTO·RPO

### Synthetic Checks

- 외부 GitHub Actions Scheduled Workflow 또는 독립 Uptime Runner가 Caddy를 통해 Public Feed를 점검한다.
- 규칙 기반 Recommendation Fallback을 별도 Scenario로 확인한다.
- Host 내부 Health가 정상이더라도 외부 Synthetic 실패는 Availability Incident 입력이 된다.

## Secret and Credential Design

- Compose Secret은 Service별로 명시적으로 Grant하고 Container의 `/run/secrets/` File로 주입한다.
- PostgreSQL Migration, API Runtime, Ingestion Worker, Notification Worker, Backup과 Monitoring Role을 분리한다.
- Caddy, Object Storage, Email·Webhook과 Provider Credential은 필요한 Service만 읽을 수 있다.
- Secret 값은 Compose File, Image, Log, CI Artifact와 `.env.example`에 포함하지 않는다.
- Secret File은 Host의 권한 제한 Directory에서 관리하고 Rotation은 Versioned Runbook을 따른다.

## Deployment and Rollback

1. GitHub Actions가 Source Revision에서 Test와 Scan을 실행한다.
2. Web, API와 Worker Image를 Build하고 GHCR에 Immutable Digest로 게시한다.
3. OpenAPI, Migration Set, PBT·Coverage와 Scan Evidence를 Release Artifact에 연결한다.
4. 운영자가 Host에서 새 Digest를 고정하고 Pre-deploy Backup과 Compatibility Gate를 실행한다.
5. Expand Migration 후 `docker compose pull`과 `docker compose up`으로 직접 배포한다.
6. Readiness, Synthetic Feed와 Recommendation Fallback을 검증한다.
7. 실패하면 이전 Image Digest와 Configuration을 재배포하고 Service Re-entry Check를 수행한다.

## Logical Component Mapping

| Logical Components | Infrastructure Resources |
|---|---|
| LC01 | Caddy Container, public_net, caddy_data |
| LC02~LC08 | API Container, private_net, PostgreSQL Policy Tables and Pools |
| LC09 | PostgreSQL Outbox and Job Tables |
| LC10 | Ingestion and Notification Worker Containers |
| LC11 | API·Worker Health Endpoints, Compose Healthcheck, Caddy Routing |
| LC12 | Application OTel SDK Configuration |
| LC13 | OpenTelemetry Collector and otel_buffer |
| LC14 | Prometheus, Loki, Grafana and Email·Webhook Contact Points |
| LC15 | GitHub Actions Artifact, GHCR Digest, Host Deployment Scripts |
| LC16 | Backup Runner, S3-compatible Storage and Backup Secret |
| LC17 | Isolated Restore Compose Profile and Smoke Test Runner |
| LC18 | GitHub Actions Quality·Security Jobs and Artifact Store |
| LC19 | Scheduled External Synthetic Workflow or Runner |

## Production Transition Gates

다음 조건을 충족하지 않으면 Prototype 구성을 상용 Production으로 분류할 수 없다.

1. Multi-zone Compute, Database와 Traffic Routing
2. Auto-scaling Minimum·Maximum과 Quota Monitoring
3. Managed 또는 검증된 Production Backup·Point-in-time Recovery
4. 외부 Synthetic와 독립 Observability 가용성
5. 정식 Change·Incident·On-call 절차
6. 개인정보·접근성·법무 검토
7. Capacity, Security, DR와 Chaos Test 결과

## Source Validation

- [Caddy Automatic HTTPS](https://caddyserver.com/docs/caddyfile/options)
- [Caddy Reverse Proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
- [Caddy Rate Limit Module Status](https://caddyserver.com/docs/modules/http.handlers.rate_limit)
- [Docker Compose Secrets](https://docs.docker.com/compose/how-tos/use-secrets/)
- [Docker Compose Networks](https://docs.docker.com/reference/compose-file/networks/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
- [Loki OTLP Ingestion](https://grafana.com/docs/loki/latest/send-data/otel/)
- [Prometheus Storage](https://prometheus.io/docs/prometheus/latest/storage/)
- [PostgreSQL Backup and Restore](https://www.postgresql.org/docs/current/backup.html)

## Extension Compliance

- **Resiliency**: 실제 Backup, Restore, Health, Monitoring, Alert, Deployment·Rollback과 Test Resource를 정의했다. RESILIENCY-08~09는 비운영 Prototype 예외이며 Production Gate로 차단한다.
- **PBT**: GitHub Actions 임시 Test 환경, Seed·Shrink Artifact와 Hypothesis 실행 기반을 정의했다.
- **Security Baseline**: 비활성화로 N/A. Network, Secret, TLS, Scan과 최소 권한은 일반 요구로 적용했다.

현재 Infrastructure Design에서 차단 상태인 Extension Finding은 없다.
