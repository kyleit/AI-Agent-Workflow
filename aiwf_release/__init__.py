"""AIWF Release Orchestrator — config-driven, project-agnostic release engine.

Reads each project's release.config.json and executes the declared pipeline
deterministically (gates -> version bump -> changelog -> arbitrary steps ->
multi-repo/submodule release in a fixed order -> propagation), then writes a
tamper-evident release receipt that the git pre-push backstop verifies.

No project-specific logic lives here — behaviour is data in release.config.json.
"""

__all__ = ["config", "versioning", "changelog", "gitsteps", "engine", "cli"]
