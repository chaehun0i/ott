"""Explicit genre and OTT subscription profile use cases."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Protocol
from uuid import UUID

from ott_feed.identity.domain.models import (
    GenrePreferenceState,
    OttSubscriptionState,
    UserProfile,
)


class ProfileRepositoryPort(Protocol):
    def get(self, user_id: UUID) -> UserProfile | None: ...

    def save(self, profile: UserProfile, expected_version: int | None = None) -> None: ...


class ProfileJobPublisher(Protocol):
    def enqueue(self, job_type: str, payload: dict[str, object], lane: str) -> UUID: ...


class ProfileWork(Protocol):
    profiles: ProfileRepositoryPort
    jobs: ProfileJobPublisher

    def __enter__(self) -> ProfileWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...


class ProfileService:
    def __init__(self, uow_factory: Callable[[], ProfileWork]) -> None:
        self.uow_factory = uow_factory

    def update(
        self,
        user_id: UUID,
        genres: Mapping[str, GenrePreferenceState | None],
        ott_subscriptions: Mapping[str, OttSubscriptionState],
        locale: str | None = None,
    ) -> UserProfile:
        with self.uow_factory() as work:
            existing = work.profiles.get(user_id)
            profile = existing or UserProfile(user_id)
            expected = existing.row_version if existing else None
            for genre_id, state in genres.items():
                profile.set_genre(genre_id, state)
            for provider_id, ott_state in ott_subscriptions.items():
                profile.set_ott(provider_id, ott_state)
            if locale:
                profile.locale = locale
            work.profiles.save(profile, expected)
            work.jobs.enqueue(
                "identity.feature.explicit-refresh",
                {
                    "userId": str(user_id),
                    "source": "profile",
                    "profileVersion": profile.profile_version,
                },
                "normal",
            )
            work.commit()
            return profile
