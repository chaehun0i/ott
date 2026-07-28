"""Reusable U04 Hypothesis strategies with shrink-friendly bounded values."""

from datetime import UTC, datetime

from hypothesis import strategies as st

unicode_titles = st.text(min_size=1, max_size=120).filter(str.strip)
identifier_maps = st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.text(min_size=1, max_size=40).filter(str.strip),
    max_size=8,
)
boundary_timestamps = st.datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2035, 1, 1),
    timezones=st.just(UTC),
)
provider_ids = st.text(min_size=1, max_size=20).filter(str.strip)
record_pages = st.lists(
    st.text(min_size=1, max_size=20).filter(str.strip),
    min_size=1,
    max_size=20,
    unique=True,
)
