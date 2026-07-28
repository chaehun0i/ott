# U07 Platform and Delivery Code Generation Plan

> **Single Source of Truth**: U07 Code Generation은 이 계획의 순서와 체크박스만 따라 실행한다. Application Code와 Build·Deployment 설정은 Workspace Root에, Markdown Summary만 `aidlc-docs/`에 저장한다.

## Part 1 — Planning Status

- [x] U07 Functional Design, NFR Requirements, NFR Design와 Infrastructure Design을 읽었다.
- [x] Unit Story Map과 US-026·US-028 Acceptance Criteria를 읽었다.
- [x] Supporting Story와 U01~U06 Interface Dependency를 식별했다.
- [x] Greenfield Multi-unit Modular Monolith의 Code 위치를 확정했다.
- [x] 정확한 Application, Test, Migration, Infrastructure와 Documentation 경로를 정의했다.
- [x] 실행 가능한 순차 Code Generation Step과 Story Traceability를 작성했다.
- [x] 현재 공식 Package Release를 확인하고 Stable Candidate Pin을 기록했다.
- [x] Code Generation Plan 승인 요청을 Audit Log에 기록했다.
- [x] 사용자가 전체 Plan과 실행 순서를 명시적으로 승인한다. 안정 버전 Resolver 검증 후 즉시 실행 조건을 포함한다.

## Unit Context

- **Unit**: U07 Platform and Delivery
- **Primary Stories**: US-026 백업·복원과 복구 검증, US-028 재현 가능한 배포와 버전 롤백
- **Supporting Stories**: US-001, US-007, US-014, US-018~US-020, US-023~US-025, US-027
- **Owned Components**: C02 REST API Boundary, 공통 Runtime Bootstrap와 Cross-cutting Adapter
- **Owned Logical Components**: LC01~LC19의 Platform 구현 및 Configuration
- **Excluded Scope**: 콘텐츠 승인, 추천 점수·AI 문구, 사용자 동의·권한 결정과 U01 Frontend Component
- **Completion Boundary**: Local·CI에서 재현 가능한 Runtime과 Versioned Contract를 만들고 Backup·Restore·Release·Rollback 실행 경로와 Test를 생성한다.

## Code Location and Structure

| Concern | Exact Root Path |
|---|---|
| Python Project and Lock | `backend/pyproject.toml`, `backend/uv.lock`, `backend/.python-version` |
| U07 Application Code | `backend/src/ott_feed/platform/` |
| Shared API Bootstrap | `backend/src/ott_feed/main.py`, `backend/src/ott_feed/api/` |
| U07 Tests | `backend/tests/platform/` |
| Shared Test Strategies | `backend/tests/strategies/` |
| Database Migration | `backend/alembic.ini`, `backend/migrations/` |
| Container and Compose | `backend/Dockerfile`, `compose.yaml`, `compose.local.yaml`, `compose.remote.yaml` |
| Edge and Observability | `infra/caddy/`, `infra/otel/`, `infra/prometheus/`, `infra/loki/`, `infra/grafana/` |
| Operations Scripts | `scripts/` |
| CI/CD | `.github/workflows/` |
| Code Summary | `aidlc-docs/construction/u07-platform-and-delivery/code/` |

`backend/src/ott_feed/platform/`은 Domain, Application, Ports와 Adapter 하위 Package로 나눈다. 이후 U02~U06은 `backend/src/ott_feed/{unit-package}/`에 추가하며 U07의 공개 Port에만 의존한다.

## Runtime and Dependency Baseline

- 실제 실행 가능한 로컬 Runtime과 Resolver 검증 결과에 맞춰 Python 3.12.13을 Runtime Baseline으로 고정하고 Container Base Image도 3.12 계열 Digest로 고정한다.
- `uv`로 Direct Dependency와 전체 Transitive Dependency를 `backend/uv.lock`에 재현 가능하게 고정한다.
- 2026-07-26 기준 Stable Candidate는 FastAPI 0.140.0, Pydantic 2.13.4, SQLAlchemy 2.0.51, Alembic 1.18.5, psycopg 3.3.4와 Uvicorn 0.51.0이다.
- Test·Quality Candidate는 pytest 9.1.1, Hypothesis 6.161.5, Ruff 0.16.0과 mypy 2.3.0이다.
- Step 1에서 Python 3.12.13 Resolver Compatibility를 확인했다. Pre-release는 사용하지 않으며 충돌 시 호환되는 최신 Stable Patch를 선택하고 이유를 Summary에 기록한다.
- Telemetry, Metrics, Settings, HTTP와 Test 보조 Package도 Direct Pin과 Lock으로 고정한다.

## Owned Data and Contracts

### Data Ownership

- `api_contract_versions`
- `idempotency_records`
- `outbox_jobs`와 Job Attempt·Lease 상태
- `release_artifacts`
- `deployment_records`
- `backup_records`
- `restore_attempts`
- Alembic Schema Version와 U07 운영 Metadata

### Provided Interfaces

- `/api/v1` FastAPI Router와 Versioned OpenAPI JSON
- `ApiError`, Cursor·Numbered Pagination과 Request Context Contract
- Idempotency Registry와 PostgreSQL Outbox·Worker Handler Registry
- Dependency Timeout·Retry·Circuit·Bulkhead Port
- Liveness, Readiness와 운영자 전용 Deep Health Contribution Port
- Structured Telemetry, Correlation·Job ID와 Redaction Contract
- Release Compatibility, Backup Manifest와 Restore Verification Port

### Unit Dependencies

| Unit | U07 Dependency or Handoff |
|---|---|
| U01 | Versioned OpenAPI, Error·Pagination Contract와 HTTPS Route를 소비한다. |
| U02 | Authorized Identity·Consent Context를 제공하고 U07 Middleware가 보호 Route에 전달한다. |
| U03 | Feed·Search Cursor Contract와 Restore Smoke Assertion을 제공한다. |
| U04 | Ingestion Job Handler와 Freshness·Quarantine Health Contribution을 제공한다. |
| U05 | Recommendation Dependency Policy, Fallback와 Synthetic Assertion을 제공한다. |
| U06 | Alert·Incident·Audit Port와 Backup·Deploy 운영 화면 Contract를 제공한다. |

의존 Unit이 아직 생성되지 않았으므로 U07은 Typed Port, Registry와 Test Double만 제공하며 Business Placeholder나 가짜 사용자 기능은 구현하지 않는다.

## Part 2 — Ordered Generation Steps

### Step 1 — Project Scaffold and Reproducible Dependency Lock

- [x] `backend/` Source Layout, `pyproject.toml`, `.python-version`, Package Initializer와 `uv.lock`을 생성한다.
- [x] Stable Candidate의 Resolver Compatibility를 확인하고 Runtime·Development Dependency를 정확히 고정한다.
- [x] Ruff, mypy, pytest, Coverage와 Hypothesis 설정 및 Test Marker를 구성한다.
- [x] `.gitignore`, `.dockerignore`와 Secret 없는 `.env.example`을 생성한다.
- **Traceability**: US-028, U07-NFR-035~043, ADR-U07-001~004

### Step 2 — Platform Domain Model and Business Rules

- [x] ApiContractVersion, IdempotencyRecord, CursorToken·Page, OutboxJob, ReleaseArtifact, DeploymentRecord, BackupRecord와 RestoreAttempt를 Framework-free Domain Model로 생성한다.
- [x] BR-U07-001~038의 상태 전이와 불변 조건을 Domain Method와 명시적 Error Type으로 구현한다.
- [x] Secret·PII·Provider Payload가 Error Detail에 포함되지 않는 Redaction Value Policy를 구현한다.
- **Traceability**: US-019, US-023~US-028, DR-008, BR-U07-001~038

### Step 3 — API Contract, Request Context and Pagination

- [x] Pydantic DTO, Domain Mapper, ApiError Envelope와 HTTP Error Mapper를 생성한다.
- [x] `/api/v1`, Correlation ID, Absolute Deadline, Locale와 Authorized Identity 전달 Middleware를 생성한다.
- [x] Opaque Cursor Codec·Fingerprint Validator와 1-based Admin Pagination을 생성한다.
- [x] Local·Test OpenAPI UI와 Remote 보호·비활성화 Policy, Versioned OpenAPI Export Command를 생성한다.
- **Traceability**: US-001, US-007, US-014, US-018, US-023~US-025, US-027; LC02~LC03

### Step 4 — Rate Limit and Idempotency Services

- [x] IP·Identity·Endpoint Class·Cost Weight를 사용하는 FastAPI Rate Limit Port와 단일 Host 구현을 생성한다.
- [x] Public, Authentication, Recommendation와 Administration Bucket을 분리하고 `429`·`Retry-After` Contract를 구현한다.
- [x] Payload Hash, Reserve, Complete, Retryable Failure와 Replay를 처리하는 Idempotency Application Service를 생성한다.
- **Traceability**: US-014, US-019, US-020, US-024, US-027; LC04~LC05

### Step 5 — Dependency Resilience and Resource Bulkheads

- [x] Versioned Dependency Policy Registry와 Absolute Deadline-aware Executor를 생성한다.
- [x] Retry-safe Guard, Exponential Backoff·Jitter, Circuit State, Fallback Result와 Dependency별 Concurrency Bulkhead를 구현한다.
- [x] AI, Content, OAuth, Notification와 Database Pool을 격리하는 Typed Policy Identifier를 생성한다.
- **Traceability**: US-024~US-025; LC06~LC08, RESILIENCY-10

### Step 6 — PostgreSQL Outbox and Worker Runtime

- [x] Outbox Repository Port, SQLAlchemy Adapter, 원자적 Enqueue와 `SKIP LOCKED` Lease Claim을 생성한다.
- [x] Retry, Dead Letter, Cancel, Authorized Requeue와 만료 Lease Recovery를 구현한다.
- [x] Job Type Handler Registry와 Ingestion·Notification용 빈 Typed Integration Slot을 생성한다.
- **Traceability**: US-019~US-020, US-024~US-025; LC09~LC10

### Step 7 — Release, Backup and Restore Application Services

- [x] Compatibility Gate, Immutable Artifact Identity, Deploy·Rollback Record Service를 생성한다.
- [x] Encrypted Backup Manifest, Checksum, 30-day Retention와 Failure Event를 생성한다.
- [x] 격리 Restore Attempt, Integrity Guard, Smoke Assertion Registry와 Verified Gate를 생성한다.
- [x] RTO·RPO 측정과 실패 시 새 Attempt 연결을 구현한다.
- **Traceability**: US-026, US-028; LC15~LC17, RESILIENCY-02~04, 11~13

### Step 8 — Repository Models and Database Migrations

- [x] U07 소유 Entity의 SQLAlchemy Model, Mapper와 Repository를 생성한다.
- [x] Alembic Initial Expand Migration, Constraint, Unique Key, Lease·Cleanup Index와 Role Grant Skeleton을 생성한다.
- [x] API와 Worker Session·Pool, Statement Timeout과 Transaction Boundary를 분리한다.
- [x] 이전 Application Version Compatibility를 검사하는 Migration Metadata를 생성한다.
- **Traceability**: US-019, US-026, US-028; BR-U07-007~038

### Step 9 — Health, Telemetry and Runtime Bootstrap

- [x] Liveness, Readiness와 인증된 Deep Health Endpoint 및 Contribution Registry를 생성한다.
- [x] JSON Log, Correlation·Job ID, Metric, Trace Context와 Redaction Middleware를 생성한다.
- [x] Telemetry Backend 실패가 Business Path를 차단하지 않는 Buffer·Failure Policy를 적용한다.
- [x] FastAPI Application Factory와 API·Worker Configuration·Secret File Loader를 조립한다.
- **Traceability**: US-023~US-025, US-027; LC11~LC14

### Step 10 — Business Logic Example Unit Tests

- [x] BR-U07-001~038의 정상·경계·거부 상태를 `backend/tests/platform/unit/`에 생성한다.
- [x] US-026 Backup·Restore 및 US-028 Release·Rollback Acceptance Criteria를 명시적 Example Test로 생성한다.
- [x] Error Redaction, Idempotency Replay, Cursor Fingerprint, Lease 경쟁과 Terminal State Test를 생성한다.
- **Traceability**: US-026, US-028, U07-NFR-036~037

### Step 11 — Property-Based and Stateful Tests

- [x] `backend/tests/strategies/`에 U07 Domain Constraint 기반 재사용 Hypothesis Strategy를 생성한다.
- [x] DTO Round-trip, Error 비노출, Idempotency, Cursor Round-trip·Mismatch와 Pagination Bound Property를 생성한다.
- [x] Outbox State Machine, Migration Compatibility Oracle와 Restore Verified Guard Property를 생성한다.
- [x] CI Seed Log, Shrinking, Replay와 Regression Promotion Policy를 구성한다.
- **Traceability**: U07-NFR-038~041, PBT-01~10

### Step 12 — API, Repository and Contract Tests

- [x] FastAPI Boundary, Middleware, Error, Rate Limit, Health와 OpenAPI Snapshot Test를 생성한다.
- [x] PostgreSQL Test Container를 대상으로 Repository, Transaction, Atomic Claim과 Migration Integration Test를 생성한다.
- [x] 이전 OpenAPI Artifact와의 Compatibility Test 및 U01 Consumer Contract Hook을 생성한다.
- [x] U02~U06 Port Test Double과 Boundary Violation Test를 생성한다.
- **Traceability**: US-001, US-014, US-018~US-020, US-023~US-025, US-027~US-028

### Step 13 — Container, Network and Observability Artifacts

- [x] Non-root Multi-stage `backend/Dockerfile`과 Healthcheck를 생성한다.
- [x] Base, Local과 Remote Compose File에 public, private와 observability Network, Volume, Secret Grant와 Resource Limit을 생성한다.
- [x] 공식 Caddy Image용 Caddyfile, Public Domain 자동 HTTPS, Trusted Client IP 경계와 Upstream Route를 생성한다.
- [x] OpenTelemetry Collector, Prometheus, Loki와 Grafana Provisioning·Alert Skeleton을 생성한다.
- **Traceability**: US-025, US-027~US-028; LC01, LC11~LC14, LC19

### Step 14 — Backup, Restore, Deploy and Rollback Operations

- [x] 일일 PostgreSQL Export·Manifest·Checksum·암호화·S3-compatible Upload Command와 Scheduler 구성을 생성한다.
- [x] 격리 Restore·Integrity·Smoke Verification Command와 분기 Drill Script를 생성한다.
- [x] Digest-pinned 직접 Deploy, Pre-deploy Backup, Readiness·Synthetic Verify와 이전 Digest Rollback Script를 생성한다.
- [x] Public Feed와 Recommendation Fallback Synthetic Check를 생성한다.
- **Traceability**: US-026, US-028; RTO 4시간, RPO 24시간

### Step 15 — GitHub Actions Quality and Release Workflows

- [x] Format, Lint, Type, Unit, Contract, Integration, PBT와 Coverage Job을 생성한다.
- [x] Dependency·Secret·Container Scan, Versioned OpenAPI와 Test Evidence Artifact 보존을 생성한다.
- [x] Main Release의 Image Build, GHCR Push와 Commit·Tag·Digest 연결을 생성한다.
- [x] Schedule 기반 Synthetic, Backup Failure·Restore Drill Evidence Hook을 생성한다.
- **Traceability**: US-025~US-026, US-028; LC15, LC18~LC19

### Step 16 — Documentation and Generation Summary

- [x] Workspace Root `README.md`에 Local Startup, Configuration, Migration, Worker와 운영 Command를 문서화한다.
- [x] `docs/`에 API Versioning, Error·Pagination, Backup·Restore와 Deploy·Rollback Runbook을 생성한다.
- [x] `aidlc-docs/construction/u07-platform-and-delivery/code/`에 생성 파일, Story·Rule·NFR Trace와 알려진 후속 Unit Handoff Summary를 생성한다.
- [x] PostgreSQL 통합 테스트를 실제 PostgreSQL에서 통과시킨 뒤 모든 Step과 Story Checkbox를 검증하고 U07 Code Generation 완료 승인 요청을 Audit Log에 기록한다.
- **Traceability**: US-026, US-028와 모든 Supporting Contract

## Story Completion Tracking

- [x] US-026 — Backup 생성·보존, Failure Alert, Isolated Restore, Integrity·Smoke Verification와 RTO·RPO Runbook
- [x] US-028 — CI Build·Test, Immutable Image, Version Trace, Direct Deploy, Migration Compatibility와 Rollback
- [x] Supporting Contract — US-001, US-007, US-014, US-018~US-020, US-023~US-025, US-027

Story Checkbox는 해당 Acceptance Boundary의 Code, Test와 운영 Artifact가 모두 생성된 Step에서만 완료한다.

## Quality and Extension Gates

- **Core**: Ruff Format·Lint, mypy, pytest, Contract·Integration, 전체 Line 80%와 핵심 BR Branch 100%
- **Resiliency**: Dependency 격리, Health·Synthetic, Backup·Restore, Release·Rollback와 월별·분기별 검증 경로 필수
- **Property-Based Testing**: Hypothesis Dependency, Domain Strategy, Shrinking, Seed·Replay Artifact와 발견 사례 Regression 승격 필수
- **Security Baseline**: 비활성화로 N/A. TLS, Secret 분리, 최소 권한, Server-side Validation, Redaction와 Scan은 Core Requirement로 유지
- **Frontend**: U07 소유 Frontend가 없어 N/A. U01에 OpenAPI와 접근성 Handoff만 제공

차단 Finding이 생기면 해당 Step은 완료로 표시하지 않고 Plan과 Audit Log에 원인과 해소를 기록한다.

## Outstanding Verification Gate

- [x] `TEST_DATABASE_URL`이 실제 PostgreSQL을 가리키는 환경에서 `pytest -m integration`이 skip 없이 통과한다.
- [x] CI에서 PostgreSQL 통합 suite를 일반 suite와 분리하고, 환경 변수가 없거나 테스트가 수집되지 않거나 실패하면 job이 실패하도록 구성한다.
- [x] PostgreSQL 통합 결과를 별도 JUnit artifact로 보존하도록 구성한다.

실제 PostgreSQL 17.10에서 integration suite 1개와 전체 suite 27개가 모두 skip 없이 통과하여 gate를 완료했다.

## Official Release References

- [FastAPI on PyPI](https://pypi.org/project/fastapi/)
- [Pydantic on PyPI](https://pypi.org/project/pydantic/)
- [SQLAlchemy on PyPI](https://pypi.org/project/SQLAlchemy/)
- [Alembic on PyPI](https://pypi.org/project/alembic/)
- [psycopg on PyPI](https://pypi.org/project/psycopg/)
- [pytest on PyPI](https://pypi.org/project/pytest/)
- [Hypothesis on PyPI](https://pypi.org/project/hypothesis/)
- [Ruff on PyPI](https://pypi.org/project/ruff/)
- [mypy on PyPI](https://pypi.org/project/mypy/)
- [Uvicorn on PyPI](https://pypi.org/project/uvicorn/)
