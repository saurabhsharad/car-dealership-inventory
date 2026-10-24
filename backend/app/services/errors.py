class DomainError(Exception):
    """A business rule refused the request; the API maps it to an HTTP error."""


class EmailAlreadyRegisteredError(DomainError):
    """The email already belongs to an account (FR-AUTH-002)."""


class InvalidCredentialsError(DomainError):
    """The email and password do not match an account (FR-AUTH-005)."""


class NotAuthenticatedError(DomainError):
    """No usable bearer token, or its user no longer exists (FR-AUTH-006)."""


class SessionExpiredError(DomainError):
    """The bearer token was genuine but has expired (FR-AUTH-006)."""


class ForbiddenError(DomainError):
    """The user is authenticated but not allowed to do this (FR-AUTH-007)."""
