class DomainError(Exception):
    """A business rule refused the request; the API maps it to an HTTP error."""


class EmailAlreadyRegisteredError(DomainError):
    """The email already belongs to an account (FR-AUTH-002)."""
