"""Dynamic capability-based agent selection (pure domain policy).

Deterministic: given a phase, the registry, and a usage history, pick the best
enabled, capable agent. Ranking:
  1. highest `priority`
  2. least-recently-used (lowest history count) — spreads load
  3. lexical `id` — final deterministic tie-break

Returns None when no enabled agent declares the phase capability, so the caller
falls back to the current session agent (backward compatibility).
"""

from __future__ import annotations

from collections.abc import Mapping

from malo.domain.models import AgentDescriptor, AgentRegistry


def select_agent(
    phase: str,
    registry: AgentRegistry,
    history: Mapping[str, int] | None = None,
) -> AgentDescriptor | None:
    candidates = registry.capable_for(phase)
    if not candidates:
        return None
    used = history or {}

    def sort_key(agent: AgentDescriptor) -> tuple[int, int, str]:
        # negative priority so higher priority sorts first
        return (-agent.priority, used.get(agent.id, 0), agent.id)

    return sorted(candidates, key=sort_key)[0]


def selection_reason(
    agent: AgentDescriptor,
    phase: str,
    candidate_count: int,
) -> str:
    return (
        f"selected '{agent.id}' ({agent.type}) for phase '{phase}': "
        f"capable, priority={agent.priority}, among {candidate_count} candidate(s)"
    )
