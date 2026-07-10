---
artifact_type: fix-spec
issue_id: FIX-014
workflow: quick-fix
status: pending
---

# Fix Specification – Parallel Only During Implementation

## 1. Issue Description
The previous Orchestrator selectable execution mode upgrade was too broad, applying parallel recommendations and user choice menus to all phases. This fix restricts parallel execution capabilities exclusively to the implementation/execution phase. All preceding phases (discovery, brainstorming, planning, blueprint generation, ADR creation, memory updates, RAG search, project discovery, workflow initialization, and approval gates) and downstream phases (release) must run strictly sequentially without prompting the user or allowing parallel workers.

## 2. Scope
- **In Scope**:
  - Restricting parallel recommendations and prompt choice gates exclusively to the start of the implementation phase.
  - Ensuring discovery, brainstorming, planning, blueprint generation, ADR creation, memory updates, RAG search, project discovery, workflow initialization, approval gates, and release run sequentially.
  - Adding checks in the runtime to enforce that parallel execution mode cannot start without an approved blueprint/spec, and cannot start before the implementation phase.
  - Updating execution-plan schema and runtime session properties with:
    ```json
    {
      "implementation_execution_mode": "pending|parallel|sequential",
      "parallel_allowed_phase": "implementation",
      "parallel_allowed": true
    }
    ```
  - Ensuring file locks and conflict detection are still fully functional during parallel implementation.
  - Updating all documentation, schemas, and writing unit tests to cover phase scope constraints.

- **Out of Scope**:
  - Removing the Orchestrator or the selectable execution mode mechanism.
  - Removing file locking or write set conflict detection capabilities.
