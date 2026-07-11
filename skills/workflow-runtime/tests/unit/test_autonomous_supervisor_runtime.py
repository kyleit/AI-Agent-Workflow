import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from autonomous_supervisor_runtime import AutonomousSupervisorRuntime

def test_supervisor_health_monitoring():
    supervisor = AutonomousSupervisorRuntime()
    
    # Simulating a deadlock scenario
    queue_state = {"running_tasks": ["task_1"], "ready_tasks": [], "stalled": True}
    agent_registry = {"active_agents": {"agent_1": "ACTIVE"}}
    
    alerts = supervisor.run_health_checks(queue_state, agent_registry)
    assert len(alerts) == 1
    assert alerts[0]["type"] == "DEADLOCK"
    
    # Heal deadlock
    heal_res = supervisor.self_heal(alerts[0])
    assert "Unlocked locks" in heal_res

def test_supervisor_starvation_monitoring():
    supervisor = AutonomousSupervisorRuntime()
    
    # Simulating a starvation scenario
    queue_state = {"running_tasks": [], "ready_tasks": ["task_2"], "stalled": False}
    agent_registry = {"active_agents": {}}
    
    alerts = supervisor.run_health_checks(queue_state, agent_registry)
    assert len(alerts) == 1
    assert alerts[0]["type"] == "STARVATION"
    
    # Heal starvation
    heal_res = supervisor.self_heal(alerts[0])
    assert "Spawned new agents" in heal_res
