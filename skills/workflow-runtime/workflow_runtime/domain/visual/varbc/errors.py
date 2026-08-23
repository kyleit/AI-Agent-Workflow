class DomainError(Exception):
    """Base error for VAR domain Bounded Context."""



class DomainValidationError(DomainError):
    """Raised on domain validation failure."""



class BrowserNotAvailableError(DomainError):
    """Raised when CDP client or browser is unavailable."""



class RepositoryIOError(DomainError):
    """Raised on repository disk I/O failure."""
