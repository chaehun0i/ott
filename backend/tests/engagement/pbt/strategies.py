from datetime import UTC, datetime, timedelta

from hypothesis import strategies as st

from ott_feed.engagement.application.health import HealthContribution, HealthState
from ott_feed.engagement.domain.models import Channel, DeliveryJob, NotificationEvent

safe_ids = st.text(alphabet=st.characters(categories=("Ll", "Lu", "Nd")), min_size=1, max_size=24)
channels = st.sampled_from(list(Channel))
base_times = st.datetimes(
    min_value=datetime(2025, 1, 1),
    max_value=datetime(2030, 1, 1),
    timezones=st.just(UTC),
)


@st.composite
def events(draw: st.DrawFn) -> NotificationEvent:
    effective = draw(base_times)
    return NotificationEvent(
        draw(safe_ids),
        draw(safe_ids),
        draw(st.integers(min_value=1, max_value=1_000_000)),
        draw(st.sampled_from(("new", "popular", "changed"))),
        effective,
        effective
        + draw(st.timedeltas(min_value=timedelta(seconds=1), max_value=timedelta(days=7))),
    )


@st.composite
def jobs(draw: st.DrawFn) -> DeliveryJob:
    available = draw(base_times)
    return DeliveryJob(
        draw(safe_ids),
        draw(st.text(alphabet="abcdef0123456789", min_size=64, max_size=64)),
        draw(safe_ids),
        draw(safe_ids),
        draw(channels),
        available,
        available + timedelta(hours=1),
    )


@st.composite
def health_contributions(draw: st.DrawFn) -> HealthContribution:
    observed = draw(base_times)
    return HealthContribution(
        draw(safe_ids),
        draw(st.sampled_from(list(HealthState))),
        draw(st.booleans()),
        observed,
        timedelta(seconds=30),
        draw(st.sampled_from(("ok", "timeout", "stale", "unavailable"))),
    )
