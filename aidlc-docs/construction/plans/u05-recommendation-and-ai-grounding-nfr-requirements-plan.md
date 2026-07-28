# U05 Recommendation and AI Grounding NFR Requirements Plan

## Context and Decision Reuse

- Unit: U05 Recommendation and AI Grounding.
- Inputs: approved U05 Functional Design, U02 consent-qualified features, U03 approved catalog, U04 validation contract and U07 runtime baseline.
- Primary stories: US-008~013, US-022 and US-024; supporting contracts for US-005/006/017/018/023.
- Enabled extensions: Resiliency Baseline (Full), Property-Based Testing (Full).
- Disabled extension: Security Baseline; core consent, de-identification, least privilege and data-minimization requirements remain mandatory.

## Question Assessment

No new question file is required. Existing approved decisions cover every NFR category needed for this stage:

- Scale: single-server prototype, fewer than 10 concurrent users and the approved 100,000-content catalog boundary.
- Performance: recommendation p95 10 seconds under normal AI response conditions and processing-state presentation.
- Availability/recovery: monthly 99.0%, RTO 4 hours, RPO 24 hours and Backup and Restore.
- Reliability: bounded external calls, circuit isolation, rule-based degradation and fail-closed metadata validation.
- AI quality: bilingual regression, hard-condition closure, evidence-grounded claims, diversity and provider/model change evaluation.
- Privacy: purpose-limited pseudonymous features, consent withdrawal, no raw prompt/chain-of-thought trace and user-controlled conversation history.
- Technology: the existing locked Python 3.12.13, FastAPI/Pydantic, HTTPX, PostgreSQL/SQLAlchemy/Alembic and pytest/Hypothesis stack.
- Delivery: Docker Compose, manual GitHub Actions during the current pause and real PostgreSQL integration `skip=0`.

Numeric U05 stage budgets below refine these approved product targets; they do not change product scope or select a new external AI provider.

## Execution Steps

- [x] Read approved U05 Functional Design artifacts, properties and story traceability.
- [x] Read project/U07 scale, latency, availability, recovery and delivery baselines.
- [x] Verify prior decisions remove the need for additional NFR questions.
- [x] Define workload criticality, request/data capacity and scale-review triggers.
- [x] Define end-to-end and stage latency, throughput, timeout and fallback objectives.
- [x] Define availability, consistency, replay, degradation and recovery requirements.
- [x] Define AI quality, grounding, bilingual evaluation, diversity and model-change gates.
- [x] Define core privacy/security, retention, trace and external-AI transfer controls.
- [x] Define observability, cost, maintainability and usability contract requirements.
- [x] Select technology using the actual `pyproject.toml` and existing `uv.lock` baseline.
- [x] Confirm Hypothesis for P-U05-01~12 and define example/PBT/contract/integration gates.
- [x] Evaluate RESILIENCY-01~15 and PBT-01/PBT-09 with no blocking findings.
- [x] Validate Markdown syntax; no diagram is embedded.
- [x] Update plan, state and audit for standardized NFR Requirements review.

## Artifacts

- `aidlc-docs/construction/u05-recommendation-and-ai-grounding/nfr-requirements/nfr-requirements.md`
- `aidlc-docs/construction/u05-recommendation-and-ai-grounding/nfr-requirements/tech-stack-decisions.md`
