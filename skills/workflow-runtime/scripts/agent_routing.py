# agent_routing.py
import os
import json
from typing import Dict, List, Tuple

def load_agents(agents_dir: str) -> Dict[str, dict]:
    # 1. Try to load from registry.json first (compiled by validate_registry)
    registry_path = os.path.join(agents_dir, "registry.json")
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "agents" in data:
                    return data["agents"]
        except Exception:
            pass

    # 2. Fallback to manual parsing
    agents = {}
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
                        # Simple flat parser fallback
                        lines = parts[1].split("\n")
                        meta = {}
                        for line in lines:
                            if ":" in line:
                                k, v = line.split(":", 1)
                                meta[k.strip()] = v.strip().strip('"').strip("'")
                        if "name" in meta:
                            agents[meta["name"]] = meta
            except Exception:
                pass
    return agents

def load_routing_table(manifest_path: str) -> Dict[str, dict]:
    routing = {}
    if not os.path.exists(manifest_path):
        return routing
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for skill in data.get("skills", []):
            name = skill.get("name")
            if name:
                routing[name] = {
                    "owner_agent": skill.get("owner_agent"),
                    "specialist_agents": skill.get("specialist_agents", []),
                    "phase": skill.get("phase"),
                    "execution_mode": skill.get("execution_mode", "sequential")
                }
    except Exception:
        pass
    return routing

def validate_routing(manifest_path: str, agents_dir: str) -> List[str]:
    errors = []
    
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
    
    # Validate each agent's schema properties
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
                
    skills = data.get("skills", [])
    skills_map = {s["name"]: s for s in skills}
    
    # Check Skill requirements
    for skill in skills:
        name = skill.get("name")
        owner = skill.get("owner_agent")
        specialists = skill.get("specialist_agents", [])
        
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
                
    # 4. Check for orphan agents (defined but never owning or specialist in any skill)
    linked_agents = set()
    for skill in skills:
        if skill.get("owner_agent"):
            linked_agents.add(skill["owner_agent"])
        for spec in skill.get("specialist_agents", []):
            linked_agents.add(spec)
            
    for agent_name in agents:
        if agent_name not in linked_agents:
            errors.append(f"Agent '{agent_name}' is orphaned (not linked to any skill).")
            
    # 5. Check for cyclic handoffs
    visited = set()
    path = []
    
    def dfs(agent_name: str):
        if agent_name in path:
            cycle = path[path.index(agent_name):] + [agent_name]
            errors.append(f"Cyclic agent handoff detected: {' -> '.join(cycle)}")
            return
        if agent_name in visited:
            return
        visited.add(agent_name)
        path.append(agent_name)
        
        agent_def = agents.get(agent_name, {})
        handoff = agent_def.get("handoff_target")
        if handoff and handoff != "done" and handoff in agents:
            dfs(handoff)
            
        path.pop()
        
    for agent_name in agents:
        dfs(agent_name)
        
    return errors


class AgentSelector:
    def __init__(self, agents_dir: str = "agents"):
        self.agents_dir = os.path.abspath(agents_dir)
        self._cache = {}

    def _parse_frontmatter(self, file_content: str) -> dict:
        if not file_content.startswith("---"):
            return {}
        parts = file_content.split("---", 2)
        if len(parts) < 3:
            return {}
        fm_text = parts[1]
        try:
            import yaml
            data = yaml.safe_load(fm_text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        
        # Fallback manual parsing if yaml is not available
        meta = {}
        lines = fm_text.split("\n")
        in_list_key = None
        for line in lines:
            if not line.strip():
                continue
            # Check for list items
            if line.strip().startswith("-") and in_list_key:
                val = line.strip().lstrip("-").strip().strip('"').strip("'")
                if in_list_key in meta:
                    if not isinstance(meta[in_list_key], list):
                        meta[in_list_key] = [meta[in_list_key]]
                    meta[in_list_key].append(val)
                else:
                    meta[in_list_key] = [val]
                continue
                
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if not v: # list start
                    in_list_key = k
                    meta[k] = []
                else:
                    in_list_key = None
                    if v.isdigit():
                        meta[k] = int(v)
                    elif v.lower() == "true":
                        meta[k] = True
                    elif v.lower() == "false":
                        meta[k] = False
                    else:
                        meta[k] = v
        return meta

    def load_agent_metadata(self, agent_id: str) -> dict:
        import time
        cache_key = f"agent:{agent_id}"
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if time.time() - entry["ts"] < 600:
                return entry["data"]
        
        fn = f"{agent_id}.md"
        fp = os.path.join(self.agents_dir, fn)
        if not os.path.exists(fp):
            if os.path.exists(self.agents_dir):
                for f in os.listdir(self.agents_dir):
                    if f.endswith(".md"):
                        path = os.path.join(self.agents_dir, f)
                        try:
                            with open(path, "r", encoding="utf-8") as file:
                                content = file.read()
                            meta = self._parse_frontmatter(content)
                            if meta.get("id") == agent_id or meta.get("name") == agent_id:
                                self._cache[cache_key] = {"ts": time.time(), "data": meta}
                                return meta
                        except Exception:
                            pass
            return {}
            
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            meta = self._parse_frontmatter(content)
            self._cache[cache_key] = {"ts": time.time(), "data": meta}
            return meta
        except Exception:
            return {}

    def recruit_agent_for_task(self, task_type: str, task_tags: list[str]) -> dict:
        candidates = []
        if os.path.exists(self.agents_dir):
            for fn in os.listdir(self.agents_dir):
                if fn.endswith(".md"):
                    fp = os.path.join(self.agents_dir, fn)
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            content = f.read()
                        meta = self._parse_frontmatter(content)
                        if not meta:
                            continue
                            
                        agent_caps = meta.get("capabilities", [])
                        if isinstance(agent_caps, str):
                            agent_caps = [agent_caps]
                            
                        spawn_conds = meta.get("spawn_conditions", {})
                        spawn_tags = []
                        if isinstance(spawn_conds, dict):
                            spawn_tags = spawn_conds.get("task_tags", [])
                            if isinstance(spawn_tags, str):
                                spawn_tags = [spawn_tags]
                        
                        cat_match = False
                        category = meta.get("agent_category")
                        phases = meta.get("phase_ownership", [])
                        if isinstance(phases, str):
                            phases = [phases]
                        
                        if category == task_type or task_type in phases:
                            cat_match = True
                        if isinstance(spawn_conds, dict) and task_type in spawn_conds.get("phases", []):
                            cat_match = True
                            
                        if not cat_match:
                            continue
                            
                        tag_match = False
                        for tag in task_tags:
                            if tag in agent_caps or tag in spawn_tags:
                                tag_match = True
                                break
                        if not task_tags:
                            tag_match = True
                            
                        if tag_match:
                            candidates.append(meta)
                    except Exception:
                        pass
                        
        if not candidates:
            return {}
            
        def get_priority(x):
            try:
                return int(x.get("priority", 999))
            except Exception:
                return 999
                
        candidates.sort(key=get_priority)
        best = candidates[0]
        
        handoffs = best.get("handoff_targets", [])
        if isinstance(handoffs, str):
            handoffs = [handoffs]
            
        return {
            "agent_id": best.get("id") or best.get("name"),
            "handoff_targets": handoffs
        }
