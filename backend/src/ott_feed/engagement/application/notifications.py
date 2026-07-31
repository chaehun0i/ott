"""Notification admission, scheduling and cancellation."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from ott_feed.engagement.domain.models import Channel, DeliveryJob, JobStatus, NotificationEvent


def stable_deduplication_key(member_ref: str, event: NotificationEvent, channel: Channel) -> str:
    raw = "\x1f".join(
        (member_ref, event.content_id, str(event.content_version), event.event_type, channel.value)
    )
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class PreferenceSnapshot:
    member_ref: str
    channels: frozenset[Channel]


class NotificationAdmission:
    def admit(
        self, event: NotificationEvent, preferences: Iterable[PreferenceSnapshot]
    ) -> tuple[DeliveryJob, ...]:
        jobs: list[DeliveryJob] = []
        for preference in preferences:
            for channel in sorted(preference.channels, key=str):
                dedup = stable_deduplication_key(preference.member_ref, event, channel)
                jobs.append(
                    DeliveryJob(
                        job_id=dedup,
                        deduplication_key=dedup,
                        event_id=event.event_id,
                        member_ref=preference.member_ref,
                        channel=channel,
                        available_at=event.effective_at,
                        expires_at=event.expires_at,
                    )
                )
        return tuple(jobs)


def ready_for_lane(
    jobs: Iterable[DeliveryJob], channel: Channel, now: datetime, limit: int
) -> tuple[DeliveryJob, ...]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    eligible = (
        job
        for job in jobs
        if job.channel is channel
        and job.status in {JobStatus.READY, JobStatus.RETRY}
        and job.available_at <= now < job.expires_at
    )
    return tuple(sorted(eligible, key=lambda job: (job.available_at, job.job_id))[:limit])


def cancel_member_jobs(jobs: Iterable[DeliveryJob], member_ref: str) -> tuple[DeliveryJob, ...]:
    return tuple(job.cancel() if job.member_ref == member_ref else job for job in jobs)
