# U07 Tech Stack Decisions

## Decision Summary

| Area | Decision | Status |
|---|---|---|
| API Framework | FastAPI | Selected |
| Contract Models | Pydantic | Selected |
| Database | PostgreSQL | Selected |
| ORM and Query | SQLAlchemy 2 style | Selected |
| Migration | Alembic | Selected |
| PostgreSQL Driver | psycopg | Selected |
| Test Runner | pytest | Selected |
| Property-Based Testing | Hypothesis | Selected |
| Packaging | Reproducible lock and pinned dependencies | Constraint selected; tool deferred |
| Containers | Docker and Docker Compose | Selected |
| CI/CD | GitHub Actions | Selected |
| Image Registry | GHCR | Selected |
| TLS Edge | Reverse Proxy | Pattern selected; product deferred |
| Telemetry | Structured JSON Log, Metrics, Health, Trace Context | Contract selected; backend deferred |

## ADR-U07-001 — FastAPI and Pydantic

- **Decision**: C02 REST API Boundary를 FastAPI와 Pydantic Typed Schema로 구현한다.
- **Rationale**: OpenAPI Contract 생성, Request·Response Validation과 Python Type Model을 하나의 Boundary에서 연결한다.
- **Constraints**: Domain Entity가 Framework Model에 의존하지 않게 Mapper를 둔다. Error Mapping과 Authorization은 공통 Dependency 또는 Middleware에서 일관되게 적용한다.
- **Rejected**: Django REST Framework는 U07 요구에 비해 초기 Framework 범위가 크며, Flask 조합은 별도 Contract 통합 작업이 증가한다.
- **Deferred**: 정확한 Package Version과 ASGI Server는 Code Generation Planning에서 Compatibility를 확인해 Lock한다.

## ADR-U07-002 — SQLAlchemy, Alembic and psycopg

- **Decision**: PostgreSQL Adapter에 SQLAlchemy 2 style, Alembic과 psycopg를 사용한다.
- **Rationale**: Repository Boundary, 명시적 Transaction과 Versioned Migration을 지원하면서 Domain Module의 저장 기술 결합을 제한한다.
- **Constraints**: Unit은 소유 Table에만 Write한다. Migration은 Expand-and-contract를 따르고 이전 Application Version Compatibility를 검사한다.
- **Rejected**: Django ORM은 선택한 FastAPI Stack과 별도 Framework 결합을 만든다. Raw SQL-only 방식은 Prototype 단계의 Mapping·Migration 유지 비용을 높인다.
- **Deferred**: 동기 또는 비동기 Session 정책, Pool Size와 Statement Timeout은 NFR Design에서 확정한다.

## ADR-U07-003 — pytest and Hypothesis

- **Decision**: Python Example Test는 pytest, Property-Based Test는 Hypothesis를 사용한다.
- **PBT-09 Fit**: Domain Strategy, Shrinking, Seed Replay와 pytest 통합을 필수로 사용한다.
- **CI Policy**: PBT Job은 명시적 Seed를 Log하고 실패 Artifact에 Seed, Shrunk 최소 반례와 Replay 정보를 포함한다.
- **Generator Policy**: Primitive만 직접 생성하지 않고 U07 Domain Constraint를 반영한 재사용 Strategy를 `backend/tests/strategies/`에 둔다.
- **Complementary Tests**: US-026·US-028과 BR-U07 핵심 Scenario는 Example Test로 고정한다. PBT 발견 사례는 Regression Test로 승격한다.
- **Dependency Requirement**: Code Generation에서 pytest와 Hypothesis를 Development Dependency에 포함하지 않으면 PBT-09 차단 Finding이다.

## ADR-U07-004 — Code Quality Tooling Direction

- **Decision**: Python Format·Lint는 Ruff 계열 통합 설정, Type Check는 mypy 계열 정적 검사, Coverage는 pytest-compatible Coverage Tool을 사용한다.
- **Required Gates**: Format, Lint, Type, Unit, Contract, Integration, PBT, 전체 Line 80%, 핵심 Rule Branch 100%.
- **Version Policy**: 도구 Version을 Lock하고 자동 Update PR 또는 정기 Review에서 변경하며 CI Green과 Rollback Note를 요구한다.
- **Deferred**: 정확한 Tool Version과 세부 Rule Set은 Code Generation Plan에서 결정한다.

## ADR-U07-005 — Docker Delivery

- **Decision**: API, Worker, Web과 PostgreSQL 개발 구성을 Docker Compose로 재현하고 배포 Image는 GitHub Actions에서 Build하여 GHCR에 게시한다.
- **Artifact Identity**: Git Commit, Release Tag와 Image Digest를 연결하고 배포는 Mutable Tag가 아니라 고정 Version 또는 Digest를 사용한다.
- **Rollback**: 이전 Image와 Configuration을 재배포한다. Database Down Migration은 기본 Rollback 경로가 아니다.
- **Security**: Secret을 Image Layer에 포함하지 않으며 Dependency·Image 취약점 검사를 CI Gate로 실행한다.
- **Deferred**: Base Image, Multi-stage Build와 Runtime User 상세는 Infrastructure Design에서 확정한다.

## ADR-U07-006 — TLS and Secret Injection

- **Decision**: Reverse Proxy가 TLS를 종료하고 운영 Secret은 권한 제한 File 또는 Docker Secret으로 Container에 주입한다.
- **Local Development**: `.env` 사용은 허용하지만 Version Control에서 제외하고 값 없는 Example만 제공한다.
- **Production Documentation**: Interactive API 문서는 비활성화하거나 운영자 인증으로 보호한다.
- **Deferred**: Reverse Proxy 제품, 인증서 발급·갱신과 Secret Rotation Mechanism은 Infrastructure Design 대상이다.

## ADR-U07-007 — Observability Contract

- **Decision**: 모든 Unit은 구조화 JSON Log, Correlation·Job ID, 표준 Request·Job Metric, Shallow·Deep Health와 Trace Context 전파를 구현하고 Log를 중앙 저장소로 수집한다.
- **Prototype Scope**: 분산 Trace Backend는 선택 사항이다. Backend와 Worker가 독립 Service로 확장되기 전에는 Trace Backend 도입을 재평가한다.
- **Required Dashboard Inputs**: Availability, Latency, Error, Throughput, Saturation, Queue, Dead Letter, Backup, Freshness.
- **Deferred**: Log Aggregator, Metrics Backend, Dashboard Product와 Alert Threshold는 NFR Design·Infrastructure Design에서 결정한다.

## ADR-U07-008 — API Documentation and Contract Artifact

- **Decision**: Local·Test Interactive Docs를 활성화하고 Production에서는 비활성화 또는 운영자 보호한다.
- **Artifact**: Versioned OpenAPI JSON을 CI에서 생성하고 Consumer Compatibility 검증 결과와 함께 보존한다.
- **Client Contract**: U01은 Versioned Artifact에서 Client를 생성하거나 검증하며 Breaking Change는 새 Major API Prefix를 요구한다.

## Compatibility and Version Policy

1. 정확한 Runtime·Library Version은 Code Generation 시 공식 지원 Compatibility를 확인한 후 Lock한다.
2. Major Upgrade는 OpenAPI, Migration, Contract, Example·PBT, Performance와 Rollback 검증을 요구한다.
3. Patch·Minor Update도 Lockfile Diff, Test와 취약점 검사를 통과해야 한다.
4. 지원 종료 또는 Critical Vulnerability는 우선순위 Update를 유발하며 예외는 소유자와 만료일을 기록한다.
5. 선택된 Stack을 바꾸면 관련 ADR과 Requirements Traceability를 갱신한다.

## Deferred Decision Register

| Decision | Target Stage | Reason |
|---|---|---|
| Exact Runtime and Package Versions | Code Generation Planning | 실제 Dependency Compatibility 검증 필요 |
| ASGI Process and Worker Concurrency | NFR Design | Load·Timeout·Pool Design과 연결 |
| Reverse Proxy Product | Infrastructure Design | 배포 Host와 인증서 방식에 의존 |
| Log and Metrics Backend | NFR Design and Infrastructure Design | 운영 비용과 단일 서버 제약에 의존 |
| Timeout, Retry, Circuit Values | NFR Design | Dependency별 Failure Budget 필요 |
| DR Test Schedule and Chaos Scope | NFR Design | RESILIENCY-14 사용자 결정 필수 |
| Secret Rotation Mechanism | Infrastructure Design | 선택된 Secret Delivery 구현에 의존 |

## PBT-09 Verification

- Framework selected: Hypothesis
- Primary test runner integration: pytest
- Custom domain Strategy support: Required
- Automatic Shrinking: Required and may not be disabled without documented technical exception
- Seed reproducibility: Explicit CI Seed logging and replay required
- CI inclusion: Mandatory
- Dependency declaration: Mandatory during Code Generation
- Multiple language note: U07에는 TypeScript PBT 대상 Frontend Logic이 없다. U01 Functional Design에서 TypeScript Property 적용성과 Framework를 별도 평가한다.

PBT-09는 NFR Requirements 단계 기준으로 Compliant이며 Code Generation에서 Dependency 등록을 다시 검증한다.

## Extension Compliance

- **Resiliency**: 선택 Stack은 Health, Telemetry, Backup·Restore, Versioned Artifact와 Rollback 요구를 지원한다. Multi-zone·Auto-scaling은 비운영 Prototype 예외이며 Production Gate로 유지한다.
- **Property-Based Testing**: pytest와 Hypothesis를 명시적으로 선택했으며 Shrinking, Seed, Generator와 CI 요건을 문서화했다.
- **Security Baseline**: 비활성화로 N/A. TLS Edge, Secret 분리, 취약점 검사와 Error Redaction은 일반 요구로 유지한다.

현재 Tech Stack 결정에서 차단 상태인 Extension Finding은 없다.
