# U06 Engagement and Operations Infrastructure Design Plan

> **Single Source of Truth**: 이 파일은 U06 Infrastructure Design의 결정, 사용자 답변과 완료 체크박스를 관리한다. 모든 답변이 유효하고 모호하지 않을 때만 설계 산출물을 생성한다.

## Context

- **Approved Inputs**: U06 Functional Design, U06-NFR-001~075, ADR-U06-001~010, U06 NFR Design.
- **Inherited Platform**: Python 3.12.13 modular monolith, PostgreSQL 17, Docker Compose, Prometheus, Grafana and U07 health registry.
- **Recovery Baseline**: 99.0% monthly availability, RTO 4 hours, RPO 24 hours, Backup and Restore, 30-day encrypted backup retention.
- **Deployment Baseline**: Single-region, single-server prototype; automatic GitHub Actions triggers remain paused and controlled verification is manual-only.
- **Enabled Extensions**: Resiliency Baseline (Full), Property-Based Testing (Full).
- **Disabled Extension**: Security Baseline. Core authorization, secrets, privacy and audit controls remain mandatory requirements.

## Execution Plan

### Step 1 - Inputs and Decision Collection

- [x] U06 Functional Design, NFR Requirements and NFR Design artifacts를 분석한다.
- [x] 배포 환경, 컴퓨트, 저장소, 메시징, 네트워크, 모니터링과 공유 인프라의 미결정 항목을 식별한다.
- [x] 상호 배타적인 선택지와 마지막 `X) Other`를 포함한 Question 1~12를 작성한다.
- [ ] 모든 `[Answer]:` 값을 수집하고 선택지 유효성, 모호성 및 결정 충돌을 검증한다.
- [ ] 필요한 경우 별도 clarification 질문을 생성하고 해소한다.

### Step 2 - Runtime and Data Infrastructure

- [ ] API, notification worker와 maintenance 실행 단위, 자원 한도 및 재시작 정책을 매핑한다.
- [ ] U06 PostgreSQL schema, runtime role, migration role, connection budget와 백업 범위를 매핑한다.
- [ ] Transactional Outbox claim/lease 처리와 확장 시 broker 진입 경계를 매핑한다.
- [ ] 이메일 provider 자격 증명, audit HMAC key ring과 secret mount/rotation 경계를 정의한다.

### Step 3 - Network and Observability Infrastructure

- [ ] 외부 노출 endpoint, 내부 network, PostgreSQL 접근과 email egress 경계를 정의한다.
- [ ] shallow/deep health, Prometheus scrape, Grafana dashboard와 alert routing을 배치에 연결한다.
- [ ] 구조화 로그의 중앙 수집 방식과 개인정보 금지 필드를 정의한다.
- [ ] 백업, 복원, dependency failure test와 운영 증적 보관 위치를 정의한다.

### Step 4 - Artifacts and Validation

- [ ] `infrastructure-design.md`를 생성한다.
- [ ] `deployment-architecture.md`를 생성하고 배포 흐름의 텍스트 대안을 포함한다.
- [ ] 공유 인프라 변경 필요성을 판정하고 필요한 경우 `shared-infrastructure.md`를 갱신한다.
- [ ] RESILIENCY-01~15 적용 여부와 U06-NFR/ADR traceability를 검증한다.
- [ ] Markdown, diagram syntax와 special-character escaping을 검증한다.
- [ ] 계획, 상태와 감사 기록을 갱신하고 표준 Infrastructure Design 승인 지점을 제시한다.

## Infrastructure Design Questions

각 `[Answer]:` 뒤에 선택한 문자 하나를 입력한다. 적합한 선택지가 없으면 `X`를 선택하고 같은 줄에 원하는 내용을 설명한다.

## Question 1
U06를 어떤 배포 환경에 추가합니까?

A) 기존 단일 지역·단일 서버 Docker Compose 프로토타입을 확장하고 새로운 cloud-managed service는 추가하지 않는다

B) 단일 cloud region의 managed container와 managed PostgreSQL로 이전한다

C) 온프레미스 다중 서버 container cluster와 별도 PostgreSQL 서버로 배포한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 2
U06 compute process를 어떻게 분리합니까?

A) 기존 API service와 별도 `u06-worker` service를 두고 worker 내부에서 in-app/email bounded lane을 분리하며 maintenance는 one-shot Compose profile로 실행한다

B) API process 안에서 notification과 maintenance background task를 모두 실행한다

C) in-app worker, email worker와 maintenance worker를 각각 독립 상시 service로 분리한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 3
초기 compute sizing과 재시작 정책을 어떻게 적용합니까?

A) API/worker에 명시적 CPU·memory limit과 health-based restart를 적용하고 lane concurrency 2/2, maintenance 1을 환경 설정으로 제한하며 자동 확장은 사용하지 않는다

B) container 자원 한도 없이 host가 허용하는 만큼 사용하고 자동 재시작만 적용한다

C) 초기부터 queue age와 CPU 기반 다중 worker 자동 확장을 구성한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 4
U06 PostgreSQL 저장소와 접근 격리를 어떻게 구성합니까?

A) 기존 PostgreSQL 17 instance에 U06 전용 schema를 만들고 migration owner, API, worker, maintenance 역할을 분리하며 connection budget 4/2/1을 강제한다

B) 기존 application schema와 runtime role을 U06가 그대로 공유한다

C) U06 전용 PostgreSQL instance를 별도로 배포한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 5
U06 데이터 lifecycle과 복구 인프라는 어떻게 구성합니까?

A) 기존 U07 암호화 백업에 U06 schema를 포함하고 30일 보관, 월별 dependency failure test와 분기별 실제 restore drill을 유지한다

B) U06 schema dump를 비정기 수동 백업하고 restore drill은 Operations 단계까지 연기한다

C) U06 전용 실시간 replica와 별도 장기 보관 저장소를 추가한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 6
비동기 notification messaging 인프라는 무엇을 사용합니까?

A) PostgreSQL Transactional Outbox와 `FOR UPDATE SKIP LOCKED` claim/lease/fencing을 사용하고 queue SLO 미달 전에는 broker를 추가하지 않는다

B) 초기부터 Redis Streams를 추가한다

C) 초기부터 Kafka 또는 cloud-managed message broker를 추가한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 7
외부·내부 network topology를 어떻게 구성합니까?

A) API만 기존 reverse proxy를 통해 노출하고 worker, PostgreSQL, Prometheus와 Grafana는 내부 network에 두며 worker는 허용된 email provider로만 outbound egress한다

B) 모든 service port를 host에 직접 공개하고 host firewall로만 제한한다

C) 별도 API Gateway, service mesh와 private subnet 계층을 추가한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 8
U06 secret과 audit HMAC key ring을 어떻게 제공합니까?

A) Git에 포함되지 않는 read-only secret file을 container에 mount하고 current/previous key ID를 지원하며 email credential도 별도 secret file로 주입한다

B) Compose environment 값에 직접 입력하고 운영자가 수동으로 교체한다

C) cloud-managed secret manager와 자동 rotation을 도입한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 9
U06 metrics, health와 dashboard를 어디에 연결합니까?

A) 기존 U07 Prometheus/Grafana에 API와 worker scrape target, shallow/deep health, queue/email/audit/incident/capacity dashboard와 alert rule을 추가한다

B) application log만 확인하고 별도 metrics/dashboard는 추가하지 않는다

C) 새로운 외부 SaaS observability platform으로 전환한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 10
구조화 로그를 어떻게 중앙 수집합니까?

A) API/worker가 JSON을 stdout으로 출력하고 기존 Docker logging driver의 host 회전 파일을 중앙 수집 지점으로 사용하며 prototype 이후 외부 backend 진입 조건을 문서화한다

B) 각 container 내부 파일에만 저장하고 회전·중앙 수집을 구성하지 않는다

C) 즉시 별도 Loki/ELK service를 Compose에 추가한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 11
U06와 기존 단위 사이의 공유 인프라 원칙은 무엇입니까?

A) PostgreSQL, reverse proxy, Prometheus/Grafana와 backup mechanism만 공유하고 schema, role, worker resource와 secrets는 U06 경계로 격리한다

B) runtime role, schema, worker pool과 secrets까지 모든 단위가 공유한다

C) U06의 database, monitoring, network와 backup을 모두 전용 instance로 분리한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 12
프로토타입 인프라의 availability·deployment 예외를 어떻게 유지합니까?

A) 승인된 99.0%, RTO 4시간, RPO 24시간과 Backup and Restore에 맞춰 단일 서버 예외를 유지하고 multi-zone/autoscale 진입 조건을 문서화하며 GitHub Actions는 수동 검증이 전부 통과할 때까지 자동 trigger를 재활성화하지 않는다

B) 지금 즉시 multi-zone compute/database와 rolling deployment로 전환한다

C) availability, recovery와 deployment gate를 별도로 두지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Planned Artifacts

- `aidlc-docs/construction/u06-engagement-and-operations/infrastructure-design/infrastructure-design.md`
- `aidlc-docs/construction/u06-engagement-and-operations/infrastructure-design/deployment-architecture.md`
- `aidlc-docs/construction/shared-infrastructure.md` (공유 경계 변경이 필요한 경우에만)

## Preliminary Extension Assessment

### Resiliency Baseline

- Questions 1~3 and 12 decide the approved prototype topology, capacity limits and RESILIENCY-08~09 exception/evolution gates.
- Questions 5, 9 and 10 decide RESILIENCY-05~07 and RESILIENCY-11~14 infrastructure evidence.
- Questions 6~7 decide RESILIENCY-06 and RESILIENCY-10 dependency isolation and failure containment.
- Final compliance remains blocked until all answers are validated and both infrastructure artifacts are generated.

### Property-Based Testing

- Infrastructure Design maps the real PostgreSQL and failure-test environments required by PBT integration gates; property definitions and test generation remain Code Generation responsibilities.

### Security Baseline

- Disabled and therefore N/A as an extension. Questions 4, 7, 8, 10 and 11 preserve mandatory core least-privilege, secret, network, audit and telemetry privacy boundaries.
