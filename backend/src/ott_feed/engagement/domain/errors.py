"""U06 domain errors."""


class EngagementError(Exception):
    """Base U06 domain error."""


class InvalidTransition(EngagementError):
    """Raised when a state transition violates the job model."""


class StaleFencingToken(EngagementError):
    """Raised when an expired worker tries to close a job."""
