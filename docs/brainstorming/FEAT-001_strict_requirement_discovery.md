---
feature_id: FEAT-001
feature_name: Refactor idea-to-planning-prompt into Strict Requirement Discovery & Feature Decomposition Skill
status: approved
stage: brainstorming
created_at: 2026-07-03
updated_at: 2026-07-03
previous_artifact: None
next_artifact: ../plans/FEAT-001_strict_requirement_discovery_plan.md
---

# Master Requirement Document – Refactor idea-to-planning-prompt

## 1. Original Idea
Refactor `idea-to-planning-prompt` from an interactive solution discovery tool into a strict requirement discovery and feature decomposition skill. The skill must be read-only, support multi-feature decomposition, evaluate 2-3 solution options with trade-offs, get user decision, and generate brainstorming documents only.

## 2. Requirement Discovery
- **Problem**: The current implementation of `idea-to-planning-prompt` is too prone to making code changes directly or automatically executing downstream planning/blueprint/implementation tasks. Additionally, it does not support multi-feature decomposition when a user provides a compound input.
- **Why**: Ensuring a clean separation of concerns prevents the agent from starting code implementation with incomplete, unstructured requirements.
- **Who**: Software developers and engineering agents using the AI Skill Framework.
- **Outcome**: A strict, read-only requirement discovery skill that decomposes compound inputs, compares architectures, and produces high-quality brainstorming documents.
- **Constraints**: Absolutely no code edits or other workspace mutations outside `docs/brainstorming/`.

## 3. Requirement Analysis & Gap Analysis
- **Functional Requirements**:
  - Auto-decomposition of compound inputs into independent features.
  - Option to generate multiple brainstorming documents or merge/select features.
  - Option selection gate (pause execution until user explicitly selects option 1, 2, 3, or customized).
  - Stop rule: Never execute downstream skills, memory updates, or git commits.
- **Non-functional Requirements**:
  - High fidelity in solution option evaluations (complexity, risks, performance metrics).
  - Strict compliance with read-only constraint.

## 4. Existing Project Context
- **Memory Baselines**: `project-summary.md` and RAG checks are consulted.
- **Existing Architecture**: The skill is located in `skills/idea-to-planning-prompt/SKILL.md`.

## 5. Architectural Options Evaluated
### Option A: Refactor SKILL.md Instructions (Selected)
- **Overview**: Rewrite the instructions inside `skills/idea-to-planning-prompt/SKILL.md` to define the strict requirement discovery process, new workflow, feature decomposition gate, solution options comparisons, and stop rules.
- **Pros**: Direct, lightweight, doesn't require extra code components.
- **Cons**: Relies on LLM instruction following (fully acceptable for prompt-based skills).
- **Complexity**: Low
- **Risk**: Low

## 6. Solution Comparison
| Criteria | Option A |
|---|---|
| Complexity | Low |
| Performance | Instant |
| Maintainability | Easy |
| Scalability | High |

## 7. Selected Architecture
- **Choice**: Option A
- **Architectural Reason**: The skill framework is designed around prompt-based instruction sets (`SKILL.md` files). Refactoring the prompt instructions is the standard way to redefine a skill's behavior.

## 8. Impact & Risk Analysis
- **Blast Radius**: `skills/idea-to-planning-prompt/SKILL.md` and `SKILLS.md`.
- **Identified Risks**: LLM bypassing constraints. (Mitigated by extremely clear negative guardrails and "STRICTLY READ-ONLY" warnings).

## 9. Acceptance Criteria
- [ ] Multi-feature decomposition is clearly defined in the workflow.
- [ ] Direct code changes or running tests/git commands are strictly forbidden.
- [ ] Pauses and stops are gated explicitly.
- [ ] Output brainstorming document matches the 10-section structure.

---

## 10. Final Planning Prompt
This is the brainstorming document that guides the refactoring of `idea-to-planning-prompt`.
- Recommended Next Skill: `planning-prompt-to-plan`
