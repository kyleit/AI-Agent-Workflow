# Audit – Legacy Global Checkpoint Blocking Defect

## 1. Problem Description

The AI Engineering Workflow Framework (AIWF) previously utilized a legacy global checkpoint model where all workflow session states were stored directly under `.agents/state/`. This model assumed a single linear execution thread.

When a parent workflow (e.g. `FEAT-113`) advanced to checkpoint 10 and completed, the file `.agents/state/workflow.json` remained updated at checkpoint 10. When starting a child workflow (e.g. `QUICK-009`) or a new subagent task, the validation check failed with:

```text
checkpoint validation failed (current=10, required=exactly 2)
```

Because the checkpoint state was global and non-isolated, the framework blocked any new or lower-checkpoint workflows from initiating or executing.

## 2. Legacy Gate Inventory & Conflict Points

We identified the following conflict points during our audit:
- `.agents/state/workflow.json`: Legacy global file containing active workflow checkpoint, types, and parent-child linkages.
- `.agents/state/approvals.json`: Legacy global file storing blueprint, spec, and release approvals.
- `.agents/state/usage.json`: Legacy global file tracking token usage.
- `.agents/state/agents.json`: Legacy global file listing running, queued, and blocked agents.
- `.agents/state/locks.json` & `handoffs.json`: Legacy global orchestrator files preventing concurrency.

## 3. Migration Strategy

The migration redirects all scoped workflow data access to `.agents/state/work-items/<work_item_id>/` when a work item is active, while maintaining backward-compatible automatic state migration.
