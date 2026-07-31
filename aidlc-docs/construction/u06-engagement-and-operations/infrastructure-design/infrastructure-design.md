# U06 Engagement and Operations Infrastructure Design

## Decision Summary

U06 extends the existing cloud-neutral, single-region and single-host Docker Compose prototype. It adds one continuously running `u06-worker` service and one `u06-maintenance` profile while keeping the FastAPI API, PostgreSQL 17, Caddy, OpenTelemetry, Prometheus, Loki, Grafana and backup mechanism shared. No Redis, broker or managed cloud service is introduced.

The prototype target remains 99.0% monthly availability, RTO four hours and RPO 24 hours with Backup and Restore. Multi-zone deployment and automatic scaling remain explicit production-transition gates rather than claims of the current topology.

## Environment Mapping

| Environment | U06 deployment contract |
|---|---|
| Local | Native PostgreSQL 17 or Docker Compose may be used; migrations and `pytest -m integration` selection must be identical and selected integration skips must equal zero |
| Controlled CI | An isolated PostgreSQL 17 database applies the complete migration chain and runs example, PBT, failure-injection, privacy and integration gates; workflows remain manual through `workflow_dispatch` |
| Remote prototype | One Linux host runs Caddy, API, `u06-worker`, PostgreSQL and the shared observability stack; maintenance runs only through an explicit Compose profile |

## Workload Classification and Dependencies

| Deployable component | Criticality | Unavailability impact | Required dependencies |
|---|---|---|---|
| API with U06 module | High | Admin, notification view, trace investigation and health operations unavailable; feed/search/recommendation must remain isolated | U02 authorization/preference ports, U03/U04 command ports, U05 trace port, PostgreSQL |
| `u06-worker` | High | In-app/email delivery delayed and queue age grows; synchronous product paths remain available | PostgreSQL, approved-event/preference ports, email provider for email lane |
| `u06-maintenance` | Medium | Retention, integrity verification and recovery evidence delayed | PostgreSQL, audit key ring, backup/restore evidence |
| PostgreSQL 17 | Critical | U06 admission, jobs, audit and incidents cannot close safely | Host storage, secret files, backup mechanism |
| Shared observability | Medium | Detection and diagnosis degrade; critical audit-integrity failure cannot be considered operationally closed | API/worker telemetry, host storage |

## Compute Mapping

| Service/profile | Placement and command responsibility | Initial resource contract | Failure behavior |
|---|---|---|---|
| `api` | Existing backend image and FastAPI process; exposes U06 HTTP routes through Caddy only | Existing 1 GiB memory ceiling; U06 database pool maximum 4 with zero overflow | Bounded dependency response; no notification delivery work in request process |
| `u06-worker` | Same immutable backend image; runs U06 notification scheduler and delivery adapters | 1.0 CPU and 1 GiB memory ceiling; database pool 2; in-app concurrency 2; email concurrency 2 | `unless-stopped` restarts only after process exit; unhealthy-with-running-process alerts require operator recreation |
| `u06-maintenance` | Same image under `maintenance` profile; retention, audit verification and recovery checks | 0.5 CPU and 512 MiB memory ceiling; database pool 1; concurrency 1 | Bounded batch/checkpoint and non-zero exit on incomplete verification |

The API limit is fixed at 1.0 CPU and its existing 1 GiB memory ceiling. Together with the 1.0 CPU worker and 0.5 CPU maintenance limit, these are blocking Code Generation inputs: Compose must render these exact limits and a capacity check must prove the concurrently active API, worker and shared services fit the approved 4-vCPU/8-GiB host. Maintenance is not enabled by default and must not overlap a capacity test unless that overlap is explicitly verified. Changing any CPU value requires Infrastructure Design re-approval. There is no automatic scaling in the prototype.

`restart: unless-stopped` is retained only for process exit, host restart and daemon restart. Docker Compose does not restart a running container merely because its health status is `unhealthy`; no health restart controller is selected. An unhealthy alert pages the operator, who follows the runbook to capture diagnostics, stop claims or routing, and recreate the affected service. Documentation and tests must not describe this as health-based automatic restart.

## PostgreSQL Infrastructure

### Schema and Roles

| Resource | Responsibility |
|---|---|
| `u06_engagement` | Notification events/jobs/attempts, override intents/receipts, append-only audit, alerts/incidents/COE, retention checkpoints and legal holds |
| `u06_migration_owner` | U06 DDL and grants only; prohibited from runtime use |
| `u06_api_runtime` | Minimum API reads/writes and privileged-operation closure functions |
| `u06_worker_runtime` | Bounded job claims, fencing-token completion and delivery attempts |
| `u06_maintenance_runtime` | Retention, integrity verification and recovery evidence only |
| Existing backup/monitor roles | Bounded shared backup and health/metric views without delivery bodies or secret material |

U06 has no direct write grant to U02 through U05 or U07 business schemas. Cross-unit data arrives through versioned application ports as detached values. Runtime roles cannot alter migration history or audit rows.

### Pool and Transaction Contract

- API, worker and maintenance pools are capped at 4, 2 and 1 connections respectively; overflow is zero and acquisition has an explicit timeout.
- External email and cross-unit calls never execute while holding a job-claim transaction.
- Ready jobs are claimed in bounded batches using `FOR UPDATE SKIP LOCKED`, an expiring lease and a monotonically increasing fencing token.
- In-app claim maximum is 100, email 50 and maintenance 500. Each batch commits and yields.
- Unique deduplication, one-open-incident, optimistic-version and append-only audit constraints remain database-enforced.

### Lifecycle and Capacity

Notification bodies/details expire after 30 days, jobs after 90 days, and audit/incident/COE evidence after 365 days unless legal hold applies. Cleanup uses bounded keyset batches and monotonic checkpoints. The initial verification boundary is 10,000 pending jobs and 100,000 audit/incident rows with query-plan evidence. Partitioning is introduced only after measured retention or index-maintenance pressure.

## Messaging and Channel Infrastructure

PostgreSQL Transactional Outbox is the only queue infrastructure. The `u06-worker` owns independent in-app and email lanes with isolated concurrency, queue-age signals and retry state. Broker adoption requires sustained queue-SLO violation after worker separation, concurrency tuning and query/index review; it also requires a new ordering, replay, idempotency, failure and observability design.

The email adapter has a five-second total attempt deadline, a maximum of three attempts and the approved circuit policy. Email egress is permitted only to the configured provider scheme, host and port. Email failure opens only the email circuit and cannot affect in-app delivery, the API or core recommendation paths.

## Network Boundary

| Source | Destination | Allowed path |
|---|---|---|
| Internet | Caddy ports 80/443 | HTTPS redirect and approved public/admin routes only |
| Caddy | API | U06 routes plus shallow readiness; API container has no remote host port |
| API/worker/maintenance | PostgreSQL | Private network and purpose-specific role only |
| `u06-worker` | Email provider | Allowlisted outbound TCP/TLS only; redirects or arbitrary destinations denied |
| API/worker/maintenance | OTel collector | Privacy-safe structured telemetry only |
| Prometheus | API/worker/collector | Internal metric scrape only |
| Internet | Worker, maintenance, PostgreSQL and observability services | Denied; Grafana is exposed only through a protected Caddy route when enabled |

The prototype's Docker network membership is not itself an enforceable egress allowlist. Remote deployment must combine application destination validation with host firewall or forward-proxy rules for email egress.

## Secrets and Audit Integrity

The following Git-ignored files are mounted read-only under `/run/secrets`: U06 API/worker/maintenance database URLs, email provider credential and the audit HMAC key ring. Compose and `.env.example` contain names and paths only.

The audit key ring contains one current signing key and bounded previous verification keys identified by key ID. Rotation changes only the current signing pointer; historical records remain verifiable during the overlap. No key, notification body, direct identity, provider payload or free-form reason may enter metrics, logs, traces or build artifacts.

Because PostgreSQL backups exclude key material, the audit HMAC key ring has an independent encrypted backup. The backup runner creates a versioned encrypted archive containing the current and required historical verification keys plus a signed manifest of key ID, algorithm, creation/activation/retirement time and archive checksum. It is written to an off-host backup location under a credential separated from PostgreSQL, runtime and email credentials. Key archives are retained for at least 400 days, covering the 365-day audit retention plus the 30-day database-backup window and restore overlap. Deletion is blocked while any retained database backup or audit record references the key ID.

Restore must obtain the database backup and the corresponding key archive independently, verify archive encryption/checksum and manifest signature, mount it read-only, enumerate every retained audit `key_id`, prove exactly one matching verification key for each ID and verify sampled plus boundary audit HMACs before trusted audit or privileged operation readiness becomes true. A missing, duplicate or mismatched key ID fails closed and raises a critical recovery incident.

## Observability Infrastructure

- API and worker emit bounded metrics and OpenTelemetry events to the existing collector.
- Prometheus gains U06 scrape targets and alert rules for latency/outcome, queue depth/oldest age, email circuit/terminal rate, pool wait, audit HMAC mismatch, health contributions, incident lifecycle, retention backlog and storage capacity.
- Grafana gains one provisioned U06 dashboard. Loki is an optional derived central-search replica populated from the stdout collection path; it is not the recovery source of record and loss or lag of the replica never changes the original log retention claim.
- JSON stdout retained by the Docker `json-file` logging driver with bounded `max-size` and `max-file` rotation is the prototype original log. Rotation settings, host access control and capacity alarms are blocking release evidence. Loki may index a filtered privacy-safe copy for search; duplicate delivery, indexing failure and Loki retention are monitored separately from original-log durability.
- `/health/live` reports process/event-loop state only and performs no downstream I/O. `/health/ready` evaluates required local configuration, PostgreSQL, audit-key availability and admission ability within a bounded budget; optional email failure is degraded rather than unready. `/health/deep` executes the bounded U02~U05/U07 and email dependency truth table for diagnostic/synthetic monitoring and is never used as a restart trigger.

### Health Endpoint Consumers

| Consumer | Endpoint | Purpose and behavior |
|---|---|---|
| API Compose healthcheck | Internal API `/health/live` | Marks process health; `unhealthy` alerts but does not cause automatic restart |
| Worker Compose healthcheck | Internal worker health server `/health/live` | Proves scheduler loop heartbeat; `unhealthy` alerts and requires operator action |
| Caddy active upstream check | API `/health/ready` | Removes an unready API from routing; public clients do not receive deep evidence |
| Prometheus metrics job | API/worker `/metrics` | Scrapes bounded operational metrics; this is not a health endpoint |
| Prometheus synthetic probe job | API and worker `/health/deep` over `observability_net` | Records dependency state/latency and alerts; response fields and labels are allowlisted |
| Operator/runbook | `/health/live`, `/health/ready`, then `/health/deep` | Diagnoses process, traffic eligibility and dependency closure in that order |

Metric labels use only bounded operation, lane/channel, status, outcome, reason code and policy/key version. Direct identifiers, notification text, trace content, incident narrative and provider bodies are prohibited.

## Backup and Recovery

The existing encrypted daily PostgreSQL backup includes the `u06_engagement` schema and non-secret key IDs but never HMAC key material. Retention is 30 days. The separately encrypted key-ring archive follows the 400-day policy above. A restore uses an isolated PostgreSQL target and independently restores the matching key archive before validating schema head, deduplication, lease/fencing, override closure, audit sequence/HMAC, one-open-incident and legal-hold/checkpoint invariants.

Re-entry order is read-only health, audit-key ID/HMAC closure, in-app lane, email lane after provider/circuit preflight, then maintenance. Monthly dependency-failure tests cover email, U02 through U05 ports, stale health and alert storms. Every quarterly actual restore drill selects a database backup, locates the matching independently stored key archive, verifies archive/manifest integrity, proves all retained database key IDs resolve, verifies audit HMAC samples across key-rotation boundaries, exercises a missing-key failure, then records checksum, duration, invariant results and RTO/RPO evidence. A database-only restore does not pass the drill.

## Delivery and Rollback

GitHub Actions automatic triggers remain paused. Controlled manual workflows or equivalent local commands must pass format, lint, type, unit, PBT, security/privacy and real PostgreSQL integration gates before an immutable image digest is deployed.

Deployment uses the approved direct/in-place Compose style: pre-deploy encrypted backup, expand-compatible migration, role/secret/network validation, pinned image deployment, health verification and bounded synthetic checks. Rollback redeploys the previous image/configuration while retaining expand-compatible schema. Destructive schema reversal is prohibited during application rollback.

## Scale and Production Transition Gates

A scale review begins at any sustained threshold: queue oldest age above five minutes, worker lane saturation, pool waits, host CPU/memory at 70%, storage growth at 70%, 15 burst RPS no longer passing, or 100,000 audit/incident rows exceeding query targets. Review order is worker-process separation, bounded concurrency adjustment, query/index/partition evidence and only then broker evaluation.

Production claims require multi-zone compute and PostgreSQL, load balancing, repeatable secret distribution, centralized durable logging, automated scaling limits and an approved automatic deployment/rollback pipeline. Until those gates pass, RESILIENCY-08 and RESILIENCY-09 are explicit prototype exceptions.

## Infrastructure Verification Gates

| Gate | Required evidence |
|---|---|
| PostgreSQL | Clean migration and upgrade, least-privilege roles, constraints/query plans and `pytest -m integration` with selected skip count zero |
| Worker | Deduplication, claim/lease/fencing, lane isolation, cancellation, retry/circuit and crash recovery |
| PBT | P-U06-01~12 with reusable strategies, shrinking and replayable seed evidence |
| Privacy/security | Secret scan, egress checks, role/non-enumeration tests and prohibited-field telemetry scan |
| Observability | Separate live/ready/deep consumers, scrape/probe/alert/dashboard provisioning, original-versus-Loki-copy evidence, bounded labels and audit-integrity alert |
| Recovery | Database and independent key-ring encrypted backups, key-ID closure, isolated restore, ordered re-entry and quarterly drill evidence |
| CPU limit | Remote Compose renders API 1.0, worker 1.0 and maintenance 0.5 CPU; host capacity evidence passes before Code Generation implementation begins |
| Release | Immutable digest, migration compatibility, manual workflow evidence and previous-image rollback |

## Extension Compliance

| Rule group | Status | Infrastructure evidence |
|---|---|---|
| RESILIENCY-01~07 | Compliant | Criticality/dependencies, targets, controlled deployment, metrics/logs/health/dashboard and capacity alarms are mapped |
| RESILIENCY-08~09 | N/A for prototype | Approved single-host/no-autoscale exception; multi-zone and scaling are blocking production-transition gates |
| RESILIENCY-10~15 | Compliant | Bounded dependencies, outbox bulkheads, backup/restore, staged recovery, monthly tests, quarterly drill and incident evidence |
| PBT-01 and PBT-09 | Compliant | Property inventory and locked pytest/Hypothesis/PostgreSQL environment are mapped to verification |
| PBT-02~08 and PBT-10 | Planned | Code Generation must supply strategies, examples, shrinking, deterministic seeds and integration execution evidence |
| Security Baseline | N/A | Disabled; core least privilege, secrets, egress, audit and telemetry privacy remain blocking controls |

No blocking enabled-extension finding remains at Infrastructure Design.
