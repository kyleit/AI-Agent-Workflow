"""Agent registry domain models (aiwf.agent-registry/1).

Pure value objects. JSON is parsed as `object` and narrowed via typed helpers
(basedpyright strict-full; no `Any`).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

from malo.domain.errors import InvalidRegistryError

REGISTRY_SCHEMA = "aiwf.agent-registry/1"
_AGENT_TYPES = ("claude", "codex", "antigravity")
_VERDICT_SOURCES = ("stdout-json", "stdout-text", "verdict-file")
_COST_HINTS = ("low", "med", "high")


def _as_str(value: object, field_name: str) -> str:
    if isinstance(value, str):
        return value
    raise InvalidRegistryError(f"Field '{field_name}' must be a string.")


def _as_bool(value: object, default: bool, field_name: str) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise InvalidRegistryError(f"Field '{field_name}' must be a boolean.")


def _as_int(value: object, default: int, field_name: str) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidRegistryError(f"Field '{field_name}' must be an integer.")
    return value


def _as_str_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        out: list[str] = []
        for item in cast("list[object]", value):
            if not isinstance(item, str):
                raise InvalidRegistryError(
                    f"Field '{field_name}' must contain only strings."
                )
            out.append(item)
        return tuple(out)
    raise InvalidRegistryError(f"Field '{field_name}' must be a list of strings.")


@dataclass(frozen=True)
class AgentDescriptor:
    """A single agent the orchestrator may spawn for a phase."""

    id: str
    type: str
    capabilities: tuple[str, ...]
    invocation: tuple[str, ...]
    enabled: bool = True
    priority: int = 0
    verdict_source: str = "stdout-text"
    cost_hint: str = "med"

    def __post_init__(self) -> None:
        if not self.id:
            raise InvalidRegistryError("agent id is required.")
        if self.type not in _AGENT_TYPES:
            raise InvalidRegistryError(
                f"agent '{self.id}' type '{self.type}' must be one of {_AGENT_TYPES}."
            )
        if not self.invocation:
            raise InvalidRegistryError(f"agent '{self.id}' invocation is required.")
        if self.verdict_source not in _VERDICT_SOURCES:
            raise InvalidRegistryError(
                f"agent '{self.id}' verdict_source must be one of {_VERDICT_SOURCES}."
            )
        if self.cost_hint not in _COST_HINTS:
            raise InvalidRegistryError(
                f"agent '{self.id}' cost_hint must be one of {_COST_HINTS}."
            )

    def can_run(self, phase: str) -> bool:
        return self.enabled and phase in self.capabilities

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "AgentDescriptor":
        return cls(
            id=_as_str(data.get("id", ""), "id"),
            type=_as_str(data.get("type", ""), "type"),
            capabilities=_as_str_tuple(data.get("capabilities"), "capabilities"),
            invocation=_as_str_tuple(data.get("invocation"), "invocation"),
            enabled=_as_bool(data.get("enabled"), True, "enabled"),
            priority=_as_int(data.get("priority"), 0, "priority"),
            verdict_source=_as_str(
                data.get("verdict_source", "stdout-text"), "verdict_source"
            ),
            cost_hint=_as_str(data.get("cost_hint", "med"), "cost_hint"),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "type": self.type,
            "capabilities": list(self.capabilities),
            "invocation": list(self.invocation),
            "enabled": self.enabled,
            "priority": self.priority,
            "verdict_source": self.verdict_source,
            "cost_hint": self.cost_hint,
        }


@dataclass(frozen=True)
class AgentRegistry:
    """The set of agents available to the orchestrator."""

    agents: tuple[AgentDescriptor, ...] = field(default_factory=tuple)
    schema: str = REGISTRY_SCHEMA

    def capable_for(self, phase: str) -> list[AgentDescriptor]:
        return [a for a in self.agents if a.can_run(phase)]

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "AgentRegistry":
        schema = _as_str(data.get("schema", REGISTRY_SCHEMA), "schema")
        if schema != REGISTRY_SCHEMA:
            raise InvalidRegistryError(
                f"Unsupported registry schema '{schema}'. Expected '{REGISTRY_SCHEMA}'."
            )
        raw_agents = data.get("agents", [])
        if not isinstance(raw_agents, list):
            raise InvalidRegistryError("'agents' must be a list.")
        agents: list[AgentDescriptor] = []
        for item in cast("list[object]", raw_agents):
            if not isinstance(item, dict):
                raise InvalidRegistryError("each agent must be an object.")
            agents.append(AgentDescriptor.from_dict(cast("Mapping[str, object]", item)))
        return cls(agents=tuple(agents), schema=schema)
