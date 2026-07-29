# U05 Infrastructure Design 검토 회의록

## 회의 정보

| 항목 | 내용 |
|---|---|
| 일자 | 2026-07-29 |
| 주제 | U05 Recommendation and AI Grounding Infrastructure Design 검토 |
| 참석 | 프로젝트 담당자, Codex |
| 진행 상태 | Infrastructure Design 완료, 사용자 승인 대기 |

## 목적

U05 추천·AI Grounding 기능을 현재 OTT Feed 플랫폼 인프라에 배치하는 방법을 확정하고, 구현 전에 성능·복원력·개인정보·검증 Gate가 빠짐없이 설계되었는지 확인한다.

## 주요 결정

1. 온라인 추천 Pipeline은 별도 마이크로서비스 없이 기존 FastAPI API 프로세스에서 동기 실행한다.
2. U05 상태는 공유 PostgreSQL 17의 `u05_recommendation` 스키마에 저장하고 migration, API, maintenance 역할을 분리한다.
3. U05 API 프로세스의 PostgreSQL 연결은 최대 2개, AI 동시 호출은 최대 4개로 시작한다.
4. Redis, 메시지 브로커, 중복 Vector Store는 초기 버전에 추가하지 않는다.
5. 후보와 근거는 U03 승인 Read Port에서만 받고 U04 검증 규칙으로 노출 전에 다시 검증한다.
6. AI는 후보 적격성이나 순위를 결정하지 않으며, 생성된 이유·요약은 Claim 단위로 검증한 뒤에만 노출한다.
7. AI 장애, timeout, circuit open 또는 사용량 초과 시 결정론적 Intent 처리와 Metadata 기반 Template으로 저하 운용한다.
8. AI Credential은 API에만 read-only Secret 파일로 제공하고, Endpoint는 HTTPS scheme·host·port allowlist로 제한한다.
9. Raw Prompt, AI 원문 응답, 실패 Draft, Chain-of-thought는 DB, 로그, Metric, Trace와 Backup에 저장하지 않는다.
10. 배포는 현재 승인된 단일 Linux Host와 Docker Compose 구성을 유지한다. GitHub Actions 자동 Trigger는 계속 중단하고 수동 Workflow만 사용한다.

## 성능 및 운영 기준

| 기준 | 목표 또는 제한 |
|---|---|
| 일반 추천 응답 | p95 10초 이하 |
| 저하 운용 응답 | p95 3초 이하 |
| 초기 사용자 규모 | 동시 사용자 10명 미만 |
| 처리량 | 지속 5 RPS, Burst 15 RPS |
| 후보 입력 | 최대 1,000개 |
| 점수 계산 후보 | 최대 500개 |
| 사용자 노출 후보 | 최대 20개 |
| 월 가용성 | 99.0% |
| RTO / RPO | 4시간 / 24시간 |

## 검증 Gate

- 실제 PostgreSQL 17 환경에서 `pytest -m integration` 선택 테스트 skip 0.
- P-U05-01부터 P-U05-12까지 Hypothesis Property-Based Test 실행.
- Hard Filter, Consent 제외, Claim 검증, 실패 Draft 비노출 Branch Coverage 100%.
- 전체 Source Coverage 80% 이상.
- 한국어·영어 Intent 및 Grounding 평가 Fixture 통과.
- Timeout, Rate Limit, Circuit, 잘못된 Schema, 응답 크기 초과, 사용량 제한 장애 주입 통과.
- Secret, Egress, Telemetry 및 Persistence 금지 필드 검사 통과.
- Backup 복원 후 AI 비활성 상태의 결정론적 추천과 U02/U03/U04 Contract 재진입 검증.

## 복구 및 Rollback

1. 장애가 발생하면 새 AI Policy 활성화를 먼저 중단하고 결정론적 추천을 유지한다.
2. 이전 Image Digest와 호환 가능한 설정·Policy Pointer로 복귀한다.
3. Application Rollback 과정에서 Session·Trace 데이터를 파괴적으로 되돌리지 않는다.
4. 복원 환경에서는 U05 상태 무결성과 U02/U03/U04 Contract를 검증한다.
5. AI를 끈 상태에서 Synthetic 추천을 확인한 후 Provider·비용·평가 Gate를 통과해야 AI를 다시 활성화한다.

## Extension 준수 결과

| Extension | 결과 |
|---|---|
| Resiliency Baseline | 준수. 단일 Host와 비자동확장은 Prototype 예외이며 Production 전환 Gate로 유지 |
| Property-Based Testing | 준수 계획 완료. 실제 실행 증거는 Code Generation과 Build and Test의 차단 Gate |
| Security Baseline | 비활성화. 다만 Secret 격리, 개인정보 최소화, Egress 제한은 Core 요구사항으로 유지 |

현재 차단된 Extension Finding은 없다.

## 미결 사항

- U05 Infrastructure Design 사용자 승인.
- 실제 AI Provider, Model, Endpoint와 단가 선택. 선택 전까지 Fake Transport와 결정론적 Fallback이 기준이다.
- Code Generation 단계에서 Compose, Secret Reference, Migration, U05 코드와 테스트를 구현한다.

## 다음 액션

| 담당 | 작업 | 상태 |
|---|---|---|
| 프로젝트 담당자 | U05 Infrastructure Design 승인 또는 변경 요청 | 대기 |
| Codex | 승인 후 U05 Code Generation 상세 계획 작성 | 대기 |
| Codex | 계획 승인 후 코드·Migration·테스트·인프라 설정 구현 및 검증 | 대기 |

## 관련 문서

- `aidlc-docs/construction/u05-recommendation-and-ai-grounding/infrastructure-design/infrastructure-design.md`
- `aidlc-docs/construction/u05-recommendation-and-ai-grounding/infrastructure-design/deployment-architecture.md`
- `aidlc-docs/construction/plans/u05-recommendation-and-ai-grounding-infrastructure-design-plan.md`
