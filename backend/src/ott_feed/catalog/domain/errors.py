"""Stable U03 catalog business errors."""


class CatalogError(ValueError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class CatalogConflict(CatalogError):
    def __init__(self, message: str = "catalog version conflict") -> None:
        super().__init__("CAT_VERSION_CONFLICT", message, retryable=True)


class ApprovalClosureError(CatalogError):
    def __init__(self, code: str = "CAT_APPROVAL_CLOSED") -> None:
        super().__init__(code, "content is not currently approved")


class AvailabilityError(CatalogError):
    def __init__(self, code: str = "AVAIL_REGION_UNAVAILABLE") -> None:
        super().__init__(code, "verified regional availability is required")


class ProjectionGapError(CatalogError):
    def __init__(self) -> None:
        super().__init__("PROJ_VERSION_GAP", "projection version gap detected", retryable=True)
