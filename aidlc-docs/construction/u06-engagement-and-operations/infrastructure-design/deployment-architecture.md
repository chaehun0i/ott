# U06 Engagement and Operations Deployment Architecture

## Runtime Topology

| Source | Destination | Contract |
|---|---|---|
| User/operator | Caddy | HTTPS only; authenticated public/admin routes |
| Caddy | FastAPI API | U06 notification, admin, trace, audit, incident and health endpoints |
| API U06 module | U02/U03/U04/U05 ports | Versioned, bounded and detached values; no cross-schema write |
| API | PostgreSQL `u06_engagement` | Private network through `u06_api_runtime` |
| `u06-worker` | PostgreSQL `u06_engagement` | Outbox claim/lease/fencing through `u06_worker_runtime` |
| `u06-worker` | Email provider | Allowlisted bounded outbound call; in-app path stays local |
| `u06-maintenance` | PostgreSQL and recovery evidence | Explicit profile with `u06_maintenance_runtime` |
| API/worker/maintenance | OTel collector | Bounded privacy-safe telemetry |
| Prometheus/Grafana/Loki | U06 telemetry | Shared internal monitoring, dashboard, alert and log query |
| Backup/restore verifier | PostgreSQL | Encrypted backup and isolated restore validation |

Text alternative: Internet traffic terminates at Caddy and reaches only the API. The API records bounded U06 intents and reads other units through in-process ports. The worker claims committed PostgreSQL outbox jobs, delivers through isolated in-app/email lanes and closes attempts with fencing tokens. Maintenance performs retention, integrity and recovery work only when explicitly invoked. All runtime processes send privacy-safe telemetry to the shared observability stack.

## Logical-to-Physical Mapping

| Logical components | Physical placement |
|---|---|
| Admission, audience reader, job coordinator, admin/trace facades and health truth table | Existing FastAPI API process |
| Lane scheduler, lease fencing, in-app/email adapters and email circuit | Dedicated `u06-worker` service |
| Retention coordinator, audit verifier and recovery verifier | `u06-maintenance` profile |
| Job, delivery, override, audit, incident and retention repositories | PostgreSQL `u06_engagement` schema |
| Alert normalizer, incident coordinator and U06 telemetry | API/worker modules with shared OTel/Prometheus/Grafana/Loki adapters |

## Compose Resource Contract

| Service/profile | Networks | Secret access | Persistent storage | Public port |
|---|---|---|---|---|
| `api` | `public_net`, `private_net`, `observability_net` | `database_u06_api`, existing API/identity secrets | Existing bounded application volumes only | None; Caddy only |
| `u06-worker` | `private_net`, `observability_net`, `email_egress_net` | `database_u06_worker`, `email_provider`, `u06_audit_keyring` | None | None |
| `u06-maintenance` | `private_net`, `observability_net` | `database_u06_maintenance`, `u06_audit_keyring` | Isolated temporary evidence only | None |
| `postgres` | `private_net` | Existing bootstrap secret | `postgres_data` | None remotely |
| OTel/Prometheus/Loki/Grafana | `observability_net` | Existing purpose-specific secrets | Existing telemetry volumes | Protected Caddy route only where configured |
| Backup/restore | `private_net` | Existing backup/restore credential, never channel credential | Isolated restore volume | None |

Code Generation must add secret references and ignored example files only; it must never commit values. The new `email_egress_net` name may reuse an existing provider-egress mechanism if the resulting host policy remains destination-restricted and independently testable.

## Deployment Sequence

1. Run format, lint, type, unit, contract, PBT, privacy/security and real PostgreSQL integration gates with selected integration skip count zero.
2. Validate clean-install and upgrade migrations, U06 roles, constraints, query plans and previous API/consumer contracts.
3. Build one backend image and record its immutable digest plus configuration and policy versions.
4. Create and validate a pre-deploy encrypted backup.
5. Apply expand-compatible U06 schema and grants as `u06_migration_owner`.
6. Validate secret-file permissions, network destinations, connection budgets, worker lane limits and telemetry prohibited fields.
7. Deploy the pinned API and `u06-worker` through the approved direct/in-place Compose flow.
8. Verify shallow/deep health, Prometheus targets, alert rules, dashboard provisioning and an in-app synthetic delivery.
9. Enable email delivery only after provider timeout, credential and circuit preflight passes.
10. Run the maintenance verification profile and record deployment/health/recovery evidence.

Automatic GitHub Actions triggers remain disabled. Steps 1 through 3 use controlled manual workflows or equivalent local commands until every paused workflow passes and reactivation is separately approved.

## Rollback Sequence

1. Stop new email claims while retaining in-app and inspection paths where healthy.
2. Disable the unready worker/API instance through health-aware routing and Compose service control.
3. Redeploy the previous image digest and compatible configuration/key pointers.
4. Keep expand-compatible U06 schema; do not destructively reverse jobs, audit or incident state.
5. Recover expired leases and verify fencing, deduplication, audit HMAC and one-open-incident invariants.
6. Re-enable in-app, then email after provider/circuit preflight, and record rollback evidence.

## Restore and Re-entry Sequence

1. Provision an isolated PostgreSQL 17 restore target.
2. Restore the encrypted shared backup including `u06_engagement` without injecting runtime secret values.
3. Validate migration head, grants, deduplication, lease/fencing, overrides, append-only audit/HMAC, incidents, retention checkpoints and legal holds.
4. Run U02 through U05 and U07 contract compatibility checks against restored state.
5. Start API read-only health and investigation paths.
6. Resume in-app delivery and verify idempotent synthetic completion.
7. Resume email only after destination, provider, timeout and circuit checks pass.
8. Resume maintenance and attach restore duration/invariant evidence to the incident record.

## Failure Routing

| Failure | Infrastructure response |
|---|---|
| PostgreSQL unavailable | API readiness false; workers stop claims without losing committed state |
| U02 preference/authorization unavailable | Fail closed for privileged changes; notification admission pauses without stale correctness cache |
| U03/U04 approval/command unavailable | Exposure-changing operation remains non-successful and reconciles by idempotency key |
| U05 trace unavailable | Bounded unavailable result plus audit outcome; no direct table/log fallback |
| Email provider unavailable | Email circuit opens and work reschedules; in-app/API lanes remain available |
| Worker crash after claim | Lease expires; a new fencing token prevents stale completion |
| Audit HMAC mismatch | Critical alert, evidence marked untrusted and privileged success fails closed |
| Observability degraded | Explicit health degradation; deploy/restore closure cannot pass without required evidence |

## Capacity Evolution

The prototype is verified at 5 sustained and 15 burst RPS, 10,000 pending jobs and 100,000 audit/incident rows. Queue age above five minutes, sustained lane/pool wait, host CPU/memory or storage above 70%, missed latency targets, or restore duration approaching four hours starts a scale review.

Evolution order is additional worker process isolation, bounded concurrency adjustment, PostgreSQL query/index/partition tuning, then a broker adapter only if queue evidence still requires it. Multiple hosts additionally require multi-zone PostgreSQL, load balancing, shared limiter/circuit state, durable centralized logs and automated scaling bounds.

## Infrastructure Verification Matrix

| Gate | Evidence |
|---|---|
| Compose | Config render, service/profile/network/secret checks and remote port denial |
| PostgreSQL | Migration chain, least-privilege grants, constraints, query plans and integration skip=0 |
| Worker resilience | Lane bulkhead, retry/circuit, lease expiry, fencing and crash recovery |
| PBT | P-U06-01~12 with seed replay and shrinking evidence |
| Observability/privacy | Scrape, alerts, dashboard, log rotation/routing and prohibited-field scans |
| Recovery | Backup checksum, isolated restore, contract closure and ordered lane re-entry |
| Delivery | Immutable digest, manual gate evidence, direct rollback and prior-version compatibility |

## Extension Compliance

| Rule group | Status | Deployment evidence |
|---|---|---|
| RESILIENCY-01~07 | Compliant | Workload map, availability/recovery targets, deployment flow, observability, health and alarms |
| RESILIENCY-08~09 | N/A for prototype | Single-host/no-autoscale exception is explicit; production transition requires both controls |
| RESILIENCY-10~15 | Compliant | Isolation, bounded calls, backup, recovery order, testing cadence and incident evidence |
| Property-Based Testing | Planned/Compliant | Environment supports real PostgreSQL and deterministic properties; Code Generation supplies execution evidence |
| Security Baseline | N/A | Disabled; core network, role, secret, audit and privacy gates remain enforced |

No blocking enabled-extension finding remains at Infrastructure Design.
