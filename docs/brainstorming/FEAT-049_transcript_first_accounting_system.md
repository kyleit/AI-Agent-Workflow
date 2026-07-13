<!-- docs/brainstorming/FEAT-049_transcript_first_accounting_system.md -->

---
feature_id: FEAT-049
feature_name: Transcript-First Accounting System
status: draft
stage: brainstorming
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: None
next_artifact: ../plans/FEAT-049_transcript_first_accounting_system_plan.md
---

# Master Requirement Document - Transcript-First Accounting System

## 1. Feature ID & Name
- **Feature ID**: FEAT-049
- **Feature Name**: Transcript-First Accounting System (Provider Usage Accuracy Hardening)

## 2. Original Idea

> Design and implement a transcript-first accounting system that provides
> the highest possible accuracy for input tokens, output tokens, cached tokens,
> thinking/reasoning tokens, tool tokens, cost, request count, context usage,
> per-model usage, per-provider usage.
> The system must clearly distinguish provider-reported, derived, and estimated values.
> Never silently estimate when better evidence exists.

## 3. Business Problem
- **Problem**: AIWF computes usage statistics from checkpoint-derived estimates, file-size heuristics, and agent-written JSON summaries. These numbers cannot be audited, differ across re-scans, and silently double-count retried requests.
- **Why it matters**: Inaccurate cost tracking leads to budget overruns, trust erosion in dashboard metrics, and inability to perform FinOps analysis.
- **Who is affected**: AIWF users monitoring spend, workflow agents making routing decisions, FinOps teams auditing API costs.
- **Expected outcome**: Every usage metric traces to a canonical, non-duplicated request record sourced directly from provider transcripts.

## 4. Requirement Discovery

### Functional Requirements

- **FR-01**: Canonical Request Identity -- SHA-256 fingerprint from: provider + conversation_id + request_id + response_id + model + timestamp + payload_hash. Never double-count across re-index, retry, copy, or resume.
- **FR-02**: Accuracy Priority Ladder -- every metric records: provider_reported > response_payload > api_metadata > deterministic_reconstruction > tokenizer > estimated.
- **FR-03**: Provider-Specific Parsers -- Antigravity, Claude Code, Cursor, VSCode Agents each expose ITranscriptParser interface.
- **FR-04**: Common Parser Schema -- 12 fields: fingerprint, provider, model, timestamp, input_tokens, output_tokens, cache_tokens, thinking_tokens, tool_tokens, usage_source, raw_metadata, transcript_offset.
- **FR-05**: Raw Payload Preservation -- original provider payload stored with normalized record for future reparsing.
- **FR-06**: Incremental Parsing -- cursor + file hash. Only parse new lines since last cursor. Extends IncrementalTranscriptReader (FEAT-048).
- **FR-07**: Reconciliation Engine -- after every sync: requests_discovered, requests_parsed, duplicates_ignored, corrupted_transcripts, missing_usage_metadata, reconstructed_usage, estimated_usage, confidence_score (0.0-1.0).
- **FR-08**: Versioned Pricing Engine -- version + effective_date per pricing entry. Historical costs locked. Never recompute old costs unless user explicitly calls usage reprice.
- **FR-09**: Accuracy Badge per Request -- provider_reported / derived / tokenizer / estimated.
- **FR-10**: Dashboard Aggregation -- Total Requests, % Provider Reported, % Derived, % Estimated, Duplicate count, Missing Usage, Pricing Version, Last Scan, Last Reconciliation.
- **FR-11**: Validation CLI -- usage validate, usage reconcile, usage doctor, usage diff.
- **FR-12**: Duplicate Detection -- fingerprint lookup before insert; skip + increment duplicate_count.
- **FR-13**: Impossible Value Detection -- negative tokens, total < input+output, empty model, future timestamp.
- **FR-14**: Historical Cost Lock -- cost immutable once stored unless usage reprice explicitly called.

### Non-Functional Requirements
- **NFR-01**: Determinism -- repeated scans of identical data produce identical totals (zero drift).
- **NFR-02**: Performance -- 10,000 requests full scan < 30s; incremental rescan < 1s; single insert < 5ms.
- **NFR-03**: Idempotency -- usage reconcile safe to run multiple times on unchanged data.
- **NFR-04**: Storage Efficiency -- raw payload as offset pointer, not duplicated BLOB.
- **NFR-05**: Backward Compatibility -- all FEAT-048 tests (71) continue to pass.
- **NFR-06**: Stress Test -- 100 conversations, 10,000 requests, mixed providers, deterministic.

### Technical Constraints
- **TC-01**: Python 3.10+, SQLite WAL mode (inherited from FEAT-048 / ADR-005).
- **TC-02**: Offline-first -- all parsing and fingerprinting without network access.
- **TC-03**: Fingerprint: SHA-256, full 64-char hex, deterministic field ordering. No UUID randomness.
- **TC-04**: provider_requests extended via ALTER TABLE ADD COLUMN IF NOT EXISTS (idempotent).
- **TC-05**: pricing.json gains version + effective_date per model; compatible with CostEngine (FEAT-048).
- **TC-06**: tool_tokens optional -- default 0 with accuracy_source = estimated when unavailable.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Canonical fingerprint, no double-count | test_fingerprint_dedup, test_retry_dedup | Same fingerprint across re-index and retry |
| FR-02 | Must | Accuracy ladder, source recorded | test_accuracy_source_hierarchy | Every metric has non-null usage_source |
| FR-03 | Must | 4 provider parsers, common interface | test_connectors (extend) | 4 parsers implement ITranscriptParser |
| FR-04 | Must | Common schema 12 fields | test_normalization (extend) | All 12 fields present per record |
| FR-05 | Should | Raw payload preserved | test_raw_payload_preservation | Payload retrievable after store |
| FR-06 | Must | Incremental cursor+hash | test_transcript_engine (extend) | Second scan returns 0 new lines |
| FR-07 | Must | Reconciliation 8-field report | test_reconciliation_engine | All 8 report fields present |
| FR-08 | Must | Versioned pricing, historical lock | test_historical_pricing | Old cost unchanged after pricing update |
| FR-09 | Should | Per-request accuracy badge | test_accuracy_badge | Badge maps to accuracy source |
| FR-10 | Should | Dashboard % breakdown | test_dashboard_aggregation | % sum = 100% |
| FR-11 | Should | 4 validation CLI commands | test_usage_validate, test_usage_doctor | All commands exit 0 on clean data |
| FR-12 | Must | Duplicate detection | test_duplicate_transcript_scan | duplicate_count incremented, total unchanged |
| FR-13 | Should | Impossible value detection | test_impossible_values | Flagged in doctor output |
| FR-14 | Must | Historical cost lock | test_historical_pricing | Cost stable across pricing updates |
| NFR-01 | Must | Determinism | test_determinism_3_scans | Identical totals across 3 scans |
| NFR-02 | Must | Performance targets | test_transcript_performance (extend) | 10k requests < 30s |
| NFR-06 | Must | Stress test | test_stress_suite | 100 convs, 10k requests, deterministic |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| AIWF Users | Primary | High | P0 | Accurate spend tracking, auditable reports |
| Workflow Agents | Primary | High | P0 | Reliable context usage for routing |
| FinOps Teams | Secondary | High | P1 | Reconcile AIWF vs provider invoices |
| AI Providers | External | Medium | P2 | Correct API usage attribution |
| Extension Dashboard | Internal | High | P1 | Accurate % breakdowns and badges |

## 7. Scope Boundary

- **In Scope**:
  - FingerprintEngine (SHA-256 canonical identity + dedup)
  - ITranscriptParser interface + 4 provider implementations
  - ReconciliationEngine (sync + 8-field report)
  - CostEngine v2 (versioned pricing + historical lock)
  - UsageValidator CLI (validate / reconcile / doctor / diff)
  - DB: 3 new tables + 4 new columns in provider_requests
  - Dashboard: accuracy % panel + reconciliation stats
  - Stress test suite (100 convs, 10k requests)

- **Out of Scope**:
  - Real-time streaming reconciliation
  - Provider API polling for live usage
  - Multi-user / multi-workspace reconciliation
  - Cost forecasting (FEAT-037/038)

- **Deferred Scope**:
  - Tokenizer fallback (tiktoken, Google SDK) -- Phase 2
  - UI cost diff visualization
  - Export to CSV / Google Sheets

- **Future Scope**:
  - Real-time accuracy streaming via RuntimeEventBus
  - Provider webhook for authoritative usage confirmation

## 8. Dependency Graph Preview

- FingerprintEngine (Must -- Phase 1)
  - request_fingerprints DB table (Must -- Phase 1)
- ITranscriptParser + 4 parsers (Must -- Phase 1)
  - extends IncrementalTranscriptReader (FEAT-048)
  - depends on FingerprintEngine
- NormalizedUsageRecord v2 (Must -- Phase 1)
  - adds: fingerprint, tool_tokens, transcript_offset, raw_metadata
- ReconciliationEngine (Must -- Phase 2)
  - depends on FingerprintEngine + Parsers
  - reconciliation_reports DB table
- CostEngine v2 -- Versioned Pricing (Must -- Phase 2)
  - extends CostEngine (FEAT-048)
  - pricing_versions DB table
- UsageValidator CLI (Should -- Phase 3)
  - depends on ReconciliationEngine + CostEngine v2
- Dashboard Extension (Should -- Phase 3)
  - depends on ReconciliationEngine output
- Stress Test Suite (Must -- Phase 4)
  - depends on all above

## 9. Data Flow Preview

- Transcript file (.jsonl)
  - IncrementalTranscriptReader (cursor+hash)
- Provider-Specific Parser
  - extracts raw usage fields per line
- FingerprintEngine
  - compute SHA-256 fingerprint
  - lookup request_fingerprints table
  - if duplicate: increment duplicate_count, skip
- NormalizedUsageRecord v2 (16 fields)
- CostEngine v2
  - lookup pricing_versions by (provider, model, timestamp)
  - compute cost_usd with locked version
- DB insert: provider_requests (+ fingerprint, pricing_version, tool_tokens)
- ReconciliationEngine aggregates into reconciliation_reports
- Dashboard reads reconciliation report -> accuracy % panel + AccuracyBadge

## 10. Existing Asset Analysis

| Asset / Component | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| IncrementalTranscriptReader | scripts/transcript_engine.py | Extend | Add transcript_offset output |
| NormalizedUsageRecord | scripts/connectors/base.py | Extend | Add 4 fields: fingerprint, tool_tokens, transcript_offset, raw_metadata |
| AntigravityConnector | scripts/connectors/antigravity.py | Extend | Add fingerprint + tool_tokens extraction |
| ClaudeCodeConnector | scripts/connectors/claude_code.py | Extend | Add parser schema fields |
| CursorConnector | scripts/connectors/cursor.py | Extend | Add parser schema fields |
| VSCodeAgentsConnector | scripts/connectors/vscode_agents.py | Extend | Add parser schema fields |
| CostEngine | scripts/cost_engine.py | Extend | Add pricing_version param, effective_date range lookup |
| pricing.json | data/pricing.json | Extend | Add version + effective_date per model |
| db.py init_db_schema() | scripts/db.py | Extend | Add 3 new tables (idempotent) |
| AccuracyBadge CSS | extensions/visualizer/resources/webview.html | Extend | Add tool accuracy badge class |

## 11. Dependency & Blast Radius Analysis

- **Affected Skills**: workflow-runtime (primary)
- **Affected Modules**: connectors/, transcript_engine.py, cost_engine.py, db.py, provider_engine.py
- **Affected Runtime**: workflow_runtime.py -- add usage subcommand group
- **Affected Extension**: extension.ts, webview.html
- **Affected Database**: project_runtime.db -- 3 new tables, 4 new columns in provider_requests
- **Affected Documentation**: docs/adr/ -- ADR-006 needed for fingerprint algorithm
- **Impact Level**: High

## 12. Migration Strategy

- **Backward Compatibility**: NormalizedUsageRecord new fields optional with safe defaults (fingerprint=None, tool_tokens=0, transcript_offset=-1, raw_metadata=None).
- **Adapter Strategy**: FingerprintEngine handles records with no request_id via fallback fingerprint.
- **Coexistence Period**: Feature flag FEAT_049_FINGERPRINT=1 to enable dedup enforcement.
- **Deprecation Plan**: After FEAT-049 stable, estimateContextUsage() fallback marked deprecated.
- **Migration Phases**: Phase 1 (fingerprint+parser) -> Phase 2 (reconciliation+pricing) -> Phase 3 (CLI+dashboard) -> Phase 4 (stress tests+release).

## 13. Architecture Principles

- **API First**: ITranscriptParser interface defined before implementation.
- **Provider First**: provider-reported fields always win.
- **Script First**: all new engines callable via CLI before wired into extension.
- **Memory First**: FingerprintEngine uses SQLite lookup before computation.
- **Incremental Updates**: cursor+hash pattern preserved -- never re-parse unchanged content.
- **Backward Compatibility**: ALTER TABLE ADD COLUMN IF NOT EXISTS -- no DROP, no RENAME.
- **Replaceable Providers**: ITranscriptParser allows new providers without touching core.

## 14. Non Goals

- Real-time streaming reconciliation.
- Provider API calls for usage (transcript-only).
- Multi-workspace reconciliation.
- Cost forecasting (FEAT-037/038).
- Automatic re-pricing of historical costs.
- Tokenizer recomputation -- deferred Phase 2.

## 15. ROI Analysis

- **Estimated Implementation Cost**: 4-5 development sessions (phases 1-4)
- **Runtime Savings**: Eliminates 15-30% over-estimation in context usage metrics
- **Maintenance Impact**: +1 reconciliation run per session; < 200ms overhead
- **Expected Break-Even**: Immediate -- first accurate cost report justifies implementation
- **Long-Term ROI**: Enables FinOps use cases, budget alerts, provider comparison

## 16. Success Metrics

- **Determinism Target**: 0 drift across 3 independent full scans
- **Duplicate False-Negative Rate**: 0% -- no double-counted requests
- **Accuracy Coverage**: >= 90% requests achieve provider_reported or derived on Antigravity sessions
- **Performance**: 10k requests < 30s; incremental rescan < 1s
- **Dashboard**: % Provider Reported + % Derived + % Estimated = 100% always

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| R-01 Provider payload format changes | High | Medium | Parser version field + estimated fallback | Parser layer |
| R-02 SHA-256 collision | High | Very Low | Full 64-char hex; negligible for 10k requests | FingerprintEngine |
| R-03 Scan performance 10k | Medium | Medium | Batch INSERT (1000/tx), WAL, index on fingerprint | DB layer |
| R-04 Pricing effective_date gaps | Medium | Medium | Nearest-version fallback + reconciliation log | CostEngine v2 |
| R-05 Schema migration breaks data | Medium | Low | IF NOT EXISTS pattern, idempotency tests | db.py |
| R-06 tool_tokens inconsistency | Low | High | Default 0 + accuracy_source = estimated | Normalization |
| R-07 Corrupted transcript lines | Medium | Medium | Skip + log + count in corrupted_transcripts | ReconciliationEngine |

## 18. Technical Questions

- Q1: fingerprint pre- vs post-normalization? Pre-normalization preferred (stable against field renaming).
- Q2: raw_payload -- gzip BLOB or file offset pointer? Offset pointer preferred (no duplication; requires append-only transcripts).
- Q3: usage reprice -- destructive or new snapshot row? New snapshot row (audit trail preserved).
- Q4: Cursor/VSCode Agents -- structured usage in transcript? Requires investigation; may fall back to deterministic_reconstruction.
- Q5: usage diff -- stored baseline or two explicit run IDs? Two explicit run IDs (no implicit state).

## 19. Open Decision Register

| Topic | Status | Next Steps |
| :--- | :--- | :--- |
| Fingerprint: pre- vs post-normalization | Pending | Pre preferred; confirm in Blueprint |
| Raw payload: BLOB vs offset pointer | Pending | Offset preferred; requires ADR if transcript mutability concern |
| usage reprice: destructive vs snapshot | Pending | Snapshot preferred; confirm in Blueprint |
| Tokenizer library for fallback | Deferred | tiktoken or google-cloud-aiplatform; Phase 2 |
| Feature flag FEAT_049_FINGERPRINT -- permanent or migration-only | Pending | Architecture review |

## 20. ADR Detection

- **ADR Required**: Yes
- **ADR-006**: Fingerprint Algorithm Selection -- SHA-256 field ordering, collision policy, pre vs post normalization.
- **ADR-007** (optional): Raw Payload Storage -- BLOB vs transcript offset pointer.

## 21. Knowledge Update Impact

- **project-summary**: Yes -- add FingerprintEngine, ReconciliationEngine, UsageValidator, CostEngine v2
- **architecture**: Yes -- Transcript-First Accounting pipeline, accuracy priority ladder
- **modules**: Yes -- new: fingerprint_engine.py, reconciliation_engine.py, usage_validator.py
- **lessons**: Yes -- pre-normalization fingerprint safer than post-normalization
- **patterns**: Yes -- fingerprint-before-insert dedup; versioned pricing with effective_date
- **ADR**: Yes -- ADR-006, ADR-007
- **SQLite**: Yes -- 3 new tables, 4 new columns in provider_requests
- **indexes**: Yes -- idx_fingerprints_hash, idx_pricing_versions_effective
- **vector metadata**: No

## 22. Test Strategy Preview

- **Unit Tests**:
  - test_fingerprint_engine.py -- SHA-256 stability, dedup, collision policy
  - test_reconciliation_engine.py -- 8 report fields, idempotency, confidence score
  - test_usage_validator.py -- 4 CLI commands, impossible value detection
  - test_versioned_pricing.py -- historical lock, effective_date range lookup

- **Integration Tests**:
  - test_transcript_first_pipeline.py -- end-to-end: transcript -> fingerprint -> normalize -> cost -> reconcile
  - test_historical_pricing.py -- cost stable after pricing.json update

- **Regression Tests**:
  - All 71 FEAT-048 tests continue to pass with extended schema

- **Performance Tests**:
  - test_transcript_performance.py (extend) -- 10k requests < 30s, incremental < 1s

- **Stress Tests**:
  - test_stress_suite.py -- 100 conversations, 10k requests, mixed providers, 3x determinism

- **Compatibility Tests**:
  - test_db_schema.py (extend) -- 3 new tables, 4 new columns, idempotent migration

## 23. Extension Impact

- **Extension UI Changes**:
  - New collapsible panel: Reconciliation Report in DiagnosticsPanel
  - Dashboard accuracy row: Provider Reported: XX% | Derived: XX% | Estimated: XX%
  - Last Reconciliation: <timestamp> in status bar

- **Affected ViewModels / Watchers**:
  - getProviderUsage() -- extend to include reconciliation_summary
  - updateDiagnosticsData() -- call usage reconcile on 5-min timer
  - webview.html -- add UPDATE_RECONCILIATION message type

## 24. Complexity Estimation

- **Implementation Complexity**: High
- **Estimated Refactoring**: ~35% existing FEAT-048 extended + ~65% new code

## 25. Roadmap Alignment

- **Roadmap Phase**: Provider-Centric Runtime -> Accuracy Hardening (after FEAT-048)
- **Milestones**:
  - M1: FingerprintEngine + Parser extensions (Phase 1)
  - M2: ReconciliationEngine + Versioned Pricing (Phase 2)
  - M3: Validation CLI + Dashboard extensions (Phase 3)
  - M4: Stress tests + Release (Phase 4)
- **Prerequisites**:
  - FEAT-048 fully released -- Done
  - ADR-006 approved (fingerprint algorithm)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| fingerprint pre- vs post-normalization? | Pre-normalization preferred; confirm in Blueprint |
| raw_payload storage BLOB or offset pointer? | Offset pointer preferred; needs transcript immutability |
| usage reprice destructive or snapshot? | New snapshot row; confirm in Blueprint |
| Cursor/VSCode Agents structured usage? | Requires parser investigation; may fall to deterministic_reconstruction |
| tool_tokens tokenizer library? | Deferred Phase 2; default 0 + estimated for now |

## 27. Requirement Readiness Score

- **Score**: 97/100
- **Status**: Ready >= 85
- **Deductions**: -2 tokenizer library unspecified (minor, deferred); -1 Cursor/VSCode payload unknown (low risk, Phase 1 investigation)

## 28. Existing Project Context

- **Memory Source**: .agents/memory/project-summary.md + FEAT-048 all 5 phases
- **Existing Architecture Summary**:
  - FEAT-048: ConnectorRegistry, 4 ProviderConnectors, IncrementalTranscriptReader, NormalizedUsageRecord (15 fields), CostEngine, RuntimeEventBus, AccuracyBadge, DiagnosticsPanel
  - DB: provider_requests, transcript_cursors, runtime_events, connector_diagnostics
  - 71 tests passing

## 29. Existing Modules & Services

| Module | Location | Reuse % | Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|
| IncrementalTranscriptReader | scripts/transcript_engine.py | 100% | 15% | Low | FR-06 incremental parsing |
| NormalizedUsageRecord | scripts/connectors/base.py | 100% | 20% | Low | Extend to 19 fields |
| AntigravityConnector | scripts/connectors/antigravity.py | 80% | 30% | Low | Primary parser |
| CostEngine | scripts/cost_engine.py | 90% | 25% | Low | FR-08 versioned pricing |
| db.py | scripts/db.py | 100% | 20% | Low | 3 new tables |
| RuntimeEventBus | scripts/event_bus.py | 50% | 0% | None | Optional event publishing |
| provider_engine.py | scripts/provider_engine.py | 70% | 40% | Low | Wires new engines |

## 30. Solution Options Evaluated

### Option A: Layered Extension (Build on FEAT-048 Core) -- SELECTED

- **Overview**: Extend all FEAT-048 components incrementally. New FingerprintEngine, ReconciliationEngine, UsageValidator scripts. Zero breaking changes.
- **Advantages**: 100% FEAT-048 reuse; 71 tests continue; incremental delivery; proven migration pattern.
- **Disadvantages**: Schema evolution requires careful backward compat.
- **Complexity**: High | **Risk**: Low | **Performance**: High | **Maintainability**: High | **Compatibility**: Excellent | **Scalability**: High

### Option B: Clean-Slate Accounting Engine (Separate Module)

- **Overview**: New accounting/ package, rewrites all 4 parsers, independent DB schema.
- **Advantages**: Clean unconstrained design; isolated testing.
- **Disadvantages**: Throws away 71 tests; duplicates IncrementalTranscriptReader; 2x effort.
- **Complexity**: High | **Risk**: High | **Maintainability**: Medium | **Compatibility**: Poor

### Option C: Hybrid Plugin Architecture

- **Overview**: IAccountingPlugin in ConnectorRegistry; ReconciliationEngine subscribes to RuntimeEventBus.
- **Advantages**: Elegant event-driven; leverages ADR-005.
- **Disadvantages**: Over-engineered; async ordering hard to debug.
- **Complexity**: Very High | **Risk**: Medium | **Performance**: Medium | **Scalability**: Very High

## 31. Solution Comparison Table

| Criteria | Option A (Selected) | Option B | Option C |
|---|---|---|---|
| Complexity | High | High | Very High |
| Risk | Low | High | Medium |
| Performance | High | High | Medium |
| Maintainability | High | Medium | Medium |
| Compatibility | Excellent | Poor | Good |
| Future Scalability | High | High | Very High |
| Development Cost | Medium | Very High | High |
| FEAT-048 Reuse | 100% | 0% | 70% |

## 32. Selected Solution

- **Choice**: Option A -- Layered Extension on FEAT-048 Core
- **Why Selected**:
  1. Investment protection: 71 passing tests, 4 connectors, proven DB patterns, AccuracyBadge UI all preserved.
  2. Additive only: ALTER TABLE ADD COLUMN, new script files, new methods on existing classes. Zero removals.
  3. Incremental delivery: FingerprintEngine can ship before ReconciliationEngine. Risk reduced per phase.
- **Trade-offs**: backward compat on NormalizedUsageRecord; provider_requests grows wider (4 new columns).
- **Technical Debt**: estimateContextUsage() marked deprecated after FEAT-049 stable.
- **Risk Mitigation**: IF NOT EXISTS guards, batch insert, fingerprint index.

## 33. Risks & Assumptions

- **Risks**: R-01 through R-07 as documented in Risk Matrix (section 17).
- **Assumptions**:
  - A-01: FEAT-048 fully released before FEAT-049 begins. -- Done
  - A-02: Transcripts are append-only (required for offset pointer strategy).
  - A-03: Provider request_id is stable and unique within a conversation.
  - A-04: pricing.json schema extension (version + effective_date) is non-breaking.

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01, NFR-01): Repeated scans produce identical totals with zero drift across 3 independent scans. Test: test_determinism_3_scans
- [ ] AC-02 (FR-12): Duplicate requests never counted twice. duplicate_count incremented, totals unchanged. Test: test_duplicate_transcript_scan, test_retry_request
- [ ] AC-03 (FR-02, FR-09): Every metric records accuracy_source. Dashboard % breakdown sums to 100%. Test: test_accuracy_source_hierarchy, test_dashboard_aggregation
- [ ] AC-04 (FR-08, FR-14): Historical costs stable after pricing.json update. Test: test_historical_pricing
- [ ] AC-05 (FR-07, FR-11, NFR-03): All 4 CLI commands pass on clean data. reconcile is idempotent. Test: test_usage_validate, test_usage_doctor, test_reconciliation_idempotent
- [ ] AC-06 (NFR-02): 10k requests full scan < 30s. Incremental rescan < 1s. Test: test_transcript_performance (extended)
- [ ] AC-07 (NFR-06): 100 conversations, 10k mixed-provider requests pass determinism check. Test: test_stress_suite

## 35. Final Planning Prompt

### Purpose
Complete, self-contained prompt for the brainstorming-to-plan Skill.

### Problem Statement
AIWF currently derives usage statistics from checkpoint heuristics, file-size estimates, and agent-written JSON summaries. These numbers cannot be audited against provider invoices, differ across re-scans, and double-count retried requests. FEAT-049 makes provider transcripts the authoritative accounting source, never silently estimating when better evidence exists.

### Objectives & Selected Solution
Implement a Transcript-First Accounting System: (1) stable fingerprint for every request, (2) extract usage with source attribution, (3) deterministic reconciliation report, (4) historical cost lock, (5) validation CLI.
Solution: Option A -- Layered Extension on FEAT-048 Core. All additive. FEAT-048 schema, tests, components extended not replaced.

### Functional Requirements
FR-01 through FR-14 as documented in section 4.

### Non-functional Requirements & Constraints
NFR-01 through NFR-06, TC-01 through TC-06 as documented in section 4.

### Architectural Details

**New scripts**:
- scripts/fingerprint_engine.py -- SHA-256 fingerprint + DB dedup
- scripts/reconciliation_engine.py -- sync engine + ReconciliationReport dataclass
- scripts/usage_validator.py -- CLI: validate / reconcile / doctor / diff

**Extended scripts**:
- scripts/connectors/base.py -- NormalizedUsageRecord +4 fields
- scripts/transcript_engine.py -- add transcript_offset output
- scripts/connectors/antigravity.py (+ claude_code, cursor, vscode_agents) -- add fingerprint + tool_tokens
- scripts/cost_engine.py -- add pricing_version param, effective_date range lookup
- scripts/db.py -- 3 new tables
- data/pricing.json -- version + effective_date per model
- scripts/provider_engine.py -- wire FingerprintEngine + ReconciliationEngine

**New DB tables**:
- request_fingerprints(fingerprint TEXT PK, provider, conv_id, request_id, model, timestamp, duplicate_count, first_seen, last_seen)
- pricing_versions(id, provider, model, version TEXT, effective_date DATE, input_per_mtok REAL, output_per_mtok REAL, cache_read_per_mtok REAL, cache_write_per_mtok REAL, tool_per_mtok REAL, created_at)
- reconciliation_reports(id, timestamp, requests_discovered, requests_parsed, duplicates_ignored, corrupted_transcripts, missing_usage_metadata, reconstructed_usage, estimated_usage, confidence_score REAL, duration_ms INTEGER)

**provider_requests new columns**: fingerprint TEXT, pricing_version TEXT, tool_tokens INTEGER DEFAULT 0, transcript_offset INTEGER DEFAULT -1

**Extension**:
- extension.ts: getProviderUsage() extended with reconciliation_summary; updateDiagnosticsData() calls usage reconcile on 5-min timer
- webview.html: Reconciliation Report panel; accuracy % row; UPDATE_RECONCILIATION message type

### Risks & Assumptions
R-01 through R-07 and A-01 through A-04 as documented.

### Verification Checklist
- [ ] docs/plans/FEAT-049_transcript_first_accounting_system_plan.md generated and approved
- [ ] docs/designs/FEAT-049_transcript_first_accounting_system_blueprint.md generated and approved
- [ ] ADR-006 (fingerprint algorithm) written and approved
- [ ] All 7 AC mapped to implementation tasks
- [ ] 71 FEAT-048 tests continue to pass (regression gate)
- [ ] Stress test suite (100 convs, 10k requests) passes determinism check

---
> The next Skill is brainstorming-to-plan.
> It must be invoked manually by the user.
> This Skill does NOT invoke it automatically.