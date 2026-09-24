"""Headless command rendering (pure).

Renders an agent's argv-array invocation template by substituting
`${task}`, `${workflow}`, `${phase}` placeholders in each element. Argv arrays
(never a shell string) prevent injection: `${task}` stays a single argument.
"""

from __future__ import annotations

from collections.abc import Mapping

from malo.domain.errors import InvalidInvocationError
from malo.domain.models import AgentDescriptor

_ALLOWED_KEYS = ("task", "workflow", "phase")


def _render_element(element: str, substitutions: Mapping[str, str]) -> str:
    rendered = element
    for key in _ALLOWED_KEYS:
        rendered = rendered.replace("${" + key + "}", substitutions.get(key, ""))
    if "${" in rendered:
        raise InvalidInvocationError(
            f"Unresolved placeholder in invocation element: '{element}'. "
            f"Allowed: {_ALLOWED_KEYS}."
        )
    return rendered


def build_headless_command(
    agent: AgentDescriptor,
    substitutions: Mapping[str, str],
) -> list[str]:
    if not agent.invocation:
        raise InvalidInvocationError(f"agent '{agent.id}' has an empty invocation.")
    return [_render_element(part, substitutions) for part in agent.invocation]
