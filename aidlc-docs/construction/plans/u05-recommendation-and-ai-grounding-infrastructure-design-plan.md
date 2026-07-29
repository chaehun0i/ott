# U05 Recommendation and AI Grounding Infrastructure Design Plan

## Decision Assessment

No new questions are required. Earlier approved decisions resolve every mandatory infrastructure category:

| Category | Approved evidence and treatment |
|---|---|
| Deployment environment | Docker-optional local/CI with real PostgreSQL 17; cloud-neutral single-host Linux Docker Compose for the remote prototype |
| Compute | Synchronous U05 orchestration in the existing API process; no separate online recommendation service |
| Storage | Shared PostgreSQL 17 with U05-owned schema, roles, retention and backup scope; no duplicate vector store |
| Messaging | No broker or correctness cache; maintenance work uses bounded one-shot/shared worker execution only |
| Networking | Caddy is the only public edge; PostgreSQL remains private; AI calls use allowlisted outbound HTTPS |
| Monitoring | Existing OTel, Prometheus, Loki and Grafana stack with U05-specific metrics, alerts and dashboard |
| Shared infrastructure | U07 owns runtime, database, delivery, telemetry and recovery; U05 owns its schema, contracts and operational assertions |

The concrete AI provider, model and price remain deployment configuration. That deferral does not block infrastructure mapping because the provider-neutral endpoint, credential, egress, usage and activation contracts are already fixed.

## Execution Steps

- [x] Record explicit approval of U05 NFR Design.
- [x] Analyze U05 Functional Design, NFR Requirements and NFR Design artifacts.
- [x] Load U02, U03, U04 and U07 dependency and shared-infrastructure constraints.
- [x] Evaluate all mandatory infrastructure question categories and document why no new answer is required.
- [x] Map U05 logical components to existing API, PostgreSQL, one-shot maintenance and shared telemetry resources.
- [x] Define U05 schema, least-privilege roles, pool, transaction, index, retention and storage budgets.
- [x] Define AI endpoint egress, credential isolation, payload bounds and provider activation gates.
- [x] Define health, metrics, dashboard, alerts, cost accounting and privacy-safe telemetry.
- [x] Define backup scope, isolated restore verification and staged service re-entry.
- [x] Define build, migration, integration skip=0, PBT, contract, quality and deployment gates.
- [x] Define direct deployment, rollback and production-transition requirements.
- [x] Update the shared infrastructure contract for U05.
- [x] Validate Markdown and confirm no Mermaid or ASCII diagram requires syntax validation.
- [x] Update workflow state and audit for the Infrastructure Design review gate.

## Artifacts

- `aidlc-docs/construction/u05-recommendation-and-ai-grounding/infrastructure-design/infrastructure-design.md`
- `aidlc-docs/construction/u05-recommendation-and-ai-grounding/infrastructure-design/deployment-architecture.md`
- Updated `aidlc-docs/construction/shared-infrastructure.md`
