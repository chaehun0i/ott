# U01 Web Experience Business Logic Model

## Scope and Boundaries

U01은 U02, U03, U05, U06, U07이 제공하는 서버 계약을 접근 가능한 브라우저 여정으로 조합한다. UI는 추천 순위, 메타데이터 승인, 권한, 동의 정책의 최종 결정을 수행하지 않는다. 서버 결과를 표현하고 사용자 명령을 전달하며, 영속 비즈니스 데이터는 소유하지 않는다.

## Actor Journeys

### Visitor Discovery

1. `/feed` 진입 시 URL query를 Feed Query로 정규화한다.
2. U03 `GET /feed`를 호출하고 승인 콘텐츠만 카드로 표시한다.
3. filter·sort·page 변경을 URL에 반영하여 새로고침, 공유, 뒤로가기를 재현한다.
4. 카드를 선택하면 `/contents/{content_id}`로 이동하고 복귀 시 목록 위치와 query를 복원한다.
5. 검색은 단일 입력을 U03 `POST /search`로 보내며 서버가 반환한 구조화 조건을 수정 가능한 chip으로 표시한다.
6. 회원 전용 동작을 선택하면 현재 route와 명령을 비민감 일회성 Pending Intent로 보존하고 로그인 성공 후 한 번만 재개한다.

### Member Recommendation

1. `/recommend`에서 자연어를 제출하고 U05 `POST /recommendations`를 호출한다.
2. 처리 중임을 접근 가능한 상태 메시지로 알리고 중복 제출을 막는다.
3. 응답의 현재 조건, 검증된 추천, 짧은 요약과 이유를 표시한다. 근거와 메타데이터는 확장 영역에서 제공한다.
4. 후속 문장은 U05 `POST /recommendations/{session_id}/refine`으로 전달한다. 적용·추가·제거 조건을 서버 응답으로 교체한다.
5. 조건 chip 제거도 명시적 refine 명령이며 전체 reset은 `POST /recommendations/{session_id}/reset` 후 로컬 대화 상태를 제거한다.
6. 세션 만료 또는 404이면 이전 결과를 오인하게 유지하지 않고 새 추천 시작을 안내한다.

### Account, Consent, Library and Notification

1. `/account`는 U02 Profile·Consent·Data Rights 계약을 화면 단위로 분리한다.
2. 개인정보 변경은 CSRF와 서버 validation 결과를 사용하며 성공 응답 전 낙관적으로 확정하지 않는다.
3. 개인화 동의 철회 성공 즉시 recommendation query/cache, conversation, 개인화 badge 및 Pending Intent를 제거한다.
4. 화면을 비개인화 Feed·Recommendation 모드로 전환하고 철회 결과를 live region으로 알린다.
5. 알림 설정은 U06 `GET /notifications` 결과와 명시적 channel/type control을 표시한다. 서버 저장 성공 후에만 확정 상태로 보인다.
6. 외부 OTT 이동은 검증된 URL만 활성화하고 외부 이동 표시 후 새 탭으로 연다. 허용된 동의 범위에서만 U02 feedback event를 기록한다.

### Operator

1. `/admin`은 일반 layout과 분리된 운영자 route guard를 사용한다.
2. 서버가 권한을 확인한 U06 API만 호출한다. 401은 재인증, 403은 접근 거부로 분리한다.
3. 콘텐츠 변경은 현재 version과 reason을 요구하고 `POST /admin/content/{content_id}/override`에 전달한다.
4. Trace와 Incident는 `/admin/traces/{trace_id}`, `/admin/incidents`에서 비식별 정보만 표현한다.
5. 권한 실패 시 일반 UI에 운영 데이터를 fallback하거나 캐시하지 않는다.

## State and Navigation Flow

| State | Source of truth | Lifetime | Transition rule |
|---|---|---|---|
| Route/query | URL | navigation history | parse-normalize-serialize round trip |
| Remote resource | server response | bounded client cache | response version replaces prior value |
| Form draft | component/form state | route lifetime | submit success or explicit reset clears |
| Recommendation conversation | U05 session plus UI projection | active session | refine replaces server-owned condition set |
| Pending Intent | session-scoped non-sensitive state | one login attempt | consume exactly once after successful login |
| Locale | explicit user selection | browser preference | UI changes immediately; content follows fallback chain |
| Consent projection | U02 response | current session | withdrawal purges personalization-derived client state |

## Loading, Error and Degraded Flow

- 각 독립 영역은 `idle`, `loading`, `success`, `empty`, `stale`, `degraded`, `error` 상태를 가진다.
- 기존 성공 데이터가 있고 재검증이 실패하면 데이터, 마지막 갱신 시각, stale/degraded 이유와 국소 재시도를 함께 표시한다.
- 성공한 sibling 영역은 다른 API 실패 때문에 제거하지 않는다.
- 인증 만료는 공개 영역을 유지하면서 보호된 명령만 재인증으로 보낸다.
- validation 오류는 관련 field와 summary에 동시에 연결하며 사용자 입력을 보존한다.
- correlation ID가 제공되면 사용자 오류 세부정보에 안전한 지원 참조로 표시하되 stack trace나 비밀정보는 노출하지 않는다.

## Traceability

| Journey | Stories | Contracts |
|---|---|---|
| Feed/detail/search | US-001~US-006 | U03 Feed, Detail, Search |
| Localization/accessibility | US-007, US-027 | U07 error/session contract and all UI surfaces |
| Recommendation conversation | US-008~US-013 | U05 Recommendation and Conversation |
| Account/personalization | US-014~US-018 | U02 Identity, Profile, Consent, Feedback, Data Rights |
| Notification | US-019 | U06 Notification |
| Operator | US-021, US-027 | U06 Admin, Trace, Incident; U07 session/error |

## Textual Flow Alternative

Feed/Search/Recommendation request → local pending state → server contract → success, empty, degraded or error projection → accessible announcement → user refinement or recovery. Protected command → authentication check → optional login → one-time intent replay → server-authoritative result.
