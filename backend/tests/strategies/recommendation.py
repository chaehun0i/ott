"""Reusable U05 Hypothesis strategies."""

from hypothesis import strategies as st

from ott_feed.recommendation.domain.models import (
    ApprovedCandidate,
    Condition,
    ConditionKind,
    Locale,
    RecommendationIntent,
)

locales = st.sampled_from(tuple(Locale))
genres = st.sampled_from(("comedy", "drama", "action"))
content_ids = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=12)


@st.composite
def intents(draw):
    locale = draw(locales)
    genre = draw(st.one_of(genres, st.none()))
    runtime = draw(st.one_of(st.integers(min_value=1, max_value=300), st.none()))
    conditions = []
    if genre:
        conditions.append(Condition(ConditionKind.GENRE, genre))
    if runtime:
        conditions.append(Condition(ConditionKind.MAX_RUNTIME, str(runtime)))
    return RecommendationIntent(locale, tuple(conditions))


@st.composite
def candidates(draw):
    content_id = draw(content_ids)
    genre = draw(genres)
    return ApprovedCandidate(
        content_id,
        "m1",
        content_id,
        "synopsis",
        (genre,),
        draw(st.integers(min_value=1, max_value=300)),
        "kr",
        ("netflix",),
        12,
        draw(st.floats(min_value=0, max_value=1)),
        draw(st.floats(min_value=0, max_value=1)),
    )
