# test_autonomous_capacity_planning.py
import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Add scripts path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

from capacity_controller import CapacityController
from adaptive_scheduler import AdaptiveTeamPlanner, RuntimeScheduler, SchedulerMetrics
from confidence_gate import ConfidenceGate

@pytest.fixture
def mock_workspace(tmp_path):
    state_dir = tmp_path / ".agents" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock workflow.json to return active work item id
    with open(state_dir / "workflow.json", "w") as f:
        json.dump({"work_item": {"id": "FEAT-999"}}, f)
        
    return tmp_path

def test_confidence_gate_failed_blocked(mock_workspace):
    # Simulate missing artifact file
    score, gaps = ConfidenceGate.calculate_confidence("brainstorm", str(mock_workspace))
    assert score == 0.0
    assert len(gaps) > 0
    assert "Missing artifact file" in gaps[0]

def test_confidence_gate_passed(mock_workspace):
    # Create valid brainstorm file
    brainstorm_dir = mock_workspace / "docs" / "brainstorming"
    brainstorm_dir.mkdir(parents=True, exist_ok=True)
    
    brainstorm_file = brainstorm_dir / "FEAT-999_brainstorm.md"
    content = """
# Brainstorming
## Feature Goal
Goal description
## Scope Boundary
Boundary details
## Trigger
Trigger details
## Success Metrics
Success metrics details
"""
    with open(brainstorm_file, "w") as f:
        f.write(content)
        
    score, gaps = ConfidenceGate.calculate_confidence("brainstorm", str(mock_workspace))
    assert score >= 95.0
    assert len(gaps) == 0

def test_capacity_controller_concurrency_throttling():
    # Setup controller with max limits
    capacity = CapacityController(max_cpu_percent=80.0, max_ram_percent=80.0, max_concurrency=4)
    
    with patch("psutil.cpu_percent") as mock_cpu, \
         patch("psutil.virtual_memory") as mock_ram:
         
        # Scenario 1: Normal system load -> full concurrency
        mock_cpu.return_value = 10.0
        mock_ram.return_value.percent = 20.0
        mock_ram.return_value.available = 8.0 * (1024 ** 3)
        assert capacity.evaluate_concurrency_limit() == 4
        
        # Scenario 2: High CPU load -> throttled to sequential
        mock_cpu.return_value = 85.0
        assert capacity.evaluate_concurrency_limit() == 1
        
        # Scenario 3: Medium CPU load -> throttled to 2
        mock_cpu.return_value = 65.0
        assert capacity.evaluate_concurrency_limit() == 2

def test_dynamic_recruitment_hardware_limits():
    capacity = CapacityController(max_cpu_percent=80.0, max_ram_percent=80.0, max_concurrency=2)
    
    with patch("psutil.cpu_percent") as mock_cpu, \
         patch("psutil.virtual_memory") as mock_ram:
         
        mock_cpu.return_value = 10.0
        mock_ram.return_value.percent = 20.0
        
        # Recruit 1
        allowed, msg = capacity.can_recruit("backend", 5)
        assert allowed is True
        capacity.recruit_agent("AGENT-DYNAMIC-1", "backend")
        
        # Recruit 2
        allowed, msg = capacity.can_recruit("frontend", 5)
        assert allowed is True
        capacity.recruit_agent("AGENT-DYNAMIC-2", "frontend")
        
        # Recruit 3 -> exceeds max_concurrency (limit: 2)
        allowed, msg = capacity.can_recruit("qa", 5)
        assert allowed is False
        assert "limit reached" in msg

def test_force_tasks_priority():
    planner = AdaptiveTeamPlanner()
    raw_tasks = [
        {"name": "task 1", "role": "development", "locks": []},
        {"name": "task 2", "role": "development", "locks": []},
        {"name": "task 3", "role": "development", "locks": []}
    ]
    agents, graph, _ = planner.plan_team_and_graph("FEAT-999", raw_tasks)
    metrics = SchedulerMetrics()
    scheduler = RuntimeScheduler(agents, graph, metrics)
    
    # We spy on execute_task to check order
    executed_order = []
    orig_execute = scheduler.execute_task
    
    def spy_execute(task_id, *args, **kwargs):
        executed_order.append(task_id)
        return orig_execute(task_id, *args, **kwargs)
        
    scheduler.execute_task = spy_execute
    
    # Run graph with TASK-003 as force task (should execute first among ready tasks)
    # Since dependencies are computed sequentially by default (TASK-001 -> TASK-002 -> TASK-003),
    # let's clear dependencies to make them all ready immediately
    for tid, t in scheduler.graph["tasks"].items():
        t["dependencies"] = []
        
    scheduler.execute_graph(force_tasks=["TASK-003"])
    
    # TASK-003 must be executed first
    assert executed_order[0] == "TASK-003"

def test_idle_agent_reused_before_recruitment():
    planner = AdaptiveTeamPlanner()
    raw_tasks = [
        {"name": "task 1", "role": "development", "locks": []}
    ]
    agents, graph, _ = planner.plan_team_and_graph("FEAT-999", raw_tasks)
    metrics = SchedulerMetrics()
    scheduler = RuntimeScheduler(agents, graph, metrics)
    
    # Set existing backend agent to IDLE
    assert "AGENT-BACKEND-001" in scheduler.agents
    scheduler.agents["AGENT-BACKEND-001"]["status"] = "IDLE"
    
    # Clear dependencies to make TASK-001 ready
    scheduler.graph["tasks"]["TASK-001"]["dependencies"] = []
    
    # Reset recruitment decisions list
    scheduler.recruitment_decisions = []
    
    # Run execution
    scheduler.execute_graph()
    
    # Existing idle agent must be reused: no recruitment should happen
    recruited_actions = [d for d in scheduler.recruitment_decisions if d["status"] == "recruited"]
    assert len(recruited_actions) == 0
