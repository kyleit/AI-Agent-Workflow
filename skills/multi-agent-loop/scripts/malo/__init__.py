"""AIWF Multi-Agent Loop Orchestration (MALO) engine.

Turn-driven, foreground orchestrator (no daemon) that drives the
loop-controller and spawns heterogeneous agents (Claude, Codex, Antigravity)
headless per phase on one shared workspace, until the loop HALTs.

Business logic lives here (Clean Architecture + DI); the loop-controller
remains the transition authority and is never re-implemented.
"""

__all__ = ["__version__"]
__version__ = "1.0.0"
