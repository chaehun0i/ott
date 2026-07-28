import pytest
from hypothesis import HealthCheck, settings

settings.register_profile(
    "ci",
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
    print_blob=True,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
