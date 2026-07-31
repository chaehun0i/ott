"""U06 PostgreSQL repositories."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ott_feed.engagement.adapters.persistence.models import IncidentRow, NotificationJobRow


class NotificationJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, job_id: str) -> NotificationJobRow | None:
        return self.session.get(NotificationJobRow, job_id)

    def add(self, row: NotificationJobRow) -> None:
        self.session.add(row)

    def claim(
        self, channel: str, owner: str, now: datetime, lease_until: datetime, limit: int
    ) -> tuple[NotificationJobRow, ...]:
        statement = (
            select(NotificationJobRow)
            .where(
                NotificationJobRow.channel == channel,
                NotificationJobRow.status.in_(("ready", "retry")),
                NotificationJobRow.available_at <= now,
                NotificationJobRow.expires_at > now,
            )
            .order_by(NotificationJobRow.available_at, NotificationJobRow.job_id)
            .limit(min(max(limit, 1), 100))
            .with_for_update(skip_locked=True)
        )
        rows = tuple(self.session.scalars(statement))
        for row in rows:
            row.status = "claimed"
            row.lease_owner = owner
            row.lease_until = lease_until
            row.fencing_token += 1
        return rows

    def complete(self, job_id: str, owner: str, token: int, status: str) -> bool:
        statement = (
            update(NotificationJobRow)
            .where(
                NotificationJobRow.job_id == job_id,
                NotificationJobRow.status == "claimed",
                NotificationJobRow.lease_owner == owner,
                NotificationJobRow.fencing_token == token,
            )
            .values(status=status, lease_owner=None, lease_until=None)
        )
        return self.session.connection().execute(statement).rowcount == 1


class IncidentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def update_state(self, incident_id: str, expected_version: int, state: str) -> bool:
        statement = (
            update(IncidentRow)
            .where(IncidentRow.incident_id == incident_id, IncidentRow.version == expected_version)
            .values(state=state, version=expected_version + 1)
        )
        return self.session.connection().execute(statement).rowcount == 1
