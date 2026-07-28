# Application Services and Orchestration

## S01 FeedQueryService

- **Entry**: REST feed·detail endpoint
- **Flow**: API → Catalog → Search Projection as needed → response
- **Guarantee**: 승인 콘텐츠만 반환하고 출처·갱신 상태를 포함한다.
- **Failure**: Search 장애 시 제한된 Catalog Query로 저하 운용한다.

## S02 SearchService

- **Entry**: REST search endpoint
- **Flow**: 언어·Filter 정규화 → PostgreSQL 전문 또는 Vector 검색 → 승인 상태 재확인 → response
- **Guarantee**: 격리 콘텐츠를 반환하지 않는다.

## S03 RecommendationApplicationService

1. Request Context와 동의된 Profile Feature를 읽는다.
2. C09가 자연어를 `RecommendationIntent`로 구조화한다.
3. C10이 C04 승인 Catalog에서 하드 Filter, Scoring, 개인화, 다양성을 적용한다.
4. C11이 후보 적격성을 검증한다.
5. C09가 검증 후보의 Evidence Bundle만 사용해 설명·요약 초안을 만든다.
6. C11이 Claim Grounding을 검증한다.
7. C08이 안전한 최종 응답과 Trace를 조립한다.

- **Timeout**: 전체 동기 요청은 요구사항 p95 10초 목표 안에서 단계별 Budget을 가진다.
- **Fallback**: AI 실패 시 C10 규칙 기반 Ranking과 승인 Metadata Template을 사용한다.
- **Transaction**: 추천 조회는 Read-only이며 Session·Trace 기록은 실패해도 추천 안전성 검증을 우회하지 않는다.

## S04 RecommendationConversationService

- 현재 Intent와 새 문장에서 `IntentDelta`를 생성한다.
- 유지·추가·제거 조건을 병합한 후 S03 전체 Pipeline을 다시 실행한다.
- Reset은 이전 Session 조건의 후속 사용을 차단한다.

## S05 AccountAndPrivacyService

- 이메일 인증과 OAuth Callback을 C03으로 조정한다.
- Profile·Consent·Data Rights를 C12로 조정한다.
- 내보내기·삭제는 별도 Job으로 처리하고 상태를 REST로 조회한다.

## S06 FeedbackService

- REST 행동 Event를 인증·동의 검증 후 정규화한다.
- Idempotency Key로 중복 기록을 방지한다.
- Feature 갱신은 Event와 분리하여 재처리 가능하게 한다.

## S07 ContentIngestionService

- Scheduler가 Provider별 Job을 PostgreSQL-backed Queue에 생성한다.
- 별도 Worker가 Provider Adapter 호출, Raw 저장, 정규화, 검증, 승인·격리를 순차 실행한다.
- 공급자 Cursor와 Idempotency Key로 재시작 가능하게 한다.
- 승인 완료 후 Search Projection 갱신과 검증된 Release Event를 생성한다.

## S08 NotificationService

- Worker가 검증된 Release Event와 회원 설정으로 Delivery Job을 만든다.
- 오래되거나 격리된 콘텐츠 Event는 거부한다.
- Channel Adapter 실패는 제한된 재시도 후 실패 상태와 알림을 남긴다.

## S09 AdminContentService

- 운영자 권한을 확인하고 Content Override·Visibility를 적용한다.
- 변경 전후 값과 Actor·Time·Reason을 Audit에 저장한다.
- 자동 수집과 Override 충돌은 명시적 우선순위 Contract로 전달한다.

## S10 OperationsService

- 얕은 Health와 PostgreSQL·Provider·AI의 깊은 Health를 제공한다.
- Metrics·Structured Log·Trace ID를 Observability Port로 보낸다.
- Recommendation Trace 조회는 민감정보와 모델 내부 추론을 제외한다.

## Communication Decisions

- Web ↔ API: 동기 REST JSON, OpenAPI
- Recommendation Pipeline: API Process 내부 동기 호출
- API·Scheduler ↔ Worker: PostgreSQL-backed Job·Outbox
- Worker ↔ External Providers: Adapter를 통한 동기 HTTP, Timeout·Retry·Rate Limit
- AI: Provider-neutral Adapter를 통한 동기 호출, 초기 단일 Provider
- Notification: Worker에서 Channel Adapter 호출

## Deferred Detailed Rules

- 추천 점수와 다양성 공식
- Metadata 병합·Override 세부 우선순위
- Intent Confidence Threshold
- Retry 횟수와 Timeout Budget
- Transaction Isolation과 Lock Strategy
- Functional Design과 NFR Design에서 확정한다.
