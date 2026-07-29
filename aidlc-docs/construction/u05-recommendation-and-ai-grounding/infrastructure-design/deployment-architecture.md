# U05 Recommendation and AI Grounding Deployment Architecture

## Runtime Topology

| Source | Destination | Contract |
|---|---|---|
| User | Caddy | HTTPS only |
| Caddy | FastAPI API | Recommendation and conversation routes; readiness-aware routing |
| API U05 module | U02 feature port | Purpose-limited consent snapshot; degrade to non-personalized |
| API U05 module | U03 approved catalog port | Required approved candidate/evidence snapshot |
| API U05 module | U04 validation contract | Required compatible predicate version |
| API U05 module | PostgreSQL `u05_recommendation` | Private, least-privilege session/decision/trace persistence |
| API AI adapter | External AI provider | Allowlisted outbound HTTPS through bounded adapter |
| API | OTel collector | Privacy-safe metrics, logs and traces |
| Prometheus/Grafana/Loki | U05 telemetry | Shared scrape, alert, dashboard and log query |
| Backup/restore verifier | PostgreSQL | Encrypted backup and isolated closure verification |
| Maintenance command | PostgreSQL | Bounded retention/integrity work with separate role |

Text flow: Caddy forwards an authenticated request to the API. U05 resolves session and consent, reads one approved U03/U04 snapshot, ranks deterministically, obtains optional AI drafts, validates every candidate and claim, commits minimized closure state and returns only safe output. AI failure changes the text-generation path but never the eligible candidate source or final validation authority.

## Logical-to-Physical Mapping

| Logical components | Physical placement |
|---|---|
| Facade, admission, consent reader and session coordinator | FastAPI API application layer |
| Intent interpreter, AI adapter and grounded draft service | API process, isolated AI semaphore/circuit and outbound HTTPS |
| Candidate reader, ranker, diversity and validators | API domain/application modules using detached port values |
| Evidence builder, claim validator and response assembler | API process; no unvalidated draft serialization path |
| Session, request, policy, ranking, validation and trace repositories | PostgreSQL `u05_recommendation` schema through `u05_api_runtime` |
| Retention/recovery coordinator and quality evaluation runner | One-shot backend-image command using `u05_maintenance_runtime` |
| Recommendation telemetry | API/maintenance to shared OTel, Prometheus, Loki and Grafana |

## Compose Resource Contract

| Service/profile | Networks | Secret access | Persistent storage | Public port |
|---|---|---|---|---|
| `api` | `public_net`, `private_net`, `observability_net`, `ai_egress_net` | `database_u05_api`, `ai_provider` plus existing purpose-specific secrets | None | None; reached only through Caddy |
| `recommendation-maintenance` profile | `private_net`, `observability_net` | `database_u05_maintenance` | None | None |
| `postgres` | `private_net` | PostgreSQL bootstrap only | `postgres_data` | None |
| `otel-collector` | `observability_net` | None | bounded buffer | None |
| `prometheus`, `loki`, `grafana` | `observability_net` | existing purpose-specific secrets | existing telemetry volumes | Grafana only through protected Caddy route |
| `backup-runner`, `restore-verifier` | `private_net` | existing backup/restore credentials; never AI credential | isolated temporary restore volume | None |

The code-generation stage must update Compose and `.env.example` with names/references only. Secret values remain ignored under `secrets/` and are never committed.

## Network Access Matrix

| Source | Destination | Allowed behavior |
|---|---|---|
| Internet | Caddy 80/443 | HTTPS and redirect only |
| Internet | API/PostgreSQL/telemetry/maintenance | Denied |
| Caddy | API | Public recommendation routes and shallow readiness |
| API | PostgreSQL | U05 runtime role over private network |
| API | U02/U03/U04 modules | In-process versioned ports; no cross-schema writes |
| API | AI provider | HTTPS to configured scheme/host/port only; redirects denied |
| API/maintenance | OTel collector | Bounded telemetry only |
| Prometheus | API/collector | Metrics scrape without payload labels |
| Backup/restore | PostgreSQL/object storage | Backup and isolated restore only |

## Deadline and Failure Routing

1. Admission establishes the 10-second monotonic deadline and rejects oversized work.
2. U02 access may degrade to a non-personalized request; stale consent features are not cached.
3. U03 or U04 failure stops exposure because candidate approval cannot be proven.
4. AI intent has a 2.75-second stage budget and AI drafting a 4.25-second stage budget, each with at most one remaining-budget-safe retry.
5. AI bulkhead, circuit, timeout or usage failure routes to deterministic parsing/templates.
6. Candidate/claim failure discards the failed output and uses a fully revalidated reserve when time permits.
7. Response assembly reserves 500 ms and cannot read raw provider objects.

## Deployment Sequence

1. Run format, lint, type, unit, contract, PBT and real PostgreSQL integration gates with zero selected skips.
2. Validate the full migration chain, previous API/consumer contract and offline quality comparison.
3. Build one backend image and record its digest with configuration/policy/model references.
4. Create a pre-deploy encrypted backup and verify checksum/readability.
5. Apply expand-compatible U05 migrations using `u05_migration_owner`.
6. Validate database roles, secret-file references, AI allowlist and cost/usage caps.
7. Deploy the pinned image through the approved direct/in-place Compose flow with AI disabled.
8. Verify shallow/deep health and a deterministic synthetic recommendation.
9. Enable the approved AI configuration only after evaluation and provider checks pass.
10. Record deployment, migration, health, fallback and activation evidence.

While automatic GitHub Actions triggers are paused, steps 1 through 3 use controlled manual workflows or equivalent local commands. Automatic triggers may be restored only after all paused workflows pass their reactivation gate.

## Rollback Sequence

1. Disable the new AI activation pointer and retain deterministic service.
2. Stop routing to an unready API if core U03/U04/database closure is unhealthy.
3. Restore the previous image digest and compatible configuration/policy pointers.
4. Keep expand-compatible schema; do not destructively reverse user/session/trace state during application rollback.
5. Verify session epoch/idempotency, approved catalog closure, validation closure and deterministic synthetic behavior.
6. Record the rollback reason, affected versions and recovery evidence.

## Restore Sequence

1. Provision an isolated PostgreSQL restore target.
2. Restore the shared backup without injecting AI credentials or expired transient text.
3. Run U05 schema, policy reference, session concurrency, ranking/validation closure and trace privacy checks.
4. Run U02/U03/U04 consumer contract checks against the restored state.
5. Start the API in AI-disabled deterministic mode.
6. Run health, synthetic recommendation and trace persistence checks.
7. Enable AI only after endpoint, credential, quota, price and evaluation compatibility pass.

## Capacity and Production Evolution

The prototype remains one API process for fewer than 10 concurrent users, 5 sustained RPS and 15 burst RPS. Scale review starts when p95 exceeds 10 seconds, AI/database queue wait is sustained, memory reaches 80%, provider quota approaches 80%, daily cap is repeatedly exhausted, or catalog size exceeds the tested 100,000-content boundary.

Moving to multiple API replicas requires shared quota/circuit/rate coordination, multi-zone PostgreSQL, load balancing and repeatable secret distribution. A separate recommendation service or broker requires measured isolation benefit and new failure, ordering, idempotency and observability design.

## Infrastructure Verification Matrix

| Gate | Required evidence |
|---|---|
| Database | Clean install/upgrade, roles, constraints, query plans and `pytest -m integration` skip=0 |
| AI isolation | Timeout/rate/circuit/size/schema/redirect/usage-cap injection and deterministic recovery |
| Recommendation safety | Hard-condition, approved-catalog and complete candidate/claim closure with zero failed-draft leakage |
| PBT | P-U05-01 through P-U05-12 with reusable strategies, shrinking and replay seed |
| Privacy | Secret scan, egress allowlist, consent withdrawal and telemetry/persistence prohibited-field scan |
| Observability | Dashboard provisioning, alert-rule validation, bounded labels and degraded dependency health |
| Recovery | Backup exclusion, isolated restore, contract re-entry and AI-disabled synthetic test |
| Release | Immutable digest, previous contract, quality comparison, activation and rollback evidence |

## Extension Compliance

| Rule group | Status | Infrastructure evidence |
|---|---|---|
| RESILIENCY-01 through RESILIENCY-07 | Compliant | Criticality/dependencies, targets, direct deployment/rollback, telemetry, health and capacity alarms |
| RESILIENCY-08 through RESILIENCY-09 | N/A for prototype | Approved single-host/no-autoscale boundary; both are mandatory production transition gates |
| RESILIENCY-10 through RESILIENCY-15 | Compliant | Timeouts, bulkheads, circuit, backup scope, restore ordering, tests and incident evidence |
| PBT-01 and PBT-09 | Compliant | Properties and locked Hypothesis/pytest environment mapped to gates |
| PBT-02 through PBT-08 and PBT-10 | Planned | Blocking Code Generation evidence, including strategies, examples, shrinking and seed replay |
| Security Baseline | N/A | Disabled; core secret, egress, privacy and least-privilege controls remain mandatory |

No blocking enabled-extension finding remains.
