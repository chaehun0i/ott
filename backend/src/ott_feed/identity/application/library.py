"""Saved, rating and completed-watch library use cases."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from ott_feed.identity.domain.errors import invalid
from ott_feed.identity.domain.models import UserLibrary
from ott_feed.identity.ports import CatalogReference


class LibraryRepositoryPort(Protocol):
    def get(self, user_id: UUID) -> UserLibrary: ...

    def save(self, library: UserLibrary, expected_version: int | None = None) -> None: ...


class LibraryJobPublisher(Protocol):
    def enqueue(self, job_type: str, payload: dict[str, object], lane: str) -> UUID: ...


class LibraryWork(Protocol):
    libraries: LibraryRepositoryPort
    jobs: LibraryJobPublisher

    def __enter__(self) -> LibraryWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...


class LibraryService:
    def __init__(
        self,
        uow_factory: Callable[[], LibraryWork],
        catalog: CatalogReference,
        now: Callable[[], datetime],
    ) -> None:
        self.uow_factory = uow_factory
        self.catalog = catalog
        self.now = now

    def save(self, user_id: UUID, content_id: str) -> UserLibrary:
        return self._mutate(user_id, content_id, "save", None)

    def unsave(self, user_id: UUID, content_id: str) -> UserLibrary:
        return self._mutate(user_id, content_id, "unsave", None)

    def rate(self, user_id: UUID, content_id: str, rating: int) -> UserLibrary:
        return self._mutate(user_id, content_id, "rate", rating)

    def unrate(self, user_id: UUID, content_id: str) -> UserLibrary:
        return self._mutate(user_id, content_id, "unrate", None)

    def complete_watch(self, user_id: UUID, content_id: str) -> UserLibrary:
        return self._mutate(user_id, content_id, "watch_complete", None)

    def _mutate(
        self, user_id: UUID, content_id: str, operation: str, rating: int | None
    ) -> UserLibrary:
        if not self.catalog.content_exists(content_id):
            raise invalid("content_not_found", "identity.content_not_found")
        with self.uow_factory() as work:
            library = work.libraries.get(user_id)
            expected = library.row_version
            at = self.now()
            changed = True
            if operation == "save":
                changed = library.save(content_id, at)
            elif operation == "unsave":
                changed = library.unsave(content_id)
            elif operation == "rate":
                if rating is None:
                    raise invalid("rating_required", "identity.rating_invalid")
                library.rate(content_id, rating)
            elif operation == "unrate":
                changed = library.unrate(content_id)
            elif operation == "watch_complete":
                library.complete_watch(content_id, at)
            else:
                raise invalid("library_operation", "identity.request_invalid")
            if changed:
                work.libraries.save(library, expected)
                work.jobs.enqueue(
                    "identity.feature.explicit-refresh",
                    {
                        "userId": str(user_id),
                        "source": "library",
                        "contentId": content_id,
                        "operation": operation,
                        "libraryVersion": library.row_version,
                    },
                    "normal",
                )
            work.commit()
            return library
