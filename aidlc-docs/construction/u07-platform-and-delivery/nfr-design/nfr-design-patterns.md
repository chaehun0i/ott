# U07 NFR Design Patterns

## Design Goals

- C02 API Boundary 자체 p95 Overhead 100ms 이하
- 월 99.0% Prototype Service Objective
- RTO 4시간, RPO 24시간의 Backup and Restore
- 외부 장애가 전체 API·Worker Resource를 고갈시키지 않는 격리
- 단일 서버에서 시작하되 Trigger 도달 시 Stateless API와 Worker Replica로 확장 가능
- 모든 실패·복구·배포가 Correlation과 Version으로 재현 가능

## Pattern 1 — Deadline and Timeout Budget

모든 동기 요청은 Absolute Deadline을 가지며 하위 호출은 남은 Budget보다 긴 Timeout을 설정할 수 없다.

| Dependency Profile | Initial Timeout | Retry Constraint | Failure Result |
|---|---|---|---|
| Synchronous AI | 추천 전체 10초 안에서 최대 8초 | 남은 Budget 안의 Retry-safe 실패만 허용 | 규칙 기반 추천과 승인 Metadata Template |
| General external HTTP | Connect 3초, Response 10초 | Worker 또는 충분한 상위 Deadline에서만 최대 2회 | Stale Data, Deferred Job 또는 Dependency Error |
| PostgreSQL online query | Statement 3초 | Transaction 안전성이 증명된 경우만 제한적 Retry | 표준 Dependency Error와 Readiness Signal |
| Batch and migration | 별도 명시 Profile | 동기 사용자 Budget과 분리 | Job Failure 또는 Release Block |

Library Default에 의존하는 무제한 Timeout은 허용하지 않는다. Timeout 값은 Configuration Schema로 중앙 관리하고 Call Site가 임의로 늘릴 수 없게 한다.

## Pattern 2 — Retry Budget with Backoff and Jitter

- Idempotent 또는 명시적으로 Retry-safe인 호출만 재시도한다.
- 최대 Retry 횟수는 2회이며 상위 Deadline을 초과하면 즉시 중단한다.
- Retry Delay는 지수 Backoff와 Jitter를 적용해 동시 재시도 폭주를 줄인다.
- Validation, Authorization, Payload Conflict와 Terminal Domain Error는 재시도하지 않는다.
- Worker Retry는 Outbox `retry_wait` 상태와 다음 시도 시각으로 영속화한다.
- 동기 AI는 10초 사용자 응답 Budget을 보존하며 Retry보다 Fallback을 우선한다.

## Pattern 3 — Circuit Breaker

각 외부 Dependency는 독립 Circuit State를 가진다.

| State | Behavior |
|---|---|
| Closed | 정상 호출과 결과 분류를 수행한다. |
| Open | 호출하지 않고 즉시 Dependency별 Fallback 또는 Retry Job으로 전환한다. |
| Half-open | 제한된 Probe만 허용하고 성공 시 Closed, 실패 시 Open으로 복귀한다. |

Failure Threshold, Observation Window와 Open Duration은 Configuration으로 관리하고 NFR 부하·장애 시험 결과로 조정한다. PostgreSQL은 일반 외부 Provider와 같은 Fallback이 없으므로 Circuit보다 Pool Timeout, Readiness와 빠른 실패를 우선한다.

## Pattern 4 — Bulkhead and Bounded Resources

- AI, Content Provider, OAuth, Notification과 PostgreSQL은 별도 Connection·Concurrency Limit을 가진다.
- API와 Worker의 Pool을 분리해 Worker 폭주가 사용자 요청 Connection을 소진하지 않게 한다.
- Queue Depth와 Dead Letter 증가를 관측하고 Producer가 무제한 Job을 생성하지 못하게 한다.
- CPU·장기 작업은 API Event Loop에서 실행하지 않고 Worker Job으로 전환한다.
- Initial Limit 값은 Infrastructure Design에서 Host Resource와 Load Test를 기반으로 확정한다.

## Pattern 5 — Graceful Degradation

| Failed Dependency | Degraded Behavior | Data Safety Rule |
|---|---|---|
| AI Provider | 규칙 기반 Ranking과 승인 Template | 검증되지 않은 AI 문구 노출 금지 |
| Content Provider | 마지막 정상 Catalog와 Stale 상태 | 기존 승인 Data 삭제 금지 |
| Notification Channel | Delivery Job Retry 또는 Dead Letter | 핵심 Feed·추천 성공과 격리 |
| Trace Backend | Local Correlation Log 유지 | 사용자 응답 차단 금지 |
| Metrics Backend | Application 기능 유지, 수집 실패 Alert | Request Path Block 금지 |
| PostgreSQL | Readiness 실패와 빠른 표준 오류 | 손상 가능 Write 금지 |

Degraded Response에는 Fallback 여부와 사용자에게 필요한 Data 상태만 표시하고 내부 장애 Detail은 숨긴다.

## Pattern 6 — Stateless API and Worker Scale-out

- API Instance는 Local Memory를 권위 있는 Session·Idempotency·Job 저장소로 사용하지 않는다.
- Idempotency, Session Reference와 Job State는 PostgreSQL 또는 명시적 공유 Store에 둔다.
- Scale Trigger 도달 후 API는 Stateless Replica로, Worker는 Job Type별 Replica로 확장한다.
- Outbox Claim은 원자적 Lease를 사용해 중복 처리를 방지한다.
- PostgreSQL Connection Budget은 전체 Replica 합계로 제한하며 Replica 추가가 Database 고갈을 만들지 않게 한다.
- Multi-host·Multi-zone은 상용 Production Gate에서 별도 승인한다.

## Pattern 7 — Async I/O and Work Separation

- FastAPI I/O Endpoint는 Async Boundary를 사용하고 Blocking Library는 제한된 Executor 또는 Adapter 뒤에 둔다.
- Backup, Restore, Migration, Provider Ingestion, Notification과 대량 Export는 Worker 또는 운영 Job으로 실행한다.
- 동기 추천은 사용자 Contract상 HTTP Response를 유지하지만 AI Deadline과 Fallback을 적용한다.
- Reverse Proxy는 정적 Asset과 정책상 허용된 대형 Response Compression을 담당한다.
- Compression은 이미 압축된 Media와 작은 Payload에는 적용하지 않는다.

## Pattern 8 — Layered Rate Limiting

1. Reverse Proxy가 IP 기반 기본 Token Bucket으로 비정상 Traffic을 우선 제한한다.
2. Application이 인증 Identity, Endpoint Category와 Cost Weight로 두 번째 Bucket을 적용한다.
3. 인증, 관리자와 AI 추천 Endpoint는 서로 다른 Bucket과 감사 Event를 가진다.
4. Rate Limit 결과는 표준 ApiError와 Retry 정보로 반환하고 Credential 존재 여부를 누설하지 않는다.
5. Limit 값은 Configuration으로 관리하고 정상 동시 사용자 10명 흐름을 차단하지 않도록 Load Test로 검증한다.

## Pattern 9 — Observability Pipeline

- API·Worker는 공통 Telemetry SDK로 JSON Log, Metric과 Trace Context를 생성한다.
- Log Collector가 Container 표준 출력을 중앙 Log Store로 전달한다.
- Prometheus-compatible Endpoint가 Request, Job, Pool, Queue, Backup과 Freshness Metric을 노출한다.
- Dashboard는 Availability, Latency, Error, Throughput, Saturation과 복원력 지표를 함께 표시한다.
- Alert Router는 경량 Incident Process와 사후 분석 Record로 연결한다.
- Trace Context는 API, Worker Job과 외부 Adapter에 전파한다. Trace Backend는 Prototype 선택 사항이다.

## Pattern 10 — Health and Synthetic Monitoring

| Check | Audience | Scope | Traffic Effect |
|---|---|---|---|
| Liveness | Runtime and Reverse Proxy | Process Event Loop 생존 | 실패 Instance 재시작 후보 |
| Readiness | Runtime and Reverse Proxy | 요청 처리에 필수인 PostgreSQL·Configuration | 실패 Instance Routing 제외 |
| Deep Health | Authorized Operator | 외부 AI·Provider·OAuth·Notification 상태 | Traffic Routing에 직접 사용하지 않음 |
| Synthetic Feed | External Monitor | 공개 Feed의 승인 Data 응답 | 사용자 관점 Availability 측정 |
| Synthetic Fallback | External Monitor | 규칙 기반 추천 Fallback | 저하 운용 가능성 검증 |

Deep Health는 Credential, Host, Error Payload를 노출하지 않는다.

## Pattern 11 — Backup and Restore Verification

- Backup Scheduler는 최소 일 1회 암호화 Backup과 Manifest를 생성하고 30일 Retention을 적용한다.
- Restore는 격리된 Target에서 실행하고 Manifest·Schema·Data Integrity 후 핵심 Smoke Test를 수행한다.
- 두 Gate가 모두 통과해야 `verified`가 된다.
- 월별 경량 Dependency Failure Test와 분기별 Backup Restore Drill을 수행한다.
- 결과는 실행 시각, Version, 대상 Backup, RTO·RPO 측정값, 실패와 Corrective Action을 포함한다.
- Drill 실패는 Incident·Correction Item으로 추적하며 다음 Drill 전에 재검증한다.

## Pattern 12 — Version-pinned Deployment and Rollback

- CI는 Git Commit, Release Tag, OpenAPI Artifact와 Image Digest를 하나의 Release Record로 연결한다.
- 직접 배포 전 Test, Vulnerability, Contract와 Migration Compatibility Gate를 통과한다.
- Expand-and-contract Migration으로 이전 Application Version 호환성을 유지한다.
- 실패 시 이전 Image Digest와 Configuration을 재배포하고 Database Down Migration은 기본 경로로 실행하지 않는다.
- Rollback 후 Readiness, Synthetic Feed와 Fallback Check를 수행해 Service Re-entry를 승인한다.

## Pattern 13 — Vulnerability Gate and Exception

- Severity 기반 Policy로 Dependency와 Container Finding을 분류한다.
- Gate 차단 기준은 Security·Infrastructure Design에서 Scanner Capability와 함께 확정한다.
- 예외는 Finding, 위험 근거, Owner, 보완 통제, 승인자와 최대 30일 만료를 가진 Versioned Record여야 한다.
- 만료된 예외는 자동으로 Gate를 다시 차단한다.
- Secret Scan은 Severity 예외 대상이 아니며 실제 Secret 발견 시 즉시 차단한다.

## Pattern 14 — Resiliency Test Program

사용자 선택에 따라 기존 조직 절차가 없는 개인 Prototype용 계획을 제안한다.

| Cadence | Test | Required Evidence |
|---|---|---|
| Monthly | AI·Content Provider Timeout, Circuit Open, Queue Retry·Dead Letter | Fallback 성공, Resource 비고갈, Alert와 Recovery 시간 |
| Quarterly | PostgreSQL Backup Restore Drill | Integrity, Smoke Test, 측정 RTO·RPO, Corrective Action |
| Before release with migration | Compatibility and Version Rollback rehearsal | 이전 Image 동작, Schema 호환, Synthetic Check |
| After major dependency change | Dependency failure regression | Timeout, Retry, Circuit와 Log·Metric Contract |

Test 결과는 Versioned Build-and-Test Evidence에 저장하고 실패는 경량 Incident·COE 흐름으로 추적한다.

## Pattern 15 — PBT Handoff

- pytest와 Hypothesis를 사용한다.
- Functional Design의 DTO Round-trip, Error 비노출, Idempotency, Cursor, Pagination, Outbox, Migration Compatibility와 Restore Guard를 유지한다.
- Domain Strategy는 유효 Version, State와 Constraint를 생성하며 Primitive-only Generator를 금지한다.
- Shrinking을 유지하고 CI Seed를 명시·기록한다.
- Stateful Outbox와 Restore Test는 Reference Model과 각 Command 이후 상태를 비교한다.
- PBT는 US-026·US-028 Example Test와 월별·분기별 복원력 Test를 대체하지 않는다.

## NFR Traceability

| NFR IDs | Design Patterns |
|---|---|
| U07-NFR-001~005 | Patterns 4, 6, 7 |
| U07-NFR-006~010 | Patterns 1, 2, 4, 7 |
| U07-NFR-011~019 | Patterns 5, 10, 11, 12, 14 |
| U07-NFR-020~026 | Patterns 8, 12, 13 and Infrastructure Secret·TLS Design |
| U07-NFR-027~034 | Patterns 1~5, 9, 10 |
| U07-NFR-035~043 | Patterns 12, 13, 15 |
| U07-NFR-044~047 | Pattern 12 and API Documentation Configuration |

## Resiliency Compliance

| Rules | Status | Pattern Coverage |
|---|---|---|
| RESILIENCY-01~02 | Compliant | 중요도, 99.0%, RTO 4시간과 RPO 24시간 유지 |
| RESILIENCY-03~04 | Compliant | Versioned Change, CI Gate, 직접 배포와 Rollback Pattern |
| RESILIENCY-05~07 | Compliant | Observability, Health, Synthetic, Capacity와 Backup Alert |
| RESILIENCY-08~09 | N/A for Prototype | 단일 서버 예외; Scale Trigger와 Production Gate 유지 |
| RESILIENCY-10 | Compliant | Deadline, Retry, Circuit, Bulkhead와 Degradation |
| RESILIENCY-11~13 | Compliant | Backup and Restore, Runbook, 검증과 Service Re-entry |
| RESILIENCY-14 | Compliant | 월별 Failure Test와 분기별 Restore Drill을 사용자 선택으로 확정 |
| RESILIENCY-15 | Compliant | Alert, Incident, COE와 Corrective Action 연결 |

## PBT Compliance

- **PBT-01**: Functional Design의 Property Category와 Component Mapping을 보존했다.
- **PBT-09**: pytest·Hypothesis, Domain Strategy, Shrinking과 Seed 재현을 Pattern 15에 반영했다.
- **PBT-02~08, PBT-10**: 구현 단계 적용을 위한 Pattern과 Handoff가 준비되었으며 현재 단계에서는 N/A이다.

현재 NFR Design에서 차단 상태인 Extension Finding은 없다.
