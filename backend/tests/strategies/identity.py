from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import strategies as st

content_ids = st.from_regex(r"content-[a-z0-9]{1,12}", fullmatch=True)
genre_ids = st.from_regex(r"genre-[a-z]{1,10}", fullmatch=True)
provider_subjects = st.binary(min_size=16, max_size=32)
ratings = st.integers(min_value=1, max_value=5)
invalid_ratings = st.integers().filter(lambda value: value < 1 or value > 5)
aware_datetimes = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2035, 1, 1),
    timezones=st.just(UTC),
)
short_deltas = st.timedeltas(min_value=timedelta(0), max_value=timedelta(days=2))
feature_values = st.dictionaries(
    st.sampled_from(
        [
            "genre:comedy",
            "ott:netflix",
            "library:saved_count",
            "behavior:click_score",
            "email",
            "userId",
            "raw_payload",
        ]
    ),
    st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.booleans()),
    max_size=7,
)
