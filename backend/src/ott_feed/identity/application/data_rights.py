"""Fresh-authenticated export and deletion saga orchestration."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from ott_feed.identity.domain.errors import denied
from ott_feed.identity.domain.models import (
    DataRightsRequest,
    DataRightsStatus,
    DataRightsType,
    ExportArtifact,
    Session,
    User,
)
from ott_feed.identity.domain.policies import deletion_status, require_fresh_auth
from ott_feed.identity.ports import ExportStorage


class DataRightsRepositoryPort(Protocol):
    def get(self, request_id: UUID) -> DataRightsRequest | None: ...

    def save(self, request: DataRightsRequest, expected_version: int | None = None) -> None: ...


class DataRightsIdentityRepository(Protocol):
    def get_user(self, user_id: UUID) -> User | None: ...

    def save_user(self, user: User, expected_version: int | None = None) -> None: ...


class DataRightsSessionRepository(Protocol):
    def revoke_all(self, user_id: UUID, reason: str, at: datetime) -> int: ...


class DataRightsJobPublisher(Protocol):
    def enqueue(self, job_type: str, payload: dict[str, object], lane: str) -> UUID: ...


class DataRightsWork(Protocol):
    data_rights: DataRightsRepositoryPort
    identities: DataRightsIdentityRepository
    sessions: DataRightsSessionRepository
    jobs: DataRightsJobPublisher

    def __enter__(self) -> DataRightsWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...


class ExportDataProvider(Protocol):
    def export(self, user_id: UUID) -> Mapping[str, object]: ...


class DeletionCategoryHandler(Protocol):
    def delete(self, user_id: UUID, category: str) -> None: ...

    def remaining(self, user_id: UUID, category: str) -> int: ...


class DataRightsService:
    def __init__(
        self, uow_factory: Callable[[], DataRightsWork], now: Callable[[], datetime]
    ) -> None:
        self.uow_factory = uow_factory
        self.now = now

    def request_export(
        self, user: User, session: Session, idempotency_key: str
    ) -> DataRightsRequest:
        require_fresh_auth(session, self.now())
        request = DataRightsRequest(user.id, DataRightsType.EXPORT, idempotency_key)
        request.authorize(session.fresh_authenticated_at)
        with self.uow_factory() as work:
            work.data_rights.save(request)
            work.jobs.enqueue("identity.data-rights.export", {"requestId": str(request.id)}, "low")
            work.commit()
        return request

    def request_deletion(
        self, user: User, session: Session, idempotency_key: str
    ) -> DataRightsRequest:
        now = self.now()
        require_fresh_auth(session, now)
        expected = user.row_version
        user.begin_deletion(now)
        request = DataRightsRequest(user.id, DataRightsType.DELETION, idempotency_key)
        request.authorize(session.fresh_authenticated_at)
        with self.uow_factory() as work:
            work.identities.save_user(user, expected)
            work.sessions.revoke_all(user.id, "account_deletion", now)
            work.data_rights.save(request)
            work.jobs.enqueue(
                "identity.data-rights.deletion", {"requestId": str(request.id)}, "high"
            )
            work.commit()
        return request

    def status(self, request_id: UUID, user_id: UUID) -> dict[str, object]:
        with self.uow_factory() as work:
            request = work.data_rights.get(request_id)
            if request is None or request.user_id != user_id:
                raise denied()
            if request.request_type == DataRightsType.DELETION:
                return deletion_status(request)
            return {
                "requestId": str(request.id),
                "status": request.status.value,
                "statusVersion": request.status_version,
            }


class ExportWorker:
    def __init__(
        self,
        uow_factory: Callable[[], DataRightsWork],
        provider: ExportDataProvider,
        storage: ExportStorage,
        now: Callable[[], datetime],
    ) -> None:
        self.uow_factory = uow_factory
        self.provider = provider
        self.storage = storage
        self.now = now
        self.artifacts: dict[UUID, ExportArtifact] = {}

    def run(self, request_id: UUID) -> ExportArtifact:
        with self.uow_factory() as work:
            request = work.data_rights.get(request_id)
            if request is None or request.request_type != DataRightsType.EXPORT:
                raise denied("export_request_invalid", "identity.export_unavailable")
            expected = request.status_version
            request.start()
            work.data_rights.save(request, expected)
            payload = json.dumps(
                self.provider.export(request.user_id),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
            expires_at = self.now() + timedelta(hours=24)
            object_key = f"exports/{request.id}"
            reference = self.storage.put_encrypted(object_key, payload, expires_at)
            artifact = ExportArtifact(
                request.id,
                reference,
                hashlib.sha256(payload).hexdigest(),
                expires_at,
                created_at=self.now(),
            )
            request.complete()
            work.data_rights.save(request, request.status_version - 1)
            work.commit()
            self.artifacts[request.id] = artifact
            return artifact

    def download_once(self, request_id: UUID, at: datetime) -> bytes:
        artifact = self.artifacts.get(request_id)
        if artifact is None:
            raise denied("export_not_found", "identity.export_unavailable")
        artifact.consume(at)
        return self.storage.get_once(artifact.encrypted_reference)


class DeletionWorker:
    def __init__(
        self,
        uow_factory: Callable[[], DataRightsWork],
        handler: DeletionCategoryHandler,
        now: Callable[[], datetime],
    ) -> None:
        self.uow_factory = uow_factory
        self.handler = handler
        self.now = now

    def run(self, request_id: UUID) -> DataRightsStatus:
        with self.uow_factory() as work:
            request = work.data_rights.get(request_id)
            if request is None or request.request_type != DataRightsType.DELETION:
                raise denied("deletion_request_invalid", "identity.deletion_unavailable")
            expected = request.status_version
            request.start()
            work.data_rights.save(request, expected)
            for step in request.deletion_steps.values():
                if step.completed_at is not None:
                    continue
                step.start()
                try:
                    self.handler.delete(request.user_id, step.category)
                    if self.handler.remaining(request.user_id, step.category) != 0:
                        raise RuntimeError("deletion closure failed")
                    step.complete(self.now())
                except Exception as exc:
                    step.fail(type(exc).__name__)
            previous = request.status_version
            request.complete()
            work.data_rights.save(request, previous)
            if request.status != DataRightsStatus.COMPLETED:
                work.jobs.enqueue(
                    "identity.data-rights.deletion", {"requestId": str(request.id)}, "high"
                )
            work.commit()
            return request.status
