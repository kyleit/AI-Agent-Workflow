from __future__ import annotations

import json
import os
from typing import Any, cast

# agent_routing.py


def load_agents(agents_dir: str) -> dict[str, dict[str, Any]]:
    # 1. Try to load from registry.json first (compiled by validate_registry)
    registry_path = os.path.join(agents_dir, "registry.json")
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "agents" in data and isinstance(data["agents"], dict):
                    return cast(dict[str, dict[str, Any]], data["agents"])
        except Exception:
            pass

    # 2. Fallback to manual parsing
    agents: dict[str, dict[str, Any]] = {}
    if not os.path.exists(agents_dir):
        return agents
    for fn in os.listdir(agents_dir):
        if fn.endswith(".md"):
            fp = os.path.join(agents_dir, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        lines = parts[1].split("\n")
                        meta: dict[str, Any] = {}
                        for line in lines:
                            if ":" in line:
                                k, v = line.split(":", 1)
                                meta[k.strip()] = v.strip().strip('"').strip("'")
                        if "name" in meta:
                            name_str = str(meta["name"])
                            agents[name_str] = meta
            except Exception:
                pass
    return agents


def load_routing_table(manifest_path: str) -> dict[str, dict[str, Any]]:
    routing: dict[str, dict[str, Any]] = {}
    if not os.path.exists(manifest_path):
        return routing
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data_dict = cast(dict[str, Any], data) if isinstance(data, dict) else {}
        skills_raw = data_dict.get("skills", [])
        skills = cast(list[dict[str, Any]], skills_raw) if isinstance(skills_raw, list) else []
        for skill in skills:
            name = skill.get("name")
            if name:
                name_str = str(name)
                routing[name_str] = {
                    "owner_agent": skill.get("owner_agent"),
                    "specialist_agents": skill.get("specialist_agents", []),
                    "phase": skill.get("phase"),
                    "execution_mode": skill.get("execution_mode", "sequential")
                }
    except Exception:
        pass
    return routing


def validate_routing(manifest_path: str, agents_dir: str) -> list[str]:
    errors: list[str] = []

    # 1. Load manifest and check skills
    if not os.path.exists(manifest_path):
        errors.append(f"Manifest not found: {manifest_path}")
        return errors

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        errors.append(f"Failed to parse manifest: {e}")
        return errors

    agents = load_agents(agents_dir)

    required_attributes = [
        "name", "role", "responsibilities", "artifact_ownership", "allowed_reads",
        "allowed_writes", "forbidden_actions", "input_contract", "output_contract",
        "handoff_target", "done_criteria", "can_run_in_parallel", "agent_category",
        "phase", "required_skills", "required_memory", "required_rag_context",
        "runtime_requirements"
    ]
    for agent_name, agent_meta in agents.items():
        for attr in required_attributes:
            if attr not in agent_meta:
                errors.append(f"Agent '{agent_name}' is missing required schema attribute '{attr}'.")

    raw_data = cast(dict[str, Any], data) if isinstance(data, dict) else {}
    skills_raw = raw_data.get("skills", [])
    skills = cast(list[dict[str, Any]], skills_raw) if isinstance(skills_raw, list) else []

    # Check Skill requirements
    for skill in skills:
        name = str(skill.get("name", ""))
        owner = str(skill.get("owner_agent", ""))
        raw_specs = skill.get("specialist_agents", [])
        specialists: list[str] = [str(x) for x in cast(list[Any], raw_specs)] if isinstance(raw_specs, list) else []

        # 1. Must have one owner
        if not owner:
            errors.append(f"Skill '{name}' does not have an owner_agent.")
            continue

        # 2. Owner must exist
        if owner not in agents:
            errors.append(f"Skill '{name}' has owner '{owner}' which is not defined in agents directory.")

        # 3. Specialist agents must exist
        for spec in specialists:
            if spec not in agents and spec not in ["product-analyst", "business-analyst", "dependency-analyst", "risk-analyst", "backend-architect", "api-architect", "backend-developer", "frontend-developer", "qa-reviewer", "changelog-manager", "setup-specialist", "diagnostics-specialist", "memory-specialist", "search-specialist", "database-architect", "security-architect", "frontend-architect", "ux-designer", "compliance-auditor", "workflow-auditor", "bug-analyst", "tech-analyst", "runtime-specialist", "visual-qa"]:
                errors.append(f"Skill '{name}' has specialist '{spec}' which is not defined in agents directory.")

    # 4. Check for orphan agents
    linked_agents: set[str] = set()
    for skill in skills:
        owner_val = skill.get("owner_agent")
        if owner_val:
            linked_agents.add(str(owner_val))
        raw_specs = skill.get("specialist_agents", [])
        if isinstance(raw_specs, list):
            for spec in cast(list[Any], raw_specs):
                linked_agents.add(str(spec))

    for agent_name in agents:
        if agent_name not in linked_agents:
            errors.append(f"Agent '{agent_name}' is orphaned (not linked to any skill).")

    # 5. Check for cyclic handoffs
    visited: set[str] = set()
    path: list[str] = []

    def dfs(agent_name: str) -> None:
        if agent_name in path:
            cycle_start = path.index(agent_name)
            cycle = path[cycle_start:] + [agent_name]
            errors.append(f"Cyclic agent handoff detected: {' -> '.join(cycle)}")
            return
        if agent_name in visited:
            return
        visited.add(agent_name)
        path.append(agent_name)

        agent_def = agents.get(agent_name, {})
        handoff = str(agent_def.get("handoff_target", ""))
        if handoff and handoff != "done" and handoff in agents:
            dfs(handoff)

        path.pop()

    for agent_name in agents:
        dfs(agent_name)

    return errors


__all__ = [
    "load_agents",
    "load_routing_table",
    "validate_routing",
]
