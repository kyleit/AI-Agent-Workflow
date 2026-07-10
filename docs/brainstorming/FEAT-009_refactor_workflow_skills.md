<!-- docs/brainstorming/FEAT-009_refactor_workflow_skills.md -->

---
feature_id: FEAT-009
feature_name: Refactor AI Workflow Skills
status: draft
stage: brainstorming
created_at: 2026-07-06
updated_at: 2026-07-06
previous_artifact: None
next_artifact: ../plans/FEAT-009_refactor_workflow_skills_plan.md
---

# Master Requirement Document – Refactor AI Workflow Skills

## 1. Feature ID & Name
- **Feature ID**: FEAT-009
- **Feature Name**: Refactor AI Workflow Skills

## 2. Original Idea
Refactor the entire AI Workflow Skills repository to significantly reduce token usage while preserving 100% of the current behavior. This is a behavior-preserving refactor, NOT a workflow redesign.

## 3. Business Problem
- **Problem**: The skill files (`SKILL.md` documents under `skills/` and `.agents/skills/`) contain heavily duplicated policy descriptions (such as Git workflow, Approval gate, Memory-First rules) and explanation templates. This causes massive token overhead when the agent loads multiple skill files into its context.
- **Why it matters**: Higher token overhead increases operational costs, slows down agent execution speed, and reduces context window room for actual code changes and diagnostics.
- **Who is affected**: AI Coding agents and developers running the workflow framework in local IDE sessions.
- **Expected outcome**: Shorter, clean skill files referencing global policies in `AI_RULES.md` and containing only necessary local declarations. This should reduce the overall skills payload size by 40%–60%.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Every skill file must reference central policies in `AI_RULES.md` (specifically for Git, Memory, RAG, Verification, and Approval gates) instead of duplicating their explanations.
  - FR-02: Every skill file must keep its exact workflow sequence, required checkpoint values, and inputs/outputs.
  - FR-03: Every skill file must keep its progressive session update declarations (atomically updating `.agents/.session.json`).
- **Non-functional Requirements**:
  - NFR-01: Behavior-preserving: All skills must continue to execute identically from the user and orchestrator's perspective.
  - NFR-02: Zero breaking changes for the VS Code Visualizer companion extension.
- **Technical Constraints**:
  - TC-01: File names, command tags, checkpoint numbering, and session JSON schemas must remain exactly as defined.
  - TC-02: Maintain prompt reliability: Crucial keywords like `MUST`, `SHALL`, `REQUIRED`, and `STOP` must not be optimized away.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Are checkpoints allowed to change? | No, numbering and transitions must remain identical. |
| Can we combine or merge skills? | No, keep all 26 skills separate. |
| Where do shared policies live? | In `AI_RULES.md` (which is already loaded as a global system rule). |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready (>= 85)

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///e:/Cloud/_protected/agents/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: AI Skill Framework. Source skills are under `skills/`, synced to `.agents/` via `update.ps1`.

## 8. Existing Modules & Services
| Module/Service | Location |
|---|---|
| Global Rules | [AI_RULES.md](file:///e:/Cloud/_protected/agents/AI_RULES.md) |
| Skills Directory | [skills/](file:///e:/Cloud/_protected/agents/skills/) |

## 9. Solution Options Evaluated

### Option A: Extract Duplications into AI_RULES.md (Centralized Policies)
- **Overview**: Move all common policies (Git, Approval, Memory, RAG, Testing, Artifact, Session) to `AI_RULES.md`. In each `SKILL.md`, replace long policy explanations with clean section links and concise local boundaries.
- **Advantages**: Keeps skill prompts clean, reduces tokens by ~100K per full reload, maintains 100% compliance.
- **Disadvantages**: None.
- **Complexity**: Medium (requires editing 26 skills).
- **Risk**: Low (behavior-preserving).
- **Performance**: High (major token savings).

### Option B: Keep skills as-is
- **Overview**: Do not refactor skills, maintaining current large payload sizes.
- **Disadvantages**: Waste of tokens and high latency.

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Medium | None |
| Risk | Low | None |
| Performance | High | Low |
| Maintainability | High | Low |

## 11. Selected Solution
- **Choice**: Option A — Extract Duplications into AI_RULES.md.
- **Why Selected**: Fits the prompt requirements perfectly, saves maximum tokens while maintaining full system reliability.

## 12. Risks & Assumptions
- **Assumptions**: The system continues to load `AI_RULES.md` along with individual skill instructions.

## 13. Acceptance Criteria
- [ ] Refactor all 26 skills under `skills/` to remove duplicated policy explanations.
- [ ] Every skill keeps its required checkpoint checks, inputs/outputs, and progressive state JSON updates.
- [ ] Runs `update.ps1` to sync changes to `.agents/`.
- [ ] Verification check runs `doctor.ps1` with zero errors.

---

## 14. Final Planning Prompt

### Purpose
Input for `brainstorming-to-plan` to design the refactoring task list.

### Problem Statement
Skills contain duplicate policy explanations, leading to large token overhead.

### Objectives & Selected Solution
Centralize all policy explanations in `AI_RULES.md`, keeping each skill file slim and focused on its specific execution steps.
