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
| `u06-worker` | Same immutable backend image; runs U06 notification scheduler and delivery adapters | 1 GiB memory ceiling; database pool 2; in-app concurrency 2; email concurrency 2 | `unless-stopped`; lane failure cannot consume another lane's slots |
| `u06-maintenance` | Same image under `maintenance` profile; retention, audit verification and recovery checks | 512 MiB memory ceiling; database pool 1; concurrency 1 | Bounded batch/checkpoint and non-zero exit on incomplete verification |

CPU limits must be explicit in remote Compose after measurement on the approved 4-vCPU/8-GiB host. Code Generation starts with conservative CPU shares and verifies that total service reservations fit the host before enabling U06. There is no automatic scaling in the prototype.

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

## Observability Infrastructure

- API and worker emit bounded metrics and OpenTelemetry events to the existing collector.
- Prometheus gains U06 scrape targets and alert rules for latency/outcome, queue depth/oldest age, email circuit/terminal rate, pool wait, audit HMAC mismatch, health contributions, incident lifecycle, retention backlog and storage capacity.
- Grafana gains one provisioned U06 dashboard. Loki remains the existing searchable log backend where collector routing is enabled.
- Per the selected prototype decision, JSON stdout with Docker logging-driver rotation is the host-level source of record. Remote Code Generation must configure bounded rotation. Promotion beyond one host requires durable collector-to-Loki routing and retention evidence before release.
- Shallow health reports process state. Deep health uses bounded PostgreSQL, port and email checks and the approved immutable truth table. Email may be degraded; missing required database or audit-integrity evidence makes readiness false.

Metric labels use only bounded operation, lane/channel, status, outcome, reason code and policy/key version. Direct identifiers, notification text, trace content, incident narrative and provider bodies are prohibited.

## Backup and Recovery

The existing encrypted daily PostgreSQL backup includes the `u06_engagement` schema and key metadata but never secret values. Retention is 30 days. A restore uses an isolated PostgreSQL target and validates schema head, deduplication, lease/fencing, override closure, audit sequence/HMAC, one-open-incident and legal-hold/checkpoint invariants.

Re-entry order is read-only health, in-app lane, email lane after provider/circuit preflight, then maintenance. Monthly dependency-failure tests cover email, U02 through U05 ports, stale health and alert storms. A quarterly actual restore drill records checksum, duration, invariant results and RTO/RPO evidence.

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
| Observability | Scrape/alert/dashboard provisioning, bounded labels, deep-health truth table and audit-integrity alert |
| Recovery | Encrypted backup, isolated restore, ordered re-entry and quarterly drill evidence |
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
