# U07 Platform and Delivery Infrastructure Design Plan

## Fixed Infrastructure Constraints

- Cloud-provider-neutral Linux 단일 서버 Prototype
- Docker Compose 기반 Web, API, Worker, PostgreSQL와 운영 Component
- GitHub Actions Build·Test, GHCR Immutable Image
- Reverse Proxy TLS와 Version-pinned 직접 배포·Rollback
- RTO 4시간, RPO 24시간, 일일 암호화 Backup과 30일 보존
- 단일 서버는 비운영 Prototype 예외이며 상용 전환 전 Multi-zone·Auto-scaling 재설계 필수
- Application Code는 Workspace Root, 문서는 `aidlc-docs/`에만 저장

## Mandatory Category Assessment

| Infrastructure Category | Applicability | Decision Needed |
|---|---|---|
| Deployment Environment | Applicable | Local·CI·Production 환경 구성 |
| Compute Infrastructure | Applicable | 초기 Host Sizing |
| Storage Infrastructure | Applicable | PostgreSQL 배치와 Off-host Backup |
| Messaging Infrastructure | Applicable | PostgreSQL Outbox 유지 또는 Broker 도입 |
| Networking Infrastructure | Applicable | Reverse Proxy와 Network Zone |
| Monitoring Infrastructure | Applicable | Metric·Log·Dashboard와 Alert 제품 |
| Shared Infrastructure | Applicable | Unit 간 Database·Telemetry·Network 공유와 격리 |

## Infrastructure Questions

### Question 1 — Environment Topology

Prototype 환경 구성을 무엇으로 확정합니까?

A) Local Docker Compose, GitHub Actions의 임시 Test 환경, 단일 Remote Prototype 환경을 사용하고 별도 Staging Host는 두지 않는다.

B) Local, 별도 Staging Host, 별도 Production Host를 운영한다.

C) Remote 환경 없이 Local Docker Compose에서만 실행한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 2 — Initial Host Size

Web, API, Worker, PostgreSQL과 경량 관측성을 함께 실행할 초기 단일 Host 기준은 무엇입니까?

A) 4 vCPU, 8GB RAM, 100GB SSD를 기준으로 시작하고 실제 부하·보존량에 따라 조정한다.

B) 2 vCPU, 4GB RAM, 50GB SSD의 최소 비용 구성을 사용한다.

C) 8 vCPU, 16GB RAM, 200GB SSD로 여유 용량을 우선한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 3 — PostgreSQL Placement

Prototype PostgreSQL을 어디에 배치합니까?

A) 같은 Host의 전용 PostgreSQL Container와 Named Volume을 사용하고 Host 밖 Backup으로 단일 서버 손실을 대비한다.

B) 외부 Managed PostgreSQL을 사용한다.

C) 별도 Database VM에 PostgreSQL을 직접 운영한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 4 — Backup Destination

암호화 Backup의 Host 외부 저장소는 무엇으로 확정합니까?

A) Versioning과 Lifecycle을 지원하는 S3-compatible Object Storage에 암호화하여 저장하고 30일 보존한다.

B) 같은 Host에 연결된 두 번째 Disk에만 저장한다.

C) 운영자가 주기적으로 Local Backup을 내려받아 보관한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 5 — Messaging and Jobs

초기 비동기 작업 Infrastructure는 무엇으로 확정합니까?

A) PostgreSQL-backed Outbox와 Job Table을 유지하고 Queue 포화 또는 Scale Trigger 도달 시 전용 Broker를 재평가한다.

B) 초기부터 Redis 기반 Queue를 도입한다.

C) 초기부터 RabbitMQ 같은 전용 Message Broker를 도입한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 6 — Reverse Proxy

TLS, Routing, Compression과 IP Rate Limit을 담당할 Reverse Proxy는 무엇으로 확정합니까?

A) Caddy를 사용해 자동 인증서 관리와 단순한 단일 Host 구성을 우선한다.

B) Nginx와 별도 인증서 자동화 도구를 사용한다.

C) Traefik과 Docker Label 기반 Routing을 사용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 7 — Monitoring Stack

단일 서버의 Metric·Log·Dashboard Infrastructure를 무엇으로 확정합니까?

A) Prometheus-compatible Metric 수집, Grafana Dashboard와 Loki-compatible 중앙 Log 저장을 사용하고 Collector는 OpenTelemetry-compatible 구성을 선택한다.

B) 외부 Hosted Observability Service를 사용한다.

C) Local Log File과 수동 Health 확인만 사용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 8 — Alert Delivery

Prototype 운영 Alert 채널은 무엇으로 확정합니까?

A) Email을 기본 채널로 사용하고 선택적 Webhook을 추가한다.

B) Email만 사용한다.

C) Webhook만 사용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 9 — Shared Resource Isolation

7개 Unit이 공유 Infrastructure를 사용하는 방식은 무엇으로 확정합니까?

A) 하나의 Compose Project 안에서 Public, Private와 Observability Network를 분리하고 Service별 Credential·Volume·Resource Limit과 Unit별 Database Write Ownership을 적용한다.

B) 모든 Container를 하나의 Flat Network와 공용 Database Credential로 연결한다.

C) Unit마다 별도 Compose Project와 PostgreSQL Instance를 운영한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Technical Validation Follow-up

Caddy 공식 문서 검증 결과 자동 HTTPS와 Reverse Proxy는 표준 기능이지만 HTTP Request Rate Limit Module은 공식 Image에 포함되지 않는 비표준 Plugin이다. 또한 자동 Public Certificate에는 실제 Domain과 DNS·Port 도달 조건이 필요하다. 다음 두 결정을 확정해야 한다.

### Follow-up Question 10 — Edge Rate Limit Implementation

Caddy를 유지하면서 Edge Rate Limit을 어떻게 구현합니까?

A) 공식 Caddy Image를 유지하고 Host의 연결 수준 제한과 FastAPI의 IP·Identity·Endpoint Rate Limit을 결합한다. 비표준 Caddy Plugin은 사용하지 않는다.

B) Version과 Source를 고정한 비표준 Caddy Rate Limit Module을 포함한 Custom Image를 Build하고 취약점·Update Gate를 적용한다.

C) Caddy 대신 Nginx와 인증서 자동화 도구로 변경해 Proxy 계층 HTTP Rate Limit을 사용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Follow-up Question 11 — Domain and Certificate

Remote Prototype의 HTTPS Domain 조건은 무엇입니까?

A) Public Domain과 DNS를 준비하고 80·443 Inbound를 허용하여 Caddy 자동 HTTPS를 사용한다.

B) 아직 Public Domain이 없으므로 초기 Remote 환경은 Private 접근과 내부·수동 Certificate를 사용하고 Domain 준비 후 자동 HTTPS로 전환한다.

C) Remote Prototype을 당분간 배포하지 않고 Local HTTPS만 사용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Execution Checklist

- [x] U07 Functional, NFR Requirements와 NFR Design Artifacts를 분석한다.
- [x] LC01~LC19의 Infrastructure Mapping 필요사항을 식별한다.
- [x] 7개 필수 Infrastructure Category를 모두 평가한다.
- [x] 기존 제약과 미확정 Resource 결정을 분리한다.
- [x] 9개 Context-specific Question을 작성한다.
- [x] 모든 답변의 완전성과 선택지 유효성을 검사한다. 11개 답변 모두 A로 유효하다.
- [x] 모호성, 결합 선택, 충돌과 NFR 위반을 분석한다. Caddy 공식 Image·Application Rate Limit·Public Domain 자동 HTTPS 결정은 상호 일관된다.
- [x] 필요한 Follow-up Question을 추가하고 해소한다. Follow-up 10~11의 A 답변을 반영했다.
- [x] `infrastructure-design.md`를 생성한다.
- [x] `deployment-architecture.md`를 생성한다.
- [x] Shared Infrastructure가 존재하므로 `aidlc-docs/construction/shared-infrastructure.md`를 생성한다.
- [x] LC01~LC19를 실제 Infrastructure Resource에 매핑한다.
- [x] Environment, Network, Storage, Backup, Monitoring과 Secret 경계를 검증한다. Edge와 Certificate 전제조건을 포함했다.
- [x] RTO·RPO, Rollback과 Resiliency Test 실행 가능성을 검증한다.
- [x] RESILIENCY-01~15와 PBT 후속 Handoff를 검증한다. Prototype 예외와 Production Gate를 유지했다.
- [x] Mermaid를 사용하는 경우 구문과 Text Alternative를 검증한다.
- [x] Infrastructure Design 완료 승인 요청을 기록한다.

## Planned Outputs

### infrastructure-design.md

- Environment와 Resource Inventory
- Compute, Storage, Messaging, Network와 Monitoring Mapping
- Secret, Backup, Recovery와 Resource Isolation
- Capacity, Security, Cost와 Production-transition Gates

### deployment-architecture.md

- Container와 Network Topology
- Request, Job, Telemetry, Backup과 Deployment Flow
- Health, Rollback와 Restore Sequence
- Mermaid Diagram과 Text Alternative

### shared-infrastructure.md

- 7개 Unit이 공유하는 Resource와 소유권
- Database Schema·Credential·Network·Telemetry 격리
- Shared Change와 Failure 영향 관리

## Extension Compliance at Planning

- **Resiliency**: Backup·Restore, Health, Monitoring, 직접 배포·Rollback과 월별·분기별 Test를 실제 Resource에 매핑할 계획이다.
- **PBT**: Infrastructure는 Hypothesis 실행·Seed Artifact를 지원하는 CI와 Test 환경을 제공한다. PBT Test 구현은 Code Generation 대상이다.
- **Security Baseline**: 비활성화로 N/A. TLS, Secret 분리, Network 격리와 취약점 Gate는 일반 요구로 유지한다.
