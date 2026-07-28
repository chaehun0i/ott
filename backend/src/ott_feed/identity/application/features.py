"""Feature projection and consent-bound U05 snapshot use cases."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Protocol
from uuid import UUID

from ott_feed.identity.domain.errors import denied
from ott_feed.identity.domain.models import (
    ConsentLedger,
    ConsentPurpose,
    FeatureContribution,
    FeatureSnapshot,
    PersonalizationFeatureSet,
)
from ott_feed.identity.domain.policies import build_feature_snapshot
from ott_feed.identity.ports import SecretCryptography


class FeatureRepositoryPort(Protocol):
    def get(self, user_id: UUID) -> PersonalizationFeatureSet | None: ...

    def replace_explicit(
        self,
        user_id: UUID,
        values: dict[str, str | int | float | bool],
        consent_version: int,
        expected_feature_version: int,
    ) -> PersonalizationFeatureSet: ...

    def apply_contribution(
        self,
        user_id: UUID,
        consent_version: int,
        contribution: FeatureContribution,
        expected_feature_version: int,
    ) -> tuple[PersonalizationFeatureSet, bool]: ...


class FeatureConsentRepository(Protocol):
    def get(self, key: tuple[str, str]) -> ConsentLedger: ...


class FeatureWork(Protocol):
    features: FeatureRepositoryPort
    consents: FeatureConsentRepository

    def __enter__(self) -> FeatureWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...


class FeatureService:
    def __init__(
        self,
        uow_factory: Callable[[], FeatureWork],
        cryptography: SecretCryptography,
        now: Callable[[], datetime],
    ) -> None:
        self.uow_factory = uow_factory
        self.cryptography = cryptography
        self.now = now

    def replace_explicit(
        self,
        user_id: UUID,
        values: Mapping[str, str | int | float | bool],
        expected_feature_version: int,
    ) -> PersonalizationFeatureSet:
        with self.uow_factory() as work:
            consent = work.consents.get(("user", str(user_id))).granted(
                ConsentPurpose.PERSONALIZATION
            )
            feature_set = work.features.replace_explicit(
                user_id, dict(values), consent.sequence, expected_feature_version
            )
            work.commit()
            return feature_set

    def apply_implicit(
        self,
        user_id: UUID,
        contribution: FeatureContribution,
        expected_feature_version: int,
    ) -> tuple[PersonalizationFeatureSet, bool]:
        with self.uow_factory() as work:
            consent = work.consents.get(("user", str(user_id))).granted(
                ConsentPurpose.PERSONALIZATION
            )
            if contribution.consent_decision_id != consent.id:
                raise denied("stale_consent_version", "identity.personalization_unavailable")
            result = work.features.apply_contribution(
                user_id, consent.sequence, contribution, expected_feature_version
            )
            work.commit()
            return result

    def snapshot(self, user_id: UUID, request_id: str) -> FeatureSnapshot | None:
        with self.uow_factory() as work:
            consent = work.consents.get(("user", str(user_id))).granted(
                ConsentPurpose.PERSONALIZATION
            )
            feature_set = work.features.get(user_id)
            if feature_set is None:
                return None
            request_subject = self.cryptography.request_pseudonym(user_id, request_id)
            return build_feature_snapshot(feature_set, consent, request_subject, self.now())
