---
artifact_type: blueprint
issue_id: FIX-014
workflow: quick-fix
status: draft
---

# Technical Design Blueprint – Parallel Only During Implementation

This blueprint details the scope corrections for multi-agent parallel execution. It restricts parallel execution to the implementation phase, ensuring discovery, brainstorming, planning, blueprint generation, ADR creation, memory updates, RAG search, project discovery, workflow initialization, and release phases are strictly sequential.

## 1. Proposed Code Changes

### [Component] Centralized Rules & Policies

#### [MODIFY] [AI_RULES.md](file:///Volumes/Kyle/AgentsProject/AI_RULES.md) & [.agents/AI_RULES.md](file:///Volumes/Kyle/AgentsProject/.agents/AI_RULES.md)
- Update Section 19 (**Multi-Agent Orchestration Policy**) items 7, 8, 9, 10 to document implementation-only parallel execution and choice timing at the start of implementation phase.

---

### [Component] Orchestrator Skill

#### [MODIFY] [SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/orchestrator/SKILL.md) & [.agents/skills/orchestrator/SKILL.md](file:///Volumes/Kyle/AgentsProject/.agents/skills/orchestrator/SKILL.md)
- Restrict parallel execution and DAG choice prompt exclusively to the beginning of Phase 6 (Implementation / Execute) after blueprint approval.
- Preceding phases (1-5) must run sequentially.
- Prompt text matches:
  ```text
  Implementation is ready.

  Choose execution mode:

  1. Run implementation in Parallel where safe
  2. Run implementation Sequentially
  3. Re-split implementation tasks
  4. Cancel
  ```

---

### [Component] CLI Runtime Engine

#### [MODIFY] [workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/.agents/skills/workflow-runtime/scripts/workflow_runtime.py)
- In `do_execution recommend`:
  - Set `"implementation_execution_mode": "pending"`.
  - Set `"parallel_allowed_phase": "implementation"`.
  - Set `"parallel_allowed": (session.get("checkpoint", 1) >= 5)`.
- In `do_execution mode`:
  - If `--mode parallel` is requested and `"parallel_allowed"` is `False` (i.e. checkpoint < 5), fail execution with status `1`.
  - Save `implementation_execution_mode` to `execution-plan.json`.
- In `do_execution summary`:
  - If `parallel_allowed` is `False`, print a notice that the current phase requires sequential execution.
- Update `sync_execution_state_to_session` and `do_compact` to output:
  - `implementation_execution_mode`
  - `parallel_allowed_phase`
  - `parallel_allowed`
  - Maintain `execution_mode` for backward compatibility.

---

### [Component] Resume Workflow Skill

#### [MODIFY] [SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/resume-workflow/SKILL.md) & [.agents/skills/resume-workflow/SKILL.md](file:///Volumes/Kyle/AgentsProject/.agents/skills/resume-workflow/SKILL.md)
- Update Step 5 (Restore Execution Plan) to read `"implementation_execution_mode"` and bypass prompt if approved.

---

### [Component] Documentation

#### [MODIFY] [README.md](file:///Volumes/Kyle/AgentsProject/README.md) & [USAGE.md](file:///Volumes/Kyle/AgentsProject/USAGE.md)
- Document scope correction of parallel execution in orchestration descriptions.

---

## 2. Test Plan

### Automated Tests
Modify `test_runtime.py` to add new test cases:
- `test_early_phases_always_sequential`: Verify that parallel execution is rejected if checkpoint < 5.
- `test_implementation_can_ask_parallel_or_sequential`: Verify that parallel execution is allowed at checkpoint 5.
- `test_locks_active_in_parallel_implementation`: Verify locking and conflict checks work.

### Manual Verification
- Simulate sequential execution during planning/blueprint and parallel execution during implementation.
