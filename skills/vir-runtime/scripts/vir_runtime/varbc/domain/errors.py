class DomainError(Exception):
    """Base error for VAR domain Bounded Context."""

    pass


class DomainValidationError(DomainError):
    """Raised on domain validation failure."""

    pass


class BrowserNotAvailableError(DomainError):
    """Raised when CDP client or browser is unavailable."""

    pass


class RepositoryIOError(DomainError):
    """Raised on repository disk I/O failure."""

    pass
