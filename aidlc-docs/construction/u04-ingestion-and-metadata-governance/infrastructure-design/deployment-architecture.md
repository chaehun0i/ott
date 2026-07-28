# U04 Ingestion and Metadata Governance Deployment Architecture

## Deployment Units

| Unit | Artifact | U04 responsibility |
|---|---|---|
| API | Existing immutable backend digest | Authorized status/retry and ValidationRuleContract boundary |
| worker-ingestion | Same backend digest, U04 command | Provider sync, validation, quarantine, publication and retention |
| PostgreSQL 17 | Existing pinned pgvector/PostgreSQL image | `u04_ingestion`, shared jobs and U03 publication transaction boundary |
| OTel/Prometheus/Loki/Grafana | Existing shared pinned stack | U04 telemetry, dashboard, alerts and health |
| Backup/Restore runner | Existing controlled tool image | U04 durable data backup and isolated restore verification |

## Runtime Flows

### Provider Synchronization

1. `worker-ingestion` claims an eligible bounded page using `u04_worker_runtime` over `private_net`.
2. It loads only the target provider secret and calls an allowlisted HTTPS origin over `provider_egress_net`.
3. Raw observation and page membership commit before transformation.
4. Pure normalization, identity, merge and validation produce a durable decision.
5. Failure creates quarantine; pass creates a publication job in the same U04 transaction.
6. Cursor advances only after all page records have durable outcomes.

### U03 Publication

1. Reserved publication capacity claims `u04_publication` work.
2. The dispatcher calls U03 ApprovedCatalogWritePort with the immutable decision key.
3. U03 returns a CatalogVersion or already-applied receipt.
4. U04 stores the unique receipt. Timeout retains the same pending key for reconciliation.

### Telemetry and Operations

Worker and API emit redacted telemetry to the shared collector/metrics path. U06/operator access reaches protected API routes; neither worker nor monitoring endpoints are public.

## Configuration Matrix

| Configuration | Local | CI | Remote prototype |
|---|---|---|---|
| PostgreSQL | Native or container PostgreSQL 17 | Isolated real PostgreSQL 17 | Shared pinned container/volume |
| Provider | Fake/sandbox | Deterministic HTTPX fake | Allowlisted provider origin |
| Credentials | Local ignored files | Ephemeral test secrets | Read-only provider-specific secrets |
| Worker | Direct command or Compose | Isolated test worker | Dedicated worker-ingestion service |
| Observability | Optional profile | Contract/rule assertions | Shared stack enabled |
| Integration | Zero selected skips | Blocking zero-skip gate | Pre/post-deploy smoke |

## Release Artifacts

Each U04-capable release links Git commit, application image digest, lockfile, Alembic head, provider/policy schema versions, U03/U05 contract versions, PBT seed/shrink evidence, integration/coverage reports, 1,000,000-row plans, security/telemetry scans and deployment/rollback manifest.

## Deployment Sequence

1. Validate root Git cleanliness, dependency lock, image and configuration/secret-reference schemas.
2. Provision real PostgreSQL 17 and pass clean plus U03-to-U04 upgrade migrations with integration skip=0.
3. Pass examples, PBT-U04-01~12, critical branches, capacity/query plans, contracts and failure/security tests.
4. Publish immutable image/evidence digest.
5. On the host, verify disk/pool headroom, backup health, provider secret permissions, egress allowlist and current pending jobs.
6. Create and verify an encrypted pre-deploy backup.
7. Apply expand-compatible migrations with `u04_migration_owner`.
8. Deploy API compatibility changes, then start `worker-ingestion` with claims initially paused.
9. Verify policy/rule readability, U03 contract and telemetry/health.
10. Reconcile pre-existing pending publications and run a sandbox/canary provider page.
11. Enable normal claims and verify cursor, quarantine, publication, freshness and saturation signals.

## Rollback Sequence

1. Pause new U04 claims while leaving durable pending state intact.
2. Redeploy the previous compatible image/configuration digest.
3. Do not delete new raw, validation, quarantine, tombstone or receipt history.
4. Preserve U03 catalog truth; never reverse published withdrawals through application rollback.
5. Verify previous image compatibility, pending-key reconciliation, cursor monotonicity and last-valid U03 reads.
6. Use database restore only for proven corruption or incompatible migration failure under the recovery runbook.

## Restore and Service Re-entry

1. Restore to an isolated PostgreSQL 17 target and apply forward-compatible migrations.
2. Enforce current legal retention by excluding or expiring disallowed raw bodies.
3. Verify policy/rule references, cursor order, decision closure, quarantine isolation and publication receipt uniqueness.
4. Reconcile each pending U03 key against U03 state.
5. Run representative provider fake/sandbox, revalidation, retention and publication tests.
6. Resume publication lanes before provider ingestion, then gradually enable incremental/full-sync work.

## Docker-Independent Verification

Docker absence is not a waiver. A native PostgreSQL path must prove PostgreSQL 17 identity, isolated database setup, clean/upgrade migrations, real transactions/claims/indexes, integration skip=0, PBT seed/shrink, U03/U05 contracts and failure injection. SQLite or mock persistence cannot satisfy this gate.

## Failure Scenarios

| Failure | Infrastructure response |
|---|---|
| One provider unavailable | Its circuit/queue pauses; other providers and U03 remain available |
| Provider rate limit | Honor retry-after and preserve fair scheduler capacity |
| Worker crash | Lease expires; fenced replay resumes the same page |
| PostgreSQL outage | Readiness fails and new work stops fail-closed |
| U03 unavailable | Passed decisions remain pending with stable keys |
| Disk pressure | Stop full sync/retention expansion, preserve publication, alert and review capacity |
| Quarantine leakage invariant | Immediately isolate affected lane and open incident |
| Restore inconsistency | Block service re-entry |
| Observability unavailable | Bounded local handling; business processing continues unless safety signals cannot be preserved |

## Shared Infrastructure Changes

U04 adds `worker-ingestion`, `u04_ingestion` roles/schema, provider egress network, purpose-separated secrets, six job lanes, 10 GB soft storage budget, U04 monitoring provisioning and migration/contract/recovery gates. These changes are recorded in `shared-infrastructure.md` and implemented during Code Generation.

## Extension Compliance

- RESILIENCY-01~15: critical paths, dependency isolation, alerts, backup/restore, rollback, re-entry and failure testing are mapped; multi-zone/autoscaling remain prototype exceptions.
- PBT-01~10: real PostgreSQL and deterministic provider infrastructure supports examples, properties, state models, seed/shrink and regression evidence.
- Security Baseline: disabled; core role, secret, egress, payload and retention controls remain.

No blocking extension finding remains.
