from __future__ import annotations

import json
import os
import sys
from typing import Any, cast

from workflow_runtime.infrastructure.session.session import load_session
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    sync_analysis_agents_to_session)


def do_analysis_agent(args: Any) -> None:
    analysis_file = os.path.join(".agents", "runtime", "analysis-agents.json")
    os.makedirs(os.path.dirname(analysis_file), exist_ok=True)

    data: dict[str, Any] = {"phase": "unknown", "agents": []}
    if os.path.exists(analysis_file):
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = cast(dict[str, Any], loaded)
        except Exception:
            pass

    session = load_session()
    current_skill = str(session.get("active_skill", "unknown"))
    data["phase"] = current_skill

    raw_agents = data.get("agents")
    agents_list: list[dict[str, Any]] = [cast(dict[str, Any], a) for a in cast(list[Any], raw_agents) if isinstance(a, dict)] if isinstance(raw_agents, list) else []

    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None)

    if subaction == "add":
        agent_id = str(getattr(args, "agent_id", "") or "")
        role = str(getattr(args, "role", "") or "")
        status = str(getattr(args, "status", "") or "")
        summary = str(getattr(args, "summary", "") or "")

        if not agent_id or not role:
            print("Error: --agent-id and --role are required.", file=sys.stderr)
            sys.exit(1)

        recs: list[Any] = []
        raw_recs = getattr(args, "recommendations", None)
        if raw_recs:
            try:
                parsed: Any = json.loads(str(raw_recs))
                if isinstance(parsed, list):
                    recs = cast(list[Any], parsed)
                else:
                    recs = [parsed]
            except Exception:
                recs = [raw_recs]

        existing_agent: dict[str, Any] | None = None
        for a in agents_list:
            if str(a.get("agent_id", "")) == agent_id:
                existing_agent = a
                break

        if existing_agent is not None:
            existing_agent["role"] = role
            existing_agent["status"] = status or "completed"
            existing_agent["summary"] = summary
            existing_agent["recommendations"] = recs
        else:
            agents_list.append({
                "agent_id": agent_id,
                "role": role,
                "status": status or "running",
                "summary": summary,
                "recommendations": recs
            })

        data["agents"] = agents_list
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Analysis agent {agent_id} ({role}) added/updated.")

    elif subaction == "list":
        data["agents"] = agents_list
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif subaction == "clear":
        data["agents"] = []
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Analysis agents cleared.")

    elif subaction == "merge":
        print("Merging recommendations from analysis agents:")
        all_recs: list[str] = []
        for a in agents_list:
            a_id = str(a.get("agent_id", ""))
            a_role = str(a.get("role", ""))
            a_sum = str(a.get("summary", ""))
            print(f"- Agent {a_id} ({a_role}): {a_sum}")
            raw_a_recs = a.get("recommendations", [])
            a_recs = [str(r) for r in cast(list[Any], raw_a_recs)] if isinstance(raw_a_recs, list) else []
            for r in a_recs:
                all_recs.append(f"[{a_role}] {r}")
        print("Merged recommendations:")
        for idx, r_str in enumerate(all_recs):
            print(f"{idx+1}. {r_str}")

    sync_analysis_agents_to_session()


__all__ = ["do_analysis_agent"]
