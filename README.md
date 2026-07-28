# OTT Latest Feed and AI Recommendation

OTT 신작·인기 콘텐츠 통합 피드와 자연어 기반 개인화 추천을 위한 모듈형 모놀리스입니다. 현재 구현된 U07은 API 경계, PostgreSQL 영속성, 비동기 작업, 복구, 배포, 관측성의 공통 기반입니다. 피드·추천 도메인 기능은 후속 U02~U06 단위에서 이 기반 위에 추가됩니다.

## 검증된 로컬 실행

요구 사항은 Python 3.12.13과 `uv` 0.11.32입니다. Python 3.12는 최신 feature line이 아니라 현재 workspace에서 resolver·설치·테스트를 동일하게 재현하기 위한 고정 baseline입니다. 자세한 결정 근거는 `aidlc-docs/construction/u07-platform-and-delivery/code/dependency-verification.md`에 있습니다.

```powershell
cd backend
uv sync --frozen
$env:APP_ENV = "local"
$env:API_SECRET = "replace-this-local-secret"
uv run alembic upgrade head
uv run uvicorn --app-dir src ott_feed.main:app --host 127.0.0.1 --port 8000
```

기본 데이터베이스는 메모리 SQLite입니다. 영속적인 로컬 데이터가 필요하면 `DATABASE_URL=sqlite+pysqlite:///./ott-feed.db`를 지정합니다. 서버가 뜨면 다음 주소를 확인합니다.

- API 문서: `http://127.0.0.1:8000/docs`
- 준비 상태: `http://127.0.0.1:8000/api/v1/health/ready`
- Prometheus 지표: `http://127.0.0.1:8000/api/v1/metrics`

## 품질 검증

```powershell
cd backend
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest --cov --cov-branch --cov-report=term-missing
```

PostgreSQL 통합 테스트는 `TEST_DATABASE_URL`이 있을 때만 실행됩니다. Docker 장애 중에도 단위·계약·속성 테스트는 독립적으로 실행할 수 있습니다.

## Docker 실행

Docker daemon이 정상일 때 `secrets/api_secret.txt`와 `secrets/postgres_password.txt`를 생성한 뒤 실행합니다.

```powershell
docker compose -f compose.yaml -f compose.local.yaml config --quiet
docker compose -f compose.yaml -f compose.local.yaml up --build
```

현재 호스트의 Docker 오류 때문에 이번 검증에서는 이미지 빌드와 컨테이너 기동을 수행하지 않았습니다. Compose 병합·구문 검사는 별도로 수행했습니다.

## 운영 문서

- API 계약: `docs/api-contract.md`
- 백업·복원: `docs/backup-restore-runbook.md`
- 배포·롤백: `docs/deploy-rollback-runbook.md`
- 현재 제한: `docs/known-limitations.md`
