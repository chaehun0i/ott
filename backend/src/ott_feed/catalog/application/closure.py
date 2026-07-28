"""Final approval/license/region closure recheck that fails closed."""

from __future__ import annotations

from datetime import datetime

from ott_feed.catalog.domain.errors import ApprovalClosureError, AvailabilityError, CatalogError
from ott_feed.catalog.domain.models import CatalogContent, CatalogState
from ott_feed.catalog.domain.policies import active_availability
from ott_feed.catalog.ports import ApprovedCatalogReadPort


class ApprovedClosureGuard:
    def __init__(self, reader: ApprovedCatalogReadPort) -> None:
        self.reader = reader

    def require(self, content_id: str, region: str, now: datetime) -> CatalogContent:
        try:
            content = self.reader.get_approved(content_id, region)
        except Exception as exc:
            raise ApprovalClosureError("CAT_CLOSURE_READ_FAILED") from exc
        if content is None or content.state is not CatalogState.APPROVED:
            raise ApprovalClosureError()
        if not content.source.license_reference:
            raise ApprovalClosureError("CAT_LICENSE_CLOSED")
        if not active_availability(content, region, now):
            raise AvailabilityError()
        return content


def stable_closure_error(exc: CatalogError) -> str:
    return exc.code
