# AI Workflow Runtime Engine CLI Reference Guide

This document lists the available commands, syntax, and options for `workflow_runtime.py`, which is the core engine controlling state, checkpoints, choice gates, and releases.

---

## Centralized Runtime CLI Commands

Every execution phase uses `python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py <command>`.

### 1. `init`
Initializes a new AI Engineering Workflow session in the target workspace.
- **Usage**:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py init
  ```

### 2. `permission`
Manages workspace permission modes.
- **Usage**:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py permission [sandbox | full_access]
  ```

### 3. `compact`
Truncates history and compactor entries in `.session.json` to keep token usage minimal and avoid context bloat.
- **Usage**:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py compact
  ```

### 4. `validate`
Validates checkpoints, specifications, and design artifacts.
- **Usage**:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint <checkpoint_number>
  ```

### 5. `start`
Marks the start of a workflow phase and transitions session status.
- **Usage**:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py start --skill <skill_name> --command <command> --checkpoint <target_checkpoint> --step "<step_description>"
  ```

### 6. `step`
Updates logs and records step progress within a running phase.
- **Usage**:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_name>" --log "<progress_message>"
  ```

### 7. `complete`
Marks a phase completed, sets the next skill/command, and transitions the checkpoint.
- **Usage**:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint <next_checkpoint> --step "Step Complete" --next-skill <next_skill_name> --next-command <next_command>
  ```

### 8. `fail`
Records a phase failure and pauses execution.
- **Usage**:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"
  ```

### 9. `choice`
Manages the interactive choice and approval protocol.
- **create**: Creates an approval gate.
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py choice create --id <choice_id> --title "<title>" --desc "<description>" --type [approval|select] --options "<option1|option2>"
  ```
- **wait**: Blocks and waits for user confirmation (displays choice prompt).
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py choice wait --id <choice_id>
  ```
- **read**: Reads the resolved choice selection.
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py choice read --id <choice_id>
  ```

### 10. `blueprint`
Registers and approves Technical Design Blueprints.
- **register**:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path <path_to_blueprint>
  ```
- **approve**:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path <path_to_blueprint> --approve
  ```

### 11. `discover`
Scans the workspace to profile the tech stack, default Git branch, and automatically generates `.agents/release.config.json` and `.agents/workflow.config.json` without overwriting existing customizations.
- **Usage**:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py discover
  ```

### 12. `release`
Coordinates release preflights and pipeline execution.
- **plan**: Prepares the release plan, checks if the workspace is clean, and identifies changed modules.
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py release plan
  ```
- **execute**: Executes the release pipeline (merging branch, executing module and global build/test commands, and pushing).
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py release execute [--approve]
  ```
