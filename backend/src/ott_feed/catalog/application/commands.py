"""Passed-validation commands accepted from U04."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ott_feed.catalog.domain.models import CatalogContent


class PublicationAction(StrEnum):
    PUBLISH = "publish"
    REPLACE = "replace"
    WITHDRAW = "withdraw"
    REACTIVATE = "reactivate"


@dataclass(frozen=True, slots=True)
class PassedValidationCommand:
    action: PublicationAction
    content_id: str
    decision_id: str
    content: CatalogContent | None = None

    def __post_init__(self) -> None:
        if not self.content_id or not self.decision_id:
            raise ValueError("content and decision IDs are required")
        if self.action in {PublicationAction.PUBLISH, PublicationAction.REPLACE} and (
            self.content is None or self.content.id != self.content_id
        ):
            raise ValueError("validated content is required for publish/replace")
