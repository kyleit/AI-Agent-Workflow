<!-- File path: docs/plans/FEAT-004_claude_xml_tags_prompts_plan.md -->

---
feature_id: FEAT-004
feature_name: Claude-Optimized XML Tag Prompts & Tool Execution
status: reviewed
stage: planning
created_at: 2026-07-04
updated_at: 2026-07-04
previous_artifact: ../brainstorming/FEAT-004_claude_xml_tags_prompts.md
next_artifact: ../designs/FEAT-004_claude_xml_tags_prompts_blueprint.md
---

# FEAT-004: Claude-Optimized XML Tag Prompts & Tool Execution

## Objective
- Establish XML tag boundary guidelines inside the AI Skill Framework policies and prompts.
- Demarcate key input/output blocks inside core skill files to prevent context confusion and improve instruction-following precision when running under Claude.

## Scope
### Included
- Adding standard XML tag definitions (e.g. `<instructions>`, `<file_content>`) to `AI_RULES.md`.
- Updating the prompt boundaries inside core skills to make use of these tags.
- Verifying that XML encapsulation works uniformly across other models (such as Gemini).

### Excluded
- Changing actual script behaviors or tool interfaces.
- Generating model-specific dynamically compiled prompts.

## Project Impact
- **Impacted Areas**: Global policy guidelines (`AI_RULES.md`), core skill instructions prompts.

## Dependencies
- Core skill templates.
- Global rules guidelines file (`AI_RULES.md`).

## Risks
- **Risk**: Over-complicating prompt files makes them hard for human developers to read or edit.
- **Mitigation**: Use simple, logical XML tag names that fit cleanly within the existing Markdown outline.

## Acceptance Criteria
- [ ] `AI_RULES.md` has a dedicated section for prompt XML boundary tagging.
- [ ] Core implementation skills (like `blueprint-to-implementation` and `fast-fix`) are updated with XML wrapping markers.
- [ ] Verifications confirm Gemini and Claude parse instructions without syntax confusion.

## Deliverables
- Updated `AI_RULES.md` policy document.
- Updated core skill prompt instruction files.

## Estimated Complexity
- **Low**: Relies on prompt text reorganization and documentation formatting changes.

## Recommended Blueprint Focus
- Layout optimization for XML tag wrappers to ensure zero impact on markdown parsing.

## Recommended Next Skill
/blueprint
