"""Domain-level application exceptions."""


class ApplicationError(Exception):
    """Base class for all application errors."""


class UserAlreadyExistsError(ApplicationError):
    """Raised when registration conflicts with an existing account."""


class InvalidCredentialsError(ApplicationError):
    """Raised when login credentials do not match any account."""


class ProfileImageNotFoundError(ApplicationError):
    """Raised when a requested profile image id does not exist."""


class UserNotFoundError(ApplicationError):
    """Raised when a user cannot be found by id."""
