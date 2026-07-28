# Consolidated Application Design

## Decision Summary

| Decision | Selected Design |
|---|---|
| Backend | Python modular Monolith |
| Web | 별도 React 정적 Web Container |
| API | REST JSON with OpenAPI |
| Database | PostgreSQL 중심, JSON·전문 검색·Vector 확장 |
| Worker | 수집·알림 별도 Process, PostgreSQL-backed Job·Outbox |
| Recommendation | 제한 시간 내 동기 HTTP Pipeline |
| AI | Provider-neutral Port, 초기 단일 Provider Adapter |
| Authentication | Application 이메일 인증과 OAuth Adapter |

## Core Architecture

- API와 Worker는 같은 Domain Codebase를 공유하지만 Entry Point와 Process를 분리한다.
- Domain Module은 Port를 정의하고 PostgreSQL, AI, OAuth, 콘텐츠 공급자, 알림 Channel은 Adapter가 구현한다.
- AI Interaction은 Intent와 문구 초안만 생성한다.
- Recommendation Engine이 승인 후보의 적격성·점수·개인화·다양성·최종 순위를 소유한다.
- Recommendation Output Validation이 사용자 노출 전 후보와 Claim Grounding을 Fail-closed로 검증한다.

## Critical Architecture Rules

1. Raw·Normalized·Quarantine Metadata는 사용자 Query와 Recommendation Candidate가 될 수 없다.
2. AI Output은 RecommendationIntent 또는 GroundedTextDraft Schema 밖에서 사용하지 않는다.
3. AI는 Candidate Eligibility와 Final Rank를 변경할 수 없다.
4. Output Validation을 통과하지 않은 Candidate·문구는 노출하지 않는다.
5. 동의되지 않은 행동 Event와 직접 식별자는 AI Context에 포함하지 않는다.
6. 외부 Dependency 실패는 Timeout·제한된 Retry·격리·Fallback 경계를 가진다.

## Artifact Index

- [components.md](components.md): Component 책임, 금지 책임, Port, 소유 상태
- [component-methods.md](component-methods.md): 고수준 Method와 Error Contract
- [services.md](services.md): Application Service와 Orchestration
- [component-dependency.md](component-dependency.md): Dependency Matrix와 Data Flow

## Requirements and Story Coverage

| Capability | Components | Story Range |
|---|---|---|
| Feed and Content | C01, C02, C04 | US-001~US-003 |
| Search and Localization | C01, C02, C04, C07, C09 | US-004~US-009 |
| Recommendation | C08, C09, C10, C11 | US-008~US-013, US-022~US-024 |
| Account and Personalization | C03, C12 | US-014~US-018, US-027 |
| Notification | C13 | US-019 |
| Ingestion and Validation | C05, C06, C04 | US-020, US-022 |
| Admin and Operations | C14 | US-021, US-023, US-025~US-028 |

## Units Generation Inputs

Units Generation은 다음 응집 경계를 평가한다.

1. Web Experience
2. Identity and Personalization
3. Content Catalog and Search
4. Content Ingestion and Metadata Validation
5. Recommendation and AI Grounding
6. Admin, Notification and Operations
7. Platform and Delivery

정확한 Unit 수와 의존 순서는 Units Generation에서 확정한다.

## Resiliency Compliance

| Rules | Status | Design Treatment |
|---|---|---|
| RESILIENCY-01~02 | Compliant | Component 중요도와 동기 추천·복구 경계를 후속 NFR에 전달한다. |
| RESILIENCY-03~04 | N/A | CI/CD와 Rollback 상세는 Infrastructure Design 대상이다. |
| RESILIENCY-05~07 | Compliant | Health·Observability Port와 C14 운영 경계를 정의했다. |
| RESILIENCY-08~09 | N/A | 초기 단일 서버·저규모 사용자 승인 예외이다. |
| RESILIENCY-10 | Compliant | Adapter Timeout·Retry·격리와 Fallback 경계를 정의했다. |
| RESILIENCY-11~13 | N/A | Backup·복구 Resource와 Runbook 상세는 Infrastructure·Build and Test 대상이다. |
| RESILIENCY-14 | N/A | 복원력 테스트 방식은 NFR Design에서 결정한다. |
| RESILIENCY-15 | Compliant | Operations Service와 Incident Reference 경계를 정의했다. |

## PBT Compliance

- PBT-01의 공식 속성 식별은 Functional Design에서 수행한다.
- 현재 설계는 다음 후보를 전달한다: 승인 Catalog 폐쇄성, 하드 조건 보존, Grounding Reference 유효성, 격리 비유출, 정규화·저장 멱등성, Session 상태 전이.
- PBT-02~PBT-10은 아직 구현·NFR 단계가 아니므로 N/A이며 차단 Finding이 아니다.

## Trade-offs

- 모듈형 Monolith는 Prototype 운영과 Transaction을 단순화하지만 Module Boundary Test가 없으면 결합도가 증가할 수 있다.
- PostgreSQL 통합 검색은 운영이 단순하지만 대규모 검색 Scale에서는 별도 Engine 재평가가 필요하다.
- 동기 AI 추천은 Client Contract가 단순하지만 Timeout Budget과 Fallback 품질이 중요하다.
- PostgreSQL-backed Job Queue는 Broker 운영을 피하지만 높은 처리량 단계에서는 Message Broker로 교체해야 한다.

현재 Application Design 단계에서 차단 상태인 확장 Finding은 없다.
