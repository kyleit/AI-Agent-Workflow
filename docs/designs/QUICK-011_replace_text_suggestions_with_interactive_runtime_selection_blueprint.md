---
artifact_type: blueprint
feature_id: QUICK-011
workflow: quick-feature
status: draft
---

# Technical Design Blueprint – Interactive Runtime Selection Upgrade (QUICK-011)

This Design Blueprint specifies the code modifications to support the interactive prompt selection mechanism.

## 1. CLI Parser Integration

In [workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py), we will add a new CLI command group `prompt` with a subcommand `select`:
```python
    prompt_p = subparsers.add_parser("prompt")
    prompt_sub = prompt_p.add_subparsers(dest="subaction", required=True)
    select_p = prompt_sub.add_parser("select")
    _ = select_p.add_argument("--question", required=True, type=str)
    _ = select_p.add_argument("--options", required=True, type=str)
    _ = select_p.add_argument("--default", type=str, default=None)
```

The handler `do_prompt` will:
1. Parse `--options` by splitting on `|`.
2. Invoke `prompt_select(args.question, options_list, args.default)`.
3. Print only the selected option to stdout.

## 2. Skill Document Prompts Conversion

The following Skill files will be updated to replace text instructions with the command pattern:
- **[initialize-workflow/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/initialize-workflow/SKILL.md)**:
  Use:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Choose permission mode:" --options "sandbox|full_access" --default "sandbox"
  ```
- **[orchestrator/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/orchestrator/SKILL.md)**:
  Use:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Choose execution mode:" --options "Run implementation in Parallel where safe|Run implementation Sequentially|Re-split implementation tasks|Cancel" --default "Run implementation Sequentially"
  ```
- **[blueprint-to-implementation/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/blueprint-to-implementation/SKILL.md)**:
  Use:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Choose Git branch action:" --options "Continue on current branch|Create new branch|Stop" --default "Stop"
  ```
- **[implementation-to-release/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/implementation-to-release/SKILL.md)**:
  Use:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Choose release action:" --options "Continue|Cancel" --default "Cancel"
  ```
- **Suggestion Gate**:
  If classifying next step, use:
  ```bash
  python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Which workflow should be used?" --options "Quick Fix|Quick Feature|Standard SDLC|Brainstorming|Cancel" --default "Cancel"
  ```

## 3. Automated Verification Tests

Create `skills/workflow-runtime/tests/test_prompt.py` verifying selection lifecycle, including fallback, index input, raw text matching, and invalid options.
