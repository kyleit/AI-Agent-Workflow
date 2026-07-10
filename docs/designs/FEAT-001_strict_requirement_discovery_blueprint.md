---
feature_id: FEAT-001
feature_name: Refactor idea-to-planning-prompt into Strict Requirement Discovery & Feature Decomposition Skill
status: approved
stage: blueprint
created_at: 2026-07-03
updated_at: 2026-07-03
previous_artifact: ../plans/FEAT-001_strict_requirement_discovery_plan.md
next_artifact: None
---

# Technical Design Blueprint - Refactor idea-to-planning-prompt

## 1. Architecture Decision Assessment
- **ADR Required**: No
- **Rationale**: The change is a direct instruction update inside the existing skill prompt definition (`SKILL.md`) and does not introduce new runtime components or systems.

## 2. Technical Specification
We will refactor `skills/idea-to-planning-prompt/SKILL.md` to enforce the following structure:
- **Header YAML**:
  `name: idea-to-planning-prompt`
- **Purpose**: Pure Requirement Discovery and Feature Decomposition.
- **Workflow (15 steps)**:
  1. User Input
  2. Issue Detection
  3. Feature Decomposition
  4. Requirement Discovery
  5. Requirement Analysis
  6. Gap Analysis
  7. Project Context Analysis
  8. Project Memory
  9. RAG Search
  10. Solution Analysis
  11. Architecture Analysis
  12. Generate Solution Options
  13. Recommend Best Option
  14. User Chooses
  15. Generate Brainstorming Document(s)
- **Rules & Guardrails**:
  - STRICTLY READ-ONLY: Never modify source code, edit project files, write tests, update memory, git operations, etc.
  - Pauses / Gates: Stopping after clarification questions or options generation.
  - Decomposes multiple features and asks user how to proceed.
- **Brainstorming Structure**: Standardized 10-section document in `docs/brainstorming/`.

## 3. Verification Plan
- Execution of `aiwf doctor` to ensure the integrity of the framework.
