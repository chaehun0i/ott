# U03 Catalog and Discovery NFR Requirements Plan

> **Single Source of Truth**: 이 파일은 U03 NFR Requirements의 계획, 사용자 결정과 체크박스 진행 상태를 관리한다. 답변 검증 전에는 NFR 산출물을 생성하지 않는다.

## Inputs and Inherited Decisions

- [x] U03 Functional Design의 business logic, domain entity와 business rule을 읽는다.
- [x] U03 primary story US-001~US-006과 supporting U04·U05·U06 contract를 확인한다.
- [x] U07의 FastAPI, Pydantic, PostgreSQL, SQLAlchemy, Alembic, psycopg, pytest, Hypothesis와 Python 3.12 baseline을 상속한다.
- [x] Prototype 동시 사용자 10명 미만, 피드·상세 p95 2초, 일반 검색 p95 3초, 월 99.0%, RTO 4시간, RPO 24시간과 Backup and Restore 결정을 상속한다.
- [x] GitHub Actions, 직접 배포, version-pinned rollback, 구조화 로그·metric·health, 단일 서버 예외와 상용 전환 gate를 상속한다.
- [x] Security Baseline extension은 disabled이지만 승인 폐쇄성, 지역·라이선스 검증과 query privacy를 core requirement로 유지한다.

## Execution Plan

### Step 1 — NFR Planning and Decision Collection

- [x] Functional Design에서 NFR에 영향을 주는 미결정 항목을 식별한다.
- [x] Question 1~15를 `[Answer]:` 형식으로 작성한다.
- [x] 모든 답변의 누락과 선택지 유효성을 확인한다.
- [x] 답변 간 모순과 상속된 U07 결정과의 충돌을 검사하고 필요한 clarification을 완료한다. Clarification B에 따라 application cache는 사용하지 않고 Q6은 N/A로 확정했다.

### Step 2 — NFR Requirements

- [x] Workload 중요도, Catalog 용량, 처리량과 scale review trigger를 정의한다.
- [x] 피드·상세·검색 latency budget, cache와 projection lag SLO를 정의한다.
- [x] 가용성, 장애 저하, 승인 폐쇄성, privacy와 abuse control을 정의한다.
- [x] 검색 품질, 관측성, 유지보수성, test quality gate와 U01 usability handoff를 정의한다.
- [x] `aidlc-docs/construction/u03-catalog-and-discovery/nfr-requirements/nfr-requirements.md`를 생성한다.

### Step 3 — Tech Stack Decisions

- [x] PostgreSQL FTS·trigram·pgvector, embedding adapter, cache와 projection processing stack을 결정한다.
- [x] U07 stack compatibility, 선택 근거, 거절 대안과 scale-up 재평가 조건을 기록한다.
- [x] pytest·Hypothesis 적용과 PBT-09 dependency requirement를 기록한다.
- [x] `aidlc-docs/construction/u03-catalog-and-discovery/nfr-requirements/tech-stack-decisions.md`를 생성한다.

### Step 4 — Compliance and Completion

- [x] U03-NFR ID와 verification matrix의 완전성을 검사한다.
- [x] RESILIENCY-01~15와 PBT-01~10의 적용·N/A·handoff를 평가한다.
- [x] Markdown parsing과 traceability를 검증한다.
- [x] NFR Requirements 완료 메시지를 기록하고 명시적 승인을 요청한다.

## NFR Requirements Questions

## Question 1
U03 내부 workload의 중요도를 어떻게 분류합니까?

A) 사용자 피드·상세·검색과 승인 폐쇄성 검증은 High, projection refresh·rebuild는 Medium으로 분류한다.

B) 사용자 API와 projection processing을 모두 High로 분류한다.

C) 사용자 API는 High, semantic search만 Medium, 나머지 background processing은 Low로 분류한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
초기 Catalog와 검색 index 용량 검증 기준은 무엇입니까?

A) 승인 콘텐츠 100,000개, provider 20개, 콘텐츠당 availability 10개와 locale 5개까지 검증한다.

B) 승인 콘텐츠 500,000개, provider 50개, 콘텐츠당 availability 20개와 locale 10개까지 검증한다.

C) 초기 prototype data만 기능 검증하고 명시적인 용량 기준은 상용 전환 때 정의한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
동시 사용자 10명 미만 baseline에서 U03 처리량 검증 기준은 무엇입니까?

A) 조회 burst 20 requests/second와 projection event 10 records/second를 10분간 처리한다.

B) 조회 burst 50 requests/second와 projection event 50 records/second를 30분간 처리한다.

C) latency 목표만 검증하고 별도의 처리량 목표는 두지 않는다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4
피드·상세 p95 2초와 검색 p95 3초 안에서 U03 내부 latency 목표를 어떻게 세분화합니까?

A) cache hit 피드·상세 300ms, cache miss 1.5초, text search 1초, semantic search 2.5초 이내로 한다.

B) 피드·상세 2초와 검색 3초의 end-to-end 목표만 사용하고 내부 budget은 NFR Design에서 측정 후 정한다.

C) 모든 U03 API를 p95 500ms 이내로 통일한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
초기 U03 read cache는 어떤 방식으로 구성합니까?

A) 단일 서버 prototype에서는 process-local bounded cache를 사용하고 PostgreSQL을 source of truth로 유지한다.

B) 처음부터 Redis를 추가하여 feed·detail·search cache를 공유한다.

C) 별도 application cache 없이 PostgreSQL query와 projection만 사용한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 6
Cache freshness와 무효화 정책은 무엇입니까?

A) CatalogVersion event로 즉시 무효화하고 안전망으로 feed 5분, detail 15분 TTL을 적용한다.

B) event 무효화 없이 모든 cache에 1분 TTL만 적용한다.

C) feed 30분, detail 1시간 TTL을 사용하고 수동 purge를 제공한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 7
승인 변경 후 feed/search projection 반영 SLO와 alert 기준은 무엇입니까?

A) 정상 상태 p95 60초 이내, 5분 초과 lag가 5분간 지속되면 alert한다.

B) 정상 상태 p95 5분 이내, 15분 초과 lag가 10분간 지속되면 alert한다.

C) 1시간 batch 반영을 허용하고 batch 실패에만 alert한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 8
초기 한국어·영어 semantic embedding 방식은 무엇입니까?

A) provider-neutral 외부 embedding adapter와 versioned model contract를 사용하고 vector는 PostgreSQL에 저장한다.

B) application container에 multilingual local embedding model을 포함하고 외부 호출 없이 생성한다.

C) text search contract만 먼저 구현하고 semantic embedding은 상용 전환까지 비활성화한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 9
Semantic dependency의 timeout과 fallback budget은 무엇입니까?

A) 연결 300ms, 전체 embedding/retrieval 1.5초에서 중단하고 남은 budget으로 승인 text/filter fallback을 수행한다.

B) 전체 검색 p95 3초를 모두 semantic 호출에 사용하고 timeout 후 오류를 반환한다.

C) semantic 호출을 최대 5초 기다리고 느리더라도 결과 품질을 우선한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 10
한국어·영어 검색 품질 release gate는 어떻게 검증합니까?

A) 언어별 versioned golden query set에서 text/semantic Recall@10 0.80 이상과 NDCG@10 0.75 이상을 요구한다.

B) US-004~US-006 acceptance example이 모두 통과하면 별도 ranking 지표 없이 승인한다.

C) 수동 탐색 평가만 수행하고 정량 기준은 사용자 행동 데이터가 쌓인 후 정의한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 11
검색 query의 privacy와 운영 로그 정책은 무엇입니까?

A) raw query를 application log에 남기지 않고 language, length bucket, parsed-field count, latency와 non-reversible query fingerprint만 기록한다.

B) 장애 분석을 위해 raw query를 7일간 제한 접근 로그에 저장한다.

C) 개인 식별자만 마스킹하고 raw query를 일반 운영 로그에 저장한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 12
검색·피드 abuse control과 입력 제한은 무엇입니까?

A) IP/subject 기준 anonymous 30, authenticated 60 requests/minute, query 500자, filter value 50개, page size 50으로 제한한다.

B) 모든 사용자에게 120 requests/minute를 적용하고 query와 filter 개수는 schema 최대 크기만 제한한다.

C) U07 공통 rate limit만 사용하고 U03 전용 limit은 두지 않는다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 13
100,000개 기준 전체 projection rebuild 목표는 무엇입니까?

A) 30분 이내에 새 snapshot을 만들고 검증 완료 전까지 이전 정상 snapshot을 계속 제공한다.

B) 2시간 이내 rebuild를 허용하고 그동안 search를 maintenance 상태로 전환한다.

C) rebuild 시간 목표 없이 야간 작업으로 실행한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 14
U03 전용 운영 alert 범위는 무엇입니까?

A) projection lag/gap, semantic fallback rate, approval-closure drop, stale-content ratio, cache error와 search zero-result spike를 모두 alert 또는 dashboard signal로 관리한다.

B) API latency/error와 projection job failure만 alert한다.

C) U07 공통 API alert만 사용하고 U03 전용 signal은 생성하지 않는다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 15
U03 test quality gate는 무엇입니까?

A) 전체 line coverage 80% 이상, CAT/AVAIL/PROJ closure branch 100%, US-001~US-006 example test와 PBT-U03-01~16을 모두 요구한다.

B) 전체 line coverage 80%와 example test만 필수로 하고 PBT는 권고로 둔다.

C) 전체 line coverage 90%를 요구하되 critical branch와 PBT 개별 gate는 두지 않는다.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Planned Outputs

- `aidlc-docs/construction/u03-catalog-and-discovery/nfr-requirements/nfr-requirements.md`
- `aidlc-docs/construction/u03-catalog-and-discovery/nfr-requirements/tech-stack-decisions.md`

## Extension Planning Status

- **RESILIENCY-01~15**: U07 전역 결정을 상속하고 U03 capacity, cache, projection lag, semantic failure isolation과 관측 신호를 구체화한다.
- **PBT-01**: Functional Design의 PBT-U03-01~16을 formal property inventory로 사용한다.
- **PBT-09**: pytest와 Hypothesis를 상속한다. Code Generation에서 dependency, seed와 shrinking을 재검증한다.
- **Security Baseline**: disabled이므로 extension으로는 N/A이다. 승인 폐쇄성, query privacy와 abuse control은 core NFR로 적용한다.
- **Frontend**: U03은 UI를 소유하지 않는다. 상태, locale, pagination과 degraded response contract를 U01에 전달한다.
