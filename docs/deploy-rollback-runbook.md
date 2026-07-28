# Deploy and Rollback Runbook

Remote 배포는 모든 이미지를 `repository@sha256:digest` 형식으로 고정합니다. Secret 값은
Compose, 이미지, 소스 저장소에 넣지 않고 배포 호스트의 `secrets/*.txt` 파일 또는 운영
secret provider가 생성한 동일 경로에 주입합니다.

## U02 배포 전 Gate

1. Ruff, strict MyPy, 전체 pytest 및 PBT-U02-01~11이 통과해야 합니다.
2. 실제 PostgreSQL에서 `pytest -m integration`이 skip 없이 통과해야 합니다.
3. 빈 데이터베이스 clean install과 U07 revision에서 U02 head로의 upgrade를 검증합니다.
4. `identity_kek`, blind-index key, session pepper, export key, Google client secret, email
   password 파일이 존재하고 서비스 계정만 읽을 수 있어야 합니다.
5. Google redirect URI는 공개 HTTPS callback과 정확히 일치해야 합니다.
6. 개인정보 export 저장소는 일반 정적 파일 및 백업 경로와 분리되어야 합니다.
7. 배포 직전 암호화된 PostgreSQL 백업과 현재 API/worker digest를 기록합니다.

```sh
export API_IMAGE='ghcr.io/org/repo/api@sha256:...'
export APP_DOMAIN='service.example.com'
sh scripts/deploy.sh
```

배포 순서는 backup, 이미지 pull, expand migration, API/worker 교체, readiness, identity
synthetic 순서입니다. U02 migration은 기존 API가 읽을 수 있는 expand 형태를 먼저
적용합니다.

## Rollback

```sh
export PREVIOUS_API_IMAGE='ghcr.io/org/repo/api@sha256:...'
export APP_DOMAIN='service.example.com'
sh scripts/rollback.sh
```

이전 이미지가 현재 schema를 읽을 수 있을 때만 이미지 rollback을 수행합니다. 다음
작업은 데이터베이스 snapshot으로 되돌리지 않습니다.

- 동의 철회 및 personalization source/feature 삭제
- 계정 삭제 및 export artifact 삭제
- key rotation checkpoint와 새 key-version 쓰기

이 작업들은 idempotent forward recovery로 재개합니다. 이전 key는 해당 버전 row가 0이고
복구 보존 기간 및 별도 승인이 끝난 뒤에만 폐기합니다. Partial deletion은 계정을 계속
비활성화한 상태로 high lane에서 재시도합니다.

## 배포 후 확인

- `/api/v1/health/ready`가 ready이며 operator deep health의 database/worker가 정상입니다.
- email login, Google login, CSRF 거부, consent withdrawal, non-personalized fallback을
  synthetic 계정으로 확인합니다.
- telemetry label에 email, UserId, OAuth subject, session ID/token, payload, object reference가
  없는지 표본 검사합니다.
- deletion oldest age, worker backlog, consent fail-closed 및 key rotation alert가 정상 평가되는지
  확인합니다.

## U03 Catalog and Discovery

1. Verify the pinned pgvector image digest and extensions `pg_trgm`, `unaccent`, and `vector`.
2. Apply expand migration `0003_u03_catalog_expand` before starting U03 workers.
3. Build feed, text, and vector candidate generations and run closure, duplicate, bilingual quality, exact-vector and smoke-latency gates.
4. Atomically activate the candidate generation only after all gates pass. Retain the previous generation for immediate pointer rollback.
5. On projection gap, stop activation, replay from the first missing CatalogVersion and keep serving the previous generation.
6. On rollback, restore the prior application image and active-generation pointers. Do not run a destructive database downgrade.

## U04 Ingestion and Metadata Governance

1. Supply separate secret files for `database_u04_api`, `database_u04_worker` and `u04_provider_credentials`; never place their values in Compose or `.env`.
2. Apply `0004_u04_ingestion_expand` and `backend/migrations/role-grants.sql` through the migration identity before starting `worker-ingestion`.
3. Confirm the API role is read-only in `u04_ingestion`, the worker role owns U04 mutations and neither U04 role has a direct grant on `u03_catalog`.
4. Start publication/reconciliation capacity before provider collection lanes, then verify U04 deep-health checks and the ingestion dashboard.
5. Permit provider outbound traffic only from `provider_egress_net`; API and general workers remain on internal networks.
6. On rollback, stop new provider claims, reconcile unknown U03 outcomes and restore the prior application image. Do not downgrade the schema or delete immutable decisions.
