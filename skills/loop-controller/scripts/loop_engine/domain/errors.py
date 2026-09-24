"""Domain errors for the loop engine.

These are pure domain exceptions. They MUST NOT depend on any framework,
IO, or infrastructure concern.
"""

from __future__ import annotations


class LoopEngineError(Exception):
    """Base class for every loop engine domain error."""


class InvalidVerdictError(LoopEngineError):
    """Raised when a verdict string cannot be mapped to a known Verdict."""


class InvalidTransitionError(LoopEngineError):
    """Raised when a transition string cannot be mapped to a known Transition."""


class InvalidLoopStateError(LoopEngineError):
    """Raised when a loop-state payload violates the aiwf.loop/1 contract."""


class LoopStateNotFoundError(LoopEngineError):
    """Raised when a requested loop-state file does not exist."""
