# U04 Ingestion and Metadata Governance NFR Requirements Plan

## Context and Decision Reuse

- Unit: U04 Ingestion and Metadata Governance
- Inputs: approved U04 Functional Design, U03 ApprovedCatalogWritePort contract, U07 runtime baseline and project requirements
- User direction: reuse prior answers, avoid redundant questions and publish completed increments directly to `main`
- Enabled extensions: Resiliency Baseline (Full), Property-Based Testing (Full)
- Disabled extension: Security Baseline; core security and data-protection requirements remain mandatory

## Question Assessment

No new question file is required. Existing approved decisions cover every NFR category:

- Scale: prototype with fewer than 10 concurrent users, 100,000-content U03 capacity and 20 provider boundary.
- Performance and freshness: provider-permitted near-real-time collection, visible last-success state and bounded external calls.
- Availability and recovery: monthly 99.0% prototype objective, RTO 4 hours, RPO 24 hours and Backup and Restore.
- Security: server-side authorization, secret injection, encrypted sensitive storage/transport, input limits and CI scanning.
- Technology: Python 3.12.13, PostgreSQL 17, FastAPI/Pydantic, SQLAlchemy/Alembic/psycopg, Docker and GitHub Actions.
- Reliability: bounded retry, dependency isolation, last-valid-catalog degradation and lightweight incident response.
- Testing: pytest plus full Hypothesis enforcement, zero-skipped PostgreSQL integration gate and branch-aware coverage.
- Usability: U04 has no end-user UI; operator-facing reason codes and status contracts support U06/U01.

## Execution Steps

- [x] Read the approved U04 Functional Design artifacts and testable properties.
- [x] Read project NFRs, U03 consumer constraints and U07 runtime/DR requirements.
- [x] Verify that prior user decisions remove the need for additional NFR questions.
- [x] Define workload criticality, capacity, throughput, latency and freshness targets.
- [x] Define availability, consistency, retry, replay, recovery and degradation requirements.
- [x] Define core security, licensed-data handling and operator authorization requirements.
- [x] Define observability, maintainability, testability and consumer-contract requirements.
- [x] Select technology using actual `pyproject.toml` and existing locked dependency baseline.
- [x] Verify PBT-09 framework selection and carry PBT-01 properties into later gates.
- [x] Evaluate RESILIENCY-01~15 and applicable PBT rules with no blocking findings.
- [x] Validate Markdown syntax and confirm that no unvalidated diagram is embedded.
- [x] Update `aidlc-state.md`, `audit.md` and this plan for stage review.

## Artifacts

- `aidlc-docs/construction/u04-ingestion-and-metadata-governance/nfr-requirements/nfr-requirements.md`
- `aidlc-docs/construction/u04-ingestion-and-metadata-governance/nfr-requirements/tech-stack-decisions.md`
