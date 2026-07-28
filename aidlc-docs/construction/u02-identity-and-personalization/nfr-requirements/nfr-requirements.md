# U02 NFR Requirements

## Scope

이 문서는 U02 Identity and Personalization의 인증, 권한, profile, library, consent, feedback, feature snapshot과 data-rights 품질 기준을 정의한다. U07의 공통 runtime·API·PostgreSQL·관측성·복구 기준을 상속하며 U02 고유 위험을 강화한다.

## Criticality and Business Impact

| Workload | Criticality | Unavailable or Incorrect Impact | Dependencies |
|---|---|---|---|
| Authentication and Session | Critical | 회원 기능 전체 접근 불가 또는 계정 탈취 위험 | U07 API, PostgreSQL, Google OAuth, email delivery |
| Authorization and Role | Critical | 개인정보·운영 기능의 권한 우회 | U07 request context, PostgreSQL, U06 audit |
| Consent Enforcement | Critical | 동의 없는 수집·개인화와 신뢰·법무 위험 | PostgreSQL, U05 feature consumer, U07 outbox |
| Account Deletion | Critical | 개인정보 권리 미이행과 재활성화 위험 | PostgreSQL, U07 worker, storage, U06 audit |
| Profile and Library | High | 설정·찜·평가·이력 손실과 추천 품질 저하 | PostgreSQL, U03 content reference |
| Feedback and Features | High | 개인화 최신성 저하 또는 잘못된 추천 신호 | PostgreSQL, U07 outbox, U05 |
| Data Export | High | 데이터 권리 처리 지연 | PostgreSQL, encrypted artifact storage, worker |

## Capacity and Scalability

- **U02-NFR-001**: Prototype 검증은 10명 동시 사용자를 재현해야 한다.
- **U02-NFR-002**: 인증 endpoint는 정상 resource limit 안에서 20 requests/second burst를 처리하고 latency·error·hashing saturation을 기록해야 한다.
- **U02-NFR-003**: load evidence는 login, authorization, profile read·write, event intake와 FeatureSnapshot을 포함해야 한다.
- **U02-NFR-004**: password hashing concurrency는 CPU·memory를 고갈시키지 않도록 별도 bounded executor 또는 concurrency limit을 가져야 한다.
- **U02-NFR-005**: PostgreSQL pool은 U07 global connection budget 안에서 API, authentication hashing 이후 transaction과 worker job을 분리해야 한다.
- **U02-NFR-006**: 동시 사용자 50명, 인증 burst 50 requests/second 또는 pool·CPU·queue 지속 포화가 예상되면 stateless API replica와 worker scale-out을 재평가해야 한다.

## Performance

- **U02-NFR-007**: email login과 server-side authorization의 p95는 정상 부하에서 각각 500ms 이하여야 한다.
- **U02-NFR-008**: profile·preference·library write p95는 500ms 이하여야 한다.
- **U02-NFR-009**: profile·library read와 FeatureSnapshot p95는 300ms 이하여야 한다.
- **U02-NFR-010**: feedback event durable acceptance p95는 200ms 이하여야 한다.
- **U02-NFR-011**: Google OAuth provider round-trip은 내부 U02 latency와 분리해 측정하고 end-to-end p95를 별도 보고해야 한다.
- **U02-NFR-012**: 성능 결과는 p50, p95, p99, throughput, error, database pool, hash executor와 worker backlog saturation을 포함해야 한다.
- **U02-NFR-013**: Argon2id parameter는 보안 목표와 500ms login budget을 함께 만족하도록 target runtime에서 benchmark하고 고정해야 한다.

## Availability, Recovery and Data Integrity

- **U02-NFR-014**: Prototype monthly service objective는 U07과 같은 99.0%이며 provider outage를 내부 availability와 분리해 측정해야 한다.
- **U02-NFR-015**: 전체 U02 persistent state는 U07의 RTO 4시간, RPO 24시간과 Backup and Restore 전략을 따른다.
- **U02-NFR-016**: OAuth 장애 시 email login과 기존 session authorization은 계속 사용할 수 있어야 한다.
- **U02-NFR-017**: consent storage 또는 current decision 조회 실패는 event collection과 personalized snapshot을 fail closed해야 한다.
- **U02-NFR-018**: explicit library mutation과 authoritative feature update는 동일 transaction 또는 원자적 outbox handoff를 가져야 한다.
- **U02-NFR-019**: implicit event는 durable commit 후에만 성공을 반환하고 worker retry가 중복 feature contribution을 만들지 않아야 한다.
- **U02-NFR-020**: deletion job 부분 실패 시 account는 disabled 상태를 유지하고 terminal completion까지 재시도해야 한다.
- **U02-NFR-021**: backup restore 검증은 user, consent decision, role, session revocation, idempotency, deletion progress와 feature version 무결성을 포함해야 한다.

## Authentication and Session Security

- **U02-NFR-022**: password는 Argon2id로 hash하고 parameter version을 credential에 저장하며 정책이 바뀌면 성공 로그인 시 점진적으로 rehash해야 한다.
- **U02-NFR-023**: password plaintext, verification token, reset token과 session token 원문은 저장·log·metric·trace·error·artifact에 포함하지 않아야 한다.
- **U02-NFR-024**: session token은 최소 128-bit entropy의 opaque secret이어야 하고 browser에는 Secure, HttpOnly와 적절한 SameSite cookie로 전달해야 한다.
- **U02-NFR-025**: server는 session token hash, 상태, owner, expiry와 revocation만 저장해야 한다.
- **U02-NFR-026**: inactivity timeout은 30분, absolute lifetime은 30일이며 export, deletion, account linking과 role administration은 최근 10분 이내 fresh authentication을 요구해야 한다.
- **U02-NFR-027**: email verification은 24시간, password reset은 30분 후 만료하며 challenge는 purpose-bound single-use여야 한다.
- **U02-NFR-028**: 인증 응답과 timing은 account 존재, verification 상태와 credential 유형을 불필요하게 식별할 수 없게 해야 한다.
- **U02-NFR-029**: Google OAuth는 state와 callback binding, issuer, audience, nonce와 provider subject를 검증해야 하며 verified email만으로 account를 자동 연결할 수 없다.
- **U02-NFR-030**: 회원, ContentOperator와 SystemAdministrator 권한은 server-side current policy와 authorization version으로 검증해야 한다.

## Encryption, Secrets and Privacy

- **U02-NFR-031**: transport는 U07 TLS edge를 사용하고 PostgreSQL volume과 backup은 저장 시 암호화해야 한다.
- **U02-NFR-032**: normalized email과 저장된 OAuth claim의 직접 식별 field는 application-level envelope encryption을 사용해야 한다.
- **U02-NFR-033**: 검색용 equality index가 필요하면 평문 대신 domain-separated keyed blind index를 사용하고 encryption key와 분리해야 한다.
- **U02-NFR-034**: envelope data key, key-encryption key와 blind-index key는 repository·image·database data와 분리하고 versioned key reference만 저장해야 한다.
- **U02-NFR-035**: key rotation은 새 write를 새 key version으로 처리하고 기존 row를 중단 가능한 background re-encryption으로 전환해야 한다.
- **U02-NFR-036**: U05 FeatureSnapshot에는 request-scoped pseudonym, allow-listed feature, FeatureVersion, ConsentVersion과 expiry만 포함해야 한다.
- **U02-NFR-037**: email, OAuth subject, session ID, raw behavior payload와 reversible user identifier는 U05 또는 external AI context로 전달할 수 없다.
- **U02-NFR-038**: 초기 대상은 대한민국이며 상용 전환 전에 국내 개인정보·소비자 보호 법무 검토를 완료해야 한다.
- **U02-NFR-039**: consent notice는 purpose, retention, external AI transfer boundary, policy version과 locale을 machine-readable contract로 제공해야 한다.

## Retention and Data Rights

- **U02-NFR-040**: personalization raw behavior event의 기본 보존 기간은 180일이다.
- **U02-NFR-041**: aggregated personalization feature의 기본 보존 기간은 365일이다.
- **U02-NFR-042**: consent withdrawal 또는 authorized deletion이 먼저 발생하면 보존 기간과 무관하게 source event와 derived feature 삭제를 시작해야 한다.
- **U02-NFR-043**: export는 승인 후 24시간 이내 완료해야 하며 encrypted artifact의 별도 download expiry를 NFR Design에서 확정해야 한다.
- **U02-NFR-044**: account와 personalization deletion은 승인 후 72시간 이내 terminal completion해야 한다.
- **U02-NFR-045**: retained consent evidence와 legal·operational tombstone은 personalization에 재사용할 수 없고 보존 근거·기간·owner를 가져야 한다.
- **U02-NFR-046**: deletion closure 검증은 credentials, OAuth links, sessions, profile, library, behavior, features, export artifacts와 cache를 모두 포함해야 한다.
- **U02-NFR-047**: export와 deletion status는 safe category status만 노출하고 삭제된 값 또는 secret reference를 반환하지 않아야 한다.

## Feature Freshness and Reliability

- **U02-NFR-048**: explicit save·rating feature는 successful command response 시점에 authoritative state와 일치해야 한다.
- **U02-NFR-049**: implicit behavior feature 반영 latency는 정상 상태 p95 5분 이하여야 한다.
- **U02-NFR-050**: oldest eligible event age 또는 backlog latency가 15분을 초과하면 alert를 발생시켜야 한다.
- **U02-NFR-051**: worker 재처리, lease recovery와 out-of-order event가 FeatureVersion을 역행시키거나 contribution을 중복 적용할 수 없다.
- **U02-NFR-052**: stale ConsentVersion의 feature는 latency 목표 충족 여부와 관계없이 노출할 수 없다.

## Observability and Incident Response

- **U02-NFR-053**: metric은 auth success·failure, verification, reset, session revoke, authorization denial, OAuth failure, rate limit, consent fail-closed, event intake, dedup, feature lag, export와 deletion status를 포함해야 한다.
- **U02-NFR-054**: alert는 인증 실패율 급증, rate-limit 증가, OAuth 오류, consent fail-closed 증가, 15분 feature backlog, deletion 72시간 위험과 export failure를 포함해야 한다.
- **U02-NFR-055**: log와 trace는 correlation 또는 job ID를 사용하되 email, provider subject, token, UserId 원문, free-form event payload와 export content를 금지해야 한다.
- **U02-NFR-056**: Critical flow dashboard는 availability, latency, error, saturation, consent failures와 data-rights SLA를 표시해야 한다.
- **U02-NFR-057**: U02 incident는 U07 경량 탐지·영향·완화·복구·공지·사후 분석 절차를 따르고 privacy impact 여부를 별도 기록해야 한다.

## Maintainability, Change and Testability

- **U02-NFR-058**: schema, consent notice, encryption 또는 session policy 변경은 U07 change record에 privacy/security review checklist를 추가해야 한다.
- **U02-NFR-059**: data migration은 이전 application version과의 compatibility, rollback note와 consent/deletion invariant 검증을 가져야 한다.
- **U02-NFR-060**: 전체 line coverage는 80% 이상이어야 한다.
- **U02-NFR-061**: BR-U02-001~051의 핵심 decision branch는 100% coverage와 명시적 example test를 가져야 한다.
- **U02-NFR-062**: PBT-U02-01~11은 pytest와 Hypothesis로 구현하고 shrinking을 비활성화할 수 없다.
- **U02-NFR-063**: CI는 seed를 기록하고 shrunk counterexample과 replay 정보를 artifact로 보존해야 한다.
- **U02-NFR-064**: PBT 발견 최소 사례는 permanent regression example test로 승격해야 한다.
- **U02-NFR-065**: identity, consent, feature와 data-rights DTO의 versioned round-trip과 direct-identifier non-disclosure를 contract gate로 검증해야 한다.

## U01 Usability and Accessibility Handoff

- **U02-NFR-066**: U02는 cookie, session expiry, reauthentication, consent notice, export·deletion status와 safe error code를 versioned OpenAPI contract로 제공해야 한다.
- **U02-NFR-067**: U01이 keyboard와 assistive technology 흐름을 구현할 수 있도록 상태·오류·대기·재시도 의미를 색상 비의존 machine-readable field로 제공해야 한다.
- **U02-NFR-068**: 인증 error는 account enumeration을 막으면서 사용자가 취할 수 있는 안전한 다음 행동을 한국어·영어 message key로 제공해야 한다.

## Verification Matrix

| NFR Set | Verification | Evidence Stage |
|---|---|---|
| 001~006 | load test, hash saturation and pool capacity report | NFR Design, Build and Test |
| 007~013 | endpoint benchmark and OAuth-separated latency report | Code Generation, Build and Test |
| 014~021 | degradation, transaction, restore and job recovery tests | NFR Design, Build and Test |
| 022~030 | credential, cookie, challenge, OAuth and authorization tests | Code Generation, Build and Test |
| 031~039 | encryption configuration, key isolation, redaction and contract review | NFR Design, Infrastructure Design, Build and Test |
| 040~047 | retention, export SLA and deletion closure tests | Code Generation, Build and Test |
| 048~057 | worker ordering, freshness metric, alert and incident drill | Code Generation, Build and Test |
| 058~065 | CI, coverage, migration, example and PBT artifacts | Code Generation, Build and Test |
| 066~068 | OpenAPI consumer and U01 accessibility contract review | Code Generation, U01 Build and Test |

## Resiliency Compliance

| Rule | Status | U02 Treatment |
|---|---|---|
| RESILIENCY-01 | Compliant | Critical and High workloads, impacts and dependencies are classified. |
| RESILIENCY-02 | Compliant | U07 99.0%, RTO 4h and RPO 24h targets are inherited. |
| RESILIENCY-03 | Compliant | U07 lightweight change record plus privacy/security checklist is required. |
| RESILIENCY-04 | Compliant | GitHub Actions, direct deployment and version-pinned rollback are inherited. |
| RESILIENCY-05 | Compliant | U02 metrics, safe logs, trace correlation, dashboard and alerts are specified. |
| RESILIENCY-06 | Compliant | U07 health applies; U02 deep contribution covers PostgreSQL, OAuth and job freshness without exposing details. |
| RESILIENCY-07 | Compliant | consent, deletion, export and feature backlog degradation alerts are required. |
| RESILIENCY-08 | N/A | Approved non-production single-server prototype exception; production multi-zone remains a blocking gate. |
| RESILIENCY-09 | N/A | Initial scale exception is inherited with explicit 50-user and saturation reevaluation trigger. |
| RESILIENCY-10 | Compliant | OAuth isolation, bounded hashing and pool resources, durable jobs and fail-closed consent are required. |
| RESILIENCY-11 | Compliant | Backup and Restore is aligned with inherited targets. |
| RESILIENCY-12 | Compliant | U02 state is included in encrypted daily backup and integrity verification. |
| RESILIENCY-13 | Compliant | Restore re-entry includes identity, revocation, consent and deletion integrity. |
| RESILIENCY-14 | Compliant | Inherited monthly dependency failure tests and quarterly restore drill cover U02 failure modes. |
| RESILIENCY-15 | Compliant | U07 incident lifecycle is extended with privacy impact recording. |

## Property-Based Testing Compliance

| Rule | Status | U02 Treatment |
|---|---|---|
| PBT-01 | Compliant | PBT-U02-01~11 are formally identified with invariants and trace. |
| PBT-09 | Compliant | pytest and Hypothesis are selected. |
| PBT-08 | Planned | seed, shrinking, counterexample artifact and regression promotion are mandatory downstream. |
| PBT-02~07, PBT-10 | N/A at NFR Requirements | Test implementation occurs in Code Generation; properties and example-test complement are specified. |

No blocking enabled-extension finding remains at this stage.

