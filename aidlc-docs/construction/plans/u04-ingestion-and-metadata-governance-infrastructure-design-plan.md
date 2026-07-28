# U04 Ingestion and Metadata Governance Infrastructure Design Plan

## Decision Assessment

No new questions are required. Prior approvals define every mandatory category: cloud-neutral single-host Docker Compose, separate API/worker services, shared PostgreSQL 17, PostgreSQL-backed jobs, Caddy/private networks, shared Prometheus/Loki/Grafana/OTel and unit-isolated roles/secrets.

## Execution Steps

- [x] Analyze U04 Functional, NFR Requirements and NFR Design artifacts.
- [x] Read U07/U03 deployment architecture and shared-infrastructure constraints.
- [x] Confirm deployment, compute, storage, messaging, networking, monitoring and sharing decisions are complete.
- [x] Map U04 worker and logical components to concrete Docker Compose services.
- [x] Define PostgreSQL schema, roles, pools, indexes, storage budget and backup scope.
- [x] Define provider egress, secret isolation and private network boundaries.
- [x] Define job lanes, resource limits, backpressure and recovery infrastructure.
- [x] Define U04 telemetry, dashboard, alerts and deep-health integration.
- [x] Define CI, real-PostgreSQL, migration, PBT and deployment gates.
- [x] Define deployment, rollback, restore and production-transition sequences.
- [x] Update shared infrastructure with the U04 resource contract.
- [x] Validate Markdown; no diagram requiring Mermaid/ASCII validation is embedded.
- [x] Update workflow state and audit for review.

## Artifacts

- `aidlc-docs/construction/u04-ingestion-and-metadata-governance/infrastructure-design/infrastructure-design.md`
- `aidlc-docs/construction/u04-ingestion-and-metadata-governance/infrastructure-design/deployment-architecture.md`
- Updated `aidlc-docs/construction/shared-infrastructure.md`
