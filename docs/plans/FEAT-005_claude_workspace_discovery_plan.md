<!-- File path: docs/plans/FEAT-005_claude_workspace_discovery_plan.md -->

---
feature_id: FEAT-005
feature_name: Workspace & Global Customization Discovery for Claude
status: reviewed
stage: planning
created_at: 2026-07-04
updated_at: 2026-07-04
previous_artifact: ../brainstorming/FEAT-005_claude_workspace_discovery.md
next_artifact: ../designs/FEAT-005_claude_workspace_discovery_blueprint.md
---

# FEAT-005: Workspace & Global Customization Discovery for Claude

## Objective
- Guide Claude Desktop and Claude Code CLI developers on how to reference project rules (`AGENTS.md`) and custom skills from the `.agents/` repository layout.
- Standardize discovery setups for Claude environments.

## Scope
### Included
- Writing clear setup instructions in `INSTALL.md` for symlinking local workspace skills to Claude configuration directories.
- Documenting standard global config directories for Claude CLI/Desktop tools on Windows, macOS, and Linux.
- Verifying manual setup flows for active developer environments.

### Excluded
- Auto-writing directly to Claude system config files to prevent file corruption risks.

## Project Impact
- **Impacted Areas**: Setup and installation documentation (`INSTALL.md`), environment configuration instructions.

## Dependencies
- Standard repository installation manual (`INSTALL.md`).
- Environment configuration parameters.

## Risks
- **Risk**: Claude tools updating their configuration specifications, rendering instructions obsolete.
- **Mitigation**: Focus on standard OS symlink commands pointing to local `.agents/skills` structures.

## Acceptance Criteria
- [ ] `INSTALL.md` contains a structured guide for integrating with Claude.
- [ ] Integration instructions are validated on Windows (PowerShell) and Unix (Shell) systems.
- [ ] Global CLI warnings recommend looking at Claude integration guide when Anthropic credentials are configured.

## Deliverables
- Updated Installation Guide file.
- Updated project documentation referencing Claude custom configurations.

## Estimated Complexity
- **Low**: Documentation and configuration layout changes.

## Recommended Next Skill
/blueprint
