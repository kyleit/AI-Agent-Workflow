---
artifact_type: quick-feature-spec
feature_id: QUICK-008
workflow: quick-feature
status: pending
---

# Mini Feature Specification – Update Interactive Docs with Orchestrator Workflow

## 1. Feature Goal
Update the interactive documentation (`interactive-docs`) in the project to include the Orchestrator skill (`/orchestrate`) and document the Orchestrated SDLC flow, highlighting the restricted scope of parallel execution during implementation.

## 2. Scope
- **In Scope**:
  - Updating `interactive-docs/docs-assets/skills-data.js` to add the `orchestrator` skill (`/orchestrate`).
  - Updating `interactive-docs/index.html` to add a new tab button "4. Quy trình Điều phối (Orchestrator)" and the corresponding `flowOrchestrate` panel describing the orchestrated workflow timeline and parallel execution constraints.
  - Ensuring the styling and interactive elements function properly.
- **Out of Scope**:
  - Modifying code logic of the Orchestrator or CLI runtime scripts themselves.
  - Changing the visualizer extension code.
