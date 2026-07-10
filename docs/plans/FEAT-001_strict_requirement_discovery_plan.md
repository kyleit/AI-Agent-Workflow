---
feature_id: FEAT-001
feature_name: Refactor idea-to-planning-prompt into Strict Requirement Discovery & Feature Decomposition Skill
status: approved
stage: planning
created_at: 2026-07-03
updated_at: 2026-07-03
previous_artifact: ../brainstorming/FEAT-001_strict_requirement_discovery.md
next_artifact: ../designs/FEAT-001_strict_requirement_discovery_blueprint.md
---

# Implementation Plan - Refactor idea-to-planning-prompt

## 1. Goal Description
Refactor the `idea-to-planning-prompt` skill inside the AI Skill Framework into a strict requirement discovery and feature decomposition skill. The refactored skill will act as a pure, read-only requirements tool.

## 2. Proposed Changes
- **Modify** `skills/idea-to-planning-prompt/SKILL.md` to incorporate the new strict requirement discovery workflow, feature decomposition gate, solution options comparisons, and stop rules.
- **Modify** `SKILLS.md` to update the skill description and example usage.

## 3. Verification Plan
- Verification using the framework's `doctor` command:
  - Command: `export PATH="$PATH:/Users/kyle/.local/share/aiwf/bin" && aiwf doctor`
- Manual check of all instruction blocks in `SKILL.md` to ensure they comply with the read-only constraints.
