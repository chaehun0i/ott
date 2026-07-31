# U06 Engagement and Operations NFR Requirements Plan

> **Single Source of Truth**: 이 파일은 U06 NFR Requirements의 계획, 사용자 결정과 완료 체크박스를 관리한다. 모든 답변이 유효하고 모호하지 않을 때까지 최종 NFR 산출물을 생성하지 않는다.

## Context and Inherited Decisions

- **Approved Functional Scope**: 인앱·이메일 알림, 버전 조건부 운영 Override, 불변 감사, 비식별 추천 Trace, Health·Alert·Incident 관리.
- **Scale Baseline**: 동시 사용자 10명 미만, 단일 리전·단일 서버 프로토타입.
- **Availability and Recovery**: 월 99.0%, 계약상 SLA 없음, RTO 4시간, RPO 24시간, Backup and Restore, 백업 30일.
- **Runtime Baseline**: Python 3.12.13, FastAPI/Pydantic, PostgreSQL/SQLAlchemy/Alembic, PostgreSQL Outbox, Docker Compose.
- **Quality Baseline**: pytest 9.1.1, Hypothesis 6.161.5, Ruff 0.16.0, strict MyPy 2.3.0, branch coverage 80% 이상.
- **Delivery Baseline**: GitHub Actions 자동 Trigger는 일시 중지 상태이며 수동 검증만 허용한다.
- **Enabled Extensions**: Resiliency Baseline (Full), Property-Based Testing (Full).
- **Disabled Extension**: Security Baseline. 핵심 권한·감사·비식별·암호화 요구는 일반 NFR로 유지한다.

## Execution Plan

### Step 1 - Context and Baseline

- [x] 승인된 U06 Functional Design과 P-U06-01~12를 확인한다.
- [x] 프로젝트 규모, 가용성, 복구, 개인정보와 운영 Baseline을 확인한다.
- [x] 실제 `pyproject.toml`과 기존 잠금 스택을 확인한다.
- [x] U02~U05/U07의 U06 소비 Contract와 기존 관측·작업 기반을 확인한다.

### Step 2 - NFR Decisions

- [x] 아직 확정되지 않은 U06 성능, 전달, 보존, 권한, 관측, 경보와 Queue 결정을 식별한다.
- [x] 상호 배타적 선택지와 마지막 `X) Other`를 포함한 Question 1~10을 작성한다.
- [ ] 모든 `[Answer]:` 값을 수집하고 선택지 유효성을 검증한다.
- [ ] 답변 간 모순과 기존 Baseline 충돌을 분석하고 필요한 경우 clarification 파일을 작성한다.

### Step 3 - NFR Requirements

- [ ] 작업 부하 중요도, 용량, 확장 검토 Trigger와 Resource Bound를 정의한다.
- [ ] API 지연, 알림 전달, 처리량, Timeout, Retry와 Expiry 목표를 정의한다.
- [ ] 가용성, 일관성, 멱등성, 저하 운용, 복구와 데이터 보존 요구를 정의한다.
- [ ] 권한, 개인정보, 감사 무결성, 비밀정보와 운영 Evidence 보호 요구를 정의한다.
- [ ] Metrics, Logs, Traces, Health, Alert, Incident와 비용·유지보수 요구를 정의한다.
- [ ] `nfr-requirements.md`를 생성한다.

### Step 4 - Technology and Quality Gates

- [ ] 기존 Python/PostgreSQL Modular Monolith와 Outbox 유지 여부를 확정한다.
- [ ] 알림 Adapter, Scheduler, Health Registry, Prometheus/Grafana와 API Contract 기술 결정을 기록한다.
- [ ] PBT-09에 따라 Hypothesis를 U06 Property Framework로 확정하고 P-U06-01~12 Gate를 연결한다.
- [ ] Example, Contract, PBT, PostgreSQL Integration, Failure, Privacy와 Capacity Gate를 정의한다.
- [ ] `tech-stack-decisions.md`를 생성한다.

### Step 5 - Validation and Completion

- [ ] U06 Story/Functional Rule/NFR/Technology traceability를 검증한다.
- [ ] RESILIENCY-01~15와 PBT-09 준수 및 N/A 근거를 평가한다.
- [ ] Markdown 문법과 표 구조를 검증한다.
- [ ] 계획·상태·감사 기록을 갱신하고 표준 NFR Requirements 승인 지점을 제시한다.

## NFR Requirements Questions

각 `[Answer]:` 뒤에 선택한 문자 하나를 입력한다. 적합한 정책이 없으면 `X`를 선택하고 원하는 내용을 함께 작성한다.

## Question 1
U06 운영·Trace API와 상태 조회의 응답 시간 목표는 무엇입니까?

A) 일반 운영·Trace 조회 p95 2초 이내, 변경 Command 접수 p95 2초 이내, 얕은 Health p95 250ms·깊은 Health p95 1초 이내

B) 모든 U06 API p95 5초 이내의 단일 목표를 사용한다

C) 프로토타입에서는 응답 시간 목표를 두지 않고 기능 정확성만 검증한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 2
신규 공개·가용성 변경 알림의 전달 시간 목표는 무엇입니까?

A) 승인 이벤트 수신 후 인앱 p95 1분, 이메일 p95 5분 이내에 전달 또는 명확한 terminal 상태로 확정한다

B) 두 채널 모두 1시간 이내 전달을 목표로 한다

C) 당일 전달만 보장하고 별도 percentile 목표를 두지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 3
U06의 초기 용량과 확장 재검토 기준은 무엇입니까?

A) 기존 5 sustained/15 burst RPS, 동시 사용자 10명 미만을 유지하고 10,000 pending Job·100,000 Audit/Incident 조회 Dataset에서 검증하며 70% 자원 사용 또는 2배 성장 시 재검토한다

B) 초기부터 100 sustained/300 burst RPS와 100만 pending Job을 목표로 한다

C) 기능 테스트만 수행하고 용량 한도는 상용 전환 시 처음 정의한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 4
이메일 전달 실패의 Timeout·Retry·Expiry 정책은 무엇입니까?

A) 시도당 5초 Timeout, 최대 3회 지수 Backoff와 Jitter를 적용하고 30분 또는 이벤트 유효기간 중 빠른 시점에 만료한다

B) 시도당 30초 Timeout으로 최대 10회 재시도하고 24시간 후 만료한다

C) 재시도 없이 첫 실패를 terminal 상태로 처리한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 5
U06 운영 데이터 보존 기간은 어떻게 설정합니까?

A) 알림 본문·전달 상세 30일, Job/상태 90일, 감사·Incident·COE 365일을 기본으로 하고 법적 보존 Hold와 사용자 삭제 시 비식별화를 우선한다

B) 모든 U06 데이터를 30일 보존 후 동일하게 삭제한다

C) 감사와 Incident를 영구 보존하고 알림 데이터만 30일 보존한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 6
운영·Trace 권한과 민감 작업 보호 수준은 무엇입니까?

A) Content Operator는 콘텐츠 조회·버전 조건부 변경, System Administrator는 Trace·Incident·감사 조회를 담당하고 고영향 변경은 최근 인증·명시적 이유·멱등 키를 요구한다

B) Content Operator 단일 역할이 모든 U06 기능을 수행한다

C) 모든 운영·Trace 기능을 두 명 승인 방식으로 제한한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 7
감사 무결성과 저장 보호를 어느 수준으로 적용합니까?

A) 별도 U06 Schema·최소 권한·append-only Application Contract·행 Digest·암호화 Backup을 적용하고 직접 식별자와 Secret을 금지한다

B) 일반 Application Table과 동일 권한을 사용하고 변경 이력만 별도 행으로 남긴다

C) 외부 전용 감사 SaaS를 신규 도입해 모든 기록을 전송한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 8
운영 Metrics·Logs·Trace의 개인정보와 Cardinality 정책은 무엇입니까?

A) 고정된 service/component/channel/outcome/reason 집합만 Label로 사용하고 사용자·콘텐츠·Trace·Incident ID와 메시지 본문은 Metric/Log Label에서 제외한다

B) 조사 편의를 위해 Trace ID와 콘텐츠 ID를 모든 Metric Label에 포함한다

C) Metrics만 수집하고 구조화 Log와 상관관계 ID는 사용하지 않는다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 9
초기 경보와 Incident 승격 기준은 어떻게 정의합니까?

A) 필수 Readiness 실패 즉시, Notification terminal 실패율 10%/10분, 가장 오래된 Job 5분 초과, Audit 실패 1건, Alert 지속 5분을 기본값으로 하고 버전 관리한다

B) 모든 오류 1건마다 즉시 Incident를 생성한다

C) 자동 경보 없이 운영자가 Dashboard를 수동 확인한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Question 10
Notification Job과 운영 Event 처리 기술은 무엇을 사용합니까?

A) 기존 PostgreSQL Transactional Outbox와 Worker를 유지하고, 규모 Trigger 초과 시 Broker 도입을 재검토한다

B) 지금 Kafka를 추가해 모든 U06 Event를 분산 처리한다

C) 외부 Managed Queue를 필수로 도입하고 PostgreSQL Outbox를 제거한다

X) Other (please describe after the `[Answer]:` tag)

[Answer]:

## Planned Artifacts

- `aidlc-docs/construction/u06-engagement-and-operations/nfr-requirements/nfr-requirements.md`
- `aidlc-docs/construction/u06-engagement-and-operations/nfr-requirements/tech-stack-decisions.md`

## Preliminary Extension Assessment

### Resiliency Baseline

- RESILIENCY-01, 05~07, 10, 15는 U06의 Criticality, 관측, Health, 실패 격리와 Incident 요구에 직접 적용한다.
- RESILIENCY-02~04와 11~14는 승인된 U07 가용성·복구·배포 기준을 유지하고 U06이 상태와 Evidence를 소비한다.
- RESILIENCY-08~09는 승인된 단일 서버·고정 용량 프로토타입 예외이며 Question 3의 Trigger로 재평가 시점을 명시한다.

### Property-Based Testing

- PBT-09는 실제 잠금 의존성인 Hypothesis 6.161.5와 pytest 9.1.1을 U06에도 유지하는 것으로 계획한다.
- P-U06-01~12의 Custom Strategy, Shrinking, Seed 재현, Stateful Model과 Example Test 병행은 Code Generation Gate로 전달한다.

### Security Baseline

- 확장은 비활성화되어 N/A다. Question 6~8은 핵심 역할·감사·개인정보 보호 요구를 일반 NFR로 확정한다.
