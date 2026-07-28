from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import strategies as st

from ott_feed.catalog.domain.models import (
    Availability,
    CatalogContent,
    CatalogSource,
    Localization,
)

NOW = datetime(2026, 7, 28, tzinfo=UTC)


@st.composite
def catalog_contents(draw: st.DrawFn) -> CatalogContent:
    content_id = draw(st.text(alphabet="abc123", min_size=1, max_size=8))
    popularity = draw(st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False))
    runtime = draw(st.integers(min_value=1, max_value=300))
    release_offset = draw(st.integers(min_value=-40, max_value=40))
    provider = draw(st.sampled_from(["netflix", "tving", "wavve"]))
    genre = draw(st.sampled_from(["comedy", "drama", "action"]))
    return CatalogContent(
        id=content_id,
        content_type="movie",
        genres=frozenset({genre}),
        release_at=NOW + timedelta(days=release_offset),
        runtime_minutes=runtime,
        popularity=popularity,
        localizations={"ko-KR": Localization("ko-KR", f"제목 {content_id}", "요약")},
        availability=(
            Availability(
                "KR",
                provider,
                NOW,
                NOW - timedelta(days=1),
                NOW + timedelta(days=5),
                detail_url=f"https://example.test/{content_id}",
            ),
        ),
        source=CatalogSource("source", content_id, f"license-{content_id}", NOW),
        last_decision_id=f"decision-{content_id}",
    )
