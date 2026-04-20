class ApplicationError(Exception):
    """Base class for all application-layer errors."""


class LeaderboardUnavailableError(ApplicationError):
    """Raised when the Redis backend cannot be reached."""
