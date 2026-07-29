# U05 Recommendation and AI Grounding NFR Design Plan

## Decision Assessment

No new questions are required because the approved Functional Design and 63 NFR Requirements resolve all mandatory NFR Design categories:

- Resilience: deadline propagation, bounded retry, AI bulkhead/circuit, deterministic fallback, U03/U04 fail-closed and Backup/Restore.
- Scalability: single-server prototype, 10 concurrent users, 5 sustained/15 burst requests per second, bounded candidates/evidence and numeric review triggers.
- Performance: recommendation p95 10 seconds, fallback p95 3 seconds and explicit stage targets.
- Security: consent-qualified pseudonymous context, allowlisted AI egress, file-injected secrets, schema/payload bounds and telemetry redaction.
- Logical components: synchronous orchestrator, pure ranking/validation, PostgreSQL session/trace state, provider-neutral HTTPX AI adapter and shared U07 observability.

## Execution Steps

- [x] Analyze approved U05 Functional Design, 63 NFRs and 11 ADRs.
- [x] Confirm prior decisions cover every mandatory NFR Design question category.
- [x] Allocate the 10-second end-to-end deadline across intent, data/ranking, drafting, validation and reserve stages.
- [x] Design AI timeout, bounded retry, bulkhead, circuit, usage-cap and deterministic fallback patterns.
- [x] Design bounded candidate/evidence processing, database pool isolation and scale-review triggers.
- [x] Design immutable policy/model activation, quality evaluation and rollback patterns.
- [x] Design session CAS/idempotency, trace closure, retention and restore re-entry patterns.
- [x] Design consent/minimization, secret/egress, output closure and telemetry privacy patterns.
- [x] Define logical component responsibilities, ports, transaction boundaries and degraded interactions.
- [x] Map patterns/components to U05 NFR groups and P-U05-01~12 verification responsibilities.
- [x] Evaluate RESILIENCY-01~15 and applicable PBT rules with no blocking findings.
- [x] Validate Markdown; no Mermaid or ASCII diagram is embedded.
- [x] Update workflow state and audit for standardized review.

## Artifacts

- `aidlc-docs/construction/u05-recommendation-and-ai-grounding/nfr-design/nfr-design-patterns.md`
- `aidlc-docs/construction/u05-recommendation-and-ai-grounding/nfr-design/logical-components.md`
