# Specification – Interactive Runtime Selection Upgrade (QUICK-011)

This specification defines the audit findings and design plan to transition the AI Skill Framework from text-only prompts to interactive selection using the central runtime.

## 1. Audit Results

We verified that:
- `prompt_select(question, options, default)` exists in `skills/workflow-runtime/scripts/utils.py`.
- No CLI command exposes this function currently under a `prompt select` subcommand.
- Many SKILL.md files (e.g. `initialize-workflow`, `software-development-workflow`, `orchestrator`, `quick-fix`, `quick-feature`, `implementation-to-release`) use plain-text suggestions or free-form prompts instead of invoking the interactive select CLI command.

## 2. Proposed Changes

### A. CLI Command Addition
We will add a new CLI parser command `prompt` with subaction `select`:
- Arguments:
  - `--question` (required)
  - `--options` (required, pipe-separated e.g. `"Option A|Option B"`)
  - `--default` (optional)
- Implementation:
  - Calls `prompt_select(args.question, options_list, args.default)`.
  - Prints ONLY the selected value to stdout.

### B. Skill Files Update
We will update all SKILL.md files in the repository (and their `.agents/` counterpart copies) to replace manual text selection prompts with the new CLI interactive select commands:
1. `initialize-workflow`: Choose permission modes, choose sandbox or full_access.
2. `software-development-workflow`: Choose next step, choose continue/cancel.
3. `orchestrator`: Choose execution mode, choose parallel vs sequential, choose re-split, choose cancel.
4. `blueprint-to-implementation`: Choose Git branch action (Continue on current branch | Create new branch | Stop).
5. `implementation-to-release`: Choose release action (Continue | Cancel).
6. `Suggestion Gate (Next Skill Suggestions)`: Choose next skill or confirm suggested workflow interactively when suggestions are classified.

### C. Safe Defaults
- Destructive actions and unrestricted permissions default to `Stop` or `Cancel`.
- Parallel implementation defaults to `Run Sequentially`.
- Overwriting/Git actions default to `Cancel` or `Stop`.

## 3. Verification Plan

### Automated Tests
- Create `skills/workflow-runtime/tests/test_prompt.py` verifying:
  - `prompt select` CLI command execution.
  - Fallback to default when stdin is unavailable.
  - Exact text choice match.
  - Numeric index choice match.
  - TESTING=1 behavior.
