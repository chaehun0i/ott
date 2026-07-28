# U07 Non-Functional Requirements

## Scope and Assumptions

U07은 REST API Boundary, 공통 Runtime, Database Migration, Job 실행 기반, CI/CD, Backup·Restore와 Rollback 품질을 책임진다. 현재 목표는 외부 Production SLA가 없는 단일 서버 Prototype이며, 상용 Production 전환은 별도 Architecture Gate를 요구한다.

## Requirement Summary

| Area | Target |
|---|---|
| Initial capacity | 동시 사용자 10명 미만, 단일 API Process와 단일 Worker |
| Scale review trigger | 동시 사용자 50명 예상 또는 지속적 Resource Saturation |
| API boundary overhead | Downstream 제외 p95 100ms 이하 |
| Availability objective | 계획 유지보수 제외 월 99.0% |
| Recovery | RTO 4시간, RPO 24시간 |
| Backup | 자동 암호화, 최소 일 1회, 30일 보존 |
| API stack | FastAPI, Pydantic |
| Persistence | PostgreSQL, SQLAlchemy 2 style, Alembic, psycopg |
| Testing | pytest, Hypothesis |
| Delivery | Docker, GitHub Actions, GHCR, Version-pinned Rollback |

## Scalability and Capacity

- **U07-NFR-001**: 초기 Runtime은 단일 API Process와 단일 Worker Process에서 동시 사용자 10명 미만의 제품 흐름을 처리해야 한다.
- **U07-NFR-002**: CI 또는 Release 검증은 Feed·Search·추천 Fallback을 포함한 대표 부하에서 10명 동시 사용을 재현하고 Error, Latency, Throughput과 Saturation을 기록해야 한다.
- **U07-NFR-003**: 동시 사용자 50명 이상이 예상되거나 CPU, Memory, PostgreSQL Connection Pool 또는 Worker Queue의 지속적 포화가 관측되면 Multi-process·Replica·Queue 분리 설계를 재평가해야 한다.
- **U07-NFR-004**: 구체 포화 Alert Threshold와 Measurement Window는 NFR Design에서 정의하고 실제 부하 시험 결과로 조정해야 한다.
- **U07-NFR-005**: Prototype의 단일 서버 예외는 Production 용량 근거로 사용할 수 없으며 상용 전환 전 Multi-zone과 Auto-scaling 검토를 차단 Gate로 실행해야 한다.

## Performance

- **U07-NFR-006**: Downstream Application Service 처리 시간을 제외한 C02 REST Boundary의 p95 Overhead는 정상 부하에서 100ms 이하여야 한다.
- **U07-NFR-007**: 전체 Endpoint는 기존 제품 목표인 Feed·Detail p95 2초, Search p95 3초, 정상 외부 AI 조건의 Recommendation p95 10초를 침해하지 않아야 한다.
- **U07-NFR-008**: Performance Result는 최소 p50, p95, p99, Error Rate, Throughput과 Resource Saturation을 함께 기록해야 한다.
- **U07-NFR-009**: Serialization, 인증 Context 연결, Idempotency Lookup, Error Mapping과 Logging 비용을 Boundary Budget에 포함해야 한다.
- **U07-NFR-010**: 외부 HTTP, Database와 Runtime I/O에는 무제한 대기가 없어야 하며 구체 Timeout Budget은 NFR Design에서 Dependency별로 확정해야 한다.

## Availability and Recovery

- **U07-NFR-011**: 계획된 유지보수를 제외한 Prototype 월간 Service Objective는 99.0%로 한다.
- **U07-NFR-012**: 외부 Content·AI·OAuth·Notification Provider 장애는 내부 Platform Availability와 분리하여 측정하고 Degraded Response 성공률을 별도로 보고해야 한다.
- **U07-NFR-013**: 전체 Prototype Recovery Time Objective는 4시간, Persistent Data Recovery Point Objective는 24시간으로 한다.
- **U07-NFR-014**: DR Strategy는 비용과 Prototype 중요도에 맞는 Backup and Restore로 한다.
- **U07-NFR-015**: 모든 Persistent PostgreSQL Data와 필수 Configuration Reference는 최소 일 1회 자동 Backup해야 한다.
- **U07-NFR-016**: Backup은 저장 시 암호화하고 30일 보존하며 성공·실패와 Artifact Manifest를 추적해야 한다.
- **U07-NFR-017**: Restore는 Manifest·Schema·Data Integrity와 핵심 사용자 흐름 Smoke Test를 모두 통과해야 Verified로 판정한다.
- **U07-NFR-018**: Failover, Failback, Restore와 Service Re-entry 절차는 RTO 단계별 Runbook, 검증 증거와 영향·진행·복구 상태를 알리는 이해관계자 Communication Step을 가져야 한다.
- **U07-NFR-019**: DR Drill 빈도와 Chaos Scenario는 NFR Design에서 RESILIENCY-14 사용자 결정을 받은 뒤 확정해야 한다.

## Security and Privacy Platform Controls

Security Baseline Extension은 비활성화되어 있지만 다음 일반 요구는 필수이다.

- **U07-NFR-020**: 외부 Traffic의 TLS는 Reverse Proxy에서 종료하고 내부 API 노출 범위는 Deployment Network Policy로 제한해야 한다.
- **U07-NFR-021**: 운영 Secret은 Repository와 Container Image 밖의 권한 제한 File 또는 Docker Secret으로 주입해야 한다.
- **U07-NFR-022**: Local `.env`는 Version Control에서 제외하고 실제 Secret 값이 Example, Log, Test Fixture와 CI Artifact에 포함되지 않아야 한다.
- **U07-NFR-023**: Error Response와 구조화 Log는 Credential, Token, 직접 식별자, Provider Raw Payload, Stack Trace와 모델 내부 추론을 노출하지 않아야 한다.
- **U07-NFR-024**: 인증·권한·입력 검증은 Server Side에서 수행하며 U07은 U02의 Authorized Context 없이 보호 Route를 호출할 수 없게 해야 한다.
- **U07-NFR-025**: Dependency와 Container Image 취약점 검사를 CI 필수 Gate에 포함해야 하며 허용 기준과 예외 만료는 NFR Design에서 정해야 한다.
- **U07-NFR-026**: Backup Encryption Key Material은 Backup Metadata와 분리하고 Key Reference만 Application Data에 저장해야 한다.

## Reliability and Observability

- **U07-NFR-027**: 모든 API·Worker Log는 구조화 JSON과 Correlation ID 또는 Job ID를 가져야 하며 NFR Design에서 선택하는 중앙 Log 저장소로 수집되어야 한다.
- **U07-NFR-028**: API는 Latency, Error, Throughput과 Saturation Metric을, Worker는 Queue Depth, Attempt, Retry, Dead Letter와 처리 지연 Metric을 제공해야 한다.
- **U07-NFR-029**: API와 Worker는 Process 생존을 확인하는 Shallow Health와 PostgreSQL·필수 Dependency를 확인하는 Deep Health를 분리해야 한다.
- **U07-NFR-030**: Health Check는 정상 Traffic Routing과 분리된 저비용 Endpoint여야 하며 Deep Health 실패가 민감한 Dependency Detail을 외부에 노출해서는 안 된다.
- **U07-NFR-031**: Trace Context 전파를 지원해야 한다. 초기 모듈러 Monolith Prototype에서는 분산 Trace Backend 운영은 선택 사항이지만 Service 분리 전 필수 재평가한다.
- **U07-NFR-032**: 운영 Dashboard는 Availability, p95 Latency, Error Rate, Throughput, Resource Saturation, Queue Depth, Dead Letter, Backup 실패와 Data Freshness를 표시해야 한다.
- **U07-NFR-033**: Alert는 경량 Incident Response 흐름의 탐지, 영향 확인, 완화, 복구, 공지와 사후 분석으로 연결해야 한다.
- **U07-NFR-034**: 외부 Dependency 실패는 Timeout, 제한된 Retry, Circuit 또는 Open 상태, Resource Isolation과 명시적 Degradation Result를 가져야 한다.

## Maintainability and Testability

- **U07-NFR-035**: CI는 Format·Lint, Type Check, Unit, Contract, Integration과 Property-Based Test를 필수로 실행해야 한다.
- **U07-NFR-036**: 전체 Line Coverage 목표는 80% 이상이고 U07의 핵심 Business Rule Branch Coverage 목표는 100%로 한다.
- **U07-NFR-037**: Coverage 수치와 별개로 US-026, US-028과 BR-U07-001~038의 핵심 Scenario는 명시적 Example Test를 가져야 한다.
- **U07-NFR-038**: PBT는 pytest와 Hypothesis를 사용하며 Shrinking을 비활성화할 수 없다.
- **U07-NFR-039**: CI PBT 실행은 재현 가능한 Seed를 명시하고 Log해야 하며 실패 시 Shrunk 최소 반례와 Replay 정보를 Artifact로 보존해야 한다.
- **U07-NFR-040**: Functional Design에서 식별한 DTO Round-trip, Error 비노출, Idempotency, Cursor, Pagination, Outbox, Migration Compatibility와 Restore Guard Property를 Code Generation Plan에 포함해야 한다.
- **U07-NFR-041**: PBT는 Example Test를 대체하지 않으며 PBT가 발견한 최소 실패 사례는 영구 Regression Test로 추가해야 한다.
- **U07-NFR-042**: Versioned OpenAPI JSON과 Consumer Contract Compatibility 결과를 CI Artifact로 보존해야 한다.
- **U07-NFR-043**: Application Dependency는 재현 가능한 Lock과 Version Pinning을 사용하고 변경은 Test·취약점 검사와 Rollback Note를 통과해야 한다.

## API Developer Usability

- **U07-NFR-044**: Interactive OpenAPI 문서는 Local과 Test 환경에서 활성화해야 한다.
- **U07-NFR-045**: Production Interactive 문서는 비활성화하거나 운영자 인증으로 보호해야 한다.
- **U07-NFR-046**: ApiError Code, Pagination 방식, Idempotency 적용 Endpoint와 Version Compatibility Policy를 OpenAPI 설명에 포함해야 한다.
- **U07-NFR-047**: U07은 사용자 UI를 소유하지 않으므로 사용자 접근성 NFR은 N/A이며 U01로 전달한다.

## Verification Matrix

| NFR Set | Verification Method | Evidence Stage |
|---|---|---|
| 001~005 | Capacity Test와 Scale Review Checklist | Build and Test |
| 006~010 | Boundary Benchmark와 End-to-end Performance Test | Code Generation, Build and Test |
| 011~019 | Availability Report, Backup Artifact, Restore Drill와 Runbook Review | Infrastructure Design, Build and Test |
| 020~026 | Configuration Review, Secret Scan, Authorization·Redaction Test | Code Generation, Build and Test |
| 027~034 | Health·Metric·Log Contract Test와 Degradation Test | NFR Design, Code Generation |
| 035~043 | CI Gate, Coverage Report, PBT Seed·Shrink Artifact | Code Generation, Build and Test |
| 044~047 | Environment Configuration과 OpenAPI Review | Code Generation |

## Resiliency Compliance

| Rule | Status | U07 Treatment |
|---|---|---|
| RESILIENCY-01 | Compliant | U07 중요도, 사용자 영향과 U01~U06 의존성이 Unit 문서에 있다. |
| RESILIENCY-02 | Compliant | Availability 99.0%, RTO 4시간, RPO 24시간을 확정했다. |
| RESILIENCY-03 | Compliant | 기존 결정에 따라 경량 Change Record, 승인과 Rollback Note를 요구한다. |
| RESILIENCY-04 | Compliant | GitHub Actions, GHCR, 직접 배포와 Version-pinned Rollback을 유지한다. |
| RESILIENCY-05 | Compliant | Metric, 구조화 Log, Trace Context와 Dashboard를 요구한다. 단일 Service의 분산 Trace Backend는 N/A다. |
| RESILIENCY-06 | Compliant | Shallow·Deep Health와 Reverse Proxy Routing 연계를 요구한다. Synthetic Check 상세는 NFR Design으로 전달한다. |
| RESILIENCY-07 | Compliant | Backup·Capacity·Queue·Freshness Alert와 상용 전환 Assessment Gate를 정의했다. |
| RESILIENCY-08 | N/A | 비운영 단일 서버 Prototype의 승인 예외다. 상용 Production 전환 전 Multi-zone은 차단 Gate다. |
| RESILIENCY-09 | N/A | 초기 10명 미만 단일 서버 예외다. 50명 예상 또는 포화 시 Auto-scaling 재평가를 요구한다. |
| RESILIENCY-10 | Compliant | 모든 외부 호출 Timeout과 Retry·Circuit·Isolation·Degradation을 요구한다. |
| RESILIENCY-11 | Compliant | RTO·RPO에 맞는 Backup and Restore DR Strategy를 확정했다. |
| RESILIENCY-12 | Compliant | 자동 일일 암호화 Backup, 30일 보존과 Restore 검증을 요구한다. Cross-region은 Prototype 범위 밖이다. |
| RESILIENCY-13 | Compliant | Failover·Failback·Restore·Re-entry Runbook과 검증을 요구한다. |
| RESILIENCY-14 | N/A at this stage | 시험 방식은 의무 사용자 결정이므로 NFR Design에서 질문한다. |
| RESILIENCY-15 | Compliant | 경량 Incident와 사후 분석 흐름에 Alert를 연결한다. |

## PBT Compliance

| Rule | Status | U07 Treatment |
|---|---|---|
| PBT-01 | Compliant | Functional Design의 Component별 Property를 전달했다. |
| PBT-09 | Compliant | pytest와 Hypothesis를 선택하고 Dependency 등록을 Code Generation 필수 항목으로 지정했다. |
| PBT-08 | Planned | Seed Logging, Shrinking과 최소 반례 Artifact를 NFR로 확정했다. 구현은 Code Generation 대상이다. |
| PBT-02~07, PBT-10 | N/A at this stage | Test 구현 단계가 아니며 식별 Property와 Example Test 병행 요구를 전달했다. |

현재 NFR Requirements 단계에서 차단 상태인 Extension Finding은 없다.
