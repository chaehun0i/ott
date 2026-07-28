"""CAS-backed feature projection repository and contribution ledger."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session as SqlSession

from ott_feed.identity.adapters.persistence.models import (
    FeatureContributionRow,
    PersonalizationFeatureRow,
)
from ott_feed.identity.domain.errors import conflict
from ott_feed.identity.domain.models import FeatureContribution, PersonalizationFeatureSet


class SqlAlchemyFeatureRepository:
    def __init__(self, session: SqlSession) -> None:
        self.session = session

    def get(self, user_id: UUID) -> PersonalizationFeatureSet | None:
        row = self.session.get(PersonalizationFeatureRow, user_id)
        if row is None:
            return None
        contributions = self.session.scalars(
            select(FeatureContributionRow).where(FeatureContributionRow.user_id == user_id)
        ).all()
        return PersonalizationFeatureSet(
            user_id=user_id,
            consent_version=row.consent_version,
            features=row.features,
            contributions={
                item.event_id: FeatureContribution(
                    item.event_id, item.name, item.value, item.consent_decision_id
                )
                for item in contributions
            },
            feature_version=row.feature_version,
            row_version=row.row_version,
        )

    def create(self, feature_set: PersonalizationFeatureSet) -> None:
        if self.session.get(PersonalizationFeatureRow, feature_set.user_id):
            raise conflict("feature_exists", "identity.feature_conflict")
        self.session.add(
            PersonalizationFeatureRow(
                user_id=feature_set.user_id,
                feature_version=feature_set.feature_version,
                consent_version=feature_set.consent_version,
                features=feature_set.features,
                row_version=feature_set.row_version,
                updated_at=datetime.now(UTC),
            )
        )
        self.session.flush()

    def replace_explicit(
        self,
        user_id: UUID,
        values: dict[str, str | int | float | bool],
        consent_version: int,
        expected_feature_version: int,
    ) -> PersonalizationFeatureSet:
        feature_set = self.get(user_id) or PersonalizationFeatureSet(user_id, consent_version)
        if feature_set.feature_version != expected_feature_version:
            raise conflict("feature_version_conflict", "identity.feature_conflict")
        feature_set.replace_explicit(values, consent_version)
        result = self.session.execute(
            update(PersonalizationFeatureRow)
            .where(
                PersonalizationFeatureRow.user_id == user_id,
                PersonalizationFeatureRow.feature_version == expected_feature_version,
            )
            .values(
                feature_version=feature_set.feature_version,
                consent_version=feature_set.consent_version,
                features=feature_set.features,
                row_version=feature_set.row_version,
                updated_at=datetime.now(UTC),
            )
        )
        if getattr(result, "rowcount", 0) == 0:
            if self.session.get(PersonalizationFeatureRow, user_id) is None:
                self.create(feature_set)
            else:
                raise conflict("feature_version_conflict", "identity.feature_conflict")
        self.session.flush()
        return feature_set

    def apply_contribution(
        self,
        user_id: UUID,
        consent_version: int,
        contribution: FeatureContribution,
        expected_feature_version: int,
    ) -> tuple[PersonalizationFeatureSet, bool]:
        existing = self.session.get(FeatureContributionRow, (user_id, contribution.event_id))
        if existing:
            feature_set = self.get(user_id)
            if feature_set is None:
                raise conflict("feature_state_missing", "identity.feature_conflict")
            return feature_set, False
        feature_set = self.get(user_id) or PersonalizationFeatureSet(user_id, consent_version)
        if feature_set.feature_version != expected_feature_version:
            raise conflict("feature_version_conflict", "identity.feature_conflict")
        created = self.session.get(PersonalizationFeatureRow, user_id) is None
        feature_set.apply(contribution, expected_feature_version)
        if created:
            self.create(feature_set)
        else:
            result = self.session.execute(
                update(PersonalizationFeatureRow)
                .where(
                    PersonalizationFeatureRow.user_id == user_id,
                    PersonalizationFeatureRow.feature_version == expected_feature_version,
                )
                .values(
                    feature_version=feature_set.feature_version,
                    consent_version=consent_version,
                    features=feature_set.features,
                    row_version=feature_set.row_version,
                    updated_at=datetime.now(UTC),
                )
            )
            if getattr(result, "rowcount", 0) != 1:
                raise conflict("feature_version_conflict", "identity.feature_conflict")
        self.session.add(
            FeatureContributionRow(
                user_id=user_id,
                event_id=contribution.event_id,
                name=contribution.name,
                value=contribution.value,
                consent_decision_id=contribution.consent_decision_id,
                applied_feature_version=feature_set.feature_version,
            )
        )
        self.session.flush()
        return feature_set, True

    def delete_user(self, user_id: UUID) -> None:
        self.session.execute(
            delete(FeatureContributionRow).where(FeatureContributionRow.user_id == user_id)
        )
        self.session.execute(
            delete(PersonalizationFeatureRow).where(PersonalizationFeatureRow.user_id == user_id)
        )
