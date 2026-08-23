class DomainException(Exception):
    """Base exception for all domain business rule violations."""



class EntityNotFoundError(DomainException):
    """Raised when a required domain entity cannot be retrieved."""



class StateValidationError(DomainException):
    """Raised when an invalid state transition is attempted."""



class PathPolicyViolation(DomainException):
    """Raised when an absolute file path is detected in relative-only contexts."""



class DependencyViolationError(DomainException):
    """Raised when Clean Architecture dependency rules are broken."""



class RevisionConflictError(DomainException):
    """Raised when a concurrent write revision conflict is detected."""



class VIRConnectionError(DomainException):
    """Raised when CDP browser connection or socket communication fails."""




class ForbiddenAISourceError(ValueError):
    """Raised when an AI source is not permitted."""

class InvalidResumeTokenError(ValueError):
    """Raised when a resume token is invalid or expired."""
