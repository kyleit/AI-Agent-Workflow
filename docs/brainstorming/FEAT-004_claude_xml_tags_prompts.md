---
feature_id: FEAT-004
feature_name: Claude-Optimized XML Tag Prompts & Tool Execution
status: draft
stage: brainstorming
created_at: 2026-07-04
updated_at: 2026-07-04
previous_artifact: None
next_artifact: ../plans/FEAT-004_claude_xml_tags_prompts_plan.md
---

# Master Requirement Document – Claude-Optimized XML Tag Prompts & Tool Execution

## 1. Feature ID & Name
- **Feature ID**: FEAT-004
- **Feature Name**: Claude-Optimized XML Tag Prompts & Tool Execution

## 2. Original Idea
I want to upgrade these skills to support Claude (tôi muốn nâng cấp các skills này hỗ trợ cho claude). This feature addresses prompt structuring to support XML tags inside skills and policy files.

## 3. Business Problem
- **Problem**: When running inside Claude (e.g. Claude Code or desktop integrations), markdown-only instructions are sometimes parsed with lower fidelity or cause hallucination when project files are mixed in the context. Claude performs at its highest instruction-following levels when structural blocks are demarcated with XML tags.
- **Why it matters**: Improving Claude's parsing structure results in higher compliance with framework policies (e.g., approval gates, git branch rules).
- **Who is affected**: AI Coding Agents running under Claude models.
- **Expected outcome**: Clear rules and template conventions utilizing XML tags inside `AI_RULES.md` and skills prompts.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Update `AI_RULES.md` to define standard XML tags to use when presenting code blocks or plans (e.g. `<system_prompt>`, `<file_diff>`, `<instruction>`).
  - FR-02: Upgrade core skills (such as `blueprint-to-implementation` and `fast-fix`) to support wrapped XML tags when feeding contexts to Claude.
- **Non-functional Requirements**:
  - NFR-01: Backwards compatibility: XML tags should not degrade Gemini/OpenAI performance (they are generally ignored or parsed successfully by these LLMs too).
- **Technical Constraints**:
  - TC-01: Must remain valid GitHub Flavored Markdown (GFM) text.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Should we convert the entire skill prompt to XML? | No, keep markdown format but embed XML tags to demarcate key data sections (e.g. `<code_context>`, `<plan>`). |
| Will this increase token counts? | Minimal overhead (a few tokens per tag), fully justified by precision gains. |

## 6. Requirement Readiness Score
- **Score**: 90/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: `project-summary.md` and `AI_RULES.md`.
- **Existing Architecture Summary**: Core policies are defined in `AI_RULES.md`, referenced by individual skills in `skills/`.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Global Policies | [AI_RULES.md](file:///e:/Cloud/_protected/agents/AI_RULES.md) | Defines the syntax and boundary rules for prompts. |
| Blueprint to Implementation | [skills/blueprint-to-implementation/SKILL.md](file:///e:/Cloud/_protected/agents/skills/blueprint-to-implementation/SKILL.md) | Standard implementation prompt wrapper. |
| Fast Fix | [skills/fast-fix/SKILL.md](file:///e:/Cloud/_protected/agents/skills/fast-fix/SKILL.md) | Standard fix prompt wrapper. |

## 9. Solution Options Evaluated

### Option A: Universal XML Integration (Selected)
- **Overview**: Embed XML tag containers within standard GFM markdown instructions inside the existing policies and skills.
- **Advantages**: Single set of files; works natively on Claude, Gemini, and GPT.
- **Disadvantages**: Minor formatting clutter in raw markdown reading.
- **Complexity**: Low
- **Risk**: Low
- **Performance**: High
- **Maintainability**: High
- **Compatibility**: High
- **Future Scalability**: High

### Option B: Conditional Prompts (Model-Specific Prompt Injection)
- **Overview**: Detect the active LLM (Gemini vs Claude) and dynamically inject XML tags at runtime.
- **Advantages**: Keeps raw prompt files clean for humans.
- **Disadvantages**: High implementation complexity; requires prompt compiler/template parser logic in wrappers.
- **Complexity**: High
- **Risk**: Medium

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Low | High |
| Risk | Low | Medium |
| Performance | High | Medium (compile overhead) |
| Maintainability | High | Low |
| Compatibility | High | Medium |
| Future Scalability | High | Medium |
| Development Cost | Low | High |

## 11. Selected Solution
- **Choice**: Option A
- **Why Selected**: Embedding XML tags natively in Markdown is fully compatible across all state-of-the-art LLMs, requires zero prompt compile engine overhead, and keeps development straightforward.
- **Trade-offs Accepted**: Markdown files will contain embedded XML wrappers which might look slightly busier to human eyes.
- **Technical Debt**: Minimal.
- **Risk Mitigation**: Test that Gemini does not break or get confused by the XML tags.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Other LLMs misinterpreting XML tags. -> Ensure standard Markdown formatting remains the primary skeleton.
- **Assumptions**:
  - A-01: Claude excels at parsing XML blocks within markdown structures.

## 13. Acceptance Criteria
- [ ] `AI_RULES.md` contains documented rules for XML tag wrappers.
- [ ] Core skills prompts are refactored to wrap inputs/outputs in tags like `<context>` and `<instructions>`.
- [ ] Execution verification shows Claude following boundaries correctly.

---

## 14. Final Planning Prompt

### Purpose
Provide a planning guideline for implementing Claude XML tags and prompts.

### Problem Statement
We need to introduce XML tag boundaries inside core prompts to support Claude's high-fidelity instruction parsing.

### Objectives
- Add guidelines for XML tags in `AI_RULES.md`.
- Wrap prompt instructions and input contexts in XML tags inside core skills.

### Verification Checklist
- [ ] docs/plans/FEAT-004_claude_xml_tags_prompts_plan.md generated and approved
- [ ] docs/designs/FEAT-004_claude_xml_tags_prompts_blueprint.md generated and approved
- [ ] Verification prompts execute correctly on Claude.
