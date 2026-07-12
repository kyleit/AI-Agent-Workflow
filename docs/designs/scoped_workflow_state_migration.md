# Design – Scoped Workflow State Migration

This design document outlines the transition of the AIWF runtime state from a legacy linear global model to a scoped, multi-work-item architecture.

## 1. Multi-Work-Item Scoped State Layout

To support concurrent multi-agent executions, state files are stored in directory paths parameterized by the active `work_item_id`.

### Layout:
```text
.agents/state/
├── active-work-items.json (Global active ID & metadata map)
├── context.json           (Global workspace/git context)
├── runtime.json           (Global runtime controller state)
└── work-items/
    ├── <work_item_id_1>/
    │   ├── workflow.json
    │   ├── approvals.json
    │   ├── usage.json
    │   ├── agents.json
    │   ├── locks.json
    │   ├── handoffs.json
    │   ├── timeline.jsonl
    │   └── orchestrator/
    │       ├── objective.json
    │       ├── queue.json
    │       ├── task_graph.json
    │       └── checkpoints/
    └── <work_item_id_2>/
        └── ...
```

## 2. Dynamic Resolution & Automatic Migration

1. **Resolution**: `get_active_work_item_id()` reads `AIWF_ACTIVE_WORK_ITEM` or `active-work-items.json`.
2. **Automatic Migration**: If a scoped workflow data file (e.g. `workflow.json`) does not exist inside `.agents/state/work-items/<work_item_id>/`, but a legacy global file exists in `.agents/state/`, the state store copies and scopes it on the first read.

## 3. CLI Argument Scoping

Subcommands (`validate`, `start`, `step`, `complete`, `fail`, `active-workflow`, `resume`, `orchestrator`) accept `--work-item` and `--workflow` options.
An interceptor sets `os.environ["AIWF_ACTIVE_WORK_ITEM"]` and registers the work item in `active-work-items.json` before execution.

## 4. Visualizer Panel Addition

- Visualizer reads `.agents/state/active-work-items.json` to extract all created work items and the current active ID.
- Displays a new "Work Items" sidebar tab presenting all work items in a card format, along with workspace runtime info.
