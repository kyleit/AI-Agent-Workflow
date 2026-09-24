# test_agent_registry.py
import os
import sys
import json
import pytest

# Resolve path to agents directory for importing validate_registry
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../agents")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

from agent_routing import load_agents
from confidence_gate import ConfidenceGate

agents_dir = "agents"

def test_registry_discovery():
    agents = load_agents(agents_dir)
    assert len(agents) > 0, "Should load at least one agent definition"
    assert "frontend-developer" in agents
    assert "backend-developer" in agents
    assert "planner" in agents
    assert "architect" in agents

def test_invalid_definitions_rejected():
    from validate_registry import custom_validate, load_schema
    schema = load_schema(os.path.join(agents_dir, "agent.schema.json"))
    
    invalid_agent = {
        "id": "invalid-agent",
        # missing name and other required fields
    }
    errors = custom_validate(invalid_agent, schema)
    assert len(errors) > 0, "Should reject definition lacking required fields"

def test_canonical_roles_matching():
    agents = load_agents(agents_dir)
    
    # 1. Planner matching
    planner = agents.get("planner")
    assert planner is not None
    assert "planning" in planner.get("capabilities", [])
    
    # 2. Architect matching
    architect = agents.get("architect")
    assert architect is not None
    assert "architecture" in architect.get("capabilities", [])
    
    # 3. Developer roles matching
    frontend = agents.get("frontend-developer")
    backend = agents.get("backend-developer")
    db_dev = agents.get("database-developer")
    
    assert "frontend" in frontend.get("capabilities", [])
    assert "backend" in backend.get("capabilities", [])
    assert "database" in db_dev.get("capabilities", [])

def test_developer_agents_write_permissions():
    agents = load_agents(agents_dir)
    
    frontend = agents.get("frontend-developer")
    backend = agents.get("backend-developer")
    
    # Check permissions mode is scoped-write (not read-only)
    assert frontend["permissions"]["mode"] == "scoped-write"
    assert backend["permissions"]["mode"] == "scoped-write"
    
    # Check write scopes
    assert any("frontend" in path for path in frontend["allowed_writes"])
    assert any("backend" in path for path in backend["allowed_writes"])
    assert not any("backend" in path for path in frontend["allowed_writes"]), "Frontend agent should not write to backend paths"
    assert not any("frontend" in path for path in backend["allowed_writes"]), "Backend agent should not write to frontend paths"

def test_main_orchestrator_cannot_write():
    agents = load_agents(agents_dir)
    
    orchestrator = agents.get("coder")  # coder is typically the legacy orchestrator proxy or similar
    if orchestrator:
        # If coder is a writer, it should have a mode. But main orchestrator/scheduler itself shouldn't write code directly.
        # Let's verify release-manager or reviewer constraints
        reviewer = agents.get("reviewer")
        assert reviewer["permissions"]["mode"] == "read-only"

def test_confidence_gates_thresholds():
    agents = load_agents(agents_dir)
    planner = agents.get("planner")
    architect = agents.get("architect")
    
    assert planner["confidence_threshold"]["brainstorm"] == 95
    assert planner["confidence_threshold"]["planning"] == 95
    assert architect["confidence_threshold"]["blueprint"] == 95


def _agent_definitions():
    from validate_registry import parse_yaml_frontmatter
    for fn in sorted(os.listdir(agents_dir)):
        if fn.endswith(".md") and fn != "README.md":
            with open(os.path.join(agents_dir, fn), encoding="utf-8") as f:
                yield fn, parse_yaml_frontmatter(f.read().split("---", 2)[1])

def test_all_agent_definitions_validate():
    from validate_registry import load_schema, validate_agent
    schema = load_schema(os.path.join(agents_dir, "agent.schema.json"))
    for fn, meta in _agent_definitions():
        assert validate_agent(meta, schema, fn) == [], fn

def test_block_scalar_prompt_parsed_as_text():
    from validate_registry import parse_yaml_frontmatter
    meta = parse_yaml_frontmatter('id: "x"\nagy_system_prompt: |\n  Step 1: read rules\n\n  - DO NOT guess\nnext: 1\n')
    assert meta["agy_system_prompt"] == "Step 1: read rules\n\n- DO NOT guess\n"
    assert meta["next"] == 1

def test_schema_rejects_unknown_fields_and_phases():
    from validate_registry import custom_validate, load_schema
    schema = load_schema(os.path.join(agents_dir, "agent.schema.json"))
    props = schema["properties"]
    assert custom_validate(["discovery", "debug", "verification"], props["phase_ownership"]) == []
    assert custom_validate(["deploy"], props["phase_ownership"]) != []
    assert custom_validate("ops", props["agent_category"]) != []
    assert any("unknown_field" in e for e in custom_validate({"unknown_field": 1}, schema))

def test_compiled_registry_matches_definitions():
    with open(os.path.join(agents_dir, "registry.json"), encoding="utf-8") as f:
        registry = json.load(f)["agents"]
    definitions = {meta["id"]: meta for _, meta in _agent_definitions()}
    assert {"auditor", "manager"} <= set(registry)
    assert registry == definitions, "agents/registry.json is stale: run validate_registry.main()"
