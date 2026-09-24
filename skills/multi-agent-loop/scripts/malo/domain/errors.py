"""Domain errors for the MALO engine (pure; no framework/IO)."""

from __future__ import annotations


class MaloError(Exception):
    """Base class for every MALO domain error."""


class InvalidRegistryError(MaloError):
    """Raised when an agent-registry payload violates aiwf.agent-registry/1."""


class NoCapableAgentError(MaloError):
    """Raised when no enabled agent can run the requested phase."""


class InvalidResultError(MaloError):
    """Raised when a phase-run result payload is malformed."""


class InvalidInvocationError(MaloError):
    """Raised when a headless invocation template cannot be rendered."""
