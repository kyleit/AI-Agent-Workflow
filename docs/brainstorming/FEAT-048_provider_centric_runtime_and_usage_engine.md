<!-- docs/brainstorming/FEAT-048_provider_centric_runtime_and_usage_engine.md -->

---
feature_id: FEAT-048
feature_name: Provider-Centric Runtime & Usage Engine
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-048_provider_centric_runtime_and_usage_engine_plan.md
---

# Master Requirement Document – Provider-Centric Runtime & Usage Engine

## 1. Feature ID & Name
- **Feature ID**: FEAT-048
- **Feature Name**: Provider-Centric Runtime & Usage Engine

---

## 2. Original Idea

> Redesign the AI Workflow Visualizer into a provider-centric platform instead of an AIWF-centric platform.
>
> The current extension reads most statistics from AIWF runtime JSON files (.agents/.session.json and generated JSON). This architecture is insufficient because: Usage statistics only work when AIWF is installed. Numbers may diverge from the provider's actual reported usage. Estimated token calculations are not acceptable. Different AI IDEs expose different transcript formats. Runtime logs are fragmented.
>
> The new architecture must treat AIWF as only ONE optional provider of workflow metadata. Usage statistics must always come from the AI provider itself whenever possible.

---

## 3. Business Problem

- **Problem**: The Visualizer Extension is hard-coupled to AIWF JSON files for all usage statistics. When AIWF is not installed, all metrics are unavailable. When it is installed, numbers are character-count estimates (÷3), not provider-reported values.
- **Why it matters**: Users working in non-AIWF environments cannot access any metrics. Users in AIWF environments see inaccurate billing estimates that diverge from their actual Anthropic/Google/OpenAI invoices. Stakeholders cannot trust the displayed numbers.
- **Who is affected**:
  - Primary: AI IDE users who use Antigravity, Claude Code, Cursor, VS Code AI Agents
  - Secondary: AIWF framework users who need accurate billing
  - Internal: Framework maintainers who extend the provider ecosystem
- **Expected outcome**: Extension displays provider-accurate usage data regardless of whether AIWF is installed. When provider-reported data exists, it wins. Estimation is the last fallback, clearly labeled. Users see the data source and accuracy level for every metric card.

---

## 4. Requirement Discovery

### Functional Requirements

- **FR-01**: Implement a Provider Connector Framework with a plugin architecture. Each connector must support: auto-detection, configurable paths, transcript discovery, conversation discovery, request discovery, usage parsing, model detection, pricing compatibility, and diagnostics output.
- **FR-02**: Implement initial connectors for: Antigravity IDE, Claude Code, Cursor, VS Code AI Agents (extensible for OpenAI Codex and future providers).
- **FR-03**: Implement a Transcript Engine that reads `transcript.jsonl`, structured JSON logs, and usage payloads. Must support incremental reading (never reread entire files). Must parse: model metadata, timestamps, conversation IDs, request IDs, latency, duration, and all token fields.
- **FR-04**: Implement a Usage Normalization layer that maps every provider's schema into one common `NormalizedUsageRecord` schema preserving provider-specific fields.
- **FR-05**: Implement a versioned Cost Engine stored in external `pricing.json`. Costs must never be hardcoded in UI or Python scripts. Must support historical and future pricing updates per model per provider.
- **FR-06**: Replace JSON aggregation with a structured SQLite schema supporting: Global Usage, Project Usage, Conversation Usage, Workflow Usage, Request History, Cost History, Accuracy metadata.
- **FR-07**: Completely separate Runtime Engine from Usage Engine. Runtime stores: checkpoint, workflow, skill, work item, status, memory, RAG, runtime events. Usage stores billing and token metrics.
- **FR-08**: Design a Runtime Event Bus capturing workflow events, skill events, build, test, debug, shell, terminal, and process events. Must support event replay and WebSocket streaming.
- **FR-09**: Implement IDE Log Collectors for supported IDEs, each responsible for: log path discovery, configurable override paths, log tailing, parsing, and normalization into RuntimeEvents.
- **FR-10**: Create a Diagnostics Page in the Extension UI that displays: detected providers, transcript paths, log paths, reader status, parser version, last sync timestamp, unknown format warnings, permission errors, and confidence level.
- **FR-11**: Every statistic must expose an Accuracy Level: `provider_reported | transcript_parsed | derived | estimated | unknown`. Provider Reported must always win. Estimated must be the last fallback.
- **FR-12**: Redesign all Extension UI cards to display: Source, Accuracy, Provider, Model, Last Updated alongside the metric value.
- **FR-13**: If AIWF is present, merge workflow metadata (checkpoint, skill, work item). If absent, workflow widgets become unavailable but usage statistics continue functioning.
- **FR-14**: Implement incremental SQLite indexing. Never parse all transcripts on every refresh. Use hash tracking to detect new content only.
- **FR-15**: Create automated tests covering: provider detection, transcript parsing, pricing engine, SQLite operations, runtime events, incremental parsing, cross-provider aggregation, large transcripts, corrupted transcripts, missing logs, performance benchmarks.

### Non-functional Requirements

- **NFR-01 (Accuracy)**: When provider-reported data is available, displayed values must exactly match. Never silently substitute estimated values for provider-reported values.
- **NFR-02 (Performance)**: Incremental transcript parsing must complete within 200ms for files up to 50MB. Full rescan (first run) allowed up to 5s.
- **NFR-03 (Compatibility)**: Zero regression. All existing AIWF workflow functionality must continue working unchanged.
- **NFR-04 (Extensibility)**: Adding a new provider connector must require only: creating a new Python class subclassing `ProviderConnector`, registering it in `ConnectorRegistry`. No changes to Extension TypeScript.
- **NFR-05 (Offline)**: Cost Engine must work offline. Pricing data bundled as `pricing.json`. Optional remote update check.
- **NFR-06 (Scale)**: SQLite must support millions of request rows. Indexed queries must complete within 100ms for dashboards.
- **NFR-07 (Security)**: Never expose absolute filesystem paths to the webview. Never log user message content. Transcript reads must be read-only.
- **NFR-08 (Distribution)**: Provider Engine must ship as a standalone Python module that works without full AIWF installation.

### Technical Constraints

- **TC-01**: Python 3.10+ required. TypeScript strict mode enforced.
- **TC-02**: Extension must not start a long-running daemon by default. CLI spawn pattern preserved.
- **TC-03**: No new npm dependencies unless strictly necessary. Prefer existing VS Code APIs.
- **TC-04**: SQLite databases remain local (project-level and global-level). No cloud sync.
- **TC-05**: `pricing.json` versioned with semver. Breaking schema changes require major version bump.
- **TC-06**: Transcript reading must be append-only safe. Never seek backwards except on first run.
- **TC-07**: The webview must continue to work with the existing HTML/CSS build pipeline (`build.js` → `webviewHtml.ts`).

---

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Provider Connector Framework | Provider Architecture | `test_connector_detection.py` | Connector auto-detects Antigravity, Claude, Cursor paths |
| FR-02 | Must | Initial provider connectors | Provider Connectors | `test_connectors.py` | 4 connectors pass detection + parsing tests |
| FR-03 | Must | Transcript Engine incremental | Transcript Engine | `test_transcript_incremental.py` | Incremental read detects only new content |
| FR-04 | Must | Usage Normalization | Normalization Schema | `test_normalization.py` | Common schema fields present for all providers |
| FR-05 | Must | Versioned Cost Engine | Cost Engine | `test_pricing.py` | Pricing matches provider published rates |
| FR-06 | Must | SQLite schema redesign | SQLite Schema | `test_db_schema.py` | All tables created, indexes present |
| FR-07 | Must | Runtime/Usage separation | Architecture | `test_runtime_isolation.py` | Runtime tables contain no billing data |
| FR-08 | Should | Runtime Event Bus | Event Bus | `test_event_bus.py` | Events captured, replayed correctly |
| FR-09 | Should | IDE Log Collectors | Log Collectors | `test_log_collectors.py` | Log paths detected for supported IDEs |
| FR-10 | Must | Diagnostics Page | Extension UI | Manual verification | Diagnostics shows all provider status |
| FR-11 | Must | Accuracy Level exposure | Accuracy System | `test_accuracy_labels.py` | All stats tagged with accuracy source |
| FR-12 | Must | UI card metadata redesign | Extension UI | Visual regression | Cards show Source, Accuracy, Provider, Model |
| FR-13 | Must | AIWF optional compatibility | AIWF Layer | `test_aiwf_optional.py` | Usage works without .agents/ directory |
| FR-14 | Must | Incremental SQLite indexing | Performance | `test_incremental_parse.py` | No full rescan on unchanged transcripts |
| FR-15 | Must | Automated test suite | Testing | CI test suite | All tests pass, coverage >= 80% |

---

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| AI IDE Power Users | Primary | High | P0 | Accurate billing, multi-provider support |
| AIWF Framework Users | Primary | High | P0 | Zero regression, enhanced accuracy |
| Non-AIWF IDE Users | Primary | High | P0 | Extension works standalone |
| Framework Maintainers | Internal | High | P1 | Easy provider plugin addition |
| New Provider Integrators | External | Medium | P2 | Documented connector spec |

---

## 7. Scope Boundary

- **In Scope**:
  - Provider Connector Framework (Antigravity, Claude Code, Cursor, VS Code AI Agents)
  - Transcript Engine (incremental, JSONL, structured log)
  - Usage Normalization (common schema)
  - Versioned Cost Engine (offline, `pricing.json`)
  - SQLite schema redesign (additive + new tables)
  - Runtime/Usage separation
  - Runtime Event Bus (design + base implementation)
  - IDE Log Collectors (Antigravity + Claude Code initially)
  - Diagnostics Page in Extension UI
  - Accuracy Level metadata on all stats
  - Extension UI card redesign (Source, Accuracy, Provider, Model, Last Updated)
  - AIWF optional compatibility layer
  - Incremental parsing + hash tracking
  - Automated test suite

- **Out of Scope**:
  - WebSocket streaming daemon (design only in this feature)
  - Real-time push to webview (uses polling or file watcher as before)
  - Cloud usage aggregation
  - Cost alert notifications (OS-level)
  - Provider API key management

- **Deferred Scope**:
  - WebSocket daemon implementation (FEAT-049)
  - OpenAI Codex native connector (FEAT-050)
  - Cursor deep integration beyond log files (FEAT-051)
  - Budget alert OS notifications (FEAT-052)

- **Future Scope**:
  - Remote pricing API with versioned updates
  - Multi-workspace aggregation
  - Team usage analytics

---

## 8. Dependency Graph Preview

```
Provider Engine Core (Must)
  ├── ProviderConnector base class
  ├── ConnectorRegistry
  ├── AntigravityConnector (Must)
  ├── ClaudeCodeConnector (Must)
  ├── CursorConnector (Should)
  └── VSCodeAgentsConnector (Should)

Transcript Engine (Must)
  └── IncrementalReader (hash-tracked)
      └── TranscriptParser (JSONL + JSON)
          └── UsageNormalizer (Must)
              └── NormalizedUsageRecord schema

Cost Engine (Must)
  └── pricing.json (versioned)
      └── CostCalculator (offline)

SQLite Schema Redesign (Must)
  └── usage_records (updated)
      └── provider_requests (extended with accuracy_source)
          └── runtime_events (new table)
              └── connector_diagnostics (new table)

Runtime Event Bus (Should)
  └── EventCapture
      └── EventReplay

Extension UI Redesign (Must)
  └── DiagnosticsPanel (new)
      └── AccuracyBadge component (new)
          └── Updated dashboard cards

AIWF Compatibility Layer (Must)
  └── WorkflowMetadataAdapter
```

---

## 9. Data Flow Preview

```
AI IDE (Antigravity / Claude Code / Cursor)
  └── generates ──> transcript.jsonl / structured logs
      └── read by ──> IncrementalTranscriptReader (hash tracked)
          └── parsed by ──> TranscriptParser (provider-specific)
              └── normalized to ──> NormalizedUsageRecord
                  ├── stored in ──> SQLite (provider_requests + usage_records)
                  └── priced by ──> CostEngine (pricing.json)
                      └── served to ──> Extension (via CLI spawn: provider_engine.py)
                          └── displayed in ──> Webview Dashboard
                              └── labeled with ──> AccuracyLevel

AIWF Runtime (if installed)
  └── provides ──> workflow metadata (checkpoint, skill, work_item)
      └── merged by ──> WorkflowMetadataAdapter
          └── injected into ──> Webview Dashboard (workflow cards only)

Diagnostics Flow
  └── ConnectorRegistry.detect_all()
      └── outputs ──> DiagnosticsReport (provider status, paths, accuracy)
          └── displayed in ──> DiagnosticsPage
```

---

## 10. Existing Asset Analysis

| Asset / Component | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| `context.py` | `skills/workflow-runtime/scripts/context.py` | Refactor | Extract provider detection. Replace char/3 estimation with connector calls. |
| `db.py` | `skills/workflow-runtime/scripts/db.py` | Extend | Add `accuracy_source`, `raw_payload` columns. Add `runtime_events`, `connector_diagnostics` tables. |
| `extension.ts` | `extensions/visualizer/src/extension.ts` | Refactor | Remove inline estimation logic. Add ProviderRegistry TS layer. Add DiagnosticsPanel watcher. |
| `webview.html` | `extensions/visualizer/resources/webview.html` | Extend | Add Diagnostics tab. Add AccuracyBadge to all metric cards. |
| `workflow_runtime.py` | `skills/workflow-runtime/scripts/workflow_runtime.py` | Extend | Add `provider` subcommand dispatching to provider_engine.py. |
| `utils.py` | `skills/workflow-runtime/scripts/utils.py` | Extend | Add `get_provider_engine_path()` helper. |
| `pricing.json` | NEW: `skills/workflow-runtime/data/pricing.json` | Create | Versioned pricing registry for all providers/models. |
| `provider_engine.py` | NEW: `skills/workflow-runtime/scripts/provider_engine.py` | Create | Main standalone entry point for provider detection + transcript parsing. |
| `connectors/` | NEW: `skills/workflow-runtime/scripts/connectors/` | Create | Provider connector plugin directory. |
| `test_runtime.py` | `skills/workflow-runtime/tests/test_runtime.py` | Extend | Add provider, transcript, pricing, diagnostics test cases. |

---

## 11. Dependency & Blast Radius Analysis

- **Affected Skills**: `initialize-workflow` (session init reads usage), `workflow-runtime` (core engine)
- **Affected Modules/Components**: `context.py`, `db.py`, `utils.py`, `workflow_runtime.py`, `session.py`
- **Affected Runtime**: SQLite schema migration required for existing `project_runtime.db` and `global_runtime.db`
- **Affected Extension**: `extension.ts`, `webview.html`, `webviewHtml.ts` (rebuild pipeline)
- **Affected Scripts**: `workflow_runtime.py` CLI (new `provider` subcommand), `provider_engine.py` (new)
- **Affected Database**: Both `project_runtime.db` and `global_runtime.db` — schema migration needed
- **Affected Documentation**: `SKILLS.md`, `USAGE.md`, `README.md`, `CHANGELOG.md`
- **Impact Level**: High — core data pipeline redesign

---

## 12. Migration Strategy

- **Backward Compatibility**: All existing AIWF session JSON files remain readable. New engine reads both old and new schemas. Existing `.agents/state/` directory structure unchanged.
- **Adapter Strategy**: `WorkflowMetadataAdapter` wraps existing `aggregate_state()` function. Provider engine operates in parallel — no replacement of existing session reads during transition.
- **Coexistence Period**: Phase 1 runs both old estimation path and new provider path. New path data flagged as `transcript_parsed`. Discrepancy logged to diagnostics.
- **Deprecation Plan**: Old `estimateContextUsage()` in extension.ts deprecated after Phase 2 validation. Old hardcoded pricing constants removed after `pricing.json` validated.
- **Migration Phases**:
  - Phase 1: Provider Engine + ConnectorRegistry (standalone, no UI change yet)
  - Phase 2: SQLite schema extension (additive only, no drops)
  - Phase 3: Extension UI redesign (DiagnosticsPanel + AccuracyBadge)
  - Phase 4: Remove deprecated estimation code

---

## 13. Architecture Principles

- **API First**: Provider Engine exposes a clean JSON CLI API. All callers use `provider_engine.py detect | parse | pricing | diagnose`.
- **Provider First**: Usage data hierarchy: Provider Reported > Transcript Parsed > Derived > Estimated > Unknown. Never promote lower-accuracy data.
- **Script First**: Provider Engine is a standalone Python script. No daemon required. Extension spawns it as needed.
- **Memory First**: Provider Engine caches parsed results in SQLite. Subsequent calls read from cache, not files.
- **Incremental Updates**: File hash tracking ensures only new transcript content is parsed. Never reread unchanged files.
- **Backward Compatibility**: Existing AIWF session JSON files continue to work. No breaking changes to `.agents/` directory structure.
- **Replaceable Providers**: ConnectorRegistry supports dynamic loading. New providers require no changes to existing code.

---

## 14. Non Goals

- No cloud usage sync or aggregation
- No real-time AI provider API key validation
- No budget alert OS notifications in this feature
- No WebSocket streaming daemon (design only)
- No modifying existing AIWF skill SKILL.md files
- No automatic billing reconciliation
- No UI changes to the interactive choice protocol
- No changes to session persistence or state split architecture

---

## 15. ROI Analysis

- **Estimated Implementation Cost**: 4–6 weeks (1 engineer)
- **Runtime Savings**: Eliminates re-estimation on every refresh via SQLite cache — ~80% reduction in Python spawn calls
- **Token Reduction Target**: N/A (infrastructure change)
- **API Call Reduction Target**: N/A
- **Maintenance Impact**: Provider additions reduced from multi-file changes to single connector class (~1 day per new provider)
- **Expected Break-Even**: After 3 provider integrations (Antigravity + Claude + Cursor)
- **Long-Term ROI**: Foundation for multi-provider billing analytics, usage-based workflow optimization recommendations

---

## 16. Success Metrics

- **Accuracy Target**: 100% of sessions with Antigravity transcript display `provider_reported` or `transcript_parsed` — never `estimated` as primary source
- **Latency Target**: Provider Engine parse call completes in <200ms for cached conversations; <5s for first-run full parse of 50MB transcript
- **Memory Usage Limit**: SQLite databases remain under 100MB for typical 30-day usage
- **Startup Time Target**: Extension activation unchanged (<500ms)
- **Cache Hit Ratio Target**: >90% of dashboard refreshes use SQLite cache (no file re-read)
- **Test Coverage Target**: >80% line coverage for `provider_engine.py`, `connectors/`, and `cost_engine.py`
- **Expected ROI**: Provider plugin development time reduced by 70% vs current ad-hoc approach

---

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Transcript format changes in future IDE versions | High | Medium | Versioned parser registry; format detection fallback | Provider Connector team |
| SQLite migration failure on existing DBs | High | Low | Additive-only migrations in Phase 2; backup before migration | DB layer |
| pricing.json becomes stale (model price changes) | Medium | High | Version warning in Diagnostics; optional remote update check | Cost Engine |
| Extension spawn performance regression | Medium | Low | Benchmark suite + SQLite cache strategy | Extension layer |
| AIWF compatibility regression | High | Low | Full existing test suite must pass before any Phase 2 merge | CI |
| New provider transcripts undocumented | Medium | High | Diagnostics shows "unknown format" with raw sample | Diagnostics |
| Python not found in PATH on some machines | High | Low | Extension gracefully shows "Python not found" in Diagnostics | Extension |

---

## 18. Technical Questions

- Q1: Should `pricing.json` be committed to the repo or fetched from a versioned URL at startup? (Recommended: bundled in repo with optional remote fetch)
- Q2: Should ConnectorRegistry be discovered by directory scanning or explicit registration in a `connectors.json` manifest? (Recommended: manifest for reliability)
- Q3: What is the fallback behaviour when a transcript file is locked by the IDE (Windows file locking)? (Recommended: retry with exponential backoff, log to diagnostics)
- Q4: Should the DiagnosticsPage be a new VS Code Tab or a new collapsible section within the existing sidebar? (Recommended: collapsible sidebar section)
- Q5: What is the desired WebSocket protocol for future streaming — standard RFC 6455 or VS Code's built-in IPC? (Recommended: RFC 6455 for IDE-agnostic compatibility)

---

## 19. Open Decision Register

| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| pricing.json storage location | Pending | Bundled vs. remote. Decide in blueprint phase. |
| ConnectorRegistry discovery mechanism | Pending | Manifest vs. directory scan. Decide in blueprint phase. |
| Phase 4 deprecation timeline | Pending | Requires Phase 3 validation. Defer to release planning. |
| WebSocket streaming design | Requires ADR | Architecture decision impacts FEAT-049. ADR required before blueprint. |
| DiagnosticsPage placement | Pending | Sidebar section vs. new tab. UX decision needed. |

---

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: The Runtime Event Bus design and WebSocket streaming protocol require an ADR before implementation. Specifically: streaming transport choice (RFC 6455 vs. VS Code IPC), event schema versioning strategy, and replay mechanism storage. This decision impacts FEAT-048, FEAT-049, and future provider streaming integrations.

---

## 21. Knowledge Update Impact

- **project-summary**: Yes — new modules: `provider_engine.py`, `connectors/`, `pricing.json`, DiagnosticsPanel
- **architecture**: Yes — Provider-Centric Architecture replaces AIWF-Centric. ProviderConnector base, ConnectorRegistry, AccuracyLevel system documented
- **modules**: Yes — `context.py`, `db.py`, `extension.ts`, `webview.html` all significantly modified
- **lessons**: Yes — "Never hardcode provider pricing in source files", "Always expose accuracy level with every metric"
- **patterns**: Yes — Provider Connector Plugin Pattern, Accuracy-First Data Display Pattern
- **ADR**: Yes — WebSocket/Event Bus ADR required
- **SQLite**: Yes — New tables: `runtime_events`, `connector_diagnostics`. Extended columns in `provider_requests`
- **indexes**: Yes — New indexes on `connector_diagnostics.provider`, `runtime_events.event_type`
- **vector metadata**: Yes — New architecture entities should be indexed for RAG: `ProviderConnector`, `ConnectorRegistry`, `AccuracyLevel`, `NormalizedUsageRecord`

---

## 22. Test Strategy Preview

- **Unit Tests**:
  - `test_connectors.py`: Detection, path resolution, transcript discovery for each connector
  - `test_transcript_parser.py`: JSONL parsing, incremental reading, corrupted file handling
  - `test_normalization.py`: NormalizedUsageRecord field completeness per provider
  - `test_pricing.py`: Cost calculation accuracy vs. published provider rates
  - `test_accuracy_labels.py`: Accuracy level assignment per data source

- **Integration Tests**:
  - `test_provider_engine_integration.py`: End-to-end: connector -> parse -> normalize -> SQLite -> CLI output
  - `test_db_migration.py`: Existing DB upgrade preserves all historical data
  - `test_aiwf_optional.py`: Full dashboard load without `.agents/` directory

- **Regression Tests**:
  - All existing `test_runtime.py` tests must pass unchanged
  - Extension loads and displays AIWF data identically to current behavior

- **Performance Tests**:
  - `test_transcript_performance.py`: 50MB JSONL parse <5s; incremental re-read <200ms
  - `test_sqlite_query_performance.py`: Dashboard queries <100ms at 1M rows

- **Migration Tests**:
  - `test_db_migration.py`: Old schema -> new schema preserves records and indexes

- **Compatibility Tests**:
  - Connector detection on Windows, macOS, Linux
  - Transcript format variations across IDE versions

---

## 23. Extension Impact

- **Extension UI Changes**:
  - New: DiagnosticsPanel section (collapsible) in sidebar
  - Modified: All metric cards — add Source, Accuracy, Provider, Model, Last Updated badges
  - Modified: Context Analytics card — display accuracy level prominently
  - Modified: Request History card — add provider column, accuracy column
  - New: `AccuracyBadge` component reusable across all cards
  - Modified: `webview.html` -> rebuild via `build.js` -> `webviewHtml.ts`

- **Affected ViewModels / Watchers**:
  - `updateSessionData()`: Replace inline estimation with ProviderRegistry call
  - `estimateContextUsage()`: Deprecated, replaced by `getProviderUsage()` with accuracy metadata
  - New: `updateDiagnosticsData()` — triggered by ConnectorRegistry status changes
  - New: `ProviderRegistryWatcher` — watches connector log paths for changes

---

## 24. Complexity Estimation

- **Implementation Complexity**: High
- **Estimated Refactoring Percentage**:
  - `context.py`: 60% rewritten (provider detection + estimation logic replaced)
  - `db.py`: 25% extended (new tables + columns, additive)
  - `extension.ts`: 40% refactored (estimation removed, ProviderRegistry added, Diagnostics added)
  - `webview.html`: 30% extended (DiagnosticsPanel, AccuracyBadge, card metadata)
  - New files: `provider_engine.py` (~500 LOC), `connectors/*.py` (4 connectors x ~200 LOC), `pricing.json` (~150 lines)

---

## 25. Roadmap Alignment

- **Roadmap Phase**: Core Infrastructure Modernization (follows FEAT-047 Runtime Visualizer)
- **Milestones**:
  - M1: Provider Engine + ConnectorRegistry + AntigravityConnector (2 weeks)
  - M2: ClaudeCodeConnector + CursorConnector + pricing.json (1 week)
  - M3: SQLite schema extension + incremental indexing (1 week)
  - M4: Extension UI redesign (DiagnosticsPanel + AccuracyBadge) (1 week)
  - M5: Test suite + migration validation + Phase 4 cleanup (1 week)
- **Prerequisites & Dependencies**:
  - FEAT-047 (Runtime Visualizer) — must be merged before FEAT-048 UI changes
  - Python 3.10+ available in development environment
  - Existing `test_runtime.py` suite must be green before starting

---

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| Should pricing.json be bundled or remote? | Bundled in repo, optional remote update check |
| Is WebSocket streaming in scope for FEAT-048? | Design only; implementation deferred to FEAT-049 |
| Should Extension work with zero Python? | No — Python required. But can be standalone provider_engine.py, not full AIWF |
| Should Diagnostics be a new VS Code tab? | New collapsible section in existing sidebar (less intrusive) |
| What is the minimum accuracy level acceptable? | All levels displayed; Estimated clearly labeled in amber/orange |

---

## 27. Requirement Readiness Score

- **Score**: 96/100
- **Status**: Ready >= 85

---

## 28. Existing Project Context

- **Memory Source**: `.agents/memory/project-summary.md`, `.agents/memory/architecture/overview.md`
- **Existing Architecture Summary**:
  - Multi-Agent Orchestrated SDLC Workflow
  - Python CLI (`workflow_runtime.py`) + TypeScript Extension (`extension.ts`) + WebView (`webview.html`)
  - SQLite dual-database: `project_runtime.db` + `global_runtime.db`
  - Qdrant RAG for semantic memory
  - Split State Architecture (`.agents/state/` JSON files)
  - `build.js` compiles `webview.html` -> `webviewHtml.ts` — must be respected
  - Extension communicates with Python via `child_process.exec()` spawning `workflow_runtime.py`

---

## 29. Existing Modules & Services

| Module/Service | Location | Owner | Public APIs | Est. Reuse % | Est. Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| `context.py` | `skills/workflow-runtime/scripts/` | Runtime | `parse_transcript()`, `sync_request_history()` | 30% | 60% | Medium | Core usage calc — refactored to use provider connectors |
| `db.py` | `skills/workflow-runtime/scripts/` | Runtime | `save_provider_request()`, `get_provider_requests()`, `init_db_schema()` | 75% | 25% | Low | Extended with new tables + accuracy columns |
| `extension.ts` | `extensions/visualizer/src/` | Extension | `updateSessionData()`, `estimateContextUsage()` | 60% | 40% | Low | Estimation logic removed, ProviderRegistry integrated |
| `webview.html` | `extensions/visualizer/resources/` | Extension | Dashboard UI | 70% | 30% | Low | DiagnosticsPanel + AccuracyBadge added |
| `workflow_runtime.py` | `skills/workflow-runtime/scripts/` | Runtime | CLI entry point | 90% | 10% | Low | New `provider` subcommand added |
| `validator.py` | `skills/workflow-runtime/scripts/` | Runtime | `get_git_info()`, `get_version_info()` | 100% | 0% | None | Unchanged |
| `utils.py` | `skills/workflow-runtime/scripts/` | Runtime | `get_memory_info()`, `get_rag_info()` | 90% | 10% | Low | Helper `get_provider_engine_path()` added |
| `session.py` | `skills/workflow-runtime/scripts/` | Runtime | `load_session()`, `save_session_atomic()` | 100% | 0% | None | Unchanged |
| `state_sync.py` | `skills/workflow-runtime/scripts/` | Runtime | `aggregate_state()`, `deconstruct_state()` | 100% | 0% | None | Unchanged |

---

## 30. Solution Options Evaluated

### Option A: Unified Python Backend with REST API Gateway

- **Overview**: Python FastAPI daemon on localhost:PORT. Extension TypeScript calls REST instead of spawning CLI. Backend manages all provider logic.
- **Architecture**: Extension -> HTTP -> ProviderGateway daemon -> ConnectorRegistry -> SQLite
- **Advantages**: Clean separation, REST easy to test, natural WebSocket extension, push-capable
- **Disadvantages**: Port conflict risk, daemon lifecycle complexity, HTTP latency, harder distribution
- **Complexity**: High
- **Risk**: Medium — daemon lifecycle management
- **Performance**: Good (~1-5ms REST round-trip)
- **Maintainability**: High
- **Compatibility**: Medium — requires process management
- **Future Scalability**: Very High

### Option B: Enhanced TypeScript Engine in Extension (Self-Contained)

- **Overview**: Move all parsing, normalization, pricing into TypeScript. Native sqlite3 module. AIWF CLI only for workflow metadata.
- **Architecture**: Extension -> TypeScript ProviderRegistry -> File I/O -> SQLite (better-sqlite3)
- **Advantages**: Zero Python dependency, native VS Code watchers, no daemon, simple distribution
- **Disadvantages**: Large bundle, TypeScript/Python divergence, pricing updates require extension rebuild
- **Complexity**: Medium
- **Risk**: Low
- **Performance**: Excellent — direct file I/O
- **Maintainability**: Medium
- **Compatibility**: High
- **Future Scalability**: Medium

### Option C: Hybrid Python Provider Layer + TypeScript Thin UI (Selected)

- **Overview**: Python `provider_engine.py` standalone CLI. Extension spawns it for provider data. TypeScript remains thin UI. AIWF optional adapter. ConnectorRegistry in Python.
- **Architecture**: Extension -> spawn -> provider_engine.py -> ConnectorRegistry -> TranscriptEngine -> SQLite; AIWF -> WorkflowMetadataAdapter (optional)
- **Advantages**: Reusable Python parsing, zero new daemon, AIWF fully optional, incremental parsing natural, provider plugins simple, pricing via JSON
- **Disadvantages**: Python still required, spawn overhead needs caching
- **Complexity**: Medium
- **Risk**: Low — evolution of existing pattern
- **Performance**: Good — incremental parsing + SQLite cache
- **Maintainability**: High
- **Compatibility**: High
- **Future Scalability**: High

---

## 31. Solution Comparison Table

| Criteria | Option A (REST Daemon) | Option B (Full TypeScript) | Option C (Hybrid — Selected) |
|---|---|---|---|
| Complexity | High | Medium | Medium |
| Risk | Medium | Low | Low |
| Performance | Good | Excellent | Good |
| Maintainability | High | Medium | High |
| Compatibility | Medium | High | High |
| Future Scalability | Very High | Medium | High |
| Development Cost | High | Medium | Medium |
| AIWF Independence | Full | Full | Full |
| Regression Risk | High | Medium | Low |

---

## 32. Selected Solution

- **Choice**: Option C — Hybrid Python Provider Layer + TypeScript Thin UI
- **Why Selected**:
  1. **Zero Regression Risk**: Evolves existing `exec(python ...)` pattern. No breaking change to Extension communication model.
  2. **Provider Independence**: `provider_engine.py` operates standalone. No `.agents/` required. AIWF data merged as optional enhancement.
  3. **Incremental Parsing Natural**: File hash tracking and append-only reads are simpler and more robust in Python.
  4. **Plugin Architecture Simple**: Adding a new connector = one Python class in `connectors/`. Zero TypeScript changes.
  5. **Pricing Maintainability**: `pricing.json` updated independently of code. No rebuild required for pricing changes.
- **Trade-offs Accepted**: Python spawn overhead (~100-200ms) mitigated by SQLite cache layer. TypeScript needs small changes to call new provider subcommand.
- **Technical Debt**: Temporary divergence between old estimation path and new provider path during Phase 1-2. Eliminated in Phase 4.
- **Risk Mitigation**: Existing test suite runs unchanged. Phase 1 runs new provider path in parallel before replacing old path. Diagnostics shows both data sources during transition.

---

## 33. Risks & Assumptions

- **Risks**:
  - R-01: Transcript format changes in future IDE versions -> Mitigation: Versioned parser registry + format detection fallback
  - R-02: SQLite migration failure on existing production DBs -> Mitigation: Additive-only Phase 2; automated backup before migration
  - R-03: `pricing.json` becomes stale -> Mitigation: Version number in pricing.json; Diagnostics warns if pricing > 30 days old
  - R-04: Python not in PATH on some machines -> Mitigation: Extension gracefully shows "Python not found" in Diagnostics; no crash
  - R-05: AIWF compatibility regression -> Mitigation: Full existing `test_runtime.py` suite must pass before Phase 2 merge
  - R-06: New provider transcripts undocumented -> Mitigation: Diagnostics captures unknown formats with raw samples
- **Assumptions**:
  - A-01: Python 3.10+ is available in target environment
  - A-02: Transcript JSONL files are append-only during active conversation
  - A-03: `pricing.json` initial version covers Antigravity (Gemini), Anthropic Claude, and OpenAI pricing as of July 2026
  - A-04: VS Code Extension host can spawn Python child processes (confirmed in current architecture)
  - A-05: DiagnosticsPanel can be added without breaking the existing `build.js` -> `webviewHtml.ts` pipeline

---

## 34. Acceptance Criteria

- [ ] AC-01 (maps to FR-01, FR-02): `provider_engine.py detect` returns at least one provider with correct path on Antigravity IDE environment. (Test: `test_connector_detection.py`)
- [ ] AC-02 (maps to FR-03, FR-14): Re-running `provider_engine.py parse` on unchanged transcript does not re-read file content — uses SQLite cache. (Test: `test_incremental_parse.py`)
- [ ] AC-03 (maps to FR-04): All providers produce `NormalizedUsageRecord` with fields: `provider`, `model`, `conversation_id`, `request_id`, `input_tokens`, `output_tokens`, `total_tokens`, `accuracy_source`. (Test: `test_normalization.py`)
- [ ] AC-04 (maps to FR-05): Cost for a known model request matches published provider rate within +-1%. (Test: `test_pricing.py`)
- [ ] AC-05 (maps to FR-11, FR-12): Every metric card displays `accuracy_source` badge. `provider_reported` badge is green; `estimated` badge is amber. (Test: Visual regression)
- [ ] AC-06 (maps to FR-10): Diagnostics page shows correct status (Connected / Not Found / Permission Error) for each detected provider. (Test: Manual + `test_diagnostics.py`)
- [ ] AC-07 (maps to FR-13): With `.agents/` directory removed, Extension loads, shows usage data from provider connectors, shows "AIWF: Not installed" in Diagnostics without crashing. (Test: `test_aiwf_optional.py`)
- [ ] AC-08 (maps to NFR-03): All existing `test_runtime.py` test cases pass unchanged after FEAT-048 implementation. (Test: Regression suite)
- [ ] AC-09 (maps to NFR-02): `provider_engine.py parse` for a 50MB transcript completes in <5s on first run; <200ms on subsequent runs with unchanged content. (Test: `test_transcript_performance.py`)
- [ ] AC-10 (maps to FR-06, NFR-06): SQLite dashboard query returns in <100ms with 1,000,000 rows in `provider_requests`. (Test: `test_sqlite_query_performance.py`)

---

## 35. Final Planning Prompt

### Purpose
Complete, self-contained prompt for the `brainstorming-to-plan` Skill. The Planning Agent must require no further clarification from this section.

### Problem Statement
The AI Workflow Visualizer Extension currently reads all usage statistics from AIWF JSON session files and estimates token counts by dividing character counts by 3. This creates hard dependency on AIWF installation, inaccurate billing numbers, and inability to support multiple AI IDE providers. The redesign must make AIWF optional, read usage directly from AI provider transcripts, expose accuracy metadata for every metric, and support a pluggable provider connector system.

### Objectives & Selected Solution
**Goal**: Provider-Centric Runtime & Usage Engine using **Option C — Hybrid Python Provider Layer + TypeScript Thin UI**.

**New modules to create**:
- `skills/workflow-runtime/scripts/provider_engine.py` — standalone CLI entry point
- `skills/workflow-runtime/scripts/connectors/__init__.py` — ConnectorRegistry
- `skills/workflow-runtime/scripts/connectors/base.py` — ProviderConnector base class
- `skills/workflow-runtime/scripts/connectors/antigravity.py` — AntigravityConnector
- `skills/workflow-runtime/scripts/connectors/claude_code.py` — ClaudeCodeConnector
- `skills/workflow-runtime/scripts/connectors/cursor.py` — CursorConnector
- `skills/workflow-runtime/scripts/connectors/vscode_agents.py` — VSCodeAgentsConnector
- `skills/workflow-runtime/scripts/cost_engine.py` — CostEngine
- `skills/workflow-runtime/data/pricing.json` — versioned pricing data

**Modules to refactor**:
- `context.py`: Replace estimation with provider connector calls
- `db.py`: Add new tables + accuracy_source column
- `extension.ts`: Remove estimation, add ProviderRegistry spawn, add DiagnosticsPanel
- `webview.html`: Add DiagnosticsPanel + AccuracyBadge components

### Functional Requirements
FR-01 through FR-15 as documented in Section 4.

### Non-functional Requirements & Constraints
NFR-01 through NFR-08 and TC-01 through TC-07 as documented in Section 4.
Key: zero regression (NFR-03), offline cost engine (NFR-05), Python 3.10+ (TC-01), no daemon (TC-02), append-only reads (TC-06), existing build pipeline unchanged (TC-07).

### Architectural Details

**provider_engine.py CLI interface**:
```
provider_engine.py detect                                          -> JSON: DetectedProvider[]
provider_engine.py parse --provider antigravity --conv-id XXX     -> JSON: NormalizedUsageRecord[]
provider_engine.py pricing --provider X --model Y --input N --output M -> JSON: {cost_usd, breakdown}
provider_engine.py diagnose                                        -> JSON: DiagnosticsReport
```

**NormalizedUsageRecord schema**:
```json
{
  "provider": "antigravity|claude_code|cursor|vscode_agents",
  "model": "gemini-2.5-flash|claude-opus-4|...",
  "conversation_id": "string",
  "request_id": "string",
  "timestamp": "ISO8601",
  "input_tokens": 0,
  "output_tokens": 0,
  "cache_read_tokens": 0,
  "cache_write_tokens": 0,
  "thinking_tokens": 0,
  "total_tokens": 0,
  "duration_ms": 0,
  "estimated_cost_usd": 0.0,
  "accuracy_source": "provider_reported|transcript_parsed|derived|estimated|unknown",
  "raw_payload": {}
}
```

**pricing.json schema**:
```json
{
  "version": "1.0.0",
  "updated_at": "2026-07-09",
  "providers": {
    "antigravity": {
      "models": {
        "gemini-2.5-flash": {
          "input_per_mtok": 0.15,
          "output_per_mtok": 0.60,
          "cache_read_per_mtok": 0.0375,
          "cache_write_per_mtok": 0.1875
        }
      }
    }
  }
}
```

**New SQLite tables**:
- `runtime_events(id, timestamp, conversation_id, provider, event_type, event_data_json)`
- `connector_diagnostics(id, timestamp, provider, status, path, error, accuracy_confidence)`

**provider_requests new columns**:
- `accuracy_source TEXT` — one of: `provider_reported|transcript_parsed|derived|estimated|unknown`
- `raw_payload TEXT` — JSON blob of original provider response

### Risks & Assumptions
R-01 through R-06 and A-01 through A-05 as documented in Section 33.

### Verification Checklist
- [ ] `docs/plans/FEAT-048_provider_centric_runtime_and_usage_engine_plan.md` generated and approved
- [ ] `docs/designs/FEAT-048_provider_centric_runtime_and_usage_engine_blueprint.md` generated and approved
- [ ] All 10 Acceptance Criteria (AC-01 through AC-10) mapped to implementation tasks
- [ ] ADR for Runtime Event Bus / WebSocket protocol created before blueprint
- [ ] SQLite migration script reviewed and tested against existing `project_runtime.db`
- [ ] `pricing.json` initial data validated against published provider pricing as of implementation date

---

> WARNING: The next Skill is `brainstorming-to-plan`.
> It must be invoked **manually** by the user with `/plan`.
> This Skill does NOT invoke it automatically.
