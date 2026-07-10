<!-- docs/brainstorming/FEAT-050_lightweight_runtime_initialization.md -->

---
feature_id: FEAT-050
feature_name: Lightweight Runtime Initialization & Runtime Dependency Resolver
status: draft
stage: brainstorming
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: None
next_artifact: ../plans/FEAT-050_lightweight_runtime_initialization_plan.md
---

# Master Requirement Document – Lightweight Runtime Initialization & Runtime Dependency Resolver

## 1. Feature ID & Name
- **Feature ID**: FEAT-050
- **Feature Name**: Lightweight Runtime Initialization & Runtime Dependency Resolver

## 2. Original Idea
Refactor `initialize-workflow` into a lightweight runtime initializer instead of a full project bootstrap. Implement a shared Runtime Dependency Resolver so every skill can explicitly declare what runtime context it needs, and the runtime can resolve and load only the required dependencies lazily.

## 3. Business Problem
- **Problem**: The current initialization is too heavy for every new conversation because it performs expensive setups repeatedly (full workspace scanning, project memory loading, RAG connecting, full environment diagnostics, and transcript estimation).
- **Why it matters**: Slow startup latency (>5s) and excessive context token overhead at the start of every developer turn increases API costs and degrades user experience.
- **Who is affected**: Developer agents, visualizer dashboard components, and CI pipelines.
- **Expected outcome**: Core initialization runs in under 0.8 seconds by shifting heavy context operations to lazy or cached evaluation.

## 4. Guardrail vs Context Distinction
To ensure safety and performance, we explicitly separate Mandatory Guardrails from Expensive Context:

### Mandatory Guardrails (Always Loaded at Init)
- `AI_RULES.md`
- `AGENTS.md`
- Active `SKILL.md`
- Approval states (blueprint, branch, implementation, release gates)
- Workflow and runtime states (`.agents/state/workflow.json`, `.agents/state/runtime.json`)
- Current checkpoint level
- Current active work item (read from cached state)
- Current Git branch and working tree status (fast cached query)

### Expensive Context (Never Loaded during Init; resolved dynamically)
- Full Project Memory (`memory-state.json`, `.agents/memory.config.json`)
- Full RAG database index loading
- Full workspace scans
- Environment/toolchain CLI version queries (Python, Go, Node, Docker, etc.)
- Docs folder hierarchy structure checks
- Project version manifest scans (parsing `package.json`, `go.mod`, etc.)
- Direct transcript token estimation

## 5. Runtime Requirements Concept
Every skill must declare its prerequisites in its `SKILL.md` frontmatter metadata:

```yaml
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: lazy
  rag: lazy
  workspace_scan: none
  environment: cached
  provider_usage: optional
  transcript_sync: none
```

### Allowed Modes
- `required`: Must be successfully resolved and loaded before the skill starts.
- `cached`: Read existing cached status only; do not run expensive tool checks automatically.
- `lazy`: Defer loading until the skill explicitly requests it during execution.
- `optional`: Use if available; do not fail or block execution if missing.
- `none`: Must not be preloaded by this skill.

## 6. CLI & Dedicated Skills Ownership
To achieve script-first optimization and minimize prompt context size, expensive operations are relocated to dedicated commands and specialized skills:

- **Environment Diagnostics**: `/environment-health` or `aiwf env check`
- **Memory Bootstrap**: `/project-memory-bootstrap`
- **Memory Incremental Updates**: `/project-memory-update`
- **RAG Lookup**: `/project-rag-search`
- **State Inspect/Resolve/Validate/Doctor**: `python workflow_runtime.py deps <subcommand>`
- **Environment Snapshot Caching**: `python workflow_runtime.py env snapshot`
- **Cached Project Version Retrieval**: `python workflow_runtime.py project version --cached`
- **Cached Active Work Item Retrieval**: `python workflow_runtime.py work-item detect --cached`

## 7. Requirement Traceability Matrix
| Req ID | Priority | Description | Related Plan Task | Expected Tests |
| :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Always load mandatory rules and active skill | Task 1.1, Task 1.3 | test_rules_loaded |
| FR-02 | Must | Verify current checkpoint and active work item | Task 1.3 | test_checkpoint_validation |
| FR-03 | Must | Support `runtime_requirements` parsing schema | Task 2.2 | test_manifest_schema |
| FR-04 | Must | Block execution on missing required dependencies | Task 2.4 | test_missing_required_blocks |
| FR-05 | Must | Load environment state from cache only | Task 3.1 | test_cached_env_only |
| FR-06 | Must | Implement lazy loading API for RAG/Memory | Task 3.2, Task 3.3 | test_lazy_memory_rag |
| FR-07 | Must | Migrate all core skills manifests | Task 4.1 | test_deps_doctor |

## 8. Compatibility
Core skills must stop assuming that `initialize-workflow` preloaded everything. They must request their dependencies explicitly through `runtime_requirements` and use the lazy loading API during execution. Legacy skills without manifestations will default to a fallback legacy preload schema.

## 9. Success Metrics
- **Startup Time**: <0.8 seconds.
- **Context Saving**: >60% token reduction at workflow boot.
- **Safety**: 100% policy enforcement of approvals and checkpoint transitions.
