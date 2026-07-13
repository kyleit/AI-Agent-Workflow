<!-- File path: docs/plans/FEAT-049_transcript_first_accounting_system_plan.md -->

---
feature_id: FEAT-049
feature_name: Transcript-First Accounting System
status: reviewed
stage: planning
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../brainstorming/FEAT-049_transcript_first_accounting_system.md
next_artifact: ../designs/FEAT-049_transcript_first_accounting_system_blueprint.md
---

# FEAT-049: Transcript-First Accounting System

## 1. Requirement Coverage Matrix

| Req ID | Priority | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :--- | :---: |
| FR-01 | Must | Phase 1 | Task 1.1 | FingerprintEngine + request_fingerprints table | [x] |
| FR-02 | Must | Phase 1 | Task 1.2 | Accuracy Priority Ladder in NormalizedUsageRecord v2 | [x] |
| FR-03 | Must | Phase 1 | Task 1.3 | ITranscriptParser interface + 4 provider implementations | [x] |
| FR-04 | Must | Phase 1 | Task 1.4 | Common parser schema (12 fields) in NormalizedUsageRecord v2 | [x] |
| FR-06 | Must | Phase 1 | Task 1.5 | IncrementalTranscriptReader extended with transcript_offset | [x] |
| FR-12 | Must | Phase 1 | Task 1.1 | Duplicate detection in FingerprintEngine | [x] |
| FR-14 | Must | Phase 2 | Task 2.2 | Historical cost lock in CostEngine v2 | [x] |
| FR-07 | Must | Phase 2 | Task 2.1 | ReconciliationEngine + ReconciliationReport (8 fields) | [x] |
| FR-08 | Must | Phase 2 | Task 2.2 | Versioned Pricing Engine + pricing_versions table | [x] |
| NFR-01 | Must | Phase 2 | Task 2.1 | Determinism guarantee in ReconciliationEngine | [x] |
| NFR-02 | Must | Phase 2 | Task 2.3 | DB batch insert + WAL + fingerprint index | [x] |
| NFR-06 | Must | Phase 4 | Task 4.1 | Stress test suite (100 convs, 10k requests) | [x] |
| FR-05 | Should | Phase 2 | Task 2.3 | Raw payload preservation (transcript_offset pointer) | [x] |
| FR-09 | Should | Phase 3 | Task 3.2 | Per-request accuracy badge extension | [x] |
| FR-10 | Should | Phase 3 | Task 3.3 | Dashboard accuracy % breakdown panel | [x] |
| FR-11 | Should | Phase 3 | Task 3.1 | Validation CLI: validate / reconcile / doctor / diff | [x] |
| FR-13 | Should | Phase 3 | Task 3.1 | Impossible value detection in UsageValidator | [x] |
| NFR-03 | Should | Phase 3 | Task 3.1 | Idempotency enforcement in usage reconcile | [x] |
| NFR-04 | Should | Phase 2 | Task 2.3 | Storage: offset pointer, not duplicated BLOB | [x] |
| NFR-05 | Must | Phase 1 | Task 1.6 | Backward compat: all 71 FEAT-048 tests pass | [x] |

## 2. Task Ownership & Roles

### Phase 1 — Core Identity & Parser Layer
- **Task 1.1**: [Coder] Implement FingerprintEngine (fingerprint_engine.py) with SHA-256 computation + DB dedup against request_fingerprints table. Extend db.py to create request_fingerprints table.
- **Task 1.2**: [Coder] Extend NormalizedUsageRecord (connectors/base.py) with 4 new fields: fingerprint, tool_tokens, transcript_offset, raw_metadata. Maintain safe defaults for backward compat.
- **Task 1.3**: [Coder] Define ITranscriptParser abstract interface. Extend all 4 provider connectors (antigravity, claude_code, cursor, vscode_agents) to implement it with fingerprint + tool_tokens extraction.
- **Task 1.4**: [Coder] Extend provider_engine.py to wire FingerprintEngine into the parse pipeline. Update common parser output to include all 12 schema fields.
- **Task 1.5**: [Coder] Extend IncrementalTranscriptReader (transcript_engine.py) to output transcript_offset per line. Update all consumers to handle the new field.
- **Task 1.6**: [Reviewer] Run full FEAT-048 regression suite (71 tests) to confirm zero regressions from Phase 1 changes.

### Phase 2 — Reconciliation & Versioned Pricing
- **Task 2.1**: [Coder] Implement ReconciliationEngine (reconciliation_engine.py) and ReconciliationReport dataclass (8 fields: discovered, parsed, duplicates_ignored, corrupted, missing_metadata, reconstructed, estimated, confidence_score). Add reconciliation_reports DB table.
- **Task 2.2**: [Coder] Extend CostEngine (cost_engine.py) with pricing_version param and effective_date range lookup. Add pricing_versions DB table. Update pricing.json schema with version + effective_date. Implement historical cost lock (immutable once stored).
- **Task 2.3**: [Coder] Implement DB performance layer: batch INSERT (1000 records/tx), WAL mode verification, idx_fingerprints_hash index, idx_pricing_versions_effective index. Implement transcript_offset storage strategy (pointer, not BLOB).

### Phase 3 — Validation CLI & Dashboard
- **Task 3.1**: [Coder] Implement UsageValidator (usage_validator.py) with 4 CLI commands: usage validate, usage reconcile, usage doctor, usage diff. Include impossible value detection (negative tokens, total < input+output, empty model, future timestamp). Enforce idempotency on reconcile.
- **Task 3.2**: [Coder] Extend AccuracyBadge CSS (webview.html) with tool_tokens accuracy class. Wire per-request badge to accuracy_source field from NormalizedUsageRecord v2.
- **Task 3.3**: [Coder] Add Reconciliation Report collapsible panel to DiagnosticsPanel (webview.html). Implement accuracy % breakdown row (Provider Reported / Derived / Estimated). Add Last Reconciliation timestamp to status bar. Add UPDATE_RECONCILIATION message type to extension.ts.

### Phase 4 — Stress Testing & Release Gate
- **Task 4.1**: [Test Developer] Implement test_stress_suite.py: 100 simulated conversations, 10,000 mixed-provider requests, 3x determinism scan verification.
- **Task 4.2**: [Reviewer] Run full regression: 71 FEAT-048 tests + all new Phase 1-3 tests. Verify AC-01 through AC-07 from brainstorming document.
- **Task 4.3**: [Documentation Writer] Update project memory (project-summary.md, architecture notes). Write ADR-006 (fingerprint algorithm decision).

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3 -> Task 1.4 -> Task 1.5 -> Task 1.6
  - FingerprintEngine must exist before connectors call it
  - NormalizedUsageRecord must be extended before parsers use new fields
- **Sequential**: Task 2.1 -> Task 2.2 -> Task 2.3 (reconciliation depends on pricing, performance layer is last)
- **Parallel Tasks in Phase 3**: [Task 3.1, Task 3.2] (CLI and badge work are independent)
- **Sequential**: Task 3.3 depends on Task 3.2 (extension dashboard needs badge CSS first)
- **Blocking Tasks**:
  - Task 1.6 (regression gate) blocks Phase 2 start
  - Task 4.2 (full regression gate) blocks release
- **Independent Tasks**: Task 4.3 (documentation) can run in parallel with Task 4.1, Task 4.2

- **Recommended Execution Groups**:
  - Group 1: Task 1.1 (FingerprintEngine + DB table)
  - Group 2: Task 1.2 (NormalizedUsageRecord v2 extension)
  - Group 3: Task 1.3 (ITranscriptParser + 4 connectors)
  - Group 4: Task 1.4, Task 1.5 (Parallel — provider_engine wire + transcript_offset)
  - Group 5: Task 1.6 (Regression gate — STOP if fails)
  - Group 6: Task 2.1 (ReconciliationEngine)
  - Group 7: Task 2.2 (CostEngine v2 + versioned pricing)
  - Group 8: Task 2.3 (DB performance layer)
  - Group 9: Task 3.1, Task 3.2 (Parallel — CLI + badge)
  - Group 10: Task 3.3 (Dashboard panel)
  - Group 11: Task 4.1, Task 4.3 (Parallel — stress tests + docs)
  - Group 12: Task 4.2 (Full regression gate — STOP if fails)

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | skills/workflow-runtime/scripts/fingerprint_engine.py | Create | New FingerprintEngine module |
| Task 1.1 | skills/workflow-runtime/scripts/db.py | Modify | Add request_fingerprints table creation |
| Task 1.2 | skills/workflow-runtime/scripts/connectors/base.py | Modify | Extend NormalizedUsageRecord +4 fields |
| Task 1.3 | skills/workflow-runtime/scripts/connectors/antigravity.py | Modify | Add ITranscriptParser impl + tool_tokens |
| Task 1.3 | skills/workflow-runtime/scripts/connectors/claude_code.py | Modify | Add ITranscriptParser impl + tool_tokens |
| Task 1.3 | skills/workflow-runtime/scripts/connectors/cursor.py | Modify | Add ITranscriptParser impl + tool_tokens |
| Task 1.3 | skills/workflow-runtime/scripts/connectors/vscode_agents.py | Modify | Add ITranscriptParser impl + tool_tokens |
| Task 1.4 | skills/workflow-runtime/scripts/provider_engine.py | Modify | Wire FingerprintEngine into parse pipeline |
| Task 1.5 | skills/workflow-runtime/scripts/transcript_engine.py | Modify | Add transcript_offset output per line |
| Task 2.1 | skills/workflow-runtime/scripts/reconciliation_engine.py | Create | New ReconciliationEngine module |
| Task 2.1 | skills/workflow-runtime/scripts/db.py | Modify | Add reconciliation_reports table |
| Task 2.2 | skills/workflow-runtime/scripts/cost_engine.py | Modify | Add pricing_version param + effective_date lookup |
| Task 2.2 | skills/workflow-runtime/scripts/db.py | Modify | Add pricing_versions table |
| Task 2.2 | skills/workflow-runtime/data/pricing.json | Modify | Add version + effective_date per model |
| Task 2.3 | skills/workflow-runtime/scripts/db.py | Modify | Add batch insert helper + performance indexes |
| Task 3.1 | skills/workflow-runtime/scripts/usage_validator.py | Create | New UsageValidator CLI module |
| Task 3.2 | extensions/visualizer/resources/webview.html | Modify | Extend AccuracyBadge CSS + tool_tokens class |
| Task 3.3 | extensions/visualizer/resources/webview.html | Modify | Add Reconciliation Report panel + accuracy % row |
| Task 3.3 | extensions/visualizer/src/extension.ts | Modify | Add reconciliation_summary + UPDATE_RECONCILIATION |
| Task 3.3 | extensions/visualizer/src/webviewHtml.ts | Do Not Modify | Auto-generated from webview.html via build.js |
| Task 4.1 | skills/workflow-runtime/tests/test_stress_suite.py | Create | Stress test: 100 convs, 10k requests |
| Task 4.1 | skills/workflow-runtime/tests/test_fingerprint_engine.py | Create | Unit tests for FingerprintEngine |
| Task 4.1 | skills/workflow-runtime/tests/test_reconciliation_engine.py | Create | Unit tests for ReconciliationEngine |
| Task 4.1 | skills/workflow-runtime/tests/test_usage_validator.py | Create | Unit tests for UsageValidator CLI |
| Task 4.1 | skills/workflow-runtime/tests/test_versioned_pricing.py | Create | Unit tests for versioned pricing + historical lock |
| Task 4.1 | skills/workflow-runtime/tests/test_transcript_first_pipeline.py | Create | Integration test: end-to-end pipeline |
| Task 4.3 | docs/adr/ADR-006_fingerprint_algorithm_selection.md | Create | ADR for SHA-256 fingerprint decision |
| Task 4.3 | .agents/memory/project-summary.md | Modify | Add FEAT-049 modules to main modules list |

## 5. Blueprint Preparation Inputs

- **Interfaces / Classes / Modules**:
  - ITranscriptParser: abstract base class with parse_conversation(), compute_fingerprint(), extract_tool_tokens()
  - FingerprintEngine: sha256_fingerprint(fields: dict) -> str; is_duplicate(conn, fingerprint) -> bool; register(conn, fingerprint, metadata)
  - ReconciliationReport: dataclass with 8 fields + to_dict(), confidence computation
  - ReconciliationEngine: sync(conn, transcript_paths) -> ReconciliationReport; is_idempotent by design
  - CostEngine v2: calculate(record, pricing_version=None) -> CostResult; get_pricing_version(provider, model, timestamp) -> str
  - UsageValidator: validate(conn), reconcile(conn), doctor(conn), diff(conn, run_id_a, run_id_b)

- **Provider Pattern Details**:
  - Each connector extends both ProviderConnector (FEAT-048) and ITranscriptParser (FEAT-049)
  - Fingerprint computed pre-normalization from raw payload fields
  - tool_tokens defaults to 0 with accuracy_source = estimated when not available in provider payload

- **Data Flow / Sequence Flow**:
  - transcript.jsonl -> IncrementalTranscriptReader (cursor+hash, +offset) -> Parser -> FingerprintEngine (dedup check) -> NormalizedUsageRecord v2 -> CostEngine v2 (versioned pricing) -> DB insert -> ReconciliationEngine (aggregate) -> Dashboard

- **Migration Strategy & Testing Architecture**:
  - All DB changes via ALTER TABLE ADD COLUMN IF NOT EXISTS (idempotent, backward-safe)
  - All NormalizedUsageRecord new fields have safe defaults (None/0/-1)
  - FEAT-048 regression suite (71 tests) run as gate before each phase merge
  - New test files isolated in skills/workflow-runtime/tests/ following existing naming conventions

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - test_fingerprint_engine.py -- SHA-256 stability, dedup detection (Task 1.1)
  - test_reconciliation_engine.py -- 8-field report, idempotency, confidence score (Task 2.1)
  - test_versioned_pricing.py -- historical lock, effective_date lookup (Task 2.2)
  - test_usage_validator.py -- 4 CLI commands, impossible value detection (Task 3.1)

- **Integration Tests**:
  - test_transcript_first_pipeline.py -- full pipeline: transcript -> fingerprint -> normalize -> cost -> reconcile (Task 4.1)
  - test_historical_pricing.py -- cost unchanged after pricing.json update (Task 2.2)

- **Compatibility / Regression Tests**:
  - All 71 FEAT-048 tests must pass after Phase 1 changes (Task 1.6 gate)
  - test_db_schema.py extended with 3 new tables + 4 new columns (Task 4.1)
  - test_normalization.py extended with 4 new NormalizedUsageRecord fields (Task 4.1)
  - test_connectors.py extended with ITranscriptParser interface tests (Task 4.1)
  - test_transcript_performance.py extended with 10k request benchmark (Task 4.1)

- **Stress Tests**:
  - test_stress_suite.py -- 100 conversations, 10k requests, mixed providers, 3x determinism scan (Task 4.1)

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] FingerprintEngine computes stable SHA-256; test_fingerprint_dedup passes.
  - [ ] NormalizedUsageRecord v2 has all 4 new fields with safe defaults.
  - [ ] All 4 provider connectors implement ITranscriptParser.
  - [ ] IncrementalTranscriptReader outputs transcript_offset.
  - [ ] All 71 FEAT-048 existing tests pass (regression gate).

- **Phase 2 Exit Criteria**:
  - [ ] ReconciliationEngine produces 8-field report; idempotency verified.
  - [ ] CostEngine v2 looks up pricing by effective_date; historical cost lock confirmed.
  - [ ] 3 new DB tables created + 4 new columns in provider_requests (idempotent).
  - [ ] Batch insert + fingerprint index present; performance baseline confirmed.

- **Phase 3 Exit Criteria**:
  - [ ] All 4 validation CLI commands (validate / reconcile / doctor / diff) exit 0 on clean data.
  - [ ] Impossible value detection flags bad records in doctor output.
  - [ ] Dashboard accuracy % panel renders; % sum = 100%.
  - [ ] Reconciliation Report panel visible in DiagnosticsPanel.
  - [ ] Extension TypeScript compiles with 0 errors.

- **Phase 4 Exit Criteria**:
  - [ ] test_stress_suite.py passes: 100 convs, 10k requests, 3x determinism (zero drift).
  - [ ] All new tests pass + all 71 FEAT-048 tests pass (full regression gate).
  - [ ] AC-01 through AC-07 from brainstorming document verified.
  - [ ] ADR-006 written and committed.
  - [ ] project-summary.md updated with FEAT-049 modules.

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - Trigger: FingerprintEngine causes incorrect dedup (false positive) failing test_fingerprint_dedup.
  - Steps: Revert fingerprint_engine.py and db.py additions; disable FingerprintEngine flag; restore FEAT-048-only pipeline.
  - Recovery: All 71 FEAT-048 tests re-verified on reverted state.

- **Phase 2 Rollback**:
  - Trigger: ReconciliationEngine produces non-deterministic output or CostEngine v2 alters historical costs unexpectedly.
  - Steps: Revert reconciliation_engine.py and cost_engine.py; revert pricing.json changes; drop new tables (pricing_versions, reconciliation_reports) via migration rollback script.
  - Recovery: Re-run FEAT-048 test suite to confirm stable baseline.

- **Phase 3 Rollback**:
  - Trigger: Extension fails to compile or webview crashes on UPDATE_RECONCILIATION message.
  - Steps: Revert extension.ts and webview.html to pre-Phase 3 state; rebuild webviewHtml.ts via build.js.
  - Recovery: Extension package re-tested in VS Code development host.

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | No | No | No | No | Yes |
| Task 1.2 | Yes | Yes | No | No | No | No | No |
| Task 1.3 | Yes | Yes | No | No | No | No | No |
| Task 1.4 | Yes | Yes | Yes | No | No | No | No |
| Task 1.5 | Yes | Yes | No | No | No | No | No |
| Task 1.6 | No | No | No | No | No | No | No |
| Task 2.1 | Yes | Yes | No | No | No | No | Yes |
| Task 2.2 | Yes | Yes | No | No | No | No | Yes |
| Task 2.3 | Yes | Yes | No | No | No | No | Yes |
| Task 3.1 | Yes | Yes | Yes | No | No | No | No |
| Task 3.2 | Yes | No | No | Yes | No | No | No |
| Task 3.3 | Yes | No | No | Yes | No | No | No |
| Task 4.1 | Yes | No | No | No | No | No | No |
| Task 4.2 | No | No | No | No | No | No | No |
| Task 4.3 | No | No | No | No | Yes | Yes | No |

## 10. Artifact Production Plan

- **Phase 1 Artifacts**:
  - skills/workflow-runtime/scripts/fingerprint_engine.py (new)
  - Extended: connectors/base.py, transcript_engine.py, all 4 connectors, db.py, provider_engine.py

- **Phase 2 Artifacts**:
  - skills/workflow-runtime/scripts/reconciliation_engine.py (new)
  - Extended: cost_engine.py, db.py, data/pricing.json

- **Phase 3 Artifacts**:
  - skills/workflow-runtime/scripts/usage_validator.py (new)
  - Extended: webview.html, extension.ts

- **Phase 4 Artifacts**:
  - 6 new test files (fingerprint, reconciliation, validator, versioned_pricing, pipeline, stress_suite)
  - docs/adr/ADR-006_fingerprint_algorithm_selection.md (new)
  - Extended: .agents/memory/project-summary.md
  - docs/plans/FEAT-049_transcript_first_accounting_system_plan.md (this document)
  - docs/designs/FEAT-049_transcript_first_accounting_system_blueprint.md (next phase)

## 11. Token & Execution Optimization

- **Sequential execution cost**: ~16 tasks across 4 phases; estimated 4-5 sessions
- **Parallel execution opportunities**:
  - Task 1.4 + Task 1.5 (Group 4): provider_engine wiring and transcript_offset extension are independent
  - Task 3.1 + Task 3.2 (Group 9): CLI validation and badge CSS are independent
  - Task 4.1 + Task 4.3 (Group 11): stress tests and documentation are independent
- **Expected token savings**: ~25% vs sequential execution by parallelizing Groups 4, 9, 11
- **Recommended execution strategy**: Follow Execution Groups 1-12 in order; stop at regression gates (Groups 5, 12) if failures detected before proceeding

## Recommended Next Skill
/blueprint