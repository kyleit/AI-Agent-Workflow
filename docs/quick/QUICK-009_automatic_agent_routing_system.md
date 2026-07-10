# Specification – Automatic Agent Routing System (QUICK-009)

This specification documents the audit findings and proposed design for implementing the Automatic Agent Routing System in the AI Engineering Workflow Framework.

## 1. Audit Results

We performed a comprehensive audit of the framework:

1. **`MANIFEST.json`**:
   - Currently lists skills with only basic metadata (`name`, `command`, `aliases`, `category`, `tags`).
   - **Missing**: `owner_agent`, `specialist_agents`, `phase`, and `execution_mode` definitions.
2. **`AGENTS.md`**:
   - Currently contains only global workflow rules and policies.
   - **Missing**: Structured definitions for `owner_agent`, `specialist_agents`, and agent capabilities (planner, architect, coder, reviewer, release-manager).
3. **Agent Definitions under `agents/`**:
   - Currently exists as separate markdown files (`planner.md`, `architect.md`, `coder.md`, `reviewer.md`, `release-manager.md`).
   - **Missing**: Structured metadata/frontmatter properties (Role, Responsibilities, Artifact Ownership, Allowed Reads, Allowed Writes, Forbidden Actions, Input Contract, Output Contract, Handoff Target, Done Criteria, Agent Category, Supported Phases, Supported Skills, Can Run Parallel, Can Analyze Only, Can Modify Source, Produces Canonical Artifact).
4. **Orchestrator & Workflow Runtime**:
   - Current orchestrator loop does not load routing metadata dynamically.
   - **Missing**: Verification logic, CLI route-resolving subcommands, validation rules, and automated unit tests.

## 2. Problems Found
- **Duplication & Hardcoding**: The framework doesn't have a single source of truth routing table, meaning downstream tools must guess or hardcode routing names.
- **Inconsistent metadata**: No YAML metadata block exists inside the markdown files in `agents/`.
- **Validation Gaps**: No mechanism currently prevents cyclic routing, duplicate ownership, or unreachable skills/orphaned agents.

## 3. Proposed Solution

### A. Extend `MANIFEST.json`
Update each skill to define:
- `owner_agent`: Exactly one owner (e.g., `planner`, `architect`, `coder`, `reviewer`, `release-manager`).
- `specialist_agents`: Array of specialist agents.
- `phase`: SDLC phase (e.g., `brainstorming`, `planning`, `blueprint`, `implementation`, `debug`, `verification`, `release`).
- `execution_mode`: Execution type (e.g., `sequential`, `parallel`).

### B. Add Frontmatter to `agents/*.md`
Ensure all 5 agent files have standard YAML frontmatter containing all 18 attributes specified in Step 6.

### C. Create `agent_routing.py`
Implement a Python helper module to:
- Resolve skills to owner and specialists.
- Validate that all owners/specialists exist and prevent orphans, cycles, and duplicates.

### D. Update CLI and Orchestrator
- Extend CLI `workflow_runtime.py` with `routing` command:
  - `workflow_runtime.py routing list` (prints the routing table).
  - `workflow_runtime.py routing validate` (runs validation rules and fails on errors).
- Update the Orchestrator SKILL.md to detail routing resolution rules.

## 4. Verification Plan

### Automated Tests
- Wrote new unit tests `test_routing.py` to:
  - Assert every skill has one owner.
  - Verify owners and specialist agents exist in the agent directory.
  - Verify that routing resolves correctly.
  - Detect invalid/cyclic routing configuration.
