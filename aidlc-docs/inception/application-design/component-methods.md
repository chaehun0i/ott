# Component Methods

고수준 Contract만 정의한다. 상세 Schema Field, Algorithm, 점수 공식과 Business Rule은 Functional Design에서 확정한다.

## Shared Types

- `Result[T, E]`: 성공 또는 명시적 Error
- `Page[T]`: Cursor 기반 Page
- `ContentId`, `UserId`, `SessionId`, `TraceId`: 불투명 식별자
- `RecommendationIntent`: 언어 독립 구조화 조건
- `ApprovedContent`: 승인 상태 Metadata View
- `GroundedText`: Claim과 Evidence Reference를 가진 생성 문구

## C02 REST API Boundary

- `get_feed(query: FeedQuery, context: RequestContext) -> Result[Page[ContentSummary], ApiError]`
- `search(query: SearchQuery, context: RequestContext) -> Result[Page[SearchHit], ApiError]`
- `recommend(command: RecommendCommand, context: RequestContext) -> Result[RecommendationResponse, ApiError]`
- `refine_recommendation(session_id: SessionId, command: RefineCommand, context: RequestContext) -> Result[RecommendationResponse, ApiError]`

## C03 Identity and Access

- `register_email(command: RegisterCommand) -> Result[Identity, IdentityError]`
- `authenticate_email(command: LoginCommand) -> Result[Session, IdentityError]`
- `authenticate_oauth(command: OAuthCallbackCommand) -> Result[Session, IdentityError]`
- `authorize(identity: Identity, permission: Permission) -> Result[AuthorizedContext, AuthorizationError]`
- `revoke_session(session_id: SessionId) -> Result[None, IdentityError]`

## C04 Content Catalog

- `list_feed(query: FeedQuery) -> Page[ContentSummary]`
- `get_approved(content_id: ContentId, region: Region) -> Option[ApprovedContent]`
- `find_approved(ids: Sequence[ContentId], region: Region) -> Sequence[ApprovedContent]`
- `publish_approved(record: ValidatedMetadata) -> Result[CatalogVersion, CatalogError]`
- `get_provenance(content_id: ContentId) -> Sequence[ProvenanceRecord]`

## C05 Content Ingestion

- `schedule_provider_sync(provider_id: ProviderId, cursor: Option[Cursor]) -> JobId`
- `run_provider_sync(job_id: JobId) -> Result[IngestionSummary, IngestionError]`
- `normalize(raw: RawProviderRecord) -> Result[NormalizedMetadata, NormalizationError]`
- `retry_failed(job_id: JobId) -> Result[JobId, RetryError]`

`run_provider_sync`는 Job ID에 대해 중복 실행 안전성을 가져야 한다.

## C06 Metadata Validation

- `validate(record: NormalizedMetadata, rules: RuleVersion) -> ValidationDecision`
- `approve(decision: PassedValidation) -> Result[CatalogVersion, ValidationError]`
- `quarantine(decision: FailedValidation) -> Result[QuarantineId, ValidationError]`
- `revalidate(quarantine_id: QuarantineId, rules: RuleVersion) -> ValidationDecision`

## C07 Search

- `search_text(query: TextSearchQuery) -> Page[SearchHit]`
- `search_semantic(query: SemanticSearchQuery) -> Page[SearchHit]`
- `refresh_projection(catalog_version: CatalogVersion) -> Result[ProjectionVersion, SearchError]`

## C08 Recommendation Orchestrator

- `recommend(command: RecommendCommand, context: RecommendationContext) -> Result[RecommendationResponse, RecommendationError]`
- `refine(session_id: SessionId, command: RefineCommand) -> Result[RecommendationResponse, RecommendationError]`
- `reset(session_id: SessionId) -> Result[None, RecommendationError]`
- `fallback(intent: RecommendationIntent, reason: FallbackReason) -> RecommendationResponse`

## C09 AI Interaction

- `interpret(text: LocalizedText, context: IntentContext) -> Result[RecommendationIntent, AIError]`
- `refine_intent(current: RecommendationIntent, text: LocalizedText) -> Result[IntentDelta, AIError]`
- `generate_explanations(candidates: Sequence[EvidenceBundle], intent: RecommendationIntent) -> Result[Sequence[GroundedTextDraft], AIError]`

모든 AI Input은 직접 식별자를 제외하고 Output은 Schema 검증을 거친다.

## C10 Recommendation Engine

- `rank(intent: RecommendationIntent, features: FeatureSnapshot) -> RankedCandidates`
- `apply_hard_filters(intent: RecommendationIntent, candidates: Sequence[ApprovedContent]) -> Sequence[ApprovedContent]`
- `apply_diversity(ranked: RankedCandidates, policy: DiversityPolicy) -> RankedCandidates`
- `rank_fallback(intent: RecommendationIntent) -> RankedCandidates`

## C11 Recommendation Output Validation

- `validate_candidates(candidates: RankedCandidates, intent: RecommendationIntent) -> CandidateValidationResult`
- `validate_grounding(drafts: Sequence[GroundedTextDraft], evidence: Sequence[EvidenceBundle]) -> GroundingValidationResult`
- `build_safe_output(candidate_result: CandidateValidationResult, grounding_result: GroundingValidationResult) -> SafeRecommendationOutput`

## C12 Personalization and Feedback

- `get_profile(user_id: UserId) -> Profile`
- `update_preferences(user_id: UserId, command: PreferenceCommand) -> Result[ProfileVersion, ProfileError]`
- `record_feedback(command: FeedbackCommand, consent: ConsentSnapshot) -> Result[EventId, FeedbackError]`
- `get_features(user_id: UserId, at: Instant) -> FeatureSnapshot`
- `export_user_data(user_id: UserId) -> DataExportJob`
- `delete_user_data(user_id: UserId) -> DataDeletionJob`

## C13 Notification

- `schedule_release_notifications(event: VerifiedReleaseEvent) -> Sequence[JobId]`
- `deliver(job_id: JobId) -> Result[DeliveryReceipt, NotificationError]`
- `cancel_for_user(user_id: UserId, preference: NotificationPreference) -> Result[None, NotificationError]`

## C14 Admin and Operations

- `override_content(command: ContentOverrideCommand, actor: OperatorContext) -> Result[AuditId, AdminError]`
- `set_visibility(command: VisibilityCommand, actor: OperatorContext) -> Result[AuditId, AdminError]`
- `get_recommendation_trace(trace_id: TraceId, actor: OperatorContext) -> Result[TraceView, AdminError]`
- `health(depth: HealthDepth) -> HealthReport`

## Error Contract Categories

- `ValidationError`: Schema, provenance, license, freshness, availability, grounding
- `DependencyError`: timeout, rate limit, unavailable, circuit open
- `AuthorizationError`: unauthenticated, forbidden
- `ConflictError`: version conflict, idempotency conflict
- `NotFoundError`: approved resource not found
- 외부 Error의 민감정보와 Provider Payload는 REST 응답에 노출하지 않는다.
