<!-- File path: docs/plans/FEAT-021_script_first_execution_plan.md -->

---
feature_id: FEAT-021
feature_name: Script-First Execution Refactoring
status: reviewed
stage: planning
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../brainstorming/FEAT-021_script_first_execution.md
next_artifact: ../designs/FEAT-021_script_first_execution_blueprint.md
---

# FEAT-021: Script-First Execution Refactoring

## Objective
- To convert deterministic, repeatable, file-based, validation-based, and environmental tasks within the framework into script-first Python commands.
- To reduce token usage, prevent LLM output formatting errors, and support automated test coverage.

## Scope
### Included
- Audit and classification of all 19 framework skills into deterministic (Group A), hybrid (Group B), or LLM-driven (Group C).
- Implementation of Python scripts under `skills/workflow-runtime/scripts/` to handle initialization, resume, discovery, memory indexing, environment check, build verification, and release planning.
- Exposing subcommands via the `workflow_runtime.py` parser interface returning structured JSON data.
- Writing a comprehensive automated verification test suite checking all 17 scenarios requested.
- Documentation updates (README, USAGE, INSTALL, CHANGELOG, SKILLS, AI_RULES, AGENTS).

### Excluded
- Modifying LLM models, routing rules of the LLM provider, or visual frontend dashboard logic itself.

## Project Impact
- **Modules**: `Workflow Runtime` engine, all modular SDLC skills.
- **Config**: `.session.json` schema updates, `.agents/project-profile.json` structure validation.
- **Testing**: Test suite runner verification.

## Dependencies
- **Existing project components**: Python CLI wrapper structure, `project_memory` logic under `runtime/scripts/project_memory/`.

## Risks
- **Windows compatibility**: Command shell and subprocess calls might raise path separator or CP1252 encoding errors.
  * *Mitigation*: Enforce UTF-8 file reads/writes, and write clean cross-platform path normalization.

## Acceptance Criteria
- All 17 verification scenarios pass via automated testing.
- Every CLI subcommand returns structured JSON data containing status and outcome summaries.
- Reduced LLM instructions in `SKILL.md` files referencing the new script actions.

## Deliverables
- Main subcommands in `workflow_runtime.py`.
- Submodule scripts: `project_discovery.py`, `environment_health.py`, `validation_runner.py`, `release_manager.py`, and `memory/` submodule.
- Unit test suite script `test_script_first.py` under `skills/workflow-runtime/tests/`.
- Updated documentation.

## Estimated Complexity
- **High**: Requires rewriting the CLI command routing parser, refactoring 19 skill files, porting memory submodules, and implementing 17 test coverage scenarios.

## Recommended Blueprint Focus
- Focus on clean submodule routing, abstracting command outputs into a unified JSON format builder helper, and robust subprocess execution wrappers on Windows.

## Recommended Next Skill
/blueprint
