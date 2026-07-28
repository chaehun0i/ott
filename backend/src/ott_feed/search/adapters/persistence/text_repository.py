"""Parameterized locale-aware PostgreSQL text retrieval."""

from __future__ import annotations

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from ott_feed.search.adapters.persistence.models import SearchDocumentRow
from ott_feed.search.domain.models import SearchCandidate, StructuredQuery


class SqlAlchemyTextSearchRepository:
    def __init__(self, session: Session, generation: str) -> None:
        self.session = session
        self.generation = generation

    def search(self, query: StructuredQuery, limit: int) -> list[SearchCandidate]:
        exact = SearchDocumentRow.normalized_title == query.text
        prefix = SearchDocumentRow.normalized_title.startswith(query.text)
        person_match = func.jsonb_path_exists(
            SearchDocumentRow.people,
            '$[*] ? (@ like_regex $term flag "i")',
            func.jsonb_build_object("term", query.text),
        )
        score = case((exact, 4.0), (prefix, 3.0), (person_match, 2.0), else_=1.0)
        statement = (
            select(SearchDocumentRow, score.label("search_score"))
            .where(
                SearchDocumentRow.generation_id == self.generation,
                or_(
                    exact,
                    prefix,
                    person_match,
                    func.similarity(SearchDocumentRow.normalized_title, query.text) > 0.15,
                ),
            )
            .order_by(
                score.desc(),
                SearchDocumentRow.popularity.desc(),
                SearchDocumentRow.content_id,
            )
            .limit(limit)
        )
        return [
            SearchCandidate(
                content_id=row.content_id,
                score=float(search_score),
                title=row.title,
                actual_locale=row.locale,
                source="text",
            )
            for row, search_score in self.session.execute(statement).all()
        ]
