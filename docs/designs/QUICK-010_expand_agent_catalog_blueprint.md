---
artifact_type: blueprint
feature_id: QUICK-010
workflow: quick-feature
status: draft
---

# Technical Design Blueprint – Expand the Agent Catalog (QUICK-010)

This Design Blueprint specifies the schema, agent files, and integration strategy for expanding the core agent system into a multi-agent catalog.

## 1. Specialist Agent Metadata Specification

Every agent file in the `agents/` and `.agents/agents/` directories will have YAML frontmatter containing:
1. `name`: Agent name.
2. `role`: Concise summary.
3. `responsibilities`: Detailed responsibilities.
4. `artifact_ownership`: Directory or files owned.
5. `allowed_reads`: Read access scopes.
6. `allowed_writes`: Write access scopes.
7. `forbidden_actions`: Forbidden actions.
8. `input_contract`: Expected input structure.
9. `output_contract`: Expected output structure.
10. `handoff_target`: Handoff target agent name.
11. `done_criteria`: Condition for completion.
12. `can_run_in_parallel`: Boolean.
13. `agent_category`: Group name.
14. `phase`: Workflow phase.
15. `required_skills`: List of skills.
16. `required_memory`: Boolean.
17. `required_rag_context`: Boolean.
18. `runtime_requirements`: List of system requirements.

## 2. Dynamic Selection in Orchestrator

The Orchestrator's [SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/orchestrator/SKILL.md) will be updated to include the dynamic selection table based on task complexity and technology keywords:
- **Frontend changes**: Add `frontend-architect` and `frontend-developer` dynamically.
- **Backend changes**: Add `backend-architect` and `backend-developer` dynamically.
- **Database changes**: Add `database-architect` and `database-developer` dynamically.
- **Release activities**: Add `version-manager` and `changelog-manager` dynamically.

## 3. Validation Logic Updates in `agent_routing.py`
We will update `agent_routing.py` to:
- Enforce the 18-attribute YAML frontmatter fields (17 spec properties + `name`).
- Warn or error on missing attributes during validation.

## 4. Test Design
Wrote unit tests `test_catalog.py` to assert:
- All 35 specialist markdown files exist and contain valid frontmatter.
- Agent properties map perfectly without spelling errors.
