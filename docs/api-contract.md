# API v1 Contract

모든 공개 API는 `/api/v1` 아래에 있습니다. Local/Test 환경에서는 OpenAPI를
`/api/v1/openapi.json`, `/docs`, `/redoc`에서 확인할 수 있습니다. Remote 환경에서는
문서 UI가 비활성화됩니다.

## 공통 보안 계약

- 브라우저 상태 변경 요청은 먼저 `GET /api/v1/identity/csrf`로 토큰을 발급받습니다.
- 클라이언트는 `ott_csrf` 쿠키 값과 같은 값을 `x-csrf-token` 헤더로 전송합니다.
- `Origin`은 배포 도메인과 정확히 일치해야 합니다.
- 세션 쿠키 `ott_session`은 `Secure`, `HttpOnly`, `SameSite=Lax`입니다.
- 비밀번호, 세션 토큰, OAuth subject, 이메일 확인/재설정 토큰은 응답이나 오류에
  포함되지 않습니다.
- 이메일 확인 및 비밀번호 재설정 요청은 계정 존재 여부와 무관하게 같은
  `202 accepted` 응답을 사용합니다.

## Identity API

| Method | Path | Authentication | Purpose |
|---|---|---|---|
| GET | `/api/v1/identity/csrf` | No | Double-submit CSRF token issue |
| POST | `/api/v1/identity/register` | CSRF | Email registration |
| POST | `/api/v1/identity/verify-email` | CSRF | Single-use email verification |
| POST | `/api/v1/identity/login` | CSRF | Password login and session issue |
| POST | `/api/v1/identity/logout` | Session + CSRF | Current session revocation |
| POST | `/api/v1/identity/sessions/rotate` | Session + CSRF | Atomic session-token rotation |
| POST | `/api/v1/identity/password-reset/request` | CSRF | Non-enumerating reset request |
| POST | `/api/v1/identity/password-reset/complete` | CSRF | Purpose-bound reset completion |
| PUT | `/api/v1/identity/profile` | Session + CSRF | Genre, OTT and locale preferences |
| POST/DELETE | `/api/v1/identity/library/{contentId}/save` | Session + CSRF | Save state |
| PUT/DELETE | `/api/v1/identity/library/{contentId}/rating` | Session + CSRF | Rating state |
| POST | `/api/v1/identity/library/{contentId}/watch-complete` | Session + CSRF | Completed watch event |
| PUT | `/api/v1/identity/consent/personalization` | Session + CSRF | Versioned consent decision |
| POST | `/api/v1/identity/feedback` | Session + CSRF | Consent-gated behavior feedback |
| POST | `/api/v1/identity/data-rights/export` | Fresh session + CSRF | Export request |
| POST | `/api/v1/identity/data-rights/deletion` | Fresh session + CSRF | Deletion request |
| GET | `/api/v1/identity/data-rights/{requestId}` | Session | Safe request status |

## Error Envelope

Errors expose a stable code, safe localized message and message key. They never disclose whether
an account, credential, provider subject or export object exists.

```json
{
  "error": {
    "code": "authentication_failed",
    "message": "로그인 정보를 확인할 수 없습니다.",
    "messageKey": "identity.authentication_failed",
    "correlationId": "6a624938-9940-4904-a385-e400136ac86f",
    "retryable": false
  }
}
```

UI는 색상만으로 상태를 구분하지 않고 `status`, `code`, `messageKey`를 함께 사용해야
합니다. 지원 언어는 `Accept-Language`의 첫 값에 따른 한국어(`ko`)와 영어(`en`)입니다.

## Health and Operations

- `GET /api/v1/health/live`: 프로세스 생존 상태
- `GET /api/v1/health/ready`: 트래픽 수신 준비 상태
- `GET /api/v1/health/deep`: `x-operator-role: operator`가 필요한 상세 상태
- `GET /api/v1/metrics`: Prometheus text exposition

## U03 Catalog and Discovery

- `GET /api/v1/feed` requires `region`; supports locale, page size, filters and an opaque signed cursor.
- `GET /api/v1/contents/{contentId}` returns only currently approved, licensed, region-available detail.
- `POST /api/v1/search` accepts a Korean or English natural-language query and returns text/vector hybrid results. `degradedReason=semantic_unavailable` identifies approved text fallback.
- Feed, detail and search responses use `Cache-Control: no-store` and expose no raw embedding or internal provider payload.

## U04 Ingestion and Metadata Governance

- `GET /api/v1/ingestion/rules/current` exposes only the versioned validation predicate contract needed by U05.
- `GET /api/v1/ingestion/jobs/{jobId}` requires `x-operator-role: operator` and returns bounded status/count facts.
- `POST /api/v1/ingestion/quarantine/{quarantineId}/retry` requires the operator role and a pseudonymous `x-actor-reference`.
- U04 responses never include raw provider payloads, provider credentials, quarantine evidence bodies or concrete U03 persistence details.
