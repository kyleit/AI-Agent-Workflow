<!-- File path: docs/plans/FEAT-048_provider_centric_runtime_and_usage_engine_plan.md -->

---
feature_id: FEAT-048
feature_name: Provider-Centric Runtime & Usage Engine
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-048_provider_centric_runtime_and_usage_engine.md
next_artifact: ../designs/FEAT-048_provider_centric_runtime_and_usage_engine_blueprint.md
---

# FEAT-048: Provider-Centric Runtime & Usage Engine

## 1. Requirement Coverage Matrix

| Req ID | Priority | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :--- | :---: |
| FR-01 | Must | Phase 1 | Task 1.1 | ProviderConnector base class + ConnectorRegistry | [x] |
| FR-02 | Must | Phase 1 | Task 1.2 | AntigravityConnector + ClaudeCodeConnector | [x] |
| FR-02 | Must | Phase 1 | Task 1.3 | CursorConnector + VSCodeAgentsConnector | [x] |
| FR-03 | Must | Phase 1 | Task 1.4 | IncrementalTranscriptReader + TranscriptParser | [x] |
| FR-04 | Must | Phase 1 | Task 1.5 | UsageNormalizer + NormalizedUsageRecord schema | [x] |
| FR-05 | Must | Phase 1 | Task 1.6 | CostEngine + pricing.json | [x] |
| FR-07 | Must | Phase 1 | Task 1.7 | provider_engine.py standalone CLI entry point | [x] |
| FR-14 | Must | Phase 1 | Task 1.8 | Hash-tracking incremental indexing | [x] |
| FR-06 | Must | Phase 2 | Task 2.1 | SQLite schema extension (new tables + columns) | [x] |
| FR-07 | Must | Phase 2 | Task 2.2 | Runtime/Usage separation in DB layer | [x] |
| FR-13 | Must | Phase 2 | Task 2.3 | WorkflowMetadataAdapter (AIWF optional layer) | [x] |
| FR-11 | Must | Phase 3 | Task 3.1 | AccuracyLevel system in Extension | [x] |
| FR-10 | Must | Phase 3 | Task 3.2 | DiagnosticsPanel in Extension UI | [x] |
| FR-12 | Must | Phase 3 | Task 3.3 | AccuracyBadge on all metric cards | [x] |
| FR-08 | Should | Phase 4 | Task 4.1 | Runtime Event Bus base implementation | [x] |
| FR-09 | Should | Phase 4 | Task 4.2 | IDE Log Collectors (Antigravity + Claude Code) | [x] |
| FR-15 | Must | Phase 5 | Task 5.1 | Automated test suite (unit + integration + perf) | [x] |
| FR-15 | Must | Phase 5 | Task 5.2 | Regression tests — AIWF compatibility | [x] |
| NFR-03 | Must | Phase 5 | Task 5.3 | Deprecation of old estimation code (Phase 4 cleanup) | [x] |

---

## 2. Task Ownership & Roles

- **Task 1.1** — [Architect] Design and implement ProviderConnector base class and ConnectorRegistry plugin system
- **Task 1.2** — [Coder] Implement AntigravityConnector and ClaudeCodeConnector with path auto-detection and transcript discovery
- **Task 1.3** — [Coder] Implement CursorConnector and VSCodeAgentsConnector
- **Task 1.4** — [Coder] Implement IncrementalTranscriptReader (hash-tracked) and provider-specific TranscriptParsers
- **Task 1.5** — [Coder] Implement UsageNormalizer and define NormalizedUsageRecord schema
- **Task 1.6** — [Coder] Implement CostEngine and create initial pricing.json with Antigravity, Claude, and OpenAI pricing
- **Task 1.7** — [Coder] Implement provider_engine.py standalone CLI (detect, parse, pricing, diagnose subcommands)
- **Task 1.8** — [Coder] Integrate hash-based incremental indexing into TranscriptReader and SQLite cache layer
- **Task 2.1** — [Database Developer] Extend SQLite schema: add runtime_events, connector_diagnostics tables; add accuracy_source, raw_payload columns to provider_requests
- **Task 2.2** — [Database Developer] Implement Runtime/Usage separation: migrate billing fields away from runtime tables
- **Task 2.3** — [Backend Developer] Implement WorkflowMetadataAdapter — wraps existing aggregate_state() for optional AIWF integration
- **Task 3.1** — [Frontend Developer] Implement AccuracyLevel system in Extension TypeScript — ProviderRegistry spawn integration
- **Task 3.2** — [Frontend Developer] Build DiagnosticsPanel component in webview.html and wire updateDiagnosticsData() in extension.ts
- **Task 3.3** — [Frontend Developer] Add AccuracyBadge to all metric cards; update all usage stat displays to show Source, Provider, Model, Last Updated
- **Task 4.1** — [Backend Developer] Implement Runtime Event Bus base: EventCapture + EventReplay + runtime_events storage
- **Task 4.2** — [Backend Developer] Implement IDE Log Collectors for Antigravity and Claude Code
- **Task 5.1** — [Test Developer] Write automated unit, integration, and performance test files as specified in FR-15
- **Task 5.2** — [QA Reviewer] Execute full regression suite; confirm 100% existing test_runtime.py tests pass
- **Task 5.3** — [Coder] Remove deprecated estimateContextUsage() and hardcoded pricing constants after Phase 3 validation

---

## 3. Parallel Execution Plan

- **Sequential Tasks** (strict order required):
  - Task 1.1 → Task 1.2 → Task 1.4 → Task 1.5 → Task 1.7
  - Task 2.1 → Task 2.2 → Task 2.3
  - Task 3.1 → Task 3.2 → Task 3.3
  - Task 5.1 → Task 5.2 → Task 5.3

- **Parallel Tasks**:
  - [Task 1.2, Task 1.3] — both connectors independent of each other
  - [Task 1.5, Task 1.6] — Normalizer and CostEngine independent
  - [Task 1.7, Task 1.8] — CLI entry point and hash indexing independent
  - [Task 4.1, Task 4.2] — Event Bus and Log Collectors independent

- **Blocking Tasks**:
  - Task 1.1 blocks all of Task 1.2, 1.3, 1.4, 1.5 (base class must exist first)
  - Task 1.5 blocks Task 1.7 (normalizer schema required by CLI)
  - Task 2.1 blocks Task 2.2, 2.3 (schema migration first)
  - Task 3.1 blocks Task 3.2, 3.3 (ProviderRegistry must be wired first)
  - Task 5.1 blocks Task 5.2, 5.3

- **Recommended Execution Groups**:
  - Group 1: Task 1.1 (foundation — must complete alone)
  - Group 2: Task 1.2, Task 1.3, Task 1.6 (parallel — all depend only on Task 1.1 / independent)
  - Group 3: Task 1.4, Task 1.5 (parallel — depend on Group 1)
  - Group 4: Task 1.7, Task 1.8 (parallel — depend on Groups 2–3)
  - Group 5: Task 2.1 (database migration — must complete alone)
  - Group 6: Task 2.2, Task 2.3 (parallel — depend on Task 2.1)
  - Group 7: Task 3.1 (Extension wiring — must complete alone)
  - Group 8: Task 3.2, Task 3.3 (parallel — depend on Task 3.1)
  - Group 9: Task 4.1, Task 4.2 (parallel — independent of Phase 3)
  - Group 10: Task 5.1, Task 5.2 (parallel after Group 8 complete)
  - Group 11: Task 5.3 (cleanup — must be last)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/workflow-runtime/scripts/connectors/__init__.py` | Create | ConnectorRegistry — discovers and routes to provider connectors |
| Task 1.1 | `skills/workflow-runtime/scripts/connectors/base.py` | Create | ProviderConnector abstract base class |
| Task 1.2 | `skills/workflow-runtime/scripts/connectors/antigravity.py` | Create | AntigravityConnector — reads BRAIN_ROOT transcripts |
| Task 1.2 | `skills/workflow-runtime/scripts/connectors/claude_code.py` | Create | ClaudeCodeConnector — reads Claude Code log paths |
| Task 1.3 | `skills/workflow-runtime/scripts/connectors/cursor.py` | Create | CursorConnector — reads Cursor log paths |
| Task 1.3 | `skills/workflow-runtime/scripts/connectors/vscode_agents.py` | Create | VSCodeAgentsConnector — reads VS Code AI log paths |
| Task 1.4 | `skills/workflow-runtime/scripts/transcript_engine.py` | Create | IncrementalTranscriptReader + TranscriptParser |
| Task 1.5 | `skills/workflow-runtime/scripts/normalizer.py` | Create | UsageNormalizer → NormalizedUsageRecord |
| Task 1.6 | `skills/workflow-runtime/scripts/cost_engine.py` | Create | CostEngine — reads pricing.json, calculates costs |
| Task 1.6 | `skills/workflow-runtime/data/pricing.json` | Create | Versioned pricing data for all providers/models |
| Task 1.7 | `skills/workflow-runtime/scripts/provider_engine.py` | Create | Standalone CLI: detect, parse, pricing, diagnose |
| Task 1.8 | `skills/workflow-runtime/scripts/transcript_engine.py` | Modify | Add hash-tracking and SQLite cache integration |
| Task 2.1 | `skills/workflow-runtime/scripts/db.py` | Modify | Add runtime_events + connector_diagnostics tables; add accuracy_source + raw_payload to provider_requests |
| Task 2.2 | `skills/workflow-runtime/scripts/db.py` | Modify | Separate runtime query functions from billing query functions |
| Task 2.3 | `skills/workflow-runtime/scripts/context.py` | Modify | Replace char-count estimation with ConnectorRegistry calls; add WorkflowMetadataAdapter |
| Task 2.3 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Add `provider` subcommand dispatching to provider_engine.py |
| Task 3.1 | `extensions/visualizer/src/extension.ts` | Modify | Remove estimateContextUsage(); add ProviderRegistry spawn; add updateDiagnosticsData() |
| Task 3.2 | `extensions/visualizer/resources/webview.html` | Modify | Add DiagnosticsPanel section (collapsible sidebar) |
| Task 3.3 | `extensions/visualizer/resources/webview.html` | Modify | Add AccuracyBadge to all metric cards; add Source/Provider/Model/Last Updated metadata |
| Task 4.1 | `skills/workflow-runtime/scripts/event_bus.py` | Create | Runtime Event Bus: EventCapture + EventReplay |
| Task 4.2 | `skills/workflow-runtime/scripts/log_collectors.py` | Create | IDE Log Collectors for Antigravity and Claude Code |
| Task 5.1 | `skills/workflow-runtime/tests/test_connectors.py` | Create | Unit tests: connector detection, path resolution |
| Task 5.1 | `skills/workflow-runtime/tests/test_transcript_engine.py` | Create | Unit tests: incremental parsing, hash tracking, JSONL |
| Task 5.1 | `skills/workflow-runtime/tests/test_normalization.py` | Create | Unit tests: NormalizedUsageRecord completeness per provider |
| Task 5.1 | `skills/workflow-runtime/tests/test_pricing.py` | Create | Unit tests: cost calculation accuracy vs. published rates |
| Task 5.1 | `skills/workflow-runtime/tests/test_db_schema.py` | Create | Integration: new tables, columns, indexes present |
| Task 5.1 | `skills/workflow-runtime/tests/test_aiwf_optional.py` | Create | Integration: dashboard loads without .agents/ directory |
| Task 5.1 | `skills/workflow-runtime/tests/test_transcript_performance.py` | Create | Performance: 50MB parse <5s; incremental <200ms |
| Task 5.2 | `skills/workflow-runtime/tests/test_runtime.py` | Do Not Modify | Regression: all existing tests must pass unchanged |
| Task 5.3 | `extensions/visualizer/src/extension.ts` | Modify | Remove estimateContextUsage() and hardcoded pricing constants |
| Task 5.3 | `skills/workflow-runtime/scripts/context.py` | Modify | Remove old char/3 estimation code path |
| All | `extensions/visualizer/src/webviewHtml.ts` | Do Not Modify | Auto-generated by build.js from webview.html — never edit directly |

---

## 5. Blueprint Preparation Inputs

- **Interfaces / Classes / Modules to design in Blueprint**:
  - `ProviderConnector` abstract base: `detect() -> DetectedProvider`, `discover_conversations() -> list[str]`, `parse_conversation(conv_id) -> list[NormalizedUsageRecord]`, `get_diagnostics() -> DiagnosticsResult`
  - `ConnectorRegistry`: `register(connector: ProviderConnector)`, `detect_all() -> list[DetectedProvider]`, `parse(provider, conv_id) -> list[NormalizedUsageRecord]`
  - `IncrementalTranscriptReader`: `read_new(file_path, last_hash) -> (new_lines[], new_hash)`
  - `CostEngine`: `calculate(provider, model, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens) -> CostResult`
  - `WorkflowMetadataAdapter`: `get_workflow_metadata(state_dir) -> WorkflowMetadata | None`
  - `EventBus`: `emit(event: RuntimeEvent)`, `subscribe(event_type, handler)`, `replay(conversation_id) -> list[RuntimeEvent]`

- **Provider Pattern details**:
  - Each connector must be discoverable from `connectors.json` manifest
  - Auto-detection must check OS-specific default paths before using environment variable overrides
  - Accuracy source must be set at parse time, not at display time

- **Data Flow / Sequence Flow**:
  - Extension calls `provider_engine.py detect` on activation → caches detected providers
  - Extension calls `provider_engine.py parse --provider X --conv-id Y` on session update → provider_engine reads SQLite cache first, if cache miss → reads transcript incrementally → normalizes → writes to SQLite → returns JSON
  - Extension merges AIWF workflow metadata (if .agents/ exists) via `workflow_runtime.py` as before
  - DiagnosticsPanel calls `provider_engine.py diagnose` → displays per-provider status

- **Migration Strategy & Testing Architecture**:
  - Phase 1 and Phase 2 run old and new code paths in parallel (dual-write)
  - Phase 3 switches UI to new path exclusively
  - Phase 5 removes old path — only after all regression tests green
  - SQLite migrations must be additive-only: ALTER TABLE ADD COLUMN or CREATE TABLE IF NOT EXISTS

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `test_connectors.py` → Task 1.2, 1.3 (connector detection and path resolution)
  - `test_transcript_engine.py` → Task 1.4, 1.8 (incremental parsing, hash tracking)
  - `test_normalization.py` → Task 1.5 (NormalizedUsageRecord field completeness)
  - `test_pricing.py` → Task 1.6 (cost calculation accuracy)
  - `test_accuracy_labels.py` → Task 3.1 (accuracy level assignment)

- **Integration Tests**:
  - `test_db_schema.py` → Task 2.1, 2.2 (schema migration, new tables)
  - `test_aiwf_optional.py` → Task 2.3 (AIWF-free usage dashboard load)
  - `test_provider_engine_integration.py` → Task 1.7 (end-to-end CLI flow)

- **Performance Tests**:
  - `test_transcript_performance.py` → Task 1.4, 1.8 (50MB parse <5s; cached <200ms)
  - `test_sqlite_query_performance.py` → Task 2.1 (dashboard queries <100ms at 1M rows)

- **Compatibility / Regression Tests**:
  - `test_runtime.py` (existing, unmodified) → Task 5.2 — all existing tests pass
  - Connector detection on Windows, macOS, Linux → Task 1.2, 1.3

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] `provider_engine.py detect` returns DetectedProvider JSON for Antigravity environment
  - [ ] `provider_engine.py parse` returns NormalizedUsageRecord[] with accuracy_source field
  - [ ] `provider_engine.py pricing` returns cost matching published rate within ±1%
  - [ ] Hash tracking confirmed: second run on unchanged transcript reads SQLite cache only
  - [ ] All unit tests in `test_connectors.py`, `test_transcript_engine.py`, `test_normalization.py`, `test_pricing.py` pass

- **Phase 2 Exit Criteria**:
  - [ ] New SQLite tables (`runtime_events`, `connector_diagnostics`) created without data loss
  - [ ] Existing `project_runtime.db` migrated successfully (all existing rows preserved)
  - [ ] `WorkflowMetadataAdapter` tested: workflow data available when .agents/ exists, graceful None when absent
  - [ ] `workflow_runtime.py provider` subcommand dispatches correctly to provider_engine.py

- **Phase 3 Exit Criteria**:
  - [ ] DiagnosticsPanel visible in Extension sidebar with correct provider status
  - [ ] All metric cards display AccuracyBadge (green for provider_reported, amber for estimated)
  - [ ] Extension loads without .agents/ directory — usage cards show provider data, workflow cards show "N/A"

- **Phase 4 Exit Criteria**:
  - [ ] Runtime Event Bus emits and replays events correctly
  - [ ] IDE Log Collectors detect log paths for Antigravity and Claude Code on all OS targets

- **Phase 5 Exit Criteria**:
  - [ ] 100% of existing `test_runtime.py` tests pass unchanged
  - [ ] `estimateContextUsage()` function removed from extension.ts with no regressions
  - [ ] Hardcoded pricing constants removed from context.py and extension.ts
  - [ ] Test coverage ≥ 80% on all new Python modules

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - Trigger: provider_engine.py returns incorrect data for known Antigravity transcript
  - Steps: Revert to existing context.py parse_transcript() flow; remove connectors/ directory
  - Recovery: Existing estimation path continues operating; no user-visible regression

- **Phase 2 Rollback**:
  - Trigger: SQLite migration causes data loss or corrupts existing records
  - Steps: Restore project_runtime.db from automated pre-migration backup; revert db.py changes
  - Recovery: All historical usage data restored; revert to pre-FEAT-048 schema

- **Phase 3 Rollback**:
  - Trigger: Extension fails to load or DiagnosticsPanel causes crash
  - Steps: Revert extension.ts and webview.html to pre-Phase-3 commit; rebuild webviewHtml.ts
  - Recovery: Extension returns to previous UI without Diagnostics features

- **Phase 5 Rollback**:
  - Trigger: Any existing test_runtime.py test fails after deprecated code removal
  - Steps: Revert deprecation commits; restore estimateContextUsage() and pricing constants temporarily
  - Recovery: Dual-path operation restored until root cause identified

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime DB | Extension | webview.html | Memory | Test Files |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Task 1.1 | Yes | Yes | No | No | No | No | No |
| Task 1.2 | Yes | Yes | No | No | No | No | Yes |
| Task 1.3 | Yes | Yes | No | No | No | No | Yes |
| Task 1.4 | Yes | Yes | No | No | No | No | Yes |
| Task 1.5 | Yes | Yes | No | No | No | No | Yes |
| Task 1.6 | Yes | Yes | No | No | No | No | Yes |
| Task 1.7 | Yes | Yes | No | No | No | No | Yes |
| Task 1.8 | Yes | Yes | Yes | No | No | No | Yes |
| Task 2.1 | Yes | Yes | Yes | No | No | Yes | Yes |
| Task 2.2 | Yes | Yes | Yes | No | No | No | No |
| Task 2.3 | Yes | Yes | No | No | No | No | Yes |
| Task 3.1 | Yes | No | No | Yes | No | No | No |
| Task 3.2 | Yes | No | No | Yes | Yes | No | No |
| Task 3.3 | Yes | No | No | Yes | Yes | No | No |
| Task 4.1 | Yes | Yes | Yes | No | No | No | Yes |
| Task 4.2 | Yes | Yes | No | No | No | No | Yes |
| Task 5.1 | No | No | No | No | No | No | Yes |
| Task 5.2 | No | No | No | No | No | No | No |
| Task 5.3 | Yes | Yes | No | Yes | No | No | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**:
  - `skills/workflow-runtime/scripts/provider_engine.py`
  - `skills/workflow-runtime/scripts/connectors/` (5 files)
  - `skills/workflow-runtime/scripts/transcript_engine.py`
  - `skills/workflow-runtime/scripts/normalizer.py`
  - `skills/workflow-runtime/scripts/cost_engine.py`
  - `skills/workflow-runtime/data/pricing.json`

- **Phase 2 Artifacts**:
  - Updated `skills/workflow-runtime/scripts/db.py`
  - Updated `skills/workflow-runtime/scripts/context.py`
  - Updated `skills/workflow-runtime/scripts/workflow_runtime.py`

- **Phase 3 Artifacts**:
  - Updated `extensions/visualizer/src/extension.ts`
  - Updated `extensions/visualizer/resources/webview.html`
  - Rebuilt `extensions/visualizer/src/webviewHtml.ts` (via build.js)

- **Phase 4 Artifacts**:
  - `skills/workflow-runtime/scripts/event_bus.py`
  - `skills/workflow-runtime/scripts/log_collectors.py`

- **Phase 5 Artifacts**:
  - 7 new test files under `skills/workflow-runtime/tests/`
  - Final cleaned `extension.ts` (deprecated functions removed)
  - Final cleaned `context.py` (estimation path removed)
  - `docs/designs/FEAT-048_provider_centric_runtime_and_usage_engine_blueprint.md`

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Full sequential execution (19 tasks × avg 3h) ≈ 57 engineer-hours
- **Parallel execution opportunities**:
  - Phase 1 Group 2 (Task 1.2, 1.3, 1.6): 3 independent tasks → parallel saves ~6h
  - Phase 1 Group 3 (Task 1.4, 1.5): 2 independent tasks → saves ~3h
  - Phase 3 Group 8 (Task 3.2, 3.3): 2 independent UI tasks → saves ~2h
  - Phase 4 (Task 4.1, 4.2): 2 independent tasks → saves ~3h
- **Expected token savings**: N/A — infrastructure feature
- **Recommended execution strategy**: Use Parallel Execution Groups as defined in Section 3. Total wall-clock time with full parallelism: ~30–35 engineer-hours (vs. 57 sequential)
- **Critical path**: Task 1.1 → Task 1.4 → Task 1.5 → Task 1.7 → Task 2.3 → Task 3.1 → Task 3.3 → Task 5.2 → Task 5.3

---

## Recommended Next Skill
/blueprint
