# U04 Ingestion and Metadata Governance Infrastructure Design

## Infrastructure Decision Summary

| Category | Selected infrastructure |
|---|---|
| Environments | Docker-optional Local/CI real PostgreSQL; Remote Linux Docker Compose |
| Compute | Dedicated `worker-ingestion` service using the immutable backend image |
| Database | Shared PostgreSQL 17, isolated `u04_ingestion` schema and roles |
| Messaging | Shared PostgreSQL job/outbox with U04 provider, publication, revalidation and retention lanes |
| Storage | PostgreSQL raw/lineage/decision storage with provider retention and 10 GB soft budget |
| Network | Private database/telemetry networks plus outbound-only provider egress; no public worker port |
| Secrets | Provider-specific credential files and separate U04 database secret |
| Monitoring | Shared OTel/Prometheus/Loki/Grafana with U04 dashboard and alerts |
| Delivery | GitHub Actions, immutable digest, migration/contract/integration/PBT gates |
| Recovery | Shared encrypted backup, isolated restore, receipt reconciliation and cursor re-entry |

## Environment Mapping

### Local

- Docker Compose is preferred but not required. Native PostgreSQL 17 is valid when it uses the same migrations, roles and integration markers.
- Provider calls default to deterministic fake adapters or explicitly configured sandbox endpoints.
- Secrets live outside Git in `secrets/` or local environment injection; only `.env.example` and secret names are versioned.
- `pytest -m integration` must execute selected U04 tests with zero skips.

### CI

- GitHub Actions provisions isolated real PostgreSQL 17 and runs the full U07→U02→U03→U04 migration chain.
- Fake HTTP transports exercise timeout, rate-limit, redirect, size and circuit behavior without production credentials.
- CI retains migration, contract, PBT seed/shrink, coverage, query-plan, failure-injection and secret/telemetry scan artifacts.
- A skipped selected PostgreSQL integration test fails the gate.

### Remote Prototype

- One cloud-neutral Linux host runs Caddy, API, existing workers, dedicated `worker-ingestion`, PostgreSQL and observability services.
- `worker-ingestion` shares the immutable backend image but uses its own command, memory/CPU budget, database role, secret mounts, health and restart policy.
- The worker has no inbound/public port. It connects to PostgreSQL privately and to approved provider origins through outbound-only egress.

## Compute and Resource Isolation

The initial `worker-ingestion` allocation is 1 vCPU equivalent and 1 GiB memory within the 4 vCPU/8 GiB host boundary. It starts with one process, global provider concurrency 4, per-provider concurrency 1, publication concurrency 1 and retention concurrency 1. These are ceilings, not throughput guarantees.

Backpressure stops new provider claims when PostgreSQL pool wait is sustained, memory reaches 80%, pending publication exceeds 5 minutes or disk reaches its critical threshold. Publication and tombstone reconciliation retain reserved capacity ahead of full synchronization.

## PostgreSQL Infrastructure

### Schema and Roles

| Resource | Purpose |
|---|---|
| `u04_ingestion` schema | Provider policies, jobs, raw/normalized/merge/validation/quarantine/publication state |
| `u04_migration_owner` | DDL only; never used by runtime |
| `u04_worker_runtime` | Claim and mutate U04 pipeline state; execute approved U03 publication port only |
| `u04_api_runtime` | Authorized operator status/retry commands and read-only rule contract publication |
| `backup_reader` | Existing shared backup access without provider credentials |
| `monitor_reader` | Bounded health/metric views without raw payload access |

U04 has no direct write grants to `u03_catalog`. Approved publication crosses the application port under U03-controlled routines/transactions. U05 receives a versioned contract rather than database grants.

### Pool and Transaction Budget

- `worker-ingestion` pool: 5 connections, overflow disabled initially.
- U04 API/operator pool contribution: at most 2 shared API connections.
- Online claim/decision statement timeout: 5 seconds maximum.
- Claims use `FOR UPDATE SKIP LOCKED`, bounded rows and fencing versions.
- External HTTP and U03 calls occur outside U04 database transactions.

### Storage and Retention

U04 receives a 10 GB soft budget inside shared PostgreSQL storage. Warning occurs at 70% and critical at 80%. Raw bodies follow ProviderPolicy retention; digests, minimum provenance and decisions remain only where legally permitted. Retention deletes in small restartable batches and VACUUM/query-plan evidence is monitored.

Required indexes cover eligible jobs, lease expiry, provider cursor, provider-record digest, attempt keys, decision state/age, quarantine reason, publication key/receipt and payload expiry. The 1,000,000-row gate validates bounded plans.

## Job and Messaging Infrastructure

The shared PostgreSQL job system adds U04 lanes:

1. `u04_withdrawal` — highest priority.
2. `u04_publication` — passed decisions and receipt reconciliation.
3. `u04_incremental` — normal provider cursor work.
4. `u04_revalidation` — source/rule/manual retry.
5. `u04_full_sync` — low-priority rebuild/import.
6. `u04_retention` — bounded raw-body expiry.

Lane, provider and job-type partial indexes support fair claims. Dead-letter is durable and operator-visible; it never becomes validation quarantine automatically.

## Network and Egress

- `worker-ingestion` joins `private_net`, `observability_net` and a dedicated outbound-only `provider_egress_net`.
- It publishes no host port and never joins `public_net`.
- PostgreSQL remains only on `private_net`.
- Provider origins are allowlisted by scheme, host and port. Redirects to other origins are rejected.
- Remote production-like deployment should route egress through a host firewall or forward proxy allowlist; application checks remain defense in depth.
- Provider DNS/TLS access is allowed; inbound connections from the egress network are not exposed.

## Secret Infrastructure

| Secret | Services | Rule |
|---|---|---|
| `database_u04_worker` | worker-ingestion | `u04_worker_runtime` only |
| `database_u04_api` | API | bounded operator/rule-contract access |
| `u04_provider_<id>` | worker-ingestion | one provider/purpose per read-only secret file |
| provider webhook/signature key, if used | worker-ingestion | separate from API token and versioned by key ID |

Secrets are mounted read-only from `/run/secrets`, excluded from image, database backup, telemetry and CI artifacts. A shared plaintext provider credential bundle is prohibited.

## Monitoring Infrastructure

U04 extends the shared stack with:

- Dashboard: throughput, job outcomes, provider fairness, cursor age, refresh compliance, pending-publication age, quarantine families, retry/rate/circuit state, retention backlog and schema/disk/pool saturation.
- Immediate alerts: quarantine leakage, duplicate publication receipt, cursor regression and count mismatch.
- Threshold alerts: pending publication over 5 minutes, cursor age beyond two refresh windows, full job over 4 hours, quarantine over 20% for 15 minutes with at least 100 records and U04 disk at 70%/80%.
- Health: shallow worker liveness, PostgreSQL/rule readiness, U03 publication status and separate provider degradation.

Telemetry prohibits payloads, provider tokens, URL queries, provider response text and licensed non-display fields.

## Backup, Restore and Re-entry

Encrypted daily backup includes U04 policy versions, jobs/cursors, permitted raw state, normalized/merge lineage, validation/quarantine, publication jobs and receipts. Retention policy remains authoritative: expired raw bodies are excluded or re-expired during restore processing.

Restore occurs in an isolated PostgreSQL target. Before service entry, checks validate schema/version references, cursor monotonicity, decision closure, quarantine non-leakage and receipt uniqueness. Pending U03 outcomes reconcile first; only then do provider claims resume.

## CI and Release Gates

Required gates are format/lint/type, unit/contract, real-PostgreSQL integration skip=0, PBT-U04-01~12, critical branch coverage 100%, overall coverage 80%, migrations, 1,000,000-row plans, failure injection, egress/payload security tests, telemetry scans and dependency/image scanning.

Deployment is blocked when migration compatibility, U03/U05 contracts, replay/idempotence, restore re-entry or provider secret-reference validation fails.

## Production Transition Gates

- Multi-zone compute/database and managed load balancing.
- Independent worker autoscaling with central rate/circuit state.
- Managed secrets/KMS and enforceable network egress policy.
- PITR and licensed raw-data restore controls.
- Capacity beyond 20 providers/100,000 contents/1,000,000 lineage rows.
- Formal provider compliance ownership, on-call and recurring recovery exercises.

## Extension Compliance

- Resiliency: compute, pool, provider, job and network isolation; monitoring; backup; replay; restore and deployment gates are mapped. Multi-zone/autoscaling retain approved prototype exceptions.
- PBT: Local/CI real PostgreSQL and fake provider transports support PBT state models, shrinking and seed evidence.
- Security Baseline: disabled. Least privilege, allowlisted egress, secret isolation and licensed retention remain mandatory core controls.

No blocking extension finding remains.
