# U01 Web Experience Infrastructure Design Plan

> **Single Source of Truth**: 이 파일은 U01 Infrastructure Design의 인프라 결정, 사용자 답변 및 완료 체크박스를 관리한다. 답변이 유효하고 모호하지 않을 때만 최종 인프라 산출물을 생성한다.

## Context

- **Approved Inputs**: U01 Functional Design, NFR-U01-01~30, U01 NFR Design and logical components.
- **Existing Platform**: single-server Docker Compose, Caddy public edge, API container, PostgreSQL 17, Prometheus/Grafana/Loki/OTel.
- **Recovery Baseline**: 99.0%, RTO 4시간, RPO 24시간, Backup and Restore.
- **Frontend Runtime**: React 19.2/Vite 8.1 static SPA; Node.js 24 LTS is a build runtime, not a production application server.
- **Enabled Extensions**: Resiliency Baseline (Full), Property-Based Testing (Full).
- **Disabled Extension**: Security Baseline. CSP, same-origin, secret exclusion and telemetry privacy remain core requirements.

## Execution Plan

### Step 1 - Inputs and Decision Collection

- [x] U01 Functional Design, NFR Requirements and NFR Design artifacts를 분석했다.
- [x] 현재 Compose, Caddy, network, logging과 observability 구성을 확인했다.
- [x] Deployment, Compute, Storage, Messaging, Network, Monitoring, Shared Infrastructure의 미결정을 식별했다.
- [x] 모든 질문에 상호 배타적 선택지와 마지막 `X) Other`를 포함했다.
- [x] Question 1~12의 모든 `[Answer]:` 값을 수집했다. 모든 답변은 `A`이다.
- [x] 답변 유효성·모순·기존 인프라 충돌을 검증했다. clarification 필요가 없다.

### Step 2 - Build and Runtime Infrastructure

- [x] frontend multi-stage build, immutable artifact 및 runtime image 경계를 정의했다.
- [x] web compute CPU/memory, filesystem, user, healthcheck와 restart 의미를 정의했다.
- [x] storage와 messaging이 U01에 N/A인지 근거를 확정했다.

### Step 3 - Network, Security and Observability

- [x] Caddy public route, SPA fallback, `/api` 우선순위, cache와 compression을 정의했다.
- [x] strict CSP, public runtime config, same-origin, source map 및 external egress 경계를 정의했다.
- [x] web health, synthetic check, Web Vitals와 privacy-safe telemetry 배치를 정의했다.
- [x] JSON stdout 원본 log와 선택적 Loki 검색 복제 관계를 정의했다.

### Step 4 - Artifacts and Validation

- [x] `infrastructure-design.md`를 생성했다.
- [x] `deployment-architecture.md`와 text alternative를 생성했다.
- [x] shared infrastructure 변경 필요성을 평가했다. 기존 공유 자원을 재사용하므로 별도 문서 변경이 불필요하다.
- [x] NFR-U01-01~30, logical component 및 extension traceability를 검증했다.
- [x] Markdown과 diagram 구문을 검증했다. Mermaid/ASCII diagram은 사용하지 않았다.
- [x] 계획·상태·감사 로그를 갱신하고 Infrastructure Design 검토를 요청한다.

## Infrastructure Design Questions

각 `[Answer]:` 뒤에 선택한 문자 하나를 입력한다. 선택지에 없는 정책이면 `X`를 쓰고 같은 줄에 원하는 내용을 설명한다.

## Question 1
U01 production artifact를 어떻게 배포할까요?

A) Node 24 multi-stage build가 정적 `dist`를 만들고 별도 unprivileged web container가 이를 제공하며 Caddy가 public reverse proxy를 담당한다

B) Vite development server를 production service로 실행한다

C) 정적 파일을 API Python container 내부에 복사해 FastAPI가 직접 제공한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 2
web container와 Caddy의 routing 책임은 어떻게 나눌까요?

A) Caddy는 `/api/*`를 API에 우선 proxy하고 나머지를 web container에 전달하며 web container가 asset과 SPA `index.html` fallback을 제공한다

B) Caddy가 host volume의 `dist`를 직접 제공하고 별도 web service는 두지 않는다

C) web container가 API reverse proxy까지 담당하고 Caddy를 제거한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 3
초기 web compute resource와 restart 정책은 무엇인가요?

A) 0.5 CPU, 256MB memory, read-only root filesystem, non-root user를 사용하고 process exit만 restart하며 unhealthy 상태는 alert와 운영자 대응으로 처리한다

B) CPU/memory 제한 없이 실행하고 unhealthy면 Docker가 자동 재시작한다고 간주한다

C) 2 CPU, 2GB memory를 예약하고 별도 health restart controller를 도입한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 4
web health와 public synthetic monitoring은 어떻게 구성할까요?

A) web container `/health/live`는 정적 process/asset readiness를 확인하고 Compose가 사용하며 Blackbox는 Caddy를 통한 `/`와 핵심 asset을 검사한다

B) API `/health/deep`만 전체 Web health로 사용한다

C) frontend에는 healthcheck와 synthetic check를 두지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 5
정적 자산 cache와 compression 정책은 무엇인가요?

A) hash asset은 1년 immutable, HTML/runtime config는 no-cache 재검증을 사용하고 Caddy의 zstd/gzip을 유지한다

B) 모든 응답을 1년 cache한다

C) 모든 응답을 no-store로 제공하고 compression을 끈다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 6
CSP와 security header는 어느 계층에서 적용할까요?

A) Caddy가 strict CSP nonce/hash, frame-ancestors, nosniff, referrer와 permissions policy를 중앙 적용하고 web image에는 executable inline script를 포함하지 않는다

B) React component가 meta tag로만 CSP를 설정하고 Caddy header는 사용하지 않는다

C) 초기에는 `unsafe-inline`과 `unsafe-eval`을 허용하고 나중에 강화한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 7
runtime configuration과 secret 경계는 무엇인가요?

A) same-origin public JSON에 API base path, locale, release만 제공하고 build/runtime에 secret을 넣지 않으며 config schema 실패 시 boot를 차단한다

B) `.env`의 모든 값을 frontend bundle에 주입한다

C) API credential을 runtime JSON에 넣어 browser가 직접 사용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 8
U01의 storage와 messaging infrastructure는 어떻게 처리할까요?

A) 영속 business storage와 queue를 추가하지 않고 browser cache는 비권위적·휘발성으로 유지하며 모든 event는 기존 U02/U05/U06 API로 전달한다

B) frontend 전용 PostgreSQL schema와 Redis queue를 추가한다

C) IndexedDB를 영속 source of truth와 offline event queue로 사용한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 9
browser telemetry infrastructure는 어떻게 연결할까요?

A) same-origin bounded ingestion endpoint가 allowlisted Web Vitals/error event를 받아 기존 OTel/Prometheus 흐름으로 전달하고 raw prompt·ID·body를 거부한다

B) browser가 Prometheus와 Loki에 직접 write한다

C) 모든 console과 network body를 외부 SaaS에 직접 전송한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 10
web access log와 중앙 검색 관계는 무엇인가요?

A) JSON stdout과 Docker rotation을 원본 log로 두고 Loki는 선택적 중앙 검색 복제이며 privacy allowlist와 bounded label만 사용한다

B) container 내부 파일만 원본으로 두고 rotation을 하지 않는다

C) Loki만 원본으로 간주하고 Docker log를 비활성화한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 11
public/private network와 outbound egress는 어떻게 구성할까요?

A) Caddy만 host port를 공개하고 web은 internal public-edge network에서 Caddy만 접근하며 browser asset에는 직접 server egress가 없다

B) web container port를 host에 추가 공개하고 Caddy와 병렬 접근을 허용한다

C) web container를 database/private network에도 연결한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Question 12
초기 규모 이후 shared infrastructure 확장 Gate는 무엇인가요?

A) asset bandwidth·LCP·image 비용 budget 위반이 지속될 때 CDN, image optimization, telemetry sampling 순으로 도입하고 초기에는 기존 shared Caddy/monitoring을 재사용한다

B) 초기 배포부터 CDN, image service, 별도 frontend telemetry cluster를 모두 추가한다

C) 측정값과 무관하게 단일 서버 구조를 영구 유지한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:A

## Planned Artifacts

- `aidlc-docs/construction/u01-web-experience/infrastructure-design/infrastructure-design.md`
- `aidlc-docs/construction/u01-web-experience/infrastructure-design/deployment-architecture.md`
- `aidlc-docs/construction/shared-infrastructure.md` (공유 경계 변경이 필요한 경우에만)

## Preliminary Extension Assessment

### Resiliency Baseline

- Questions 1~5, 9~12가 RESILIENCY-05~10의 health, public synthetic, resource bound, failure isolation과 scale evolution을 결정한다.
- RESILIENCY-02~04, 11~15는 승인된 U06/U07 availability, recovery, logging 및 incident 인프라를 상속한다.

### Property-Based Testing

- Infrastructure Design은 PBT 실행 대상이 아니며 Code Generation에서 Node/Vitest/fast-check reproducibility와 containerized E2E 환경을 제공해야 한다.

### Security Baseline

- 확장은 비활성화로 N/A이다. Questions 3, 6~11은 non-root/read-only runtime, CSP, secret exclusion, telemetry privacy와 network isolation을 일반 인프라 요구로 유지한다.
