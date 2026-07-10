<!-- docs/plans/FEAT-019_selectable_execution_mode_plan.md -->

---
feature_id: FEAT-019
feature_name: User Selectable Execution Mode (Parallel vs Sequential)
status: draft
stage: planning
created_at: 2026-07-07
updated_at: 2026-07-07
previous_artifact: ../brainstorming/FEAT-019_selectable_execution_mode.md
next_artifact: ../designs/FEAT-019_selectable_execution_mode_blueprint.md
---

# Implementation Plan – User Selectable Execution Mode (Parallel vs Sequential)

## 1. Scope & Impact Analysis
- **Scoping**: Refactor the Orchestrator to support user-controlled Parallel vs Sequential execution modes. Avoid automatic selection.
- **Affected Files**:
  - `AI_RULES.md`
  - `.agents/AI_RULES.md`
  - `skills/orchestrator/SKILL.md`
  - `.agents/skills/orchestrator/SKILL.md`
  - `.agents/skills/workflow-runtime/scripts/workflow_runtime.py`
  - `.agents/skills/resume-workflow/SKILL.md`
  - `docs/plans/FEAT-019_selectable_execution_mode_plan.md`

## 2. Step-by-Step Task Decomposition
- **Task 1: Rule & Policy Update**
  - Append the "User Execution Mode Policy" to Rule 19 in `AI_RULES.md` and `.agents/AI_RULES.md`.
- **Task 2: CLI Runtime Command Extensions**
  - Update `workflow_runtime.py` to support new subcommands under `execution`:
    - `execution recommend --mode <parallel|sequential> --reason <reason>`
    - `execution mode --mode <parallel|sequential> [--approve]`
    - `execution summary`
  - Extend the `execution-plan.json` schema to include: `execution_mode`, `recommended_mode`, `recommended_reason`, `approved`.
  - Extend the `parallel-tasks.json` schema to support task `execution_group`.
- **Task 3: Refactor Orchestrator Skill**
  - Modify `skills/orchestrator/SKILL.md` to define the user selection prompt format (Parallel, Sequential, Re-split, Cancel) and explain task scheduling for Option 1 and Option 2.
- **Task 4: Resume workflow checks**
  - Modify resume check logic to read `execution-plan.json` and restore tasks state without prompting the user if `approved` is true.
- **Task 5: Documentation & Testing**
  - Update `USAGE.md` and `README.md`.
  - Add Python test cases in `test_runtime.py` covering all execution modes, recommendations, resume logic, and lock validations.

## 3. Test Strategy & Verification Plan
- **Automated Tests**:
  - Run `python3 .agents/skills/workflow-runtime/tests/test_runtime.py` to verify CLI command updates.
- **Manual Verification**:
  - Call `/orchestrate` with sample goal to test the choice prompt interface.

## 4. Rollback Plan
- **Rollback Strategy**:
  - If errors occur during execution, tasks in `parallel-tasks.json` are marked as `failed`, lock files are released, and the orchestrator state is reset to pending.
