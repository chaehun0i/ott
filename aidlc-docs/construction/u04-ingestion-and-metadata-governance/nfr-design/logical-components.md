# U04 Ingestion and Metadata Governance Logical Components

## Component Inventory

| Component | Responsibility | Owned durable state |
|---|---|---|
| ProviderScheduler | Creates incremental/full/revalidation work and applies fair priority | Schedule and job references |
| JobClaimRepository | Bounded claims, leases, fencing and cursor reconciliation | Jobs, attempts, cursors and counts |
| ProviderAdapterRegistry | Resolves configured ProviderPort without exposing credentials | No business state |
| ProviderClient | Allowlisted HTTP, limits, timeout, rate and circuit behavior | Circuit/rate operational state |
| RawRecordRepository | Atomic raw observation, digest, tombstone and page membership | Raw records and lineage |
| NormalizationEngine | Pure versioned provider-to-canonical mapping | Normalized versions through repository |
| IdentityResolver | Deterministic identity tiers and ambiguity decision | Resolution attempts |
| MergeEngine | Field-level deterministic precedence and provenance preservation | Merged versions |
| ValidationEngine | Executes immutable rules and produces complete rule matrix | Runs, results and decisions |
| QuarantineService | Opens cases and schedules source/rule/manual revalidation | Quarantine and attempt links |
| PublicationDispatcher | Delivers passed/withdrawal decisions with stable key | Pending jobs and receipts |
| ValidationRuleContractPublisher | Exposes versioned pure predicates to U05 | Contract version references |
| RetentionSweeper | Expires licensed raw bodies in bounded restartable batches | Expiry progress |
| IngestionTelemetry | Structured signals, metrics and health without payload leakage | No business state |
| RecoveryCoordinator | Post-restore closure checks, receipt reconciliation and cursor resume | Recovery run evidence |

## Interaction Rules

1. ProviderScheduler asks JobClaimRepository for eligible work; it never calls a provider directly.
2. A worker resolves ProviderClient through ProviderAdapterRegistry and persists every observation through RawRecordRepository before transformation.
3. NormalizationEngine, IdentityResolver, MergeEngine and ValidationEngine are deterministic for explicit inputs, versions and evaluation time.
4. ValidationEngine writes a complete decision transaction. Failed decisions call QuarantineService; passed decisions enqueue PublicationDispatcher atomically.
5. PublicationDispatcher is the only U04 component calling U03 ApprovedCatalogWritePort. It stores the returned CatalogVersion before completing work.
6. ValidationRuleContractPublisher exposes no raw, merge or quarantine internals to U05.
7. RetentionSweeper cannot delete lineage or business decisions.
8. RecoveryCoordinator blocks normal claims until restore re-entry invariants pass.

## Logical Storage Boundaries

| Store group | Access pattern | Required indexes/constraints |
|---|---|---|
| Provider policy | Active version lookup and historical reference | provider/version unique, effective window |
| Jobs/cursors | Eligible claim, lease expiry, next time and priority | partial eligible index, fencing version, provider cursor unique |
| Raw/normalized | Provider record/digest lookup and lineage traversal | provider record plus digest, raw/version unique |
| Identity/merge | Candidate and immutable input-set lookup | attempt key unique, canonical/version index |
| Validation/quarantine | Decision closure, reason and revalidation eligibility | attempt key unique, state/age, rule version, reason family |
| Publication | Pending age and receipt reconciliation | publication key unique, state/next attempt, CatalogVersion receipt unique |
| Retention | Expired payload batch scan | payload-present plus expiry/ID index |

## Configuration Boundaries

- Static runtime: PostgreSQL DSN reference, process/worker identity and telemetry endpoint.
- Versioned business configuration: provider/legal/retention policy, normalization, identity, merge and validation versions.
- Operational tuning: claim size, concurrency, connection pools, timeouts, retry/circuit and backpressure thresholds.
- Secrets: provider tokens and signing material supplied only to ProviderClient factories.

Business configuration is persisted and auditable. Operational tuning is validated at startup and recorded as a non-secret configuration fingerprint.

## Failure Isolation Matrix

| Failure | Isolated by | Observable behavior |
|---|---|---|
| One malformed record | Record transaction and QuarantineService | Siblings progress; partial-success summary |
| Provider timeout/rate limit | Provider bulkhead, retry-after and circuit | Only provider queue pauses; last catalog remains |
| U03 timeout | Durable PublicationDispatcher key | Pending age grows; no revalidation or duplicate decision |
| PostgreSQL unavailable | Readiness and claim/write guard | New work stops fail-closed |
| Rule version missing | ValidationEngine version guard | Affected record holds; no fallback to another rule |
| Worker crash | Lease expiry, fencing and replay | New worker resumes durable page |
| Retention batch crash | Ordered checkpoint and idempotent body removal | Next run resumes without lineage loss |
| Restore inconsistency | RecoveryCoordinator | Service re-entry blocked and incident emitted |

## Capacity Allocation

The prototype starts with one scheduler and one worker process. Within the worker, provider concurrency is bounded and publication dispatch has a reserved slot so provider backlog cannot starve U03 delivery. PostgreSQL connection allocation reserves capacity for API/U03 work defined by U07/U03; U04 cannot consume the whole pool. Exact pool counts are finalized from the single-server resource profile in Infrastructure Design/Code Generation configuration.

## Observability Contract

Every component emits correlation/job/attempt IDs, component, operation, bounded outcome, duration and applicable policy/rule version. ProviderClient records rate/circuit state without URL queries or response text. ValidationEngine reports rule/reason families. PublicationDispatcher reports pending age and receipt outcome. RecoveryCoordinator reports each re-entry gate.

## Test Responsibility Map

| Component | Examples | Property/integration evidence |
|---|---|---|
| RawRecordRepository | duplicate and expired payload cases | PBT-U04-01/12, PostgreSQL transaction tests |
| NormalizationEngine | locale/date/provider fixtures | PBT-U04-02/03 |
| IdentityResolver | unique, absent, conflicting and ambiguous IDs | PBT-U04-04 |
| MergeEngine | authority/freshness and tombstone examples | PBT-U04-05/06/11 |
| ValidationEngine | every failure family and unknown state | PBT-U04-07/08, 100% safety branches |
| JobClaimRepository | expiry, reclaim and cursor boundaries | PBT-U04-10/12, concurrent PostgreSQL tests |
| PublicationDispatcher | timeout before/after U03 commit | PBT-U04-09, contract/integration tests |
| ProviderClient | SSRF, size, timeout, rate and circuit | fake transport and isolation load tests |
| RetentionSweeper | licensed expiry and restart | stateful batch tests and restore drill |
| RecoveryCoordinator | corrupt reference/cursor/receipt | restore re-entry integration tests |

## Traceability

- Performance and scale: U04-NFR-003~016.
- Reliability and consistency: U04-NFR-017~027.
- Recovery and retention: U04-NFR-028~033.
- Security and licensed data: U04-NFR-034~043.
- Observability: U04-NFR-044~051.
- Maintainability and testing: U04-NFR-052~060.

All logical components preserve the U03/U04/U05 ownership boundary and introduce no new cache, broker or external datastore.
