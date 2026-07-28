# U03 Catalog and Discovery NFR Design Plan

> **Single Source of Truth**: 이 파일은 U03 NFR Design의 설계 결정, 답변과 체크박스 진행 상태를 관리한다. 모든 답변과 모호성이 해소되기 전에는 설계 산출물을 생성하지 않는다.

## Inputs and Inherited Decisions

- [x] U03 Functional Design, U03-NFR-001~057과 9개 Tech Stack ADR을 읽는다.
- [x] U07 PostgreSQL/outbox worker, bounded pool, timeout·retry·circuit·bulkhead, telemetry, health와 deployment pattern을 상속한다.
- [x] Cache 없음, PostgreSQL FTS·trigram·vector, 외부 embedding adapter, projection p95 60초와 rebuild 30분 결정을 확인한다.
- [x] U07에서 선택한 경량 dependency failure test와 분기별 restore drill을 RESILIENCY-14 공통 접근법으로 상속한다.
- [x] Security Baseline은 disabled이며 query privacy, cursor integrity, parameterization과 rate limit은 core security pattern으로 유지한다.

## Mandatory Category Assessment

| Category | Applicability | Design focus |
|---|---|---|
| Resilience patterns | Required | Embedding timeout/retry/circuit, projection gap/replay, safe fallback, failure injection |
| Scalability patterns | Required | Stateless query path, partitionable projection worker, PostgreSQL connection/index budget |
| Performance patterns | Required | FTS/vector index, hybrid rank, statement timeout, online rebuild and query plan |
| Security patterns | Required | Query minimization, keyed fingerprint, cursor integrity, parameterized search and rate limit |
| Logical components | Required | Catalog repository, search planner, embedding adapter, projection coordinator, telemetry and health |

## Execution Plan

### Step 1 — NFR Design Decision Collection

- [x] 다섯 필수 category의 미결정 pattern을 분석한다.
- [x] Question 1~14를 `[Answer]:` 형식으로 작성한다.
- [x] 모든 답변의 누락과 선택지 유효성을 확인한다.
- [x] 답변 간 모순과 U03 NFR·U07 상속 결정 충돌을 검사하고 clarification을 완료한다. 추가 질문은 필요하지 않다.

### Step 2 — NFR Design Patterns

- [x] PostgreSQL text/vector index, hybrid rank와 bounded query execution pattern을 설계한다.
- [x] Embedding timeout·retry·circuit·bulkhead와 approved fallback pattern을 설계한다.
- [x] Projection claim·replay·online rebuild·atomic swap와 scale-out pattern을 설계한다.
- [x] Query privacy, cursor/fingerprint key rotation과 rate-limit pattern을 설계한다.
- [x] `aidlc-docs/construction/u03-catalog-and-discovery/nfr-design/nfr-design-patterns.md`를 생성한다.

### Step 3 — Logical Components

- [x] API/application/domain/repository/search/embedding/projection logical boundary를 정의한다.
- [x] 동기·비동기 호출, data ownership, error propagation과 degraded response를 명시한다.
- [x] Telemetry, health, alert, quality evaluation과 integration gate component를 정의한다.
- [x] U01, U04, U05, U06와 U07 contract 연결을 표시한다.
- [x] `aidlc-docs/construction/u03-catalog-and-discovery/nfr-design/logical-components.md`를 생성한다.

### Step 4 — Validation and Completion

- [x] U03-NFR-001~057과 pattern·component traceability를 검증한다.
- [x] RESILIENCY-01~15와 PBT-01~10의 적용·N/A·handoff를 검증한다.
- [x] Markdown과 embedded content의 parsing compatibility를 검증한다.
- [x] NFR Design 완료 메시지를 기록하고 표준 2개 선택지로 명시적 승인을 요청한다.

## NFR Design Questions

## Question 1
U03 online query의 PostgreSQL 실행 budget과 connection bulkhead를 어떻게 구성합니까?

A) API와 projection worker에 별도 pool budget을 두고 online statement timeout 1.2초, text search 800ms, closure recheck 300ms를 적용한다.

B) API와 worker가 하나의 pool을 공유하고 모든 statement timeout을 3초로 통일한다.

C) Query별 timeout 없이 전체 HTTP request timeout만 사용한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
한국어·영어 text search index pattern은 무엇입니까?

A) Locale별 normalized document와 weighted `tsvector` GIN index를 사용하고 title/person variant에는 `pg_trgm` GIN index를 병행한다.

B) 모든 locale을 하나의 `tsvector`에 합치고 단일 GIN index만 사용한다.

C) Trigram similarity index만 사용하고 PostgreSQL full-text index는 사용하지 않는다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
100,000개 기준 vector index pattern은 무엇입니까?

A) HNSW index를 기본으로 사용하고 exact scan oracle과 Recall@10을 비교해 검색 parameter를 조정한다.

B) IVFFlat index를 기본으로 사용하고 주기적 training/rebuild로 list 수를 조정한다.

C) 초기에는 exact vector scan만 사용하고 approximate index를 적용하지 않는다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4
Text와 semantic 결과를 결합하는 hybrid ranking pattern은 무엇입니까?

A) Text rank와 vector rank를 Reciprocal Rank Fusion으로 결합하고 exact-title tier와 hard filter를 fusion 밖의 우선 규칙으로 유지한다.

B) 정규화된 text score와 cosine similarity를 고정 가중 합산한다.

C) Semantic 결과가 있으면 text 결과를 사용하지 않고 semantic 순위만 반환한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
승인 콘텐츠 변경 시 embedding 생성과 projection publication을 어떻게 조정합니까?

A) Versioned outbox로 embedding을 비동기 생성하고 새 vector가 준비·검증되기 전에는 이전 정상 projection을 유지한다.

B) 승인 transaction 안에서 외부 embedding을 동기 호출하고 성공해야 publication을 완료한다.

C) 매일 전체 embedding batch만 수행하고 개별 변경 event는 무시한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 6
Semantic provider circuit breaker와 bulkhead의 초기 기준은 무엇입니까?

A) 최근 20회 중 50% 이상 실패 시 30초 open, half-open probe 2회로 복구하며 request concurrency를 4로 제한한다.

B) 연속 3회 실패 시 5분 open하고 concurrency 제한은 두지 않는다.

C) Circuit breaker 없이 1.5초 timeout만 적용한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 7
Embedding 호출의 retry pattern은 무엇입니까?

A) 사용자 검색 경로는 latency budget 보호를 위해 자동 retry하지 않고, background embedding job만 retry-safe 오류에 최대 2회 exponential backoff와 jitter를 적용한다.

B) 사용자 검색과 background job 모두 최대 2회 retry한다.

C) 모든 embedding 오류를 retry 없이 즉시 실패 처리한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 8
Projection worker의 claim과 병렬 처리 pattern은 무엇입니까?

A) PostgreSQL `FOR UPDATE SKIP LOCKED`로 event를 claim하고 content ID partition 내 순서를 보존하며 CatalogVersion gap barrier를 별도로 둔다.

B) 하나의 worker가 전역 CatalogVersion 순서로 모든 event를 직렬 처리한다.

C) 여러 worker가 순서 보장 없이 event를 처리하고 최종 rebuild로 정합성을 맞춘다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 9
Online projection rebuild와 atomic swap pattern은 무엇입니까?

A) 새 immutable generation을 별도 구축·검증한 뒤 active generation pointer를 한 transaction에서 교체하고 이전 generation은 rollback window 동안 보존한다.

B) 현재 projection table을 truncate한 후 같은 table에 다시 구축한다.

C) 새 table을 만든 뒤 application 재시작 시 configuration으로 전환한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 10
Scale review 이후 U03 확장 pattern은 무엇입니까?

A) Stateless API replica와 projection job-type/content partition worker를 확장하고 PostgreSQL connection budget을 중앙 제한하며, 별도 search engine은 추가 gate에서만 도입한다.

B) U03을 즉시 독립 microservice로 분리하고 별도 database를 둔다.

C) 단일 process vertical scaling만 허용한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 11
Query fingerprint와 opaque cursor integrity key rotation pattern은 무엇입니까?

A) 용도별 HMAC key를 분리하고 key ID를 payload에 포함하며 current/previous key dual-verify와 new-sign 방식으로 무중단 회전한다.

B) Query fingerprint와 cursor에 하나의 공통 HMAC key를 사용하고 회전 시 기존 cursor를 모두 무효화한다.

C) Key 없이 SHA-256 hash와 Base64 encoding만 사용한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 12
U03 rate limiting logical topology는 무엇입니까?

A) Reverse proxy IP bucket과 application subject/endpoint-cost bucket을 함께 사용하고 semantic 검색은 별도 고비용 bucket으로 격리한다.

B) Application의 subject bucket만 사용하고 anonymous 사용자는 제한하지 않는다.

C) Reverse proxy의 공통 IP bucket만 사용한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 13
U03 운영 signal의 초기 alert threshold는 어떻게 설정합니까?

A) Projection gap 즉시, lag 5분 초과 지속 5분, closure drop 1건 이상 즉시, semantic fallback 15분간 20% 초과, zero-result·stale ratio는 baseline 대비 2배로 설정한다.

B) API error rate 5%와 latency SLO 위반만 alert하고 나머지는 dashboard에서 관찰한다.

C) 모든 U03 signal이 1건이라도 발생하면 즉시 alert한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 14
U03 resilience failure-injection 자동화 범위는 무엇입니까?

A) Embedding timeout/circuit, PostgreSQL closure read 실패, duplicate·out-of-order·gap event, worker restart, rebuild 검증 실패와 active-pointer swap 실패를 component/integration test로 자동화한다.

B) Embedding timeout과 PostgreSQL 연결 실패만 자동화하고 projection failure는 runbook 검토로 대체한다.

C) 기능 테스트만 수행하고 failure injection은 Operations 단계의 수동 점검으로 연기한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Planned Outputs

- `aidlc-docs/construction/u03-catalog-and-discovery/nfr-design/nfr-design-patterns.md`
- `aidlc-docs/construction/u03-catalog-and-discovery/nfr-design/logical-components.md`

## Extension Planning Status

- **RESILIENCY-01~15**: U03 dependency isolation, projection recovery, online rebuild, health/alert와 failure injection으로 구체화한다. RESILIENCY-14의 조직 차원 답변은 U07의 경량 자동 failure test와 분기별 restore drill을 상속한다.
- **PBT-01~10**: PBT-U03-01~16의 invariant·generator 경계를 logical component와 Code Generation handoff에 보존한다.
- **Security Baseline**: disabled이므로 N/A이다. Query/cursor integrity, parameterization과 rate limiting은 core requirement로 설계한다.
