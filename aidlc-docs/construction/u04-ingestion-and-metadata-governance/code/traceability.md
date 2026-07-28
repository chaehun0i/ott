# U04 Requirements and Story Traceability

| Story or requirement | Implementation evidence | Verification evidence |
|---|---|---|
| US-020 | Provider collection, raw governance, normalization, identity/merge, validation, quarantine and reprocessing | U04 unit, contract, PBT and PostgreSQL suites |
| US-003 | Durable source time, freshness, policy and cursor facts | Raw/retention/cursor tests and PostgreSQL recovery gate |
| US-010, US-011, US-022 | Versioned validation predicates and complete rule-result closure | U05 contract, validation examples, PBT-U04-07/08, 100% safety branches |
| US-021 | Authorized job status and quarantine retry | API authorization/OpenAPI/privacy contract tests |
| US-024 | Provider/U03 isolation and last-approved-catalog preservation | Circuit, partial-success and unknown-publication reconciliation tests |
| FR-006, FR-030~032, FR-039~041 | Freshness, provenance, precedence and immutable rule versions | Normalization/merge/validation code and contract tests |
| DR-001~006, DR-009~012, AC-014 | Lawful collection, lineage, deterministic transformation, quarantine and passed-only publication | Policy, retention, PBT-U04-01~12 and U03 publication contract |
| U04-NFR-003~016 | Provider/record capacity, bounded claims and full-sync budget | 20-provider, 1,000,000-row and 100,000-record PostgreSQL/throughput gates |
| U04-NFR-017~033 | Isolation, recovery, replay and restore re-entry | Failure-injection, lease, cursor, publication and RecoveryCoordinator tests |
| U04-NFR-034~043 | Least privilege, egress, secret and payload boundaries | Role grant, Compose, API/telemetry and tracked-secret scans |
| U04-NFR-044~051 | Health, safe telemetry, dashboard and alerts | Health/telemetry contracts and U04 Prometheus/Grafana artifacts |
| U04-NFR-052~060 | Architecture, coverage, PBT and integration skip=0 | Boundary tests, 85.87% overall, 100% safety branches, 27 integration passed |

## Extension Compliance

| Resiliency rule | Status | Final evidence |
|---|---|---|
| RESILIENCY-01 | Compliant | Critical publication and collection workloads, impacts and dependencies are classified |
| RESILIENCY-02 | Compliant | 99.0% objective, RTO 4 hours and RPO 24 hours retained |
| RESILIENCY-03 | Compliant | Immutable policy/rule versions, migration chain and rollback notes |
| RESILIENCY-04 | Compliant | Expand migration and forward-compatible image rollback procedure |
| RESILIENCY-05 | Compliant | U04 Prometheus alerts and Grafana dashboard parse successfully |
| RESILIENCY-06 | Compliant | Required database/rule readiness and separate provider degradation checks |
| RESILIENCY-07 | Compliant | Cursor, publication, quarantine, circuit and recovery signals |
| RESILIENCY-08 | N/A | Approved single-server prototype; production transition requires multi-zone review |
| RESILIENCY-09 | N/A | Prototype has fixed bounded capacity; numeric scale-review triggers replace autoscaling |
| RESILIENCY-10 | Compliant | Allowlisted adapter, timeouts, retry, circuit and provider bulkheads tested |
| RESILIENCY-11 | Compliant | Inherited Backup and Restore strategy with U04 re-entry sequence |
| RESILIENCY-12 | Compliant | Durable U04 state backed up subject to licensed raw retention |
| RESILIENCY-13 | Compliant | Fail-closed restore verification and pending-publication reconciliation |
| RESILIENCY-14 | Compliant | Crash, timeout, rate, replay, expiry and restore inconsistency tests passed |
| RESILIENCY-15 | Compliant | Alert, immutable version and recovery evidence supports incident correction |

- Property-Based Testing: PBT-01 through PBT-10 are individually compliant in `pbt-summary.md`; PBT-U04-01~12 pass with domain strategies, shrinking and reproducible seed evidence.
- Security Baseline extension: N/A because it is disabled in `aidlc-state.md`. Core least-privilege, provider legality, egress, secret isolation, payload limits and telemetry privacy controls remain mandatory and passed.

No blocking traceability or enabled-extension finding remains.
