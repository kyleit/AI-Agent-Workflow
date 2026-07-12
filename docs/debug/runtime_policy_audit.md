# Audit Report: AIWF Runtime Policy Configuration

## 1. Objective
Audit the AIWF Runtime to determine whether a centralized Runtime Policy already exists, locate existing configurations, and plan migration/implementation.

## 2. Findings & Inventory

### Existing Scattered Configurations
1. **`skills/workflow-runtime/scripts/session.py`**:
   - Defines default dictionaries: `DEFAULT_RESOURCE_LIMITS`, `DEFAULT_TEST_EXECUTION`, and `DEFAULT_SPAWN_LIMITS`.
   - Uses `load_config_section` to load overrides from `.agents/workflow.config.json`.
2. **`skills/workflow-runtime/scripts/hierarchical_runtime.py`**:
   - Checks limits in `can_spawn_subagent()` using `load_config_section` for `"resource_limits"` and `"spawn_limits"`.
   - Enforces CPU percentage (`max_cpu_percent` defaulting to 85) and memory percentage (`max_memory_percent` defaulting to 80).
   - Enforces global subagent count limits (`max_total_subagents` defaulting to 8) and per-work-item limits (`max_subagents_per_work_item` defaulting to 4).
   - Enforces concurrency limit (`max_concurrency` defaulting to 4).
3. **`skills/workflow-runtime/scripts/workflow_runtime.py`**:
   - Coordinates pytest execution inside `do_test_action()`.
   - Uses `test_config = load_config_section("test_execution", DEFAULT_TEST_EXECUTION)`.
   - Hardcodes parallel worker count `["-n", "2"]` if `-n` is not provided.
4. **`extensions/visualizer/src/extension.ts`**:
   - Reads `orchestrator.json`, `runtime.json`, and `runtime-manager.json` but has no reference to any centralized runtime policy.

### Conclusion of Audit
No centralized, unified configuration file named `runtime-policy.json` exists in `.agents/config/` or anywhere else in the repository.

---

## 3. Implementation Plan Proposal
We will implement the canonical configuration `.agents/config/runtime-policy.json` and configure all runtime components to load limits from this file.

### Required Changes:
- **`session.py`**: Add schema validation, default policy constants, path helpers, and `load_runtime_policy()` functions.
- **`hierarchical_runtime.py`**: Read all subagent, concurrency, rate limits, and threshold checks from the new policy. Implement adaptive concurrency scaling.
- **`workflow_runtime.py`**: Update `do_init` to validate/load the policy, update `do_test_action` to use policy limits (workers, default mode, coalescing), and add new CLI commands: `aiwf runtime policy [validate|reset]`.
- **`extension.ts`**: Pass `runtime_policy` safely into the state payload sent to the Webview.
- **`webview.html`**: Render the Runtime Policy card dynamically within the Orchestrator tab.
