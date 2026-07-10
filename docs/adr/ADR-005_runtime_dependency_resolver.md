<!-- File path: docs/adr/ADR-005_runtime_dependency_resolver.md -->

# ADR-005: Runtime Dependency Resolver for AIWF Skills

## Status
Proposed

## Related Feature
FEAT-050 — Lightweight Runtime Initialization & Runtime Dependency Resolver

## Context

The AI Engineering Workflow Framework (AIWF) currently relies on `initialize-workflow` to perform a full project bootstrap at the start of every conversation turn. This includes:

- Loading the entire Project Memory index (`memory-state.json`)
- Connecting and validating the RAG vector database
- Scanning workspace directories for active work item detection
- Reading version manifests (`package.json`, `go.mod`, `pyproject.toml`)
- Validating documentation folder structure
- Running CLI toolchain version checks (`git`, `python`, `node`, `go`, `docker`, `tree-sitter`, `qdrant`, `ollama`)
- Estimating transcript token usage

This design couples every skill to a monolithic initialization phase, causing:

1. **High startup latency** (~5+ seconds per turn).
2. **Excessive context token usage** (~15k+ tokens consumed before any skill logic runs).
3. **Hidden coupling** between skills and initialization assumptions — skills silently depend on resources being pre-loaded without declaring those dependencies.
4. **Poor scalability** — adding a new resource type requires modifying the central init flow.

The framework needs a way to:
- Make initialization fast and lightweight (guardrails only).
- Allow each skill to explicitly declare what resources it actually requires.
- Resolve only those required resources, lazily when possible.

## Decision

Implement a **shared Runtime Dependency Resolver** as a core module of the AIWF runtime engine.

The resolver introduces three changes to the framework architecture:

### 1. Lightweight `initialize-workflow`

Initialization is restricted to loading mandatory guardrails only:
- `AI_RULES.md`, `AGENTS.md`, and the active `SKILL.md`.
- Approval gates (blueprint, branch, implementation, release).
- Current workflow state, runtime state, and checkpoint level.
- Active work item from cached state (no live filesystem scan).
- Git branch and working tree status via fast cached query.

All other expensive operations are removed from initialization and moved to dedicated skills or runtime CLI commands.

### 2. `runtime_requirements` Skill Manifest Schema

Every skill declares its dependencies in its `SKILL.md` YAML frontmatter:

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

**Allowed modes:**

| Mode | Behaviour |
|------|-----------|
| `required` | Must resolve successfully before the skill starts. Blocks on failure. |
| `cached` | Read from existing cached snapshot only. Never runs live CLI checks. |
| `lazy` | Deferred until the skill explicitly requests the resource during execution. |
| `optional` | Use if available; warn and continue if missing. |
| `none` | Must not be loaded by this skill. |

### 3. `dependency_resolver.py` — Shared Resolver Module

A new shared runtime module located at:

```text
skills/workflow-runtime/scripts/dependency_resolver.py
```

Exposing the following API:

```python
resolve_requirements(skill_name, requirements) -> ResolvedRuntimeContext
validate_requirements(skill_name, requirements) -> ValidationResult
load_required_dependency(name, mode) -> DependencyResult
```

**Resolver behaviour:**

1. Parse `runtime_requirements` from the skill's SKILL.md frontmatter.
2. Validate that all declared keys and modes are supported.
3. For `required` dependencies: load immediately; block skill execution on failure.
4. For `cached` dependencies: read from existing snapshot files; never run live queries.
5. For `lazy` dependencies: register as deferred; load only when explicitly called.
6. For `optional` dependencies: attempt to load; warn only on failure.
7. For `none` dependencies: skip entirely; block if the skill attempts to access them.
8. Record the resolution outcome to `.agents/state/runtime/dependencies.json`.

**CLI commands added:**

```bash
python workflow_runtime.py deps inspect --skill <name>
python workflow_runtime.py deps resolve --skill <name>
python workflow_runtime.py deps validate --skill <name>
python workflow_runtime.py deps doctor
```

**Safety invariant:** The resolver must never bypass approval gates, blueprint gates, release gates, or workflow state checks. These are always treated as `required`.

## Alternatives Considered

### Option B: Per-Skill Manual Loading

Each skill loads its own dependencies directly in its execution block using inline code.

- **Advantage**: No shared resolver needed; each skill is fully self-contained.
- **Disadvantage**: Heavy code duplication across skills; no centralized enforcement of policies; impossible to audit what a skill loads; inconsistent loading behaviour.

**Rejected** because it creates an unmaintainable sprawl and makes audit/debugging of loading behaviour impossible.

### Option C: On-Demand Hook Middleware

A middleware layer intercepts each skill invocation and dynamically injects required context based on heuristics (e.g. inspecting which CLI commands the skill calls).

- **Advantage**: Skills require no manifest changes.
- **Disadvantage**: Heuristic-based dependency detection is unreliable; it creates invisible coupling instead of explicit coupling; future skill authors cannot predict what gets loaded.

**Rejected** because it solves the performance problem while making the dependency contract even more opaque.

### Option D: Full Session Pre-warm Cache

Pre-load all resources once per project session (not per conversation turn) and cache everything in a long-lived session object.

- **Advantage**: Zero per-turn overhead after the first run.
- **Disadvantage**: Stale data risks if memory/RAG/environment change during a session; unclear cache invalidation rules; still loads unnecessary context for simple skills.

**Rejected** because cache invalidation at session scope is complex and still couples all skills to a global preload.

## Trade-offs

| Criterion | Option A (Selected) | Option B | Option C | Option D |
|-----------|-------------------|----------|----------|----------|
| Startup latency | ✅ Very low | ✅ Very low | ✅ Very low | ✅ Zero after warmup |
| Explicit coupling | ✅ Explicit manifest | ❌ None | ❌ Heuristic | ❌ Global |
| Auditable | ✅ Full resolution log | ❌ None | ❌ Partial | ❌ Partial |
| Implementation cost | Medium | Low | High | High |
| Safety enforcement | ✅ Centralized | ❌ Per-skill | ❌ Fragile | ❌ Global |
| Backward compatibility | ✅ Fallback preload | ✅ N/A | ✅ N/A | ⚠️ Session coupling |

## Consequences

1. **`initialize-workflow` becomes lightweight**: It no longer runs expensive operations. Response latency drops from ~5s to under 0.8s.
2. **All core skills must be migrated**: Each core skill must add `runtime_requirements` to its `SKILL.md` manifest. A migration guide will be included.
3. **New CLI surface**: The `deps` command group becomes a first-class debugging and auditing tool for the framework.
4. **Resolution log**: Every skill execution produces a `dependencies.json` resolution record, making it possible to audit what was loaded for any given skill run.
5. **New skill authors must declare dependencies**: The framework will provide a documented schema and validation command (`deps validate`) to guide correct declarations.
6. **Environment checks move to dedicated commands**: `environment-health` and `aiwf env check` become the canonical owners of all toolchain version queries.

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Legacy skills crash on missing preloaded context | Medium | High | Default fallback to legacy full-preload for skills without `runtime_requirements` |
| Stale environment snapshots mislead health checks | Low | Medium | Warn on snapshots older than 24h; remind user to run `aiwf env check` |
| Required dependency accidentally set to `lazy` | Low | Medium | `deps doctor` scans all skills and flags safety-critical dependencies set incorrectly |
| ADR schema drift across skills | Low | Low | `deps validate` and CI integration can catch invalid keys/modes |

## References

- [FEAT-050 Brainstorming](../brainstorming/FEAT-050_lightweight_runtime_initialization.md)
- [FEAT-050 Execution Plan](../plans/FEAT-050_lightweight_runtime_initialization_plan.md)
- [ADR-001: Workflow Runtime Engine](ADR-001_workflow_runtime_engine.md)
- [ADR-004: Pure Split State Management](ADR-004_pure_split_state_management.md)
- [AI_RULES.md](../../AI_RULES.md)
