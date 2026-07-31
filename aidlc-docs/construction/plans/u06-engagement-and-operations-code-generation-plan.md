# U06 Engagement and Operations Code Generation Plan

> **Single Source of Truth**: 이 계획의 Step 1~20만 정의된 순서대로 실행한다. 각 Step을 완료한 같은 상호작용에서 해당 체크박스를 `[x]`로 바꾸며, 계획에 없는 기능이나 파일은 생성하지 않는다.

## Approval Status

- **Infrastructure Design**: Approved after remediation on 2026-07-31.
- **Code Generation Part 1**: Planning complete; explicit execution approval required.
- **Code Generation Part 2**: Not started.
- **Automatic GitHub Actions**: Paused; verification uses local commands and controlled manual workflows only.

## Unit Context

| Item | U06 scope |
|---|---|
| Primary stories | US-019 notification management, US-021 catalog exposure operations, US-023 privacy-safe recommendation trace, US-025 health/alert/incident operations |
| Requirements | FR-028~032, FR-042 operations, DR-008, U06-NFR-001~075, ADR-U06-001~010 |
| Upstream ports | U02 authorization/preferences, U03 approved event/catalog command, U04 governance command, U05 recommendation trace, U07 clock/random/health/telemetry/runtime |
| Downstream consumer | U01 Web Experience APIs; U07 observability, backup and delivery runtime |
| Owned data | Notification events/jobs/attempts, override intents/receipts, append-only audit, alerts/incidents/COE, retention checkpoints and legal holds |
| Runtime | FastAPI API, dedicated U06 worker and explicit maintenance command in the existing backend image |

## Code Locations

Application code remains in the workspace root, never under `aidlc-docs/`.

| Layer | Planned paths |
|---|---|
| Domain/application | `backend/src/ott_feed/engagement/domain/`, `backend/src/ott_feed/engagement/application/` |
| Ports/adapters | `backend/src/ott_feed/engagement/ports.py`, `backend/src/ott_feed/engagement/adapters/` |
| API/config/health/telemetry | `backend/src/ott_feed/engagement/api/`, `config.py`, `health.py`, `telemetry.py` |
| Runtime commands | `backend/src/ott_feed/engagement/worker.py`, `maintenance.py`, existing `main.py` and `worker.py` integration |
| Persistence | `backend/src/ott_feed/engagement/adapters/persistence/`, `backend/migrations/versions/0006_u06_engagement_expand.py`, `backend/migrations/role-grants.sql` |
| Tests | `backend/tests/engagement/{unit,contract,integration,pbt,quality}/` and shared test configuration only where required |
| Deployment | `compose.yaml`, `compose.remote.yaml`, `.env.example`, `infra/prometheus/`, `infra/grafana/provisioning/`, `infra/otel/` or `infra/loki/` only where the approved log-copy path requires it |
| Documentation | `aidlc-docs/construction/u06-engagement-and-operations/code/` Markdown summaries only |

## Planning Completion

- [x] Functional, NFR and remediated Infrastructure Design artifacts를 읽고 구현 경계를 추출했다.
- [x] U06 Story Map, dependency map, requirements와 P-U06-01~12를 확인했다.
- [x] 실제 repository 구조, migration 순서, Compose와 observability 파일을 확인했다.
- [x] exact code/test/config paths와 20개 순차 Step을 정의했다.
- [x] Resiliency, PBT, PostgreSQL integration skip=0, privacy와 CPU admission Gate를 계획에 포함했다.
- [x] 계획 승인 전 Application Code를 변경하지 않았다.

## Part 2 Execution Plan

### Step 1 - Minimal Compose Contract and Blocking CPU Admission

- [x] Domain code보다 먼저 최소 Compose 계약을 추가한다. 기존 `api`에 1.0 CPU를 명시하고, `u06-worker`와 `u06-maintenance` service/profile skeleton에 CPU 1.0/0.5, memory 1 GiB/512 MiB, command placeholder, `private_net`/`observability_net`/`email_egress_net`, database/email/audit-key secret reference, pool 4/2/1과 lane 2/2/1 환경변수를 반영한다. Base/maintenance/remote overlay render에서 CPU 1.0/1.0/0.5, memory, profiles, references와 fail-closed exit 78 placeholder를 검증했다. 동시 U06 CPU ceiling은 2.5로 4-vCPU host에 1.5 CPU를 공유 infrastructure headroom으로 남긴다.

### Step 2 - Baseline, Package Skeleton, Configuration and Ports

- [x] Step 1 Compose render evidence를 다시 확인하고 실제 PostgreSQL 17.10 격리 DB에 migration 0001~0005를 적용했다. Baseline은 Ruff, strict MyPy 188 files와 전체 pytest 288 passed/skip 0을 통과했다. `backend/src/ott_feed/engagement/` package, typed config, versioned U02/U03/U04/U05/U07 ports, bounded interfaces/public exports와 3개 unit tests를 생성했으며 재검증은 Ruff, strict MyPy 195 files, 3 tests passed다. Domain business logic은 추가하지 않았다.

### Step 3 - Notification Domain

- [x] Notification event/job/attempt/channel/lease/fencing/cancellation domain models와 invariants를 구현했다. Active lease 보호, expiry, 재claim fencing-token 증가, stale completion 거부, idempotent cancellation과 US-019 example tests를 추가했으며 Ruff, strict MyPy 197 files와 engagement unit 7 tests를 통과했다.

### Step 4 - Notification Admission and Scheduling

- [x] Approved-event admission, preference projection, SHA-256 stable deduplication, bounded lane scheduling과 idempotent member cancellation services를 구현하고 unit tests를 추가했다.

### Step 5 - Delivery Resilience

- [x] Five-second/three-attempt retry schedule, bounded jitter와 rolling-window email-only circuit을 구현했다. Lease heartbeat/recovery와 stale-token rejection은 Step 3 model과 함께 deterministic tests로 검증했다.

### Step 6 - Override and Privileged Operations Domain

- [x] Expected-version override, allowlisted patch, recent-auth와 idempotency admission rules를 구현하고 US-021 examples를 추가했다. Intent/receipt persistence는 Step 12~13 schema/repository가 담당한다.

### Step 7 - Audit Integrity

- [x] Versioned canonical audit encoding, HMAC-SHA-256 current/previous key ring, key-ID verification와 fail-closed missing-key behavior를 구현하고 rotation/tamper tests를 추가했다. Append-only enforcement는 Step 12 database grant/trigger로 이어진다.

### Step 8 - Trace Investigation

- [x] U05 allowlisted trace projection과 1~100 bounded result를 구현하고 직접 owner/raw field 제거를 검증했다. Router-level authorization와 indistinguishable response contract는 Step 14에 연결한다.

### Step 9 - Health Truth Model

- [x] Immutable health contribution, freshness, required/optional pure truth table와 live/ready/degraded snapshot을 구현하고 input permutation oracle test를 추가했다. Endpoint wiring은 Step 14/18에 유지한다.

### Step 10 - Alert, Incident and COE Domain

- [x] Bounded correlation key, optimistic incident transitions, monitoring recurrence, resolution owner/evidence와 COE reference model을 구현하고 US-025 state-machine examples를 추가했다.

### Step 11 - Retention and Recovery Verification

- [x] Class별 expiry 입력을 받는 500-record bounded retention, legal-hold precedence와 database/key-archive key-ID recovery closure를 구현했다. 30/90/365 policy wiring, de-link/checkpoint persistence와 ordered runtime re-entry는 Step 12~15/19에 연결한다.

### Step 12 - PostgreSQL Migration and Roles

- [x] `0006_u06_engagement_expand.py`, persistence models, claim/audit/incident indexes/constraints와 schema-scoped `role-grants.sql`을 생성했다. Migration head와 append-only audit trigger를 실제 PostgreSQL에서 검증했다.

### Step 13 - PostgreSQL Repositories and Unit of Work

- [x] Job `SKIP LOCKED` claim/lease/fencing completion, optimistic incident repository와 short-transaction UoW를 구현했다. 실제 PostgreSQL integration 전체가 33 passed, 273 deselected, skip 0으로 통과했다.

### Step 14 - API Contracts and Routing

- [x] Notification/admin override/trace/incident contracts와 router를 구현하고 `main.py`에 연결했다. Existing live/ready/deep health와 rate middleware를 재사용하고 administrator trace는 forbidden/missing 동일 404 contract로 검증했다.

### Step 15 - Worker and Maintenance Runtime

- [x] Dedicated U06 worker registration, independent bounded semaphores와 retention/audit/recovery maintenance commands를 구현하고 root worker composition에 연결했다. Runtime command와 unknown-command non-zero behavior를 unit-tested했다.

### Step 16 - Property-Based Testing

- [x] Reusable constrained ID/event/job/health strategies와 P-U06-01~12를 별도 PBT package에 구현했다. Dedup/fencing/stale/idempotency/retry/circuit/canonical-HMAC/trace/health/incident/retention properties가 Hypothesis seed 260726, shrinking enabled로 12 passed다. PBT가 health duplicate ordering bug를 축소해 발견했고 total-order fix를 반영했다.

### Step 17 - Failure, Privacy and Capacity Gates

- [x] Email circuit, stale lease/health, incident recurrence, missing key, audit tamper, secret/non-enumeration/prohibited trace fields와 bounded query-plan gates를 구현했다. Quality suite는 실제 PostgreSQL에서 6 passed이며 기존 U02~U05 failure suites는 Step 20 전체 회귀에 포함한다.

### Step 18 - Compose, Health and Secret Infrastructure

- [x] 최소 skeleton을 실제 worker/maintenance commands와 final role/secret/network wiring으로 교체했다. CPU 1.0/1.0/0.5, memory와 pool/lane 값, bounded JSON rotation을 유지했다. API/worker Compose live checks, existing Caddy ready route와 blackbox deep probe를 연결했고 rendered config에 placeholder가 없음을 검증했다. `unless-stopped`는 process-exit restart only다.

### Step 19 - Observability, Backup and Restore Artifacts

- [x] Prometheus worker scrape/deep blackbox probe, U06 alerts와 Grafana dashboard를 추가했다. JSON stdout이 original이며 existing Loki는 optional search copy다. AES-GCM encrypted HMAC key archive, SHA-256 checksum, signed manifest, 400-day retention metadata, wrong-key/missing-key failure와 round-trip recovery tests를 구현했다.

### Step 20 - Full Verification and Code Summary

- [x] Format, Ruff, strict MyPy 212 files, full 324 tests, P-U06-01~12, real PostgreSQL integration 34 passed/skip 0, branch coverage 85.36%, privacy/recovery/Compose CPU/placeholder gates를 통과했다. US-019/021/023/025 체크박스와 code/test/traceability summaries, 상태/감사/계획을 완료했다.

## Story and Step Traceability

| Story | Implementation steps | Verification steps |
|---|---|---|
| US-019 | 3~5, 12~15 | 16~17, 20 |
| US-021 | 6~7, 12~14 | 16~17, 20 |
| US-023 / DR-008 | 7~8, 12~14 | 16~17, 20 |
| US-025 | 9~11, 14~15, 18~19 | 16~17, 20 |

## PBT Compliance Plan

| Rule | Planning status | Evidence target |
|---|---|---|
| PBT-01 | Compliant | Approved P-U06-01~12 inventory is carried into Steps 3~11 and 16 |
| PBT-02~06 | Planned, blocking | Canonical codec round-trip, invariants/idempotency, truth-table oracle and job/incident state machines |
| PBT-07 | Planned, blocking | Reusable constrained engagement strategies under the PBT test package |
| PBT-08 | Planned, blocking | Hypothesis shrinking plus recorded/replayable seed in local/manual workflow evidence |
| PBT-09 | Compliant | Locked Hypothesis 6.161.5 with pytest 9.1.1 in the actual `pyproject.toml`/`uv.lock` environment |
| PBT-10 | Planned, blocking | US-019/021/023/025 example tests remain explicit alongside properties |

No PBT generation claim is complete until Step 16 and the Step 20 execution evidence pass.

## Resiliency and Release Gates

- Real PostgreSQL integration tests selected by `-m integration` must run with zero skips; a skipped PostgreSQL test cannot complete U06.
- API/worker/maintenance CPU limits are fixed at 1.0/1.0/0.5 and must render in Compose before implementation proceeds past Step 1.
- Step 1 owns the minimal renderable Compose contract; Step 18 completes health, routing, log rotation and final runtime/secret/network integration without moving the CPU admission gate later.
- `restart: unless-stopped` is process-exit behavior only. Unhealthy state generates an operator action and is never claimed as automatic health restart.
- Database restore does not pass without the independently restored HMAC key archive and complete key-ID/HMAC closure.
- Live, ready, deep and metrics endpoints have separate consumers and tests.
- Docker rotated JSON is the prototype original log; Loki is a monitored optional search replica.
- Automatic GitHub Actions triggers remain paused throughout U06 Code Generation.

## Planned Summaries

- `aidlc-docs/construction/u06-engagement-and-operations/code/code-generation-summary.md`
- `aidlc-docs/construction/u06-engagement-and-operations/code/test-evidence.md`
- `aidlc-docs/construction/u06-engagement-and-operations/code/traceability.md`

## Approval Gate

Part 2 must not start until the user explicitly approves this complete 20-Step plan and sequence.
