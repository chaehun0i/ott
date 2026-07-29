# U05 Recommendation and AI Grounding Infrastructure Design

## Infrastructure Decision Summary

| Category | Selected infrastructure |
|---|---|
| Environments | Docker-optional local/CI with real PostgreSQL 17; remote Linux Docker Compose |
| Online compute | Existing FastAPI API process with U05 request, AI and database bulkheads |
| Offline compute | Bounded one-shot maintenance/evaluation command from the immutable backend image |
| Database | Shared PostgreSQL 17, isolated `u05_recommendation` schema and roles |
| Messaging/cache | No new broker, Redis or correctness cache |
| Catalog/vector data | U03-owned approved read ports and projections; no U05 duplicate store |
| Network | Caddy-only ingress, private PostgreSQL, allowlisted outbound AI HTTPS |
| Secrets | Separate U05 database and AI provider credential files |
| Monitoring | Shared OTel, Prometheus, Loki and Grafana with U05 dashboard and alerts |
| Delivery | Manual GitHub Actions while automatic triggers are paused; immutable image digest |
| Recovery | Shared encrypted backup, isolated restore verification and AI-disabled re-entry |

## Environment Mapping

### Local

- Docker Compose is optional. Native PostgreSQL 17 is valid when it runs the same migrations and integration marker selection.
- AI behavior defaults to deterministic fake HTTP transports. A developer may opt into a sandbox provider using a local, ignored secret file.
- `pytest -m integration` must execute selected U05 PostgreSQL tests with zero skips.
- No prompt, draft, credential or production behavior data is stored as a test artifact.

### CI

- CI provisions isolated real PostgreSQL 17 and applies the full U07 through U05 migration chain.
- Fake AI transports exercise timeout, malformed schema, oversized response, rate limit, circuit, usage cap and recovery paths.
- CI retains only bounded migration, coverage, contract, PBT seed/shrink, quality evaluation and failure-injection evidence.
- Automatic GitHub Actions triggers remain paused. The same workflows are available through controlled `workflow_dispatch` runs until the reactivation gate is approved.

### Remote Prototype

- One cloud-neutral Linux host runs Caddy, API, existing workers, PostgreSQL and the shared observability stack.
- U05 online work remains inside the API image and process. There is no independently addressable recommendation container or public port.
- A one-shot `recommendation-maintenance` profile may run retention, integrity and offline evaluation commands from the same immutable backend image with a separate role and resource limit.

## Compute and Isolation

The API retains an initial 1 vCPU equivalent and 1 GiB memory allocation within the approved 4 vCPU/8 GiB host boundary. U05 adds these ceilings per API process:

| Resource | Initial ceiling | Saturation behavior |
|---|---:|---|
| Concurrent AI calls | 4 | Queue for at most 100 ms, then deterministic fallback |
| U05 PostgreSQL connections | 2 | Acquire for at most 100 ms, then bounded dependency result |
| Candidate input | 1,000 | Reject or truncate before scoring allocation |
| Scored candidates | 500 | Deterministic pre-order truncation |
| Reserve candidates | 100 | Return fewer results after exhaustion |
| Exposed/evidence candidates | 20 | Enforce request/policy cap |
| Claims per item | 64 | Reject AI output and use a validated template |

The AI semaphore is independent from database and cross-unit read budgets. External calls never hold a U05 database transaction. CPU, memory, connection wait, provider quota and p95 latency are reviewed together before increasing concurrency.

## PostgreSQL Infrastructure

### Schema and Roles

| Resource | Purpose |
|---|---|
| `u05_recommendation` | Sessions, requests, immutable policy versions, ranking proof, validation closure, minimized trace and retention checkpoints |
| `u05_migration_owner` | U05 DDL only; prohibited from runtime use |
| `u05_api_runtime` | Minimum online session, recommendation and trace writes/reads |
| `u05_maintenance_runtime` | Bounded retention, integrity and offline evaluation operations |
| `backup_reader` | Existing shared backup access without AI credentials |
| `monitor_reader` | Bounded health/metric views without request or draft text |

U05 receives detached snapshots through U02, U03 and U04 ports. It has no direct write grant to their schemas and no privilege to read raw behavior, raw ingestion or quarantine tables.

### Pool, Transaction and Index Budget

- U05 contributes at most two connections per API process; overflow is disabled initially.
- Statement timeout is 5 seconds, while individual repository operations use smaller remaining-deadline budgets.
- Session patch/reset uses optimistic versioning, epoch fencing and unique idempotency constraints.
- Decision closure commits only after external AI calls and candidate/claim validation finish.
- Required indexes cover session owner/epoch/version, request idempotency, active policy pointers, ranking request/position, validation request/candidate/claim, trace retention age and purge checkpoints.

### Storage and Retention

U05 receives a 5 GB soft budget inside shared PostgreSQL storage. Warning occurs at 70% and critical at 80%. Ranking proof and minimized traces follow approved retention; raw prompts, model responses, failed drafts and chain-of-thought are never persistent state. Cleanup claims at most 500 records per transaction and checkpoints progress.

## AI Provider Infrastructure

- `AI_PROVIDER_ENDPOINT` is an HTTPS scheme/host/port allowlist entry; redirects are disabled and cross-origin redirects are rejected.
- `AI_PROVIDER_CREDENTIAL_FILE` is mounted read-only from `/run/secrets/ai_provider` into the API only.
- Provider response size is capped at 256 KiB and the internal assembled response at 512 KiB.
- Connect/read/total budgets, output/token caps, daily usage cap and price configuration are validated before provider activation.
- The circuit, concurrency semaphore and usage counter are process-local for the single-process prototype. Multi-process deployment requires a coordinated state/quota design before activation.
- AI provider unavailability does not fail readiness while deterministic safe fallback is healthy.

## Network and Secret Boundaries

- Internet traffic reaches only Caddy on ports 80/443; Caddy routes authenticated recommendation APIs to the API container.
- PostgreSQL remains on `private_net` with no host port.
- API telemetry uses `observability_net`; general telemetry cannot contain request, synopsis, explanation or provider response text.
- AI egress uses a dedicated `ai_egress_net` path plus application allowlisting. Production-like deployment additionally enforces the allowlist through a host firewall or forward proxy.
- The API's public network membership is not treated as an egress control.
- U05 database and AI credentials are purpose-separated from API authentication, OAuth, embedding and ingestion credentials.

## Monitoring and Cost Controls

The shared stack gains a U05 dashboard for request/stage latency, throughput, candidate counts, hard-filter reasons, fallback mode, circuit state, validation replacement, trace failures, session conflicts, token use and estimated cost. Labels are bounded reason/version/outcome values only.

Immediate alerts cover catalog/condition/grounding leakage, unknown validation version and prohibited telemetry fields. Threshold alerts cover p95 latency above 10 seconds, fallback p95 above 3 seconds, AI circuit/error rate, elevated template replacement, U05 pool wait, storage at 70%/80%, retention backlog and daily usage/cost cap approach.

Readiness requires U05 database/policy access, U03 approved candidates and U04 compatible rules. U02 and AI report explicit degraded states. A synthetic check verifies a deterministic recommendation path through Caddy without real user data.

## Backup, Restore and Re-entry

Encrypted daily backup includes U05 sessions within retention, immutable policies, request/ranking proof, validation outcomes, minimized traces and cleanup checkpoints. It excludes raw prompt/response bodies, failed drafts, AI credentials and transient circuit state.

Restore occurs in an isolated PostgreSQL target. Verification checks epoch/idempotency constraints, policy references, complete candidate/claim matrices, trace allowlists and U02/U03/U04 contract compatibility. Service re-entry starts with AI disabled, validates deterministic recommendations, and enables AI only after endpoint, credential, price, evaluation and health gates pass. Targets remain 99.0% monthly availability, RTO four hours and RPO 24 hours.

## Release and Verification Gates

Deployment requires format/lint/type checks, unit and contract tests, real PostgreSQL integration `skip=0`, P-U05-01 through P-U05-12, critical safety branch coverage 100%, overall coverage at least 80%, migration upgrade/clean-install, deterministic bilingual quality fixtures, grounding closure, failure injection, secret/egress checks, telemetry privacy scans and restore re-entry evidence.

The provider smoke test is opt-in and cannot replace fake-transport or deterministic safety evidence. A model, prompt, scoring, diversity, feature or validation change must pass versioned comparison and explicit activation.

## Production Transition Gates

- Multi-zone compute/database and managed load balancing.
- Coordinated circuit, quota and rate state before multiple API processes.
- Managed secrets/KMS and enforceable outbound AI policy.
- PITR or a stronger DR strategy if RPO/RTO targets tighten.
- Independent online recommendation workers only after measured latency or scaling evidence.
- Formal AI provider legal/privacy review, pricing ownership, on-call and recurring recovery exercises.

## Extension Compliance

- Resiliency: workload criticality, dependency isolation, 99.0%/RTO/RPO, direct digest rollback, layered health, backup, staged recovery and failure tests are mapped. Multi-zone/autoscaling remain the approved prototype exceptions and are production transition gates.
- Property-Based Testing: real PostgreSQL and deterministic fake transports support P-U05-01 through P-U05-12, replayable seeds, shrinking and stateful session tests.
- Security Baseline: disabled and N/A. Least privilege, secret isolation, consent minimization, allowlisted egress and telemetry privacy remain blocking core controls.

No blocking enabled-extension finding remains.
