# U07 Platform and Delivery NFR Requirements Plan

## Context and Fixed Constraints

- Python Backend, React Frontend, PostgreSQL, Docker
- GitHub Actions Build·Test와 GHCR Versioned Image
- Cloud-provider-neutral 단일 서버 Prototype
- 초기 동시 사용자 10명 미만
- Feed·Detail p95 2초, Search p95 3초, AI Recommendation p95 10초의 제품 목표
- 수 시간 단위 RTO·RPO, 암호화 Backup과 30일 보존
- Application Version Rollback과 Expand-and-contract Migration
- Security Baseline Extension은 비활성화되었으나 핵심 보안·개인정보 요구는 필수
- Resiliency Baseline과 Property-Based Testing은 Full Mode

## Category Assessment

| NFR Category | Applicability | Existing Evidence | Decision Needed |
|---|---|---|---|
| Scalability | Applicable | 단일 서버, 동시 사용자 10명 미만 | 용량 운영 방식과 확장 Trigger |
| Performance | Applicable | 제품 API p95 목표 | U07 Boundary Overhead Budget |
| Availability | Applicable | 단일 서버 예외, 수 시간 복구 | Service Objective와 정확한 RTO·RPO |
| Security | Applicable | TLS, Secret 분리, 권한·입력 검증 | Prototype Secret·TLS 운영 방식 |
| Tech Stack | Applicable | Python, PostgreSQL, Docker | Framework, Persistence, Test Stack |
| Reliability | Applicable | Health, Fallback, Backup, Rollback | Telemetry 최소 집합과 Alert 입력 |
| Maintainability | Applicable | CI, Contract, PBT | 품질 Gate와 Coverage Policy |
| Usability | Limited | U07은 UI를 소유하지 않음 | API 문서의 안전한 Developer Usability |

## NFR Questions

### Question 1 — Scalability Posture

Prototype의 용량과 확장 정책을 무엇으로 확정합니까?

A) 단일 API Process·단일 Worker 기준으로 부하 시험하고, 지속적인 CPU·Memory·DB Pool 포화 또는 동시 사용자 50명 예상 시 수평 확장 설계를 재평가한다.

B) 초기부터 여러 API·Worker Replica의 수평 확장을 지원한다.

C) 부하 시험과 확장 Trigger 없이 동시 사용자 10명 미만 가정만 유지한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 2 — API Boundary Performance Budget

Downstream 처리 시간을 제외한 U07 API Boundary의 p95 Overhead 목표는 무엇입니까?

A) 정상 조건에서 p95 100ms 이하를 목표로 한다.

B) 정상 조건에서 p95 250ms 이하를 목표로 한다.

C) 별도 Boundary Budget을 두지 않고 전체 Endpoint 목표만 측정한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 3 — Prototype Availability Objective

계획된 유지보수를 제외한 Prototype의 월간 Availability 목표는 무엇입니까?

A) 99.0% Service Objective를 두되 외부 Provider 장애는 별도 지표로 분리한다.

B) 99.5% Service Objective를 적용한다.

C) 정량 목표 없이 Best-effort로 운영한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 4 — Recovery Objectives

수 시간 단위 복구 목표를 어떤 값으로 확정합니까?

A) RTO 4시간, RPO 24시간으로 시작하고 상용 전환 전에 재평가한다.

B) RTO 8시간, RPO 24시간으로 시작한다.

C) RTO 4시간, RPO 4시간으로 더 잦은 Backup을 요구한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 5 — TLS and Secret Delivery

Cloud-neutral 단일 서버에서 TLS와 Secret을 어떻게 제공합니까?

A) Reverse Proxy에서 TLS를 종료하고, 운영 Secret은 Repository·Image 밖의 권한 제한 File 또는 Docker Secret으로 주입한다. Local `.env`는 Git에서 제외한다.

B) Python API가 TLS를 직접 종료하고 모든 Secret은 Environment Variable만 사용한다.

C) Prototype에서는 TLS 없이 Private Network에서 실행하고 Secret은 `.env`로만 관리한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 6 — Python API Framework

REST/OpenAPI Boundary 구현 Stack을 무엇으로 확정합니까?

A) FastAPI와 Pydantic 기반 Typed Contract를 사용한다.

B) Django와 Django REST Framework를 사용한다.

C) Flask와 별도 OpenAPI Schema Tool을 사용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 7 — PostgreSQL Access and Migration

Database Access와 Migration Stack을 무엇으로 확정합니까?

A) SQLAlchemy 2 style, Alembic, psycopg를 사용하고 Repository Adapter 경계를 둔다.

B) Django ORM과 Django Migration을 사용한다.

C) Raw SQL과 수동 Versioned Migration Script를 사용한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 8 — Python Test and PBT Framework

PBT-09를 충족할 Python Test Stack은 무엇으로 확정합니까?

A) pytest와 Hypothesis를 사용하고 Shrinking을 유지하며 실패 Seed와 최소 반례를 CI Artifact에 기록한다.

B) unittest와 Hypothesis를 사용한다.

C) 예제 기반 pytest만 사용하고 PBT는 나중에 도입한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 9 — Observability Baseline

U07이 모든 Unit에 제공할 최소 관측성 Contract는 무엇입니까?

A) 구조화 JSON Log, Correlation ID, Request·Job Metric, Health Endpoint를 필수로 하고 Trace Context 전파는 지원하되 분산 Trace Backend는 Prototype에서 선택 사항으로 둔다.

B) Text Log와 Health Endpoint만 제공한다.

C) Log, Metric, Trace Backend를 초기부터 모두 운영한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 10 — Maintainability Quality Gates

CI의 필수 품질 Gate를 무엇으로 확정합니까?

A) Format·Lint, Type Check, Unit·Contract·Integration·PBT를 필수로 하고 전체 Line Coverage 80% 및 핵심 Business Rule Branch Coverage 100%를 목표로 한다.

B) Test 통과만 필수로 하고 Coverage 수치와 정적 검사는 권고로 둔다.

C) Format·Lint와 Unit Test만 필수로 하며 Integration·PBT는 수동 실행한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 11 — API Documentation Usability

Interactive OpenAPI 문서 노출 정책은 무엇입니까?

A) Local·Test에서는 활성화하고, Production에서는 비활성화하거나 운영자 인증 뒤에 둔다. Versioned OpenAPI JSON은 CI Contract Artifact로 게시한다.

B) 모든 환경에서 인증 없이 공개한다.

C) Interactive 문서는 만들지 않고 정적 Markdown API 문서만 유지한다.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Execution Checklist

- [x] U07 Functional Design 세 문서와 PBT-01 Property를 분석한다.
- [x] Scalability, Performance, Availability, Security, Tech Stack, Reliability, Maintainability, Usability 범주를 모두 평가한다.
- [x] 기존 확정 NFR과 미확정 결정을 분리한다.
- [x] 11개 Context-specific Question을 작성한다.
- [x] 모든 답변의 완전성과 선택지 유효성을 검사한다.
- [x] 모호성, 결합 선택, 충돌과 기존 요구사항 위반을 분석한다.
- [x] 필요한 Follow-up Question을 추가하고 해소한다. 추가 질문 불필요.
- [x] `nfr-requirements.md`를 생성한다.
- [x] `tech-stack-decisions.md`를 생성한다.
- [x] PBT-09 Framework 선택, Shrinking과 Seed 재현 요구를 검증한다.
- [x] Resiliency Baseline의 적용 Rule별 준수 상태를 검증한다.
- [x] Security Baseline 비활성 상태와 일반 핵심 보안 요구의 보존을 검증한다.
- [x] Markdown과 복잡 콘텐츠를 검증한다.
- [x] NFR Requirements 완료 승인 요청을 기록한다.

## Planned Outputs

### nfr-requirements.md

- Capacity and scalability target
- Latency and throughput budget
- Availability, RTO and RPO
- Security and privacy platform controls
- Reliability, observability and operational quality
- Maintainability and API usability
- Requirement identifiers and verification methods

### tech-stack-decisions.md

- Python API framework
- PostgreSQL access and migration libraries
- Test runner and Property-Based Testing framework
- Logging, Metrics, Health and Contract tooling direction
- Docker, GitHub Actions and GHCR constraints
- Version pinning and update policy

## Extension Compliance at Planning

- **PBT-09**: Framework 선택을 Question 8과 필수 산출물로 포함했다. 답변 전 상태는 진행 중이며 차단 Finding은 없다.
- **PBT-01**: Functional Design에서 식별한 Property를 NFR과 Code Generation으로 전달한다.
- **Resiliency**: Availability, RTO, RPO, 관측성, Backup·Restore와 Rollback 요구를 Questions 3~5, 9~10에 포함했다.
- **Security Baseline**: Extension은 비활성화로 N/A. TLS, Secret, 오류 비노출과 CI 취약점 검사는 일반 요구사항으로 유지한다.
