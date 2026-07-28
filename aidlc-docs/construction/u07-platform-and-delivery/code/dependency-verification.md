# Dependency and Python Runtime Verification

## Verification Scope

- 검증 시각: 2026-07-26 UTC
- 선언 기준: `backend/pyproject.toml`
- 해석 기준: `backend/uv.lock` revision 3
- resolver runtime: CPython 3.12.13
- registry: PyPI official JSON API와 `https://pypi.org/simple`

`uv.lock`을 다시 생성한 뒤 registry package 46개의 정확한 name/version endpoint를 PyPI JSON API로 조회했다. 46개 모두 배포 파일이 존재했고 모든 파일이 yanked된 고정 버전은 0개였다. workspace 자체의 virtual package `ott-feed-platform==0.1.0`은 PyPI 검증 대상에서 제외했다.

## Direct Dependency Results

| Package | pyproject/lock pin | PyPI stable at verification | Python requirement | Result |
|---|---:|---:|---|---|
| FastAPI | 0.140.0 | 0.140.0 | >=3.10 | exact, not yanked |
| Pydantic | 2.13.4 | 2.13.4 | >=3.9 | exact, not yanked |
| SQLAlchemy | 2.0.51 | 2.0.51 | >=3.7 | exact, not yanked |
| Alembic | 1.18.5 | 1.18.5 | >=3.10 | exact, not yanked |
| psycopg | 3.3.4 | 3.3.4 | >=3.10 | exact, not yanked |
| psycopg-binary | 3.3.4 | 3.3.4 | >=3.10 | `psycopg[binary]` extra resolved, not yanked |
| Uvicorn | 0.51.0 | 0.51.0 | >=3.10 | exact, not yanked |
| HTTPX | 0.28.1 | 0.28.1 | >=3.8 | exact, not yanked |
| pytest | 9.1.1 | 9.1.1 | >=3.10 | exact, not yanked |
| Hypothesis | 6.161.5 | 6.161.5 | >=3.10 | exact, not yanked |
| Ruff | 0.16.0 | 0.16.0 | >=3.7 | exact, not yanked |
| mypy | 2.3.0 | 2.3.0 | >=3.10 | exact, not yanked |
| pytest-cov | 7.1.0 | 7.1.0 | >=3.9 | 7.0.0에서 재검증 시점 안정판으로 갱신, not yanked |

공식 확인 링크: [FastAPI](https://pypi.org/project/fastapi/), [Pydantic](https://pypi.org/project/pydantic/), [SQLAlchemy](https://pypi.org/project/SQLAlchemy/), [Alembic](https://pypi.org/project/alembic/), [psycopg](https://pypi.org/project/psycopg/), [Uvicorn](https://pypi.org/project/uvicorn/), [HTTPX](https://pypi.org/project/httpx/), [pytest](https://pypi.org/project/pytest/), [Hypothesis](https://pypi.org/project/hypothesis/), [Ruff](https://pypi.org/project/ruff/), [mypy](https://pypi.org/project/mypy/), [pytest-cov](https://pypi.org/project/pytest-cov/).

## Why Python Was Changed to 3.12.13

초기 후보였던 Python 3.14 계열을 그대로 선언하지 않고 3.12.13으로 변경한 직접적인 이유는 이 workspace에서 실제 제공되는 CPython runtime이 3.12.13이었기 때문이다. 버전 선언만 최신으로 두고 다른 interpreter에서 lock·설치·테스트하는 상태를 피하고, 다음 네 위치를 하나의 실행 기준으로 맞췄다.

- `pyproject.toml`: `>=3.12.13,<3.13`
- `uv.lock`: `requires-python = ">=3.12.13, <3.13"`
- `.python-version`: `3.12.13`
- Dockerfile/CI: Python 3.12.13

모든 직접 의존성의 PyPI `Requires-Python` 하한은 3.12.13 이하이고, 실제 resolver가 3.12.13에서 46개 PyPI package와 hashes를 해석했으며 설치·정적 검사·비-PostgreSQL 테스트도 같은 runtime에서 수행됐다. `<3.13` 상한은 의도하지 않은 minor interpreter 변경으로 lock과 binary wheel 선택이 달라지는 것을 막는다.

이 결정은 Python 3.12가 최신 feature line이라는 뜻이 아니다. [Python 3.12.13 공식 릴리스](https://www.python.org/downloads/release/python-31213/)는 3.12가 security-fixes-only 단계이고 3.14가 최신 feature series라고 명시한다. 따라서 3.12.13 채택은 **현재 workspace의 재현 가능한 안정 baseline**을 위한 선택이며 장기 플랫폼 권고가 아니다. Python 3.14 전환은 CI·container runtime, psycopg/SQLAlchemy binary wheels, 전체 테스트와 복구·배포 증적을 별도 matrix에서 통과시킨 뒤 수행한다.

## Lock Integrity Decision

- `uv lock` 결과: 47 package resolved; PyPI registry package 46개와 workspace virtual package 1개
- dependency update: pytest-cov 7.0.0 → 7.1.0
- missing release: 0
- fully yanked pinned release: 0
- PostgreSQL runtime integration: 아직 검증되지 않음; dependency integrity 성공과 별개의 차단 gate

