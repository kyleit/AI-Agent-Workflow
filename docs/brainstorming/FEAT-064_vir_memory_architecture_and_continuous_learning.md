<!-- docs/brainstorming/FEAT-064_vir_memory_architecture_and_continuous_learning.md -->

---
feature_id: FEAT-064
feature_name: Visual Intelligence Runtime — Memory Architecture & Continuous Learning
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-063_vir_multi_agent_orchestration_and_consensus_engine.md
next_artifact: ../plans/FEAT-064_vir_memory_learning_plan.md
---

# Master Requirement Document – VIR Memory Architecture & Continuous Learning

## 1. Feature ID & Name
- **Feature ID**: FEAT-064
- **Feature Name**: Visual Intelligence Runtime — Memory Architecture & Continuous Learning

## 2. Original Idea
Design and implement VIR's complete memory architecture: per-agent memory (5 types), runtime-level Visual Memory, Regression Engine (baseline management + regression detection), and a Continuous Learning pipeline that promotes durable lessons from closed investigations to long-term memory and the Knowledge Runtime.

## 3. Business Problem
- **Problem**: Without memory, VIR must rediscover the same bugs and patterns every run. Without baseline management, regression detection is impossible. Without continuous learning, VIR cannot improve its reasoning accuracy over time. A truly intelligent runtime must remember its past and improve from it.
- **Why it matters**: Memory is the difference between a static checker and an intelligent runtime. Each investigation makes VIR smarter, faster, and more accurate.
- **Who is affected**: All VIR agents (use long-term memory), Regression Engine (needs baselines), Cognitive Engines (need pattern history), Memory Engine (manages storage), Knowledge Runtime (receives promoted lessons).
- **Expected outcome**: A hybrid memory architecture (filesystem + SQLite + Qdrant) supporting per-agent memory, visual baseline management, regression detection, and automated learning promotion.

## 4. Requirement Discovery

### Functional Requirements

#### Storage Architecture
- FR-01: Implement hybrid storage: filesystem (binary artifacts), SQLite (structured metadata), Qdrant (semantic memory).
- FR-02: Filesystem structure under `.agents/visual-runtime/`:
  - `artifacts/baselines/` — baseline screenshots per page+viewport+feature
  - `artifacts/current/` — current run screenshots
  - `artifacts/diffs/` — diff images
  - `artifacts/annotated/` — annotated screenshots with issue overlays
  - `artifacts/videos/` — optional video recordings
  - `artifacts/traces/` — Playwright trace files
  - `artifacts/har/` — HTTP Archive files
  - `state/` — runtime state files
  - `reports/` — generated reports
  - `memory/` — long-term memory snapshots
  - `database/` — SQLite database files
- FR-03: SQLite stores all structured metadata: test runs, observations, evidence, contradictions, confidence scores, page fingerprints, component fingerprints, baseline versions, feature IDs, git commit hashes, browser/viewport metadata, issue history, fix history, regression results, agent decisions, report indexes.
- FR-04: Qdrant stores embeddings for: visual issue descriptions, UX findings, root causes, fix summaries, design lessons, similar historical failures, component-pattern knowledge.
- FR-05: Raw binary assets (screenshots) must never be stored in Qdrant; only metadata references and embeddings.

#### Per-Agent Memory
- FR-06: Short-term Memory: asyncio dict, scoped to current run, auto-cleared.
- FR-07: Working Memory: asyncio dict, scoped to current investigation, cleared on investigation close.
- FR-08: Long-term Memory: SQLite-backed, keyed by agent+entity+pattern type; persists indefinitely.
- FR-09: Shared Memory: event bus evidence stream; all agents read-only access to published evidence.
- FR-10: Knowledge Memory: query interface to Knowledge Runtime API; promoted lessons readable by all agents.

#### Visual Memory & Regression Engine
- FR-11: Baseline Management: capture, store, version, retrieve, and update visual baselines per (feature_id, page_route, viewport, git_commit).
- FR-12: Regression Detection: compare current screenshot to baseline using configurable pixel diff tolerance; classify as NO_CHANGE, MINOR_SHIFT, VISUAL_REGRESSION, CRITICAL_REGRESSION.
- FR-13: Page Fingerprinting: generate deterministic fingerprint of page DOM structure for cache validity checking.
- FR-14: Baseline Update: require human confirmation when: new baseline 30% different from old; Regression Agent would block PASS; automatic update only when diff < configurable threshold.
- FR-15: Regression Engine publishes regression findings as Evidence to event bus.
- FR-16: Regression Engine maintains regression history per feature per commit in SQLite.

#### Continuous Learning
- FR-17: After each concluded Investigation, extract LearningOutcome: problem pattern, root cause category, fix pattern, affected component types, evidence signatures.
- FR-18: LearningOutcome embedded and stored in Qdrant for semantic similarity search.
- FR-19: Promote only durable, validated lessons (confidence > configurable threshold) to Knowledge Runtime.
- FR-20: Knowledge Memory promotion writes to `.agents/memory/` and optionally to Obsidian vault if configured.
- FR-21: When a new investigation starts on a similar entity, VIR must query long-term memory for similar past issues before generating hypotheses.
- FR-22: Learning feedback loop: agents whose past memory helped resolve an investigation receive authority weight boost for that domain.

### Non-functional Requirements
- NFR-01: Baseline load from filesystem < 200ms per screenshot.
- NFR-02: Pixel diff comparison < 2s per viewport.
- NFR-03: Qdrant semantic search < 500ms for similar issue retrieval.
- NFR-04: SQLite metadata write < 50ms per record.
- NFR-05: Memory architecture must survive process restart; all memory durable unless explicitly cleared.

### Technical Constraints
- TC-01: File naming convention: `{feature_id}_{route_slug}_{viewport}_{git_hash}_{timestamp}.png`.
- TC-02: SQLite WAL mode enabled; single-writer-per-table pattern for agent long-term memory.
- TC-03: Qdrant collection: `vir_visual_memory`; embedding model configurable (default: text-embedding-3-small or local equivalent).
- TC-04: Baseline update requires approval gate for large diffs (> 30% pixel change).
- TC-05: Memory Adapter interface abstracts all storage implementations.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-02 | Must | Filesystem structure | BP-VIR-009 | Create directories; verify structure | All required directories created |
| FR-03 | Must | SQLite structured metadata | BP-VIR-009 | Store and retrieve test run record | Record retrieved matches stored |
| FR-11 | Must | Baseline management | BP-VIR-009 | Capture baseline; retrieve by feature+route+viewport | Correct baseline returned |
| FR-12 | Must | Regression detection | BP-VIR-009 | Compare identical → NO_CHANGE; compare shifted → REGRESSION | Classification correct |
| FR-14 | Must | Baseline update approval | BP-VIR-009 | 40% diff baseline update attempted | Human confirmation required |
| FR-18 | Should | Qdrant learning storage | BP-VIR-009 | Embed LearningOutcome; search for similar | Similar past issue retrieved |
| FR-21 | Must | Memory-first hypothesis | BP-VIR-009 | Start investigation on entity with past issue | Past issue retrieved before new hypotheses generated |
| FR-22 | Should | Authority weight feedback | BP-VIR-009 | Agent memory helped resolve → weight boost logged | Weight boost recorded in agent long-term memory |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Regression Engine | Internal | Critical | Critical | Baseline storage and comparison |
| All VIR Agents | Internal | High | High | Long-term memory for pattern learning |
| Cognitive Engines | Internal | High | High | Past issue patterns for hypothesis priming |
| Knowledge Runtime | Internal | Medium | High | Promoted design and bug lessons |
| Reporting System | Internal | Medium | Medium | Historical comparison data |
| Human Engineers | Primary | Medium | Medium | Learning trends visible in reports |

## 7. Scope Boundary

### In Scope
- Filesystem structure and artifact management
- SQLite schema for all VIR metadata
- Qdrant integration for semantic memory
- Per-agent memory implementation (all 5 types)
- Visual baseline management
- Regression Engine + regression classification
- Continuous learning pipeline
- Knowledge Runtime promotion
- Optional Obsidian sync

### Out of Scope
- Knowledge Runtime implementation (FEAT-045)
- Report generation (FEAT-066)
- Agent-specific memory usage (defined in each agent's FEAT document)

### Deferred Scope
- Cross-project memory sharing
- Cloud memory synchronization
- Memory compression for large artifact stores

### Future Scope
- Memory analytics dashboard
- Automatic memory pruning and archival policies

## 8. Dependency Graph Preview

- FEAT-064: Memory Architecture & Continuous Learning (Should)
  - FEAT-056: Event Bus (prerequisite — shared memory via bus)
  - FEAT-061: Evidence Domain (learning derived from investigations)
  - FEAT-063: Multi-Agent (agent memory types consumed here)
  - FEAT-045: Knowledge Runtime (promotion target)

## 9. Data Flow Preview

- Investigation CONCLUDED → LearningOutcome extracted
  └── LearningOutcome embedded → Qdrant(vir_visual_memory)
      └── SQLite: investigation record updated with learning_id
          └── If confidence > 0.85 → promote to Knowledge Runtime
              └── Knowledge Runtime update: new lesson in architecture/patterns/lessons layers
                  └── Optional: write to Obsidian if vault configured
  └── Next investigation on same entity
      └── Memory-First: query Qdrant for similar past issues
          └── Top-3 similar issues returned as hypothesis seeds
              └── Hypothesis Engine primes H1 from past root cause
                  └── Investigation proceeds faster with prior knowledge

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| connectors/qdrant.py | scripts/connectors/ | Extend | VIR semantic memory uses existing Qdrant connector |
| db.py | scripts/ | Extend | VIR SQLite schema extends existing db patterns |
| FEAT-045 Knowledge Runtime | docs/ | Consume | VIR promotes lessons to existing Knowledge Runtime |

## 11. Dependency & Blast Radius Analysis

- **Affected Agents**: All VIR agents (long-term memory backed by this system)
- **Affected Storage**: `.agents/visual-runtime/` (new directory structure)
- **Impact Level**: High — memory architecture supports all agents and continuous improvement

## 12. Migration Strategy

- **Backward Compatibility**: New storage layer; no existing artifacts to migrate
- **Migration Phases**: Phase 7 implements full memory architecture; Phase 2 uses stub memory for early agents

## 13. Architecture Principles

- **Memory First**: Always query long-term memory before generating new hypotheses
- **Provider First**: All storage via Memory/Storage Adapters
- **Incremental Updates**: Baselines updated incrementally; no full regeneration needed

## 14. Non Goals

- Memory Engine does not make quality decisions
- Does not replace the Knowledge Runtime (it feeds it)
- Does not store raw evidence text in Qdrant (only embeddings + metadata references)

## 15. ROI Analysis

- **Regression Prevention Value**: Automatic baseline comparison catches layout regressions before release
- **Learning Value**: Each investigation makes future investigations faster and more accurate
- **Storage Efficiency**: Hybrid architecture stores binary efficiently (filesystem) and metadata compactly (SQLite)
- **Long-Term ROI**: After 50+ investigations, VIR operates with rich institutional memory

## 16. Success Metrics

- **Baseline Retrieval**: < 200ms
- **Regression Detection**: 100% detection on known test regressions; < 5% false positive rate
- **Learning Promotion**: > 85% of confidence-passing learning outcomes promoted successfully
- **Memory-First Hit Rate**: > 70% of new investigations find relevant past issue in memory
- **SQLite Write**: < 50ms per record

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Artifact storage grows unbounded | High | Medium | Configurable retention policy; archive old artifacts | Storage Engineer |
| False regression on legitimate UI updates | High | High | Configurable tolerance; manual baseline update workflow | QA Engineer |
| Qdrant unavailable degrades learning | Medium | Low | Learning stored in SQLite first; Qdrant sync async | Backend Engineer |
| Memory confidentiality (screenshots contain user data) | High | Medium | Artifacts stored locally only; no cloud upload without explicit consent | Security |
| Schema migration breaks long-term memory | High | Low | Schema versioning; migration scripts | Database Engineer |

## 18. Technical Questions

- Should page fingerprints include dynamic content (timestamps, user IDs) or strip it for consistency?
- What is the maximum artifact retention period before automatic archival?
- Should learning outcomes be reviewed by a human before promotion to Knowledge Runtime?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Page fingerprint content | Pending | Strip dynamic content; canonical DOM structure hash; decide in BP-VIR-009 |
| Artifact retention | Pending | Default: 90 days; configurable; decide in BP-VIR-009 |
| Learning review before promotion | Pending | Auto-promote for confidence > 0.9; human review for 0.75–0.89 |

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: ADR-VIR-009: Hybrid memory architecture (filesystem + SQLite + Qdrant) vs single-store approach

## 21. Knowledge Update Impact

- **architecture**: Yes — VIR memory architecture
- **patterns**: Yes — Hybrid memory pattern; learning promotion pattern
- **ADR**: Yes — ADR-VIR-009
- **SQLite**: Yes — comprehensive VIR SQLite schema
- **vector metadata**: Yes — vir_visual_memory Qdrant collection

## 22. Test Strategy Preview

- **Unit Tests**: Baseline CRUD; regression classification; learning embedding; memory-first query
- **Integration Tests**: Full pipeline → investigation → learning → Qdrant → next investigation primed
- **Retention Tests**: Auto-archival of old artifacts after retention period
- **Drift Tests**: Baseline update workflow with human confirmation gate

## 23. Extension Impact

- **Extension UI Changes**: Memory browser in Visualizer (Phase 8) — past investigations, baseline gallery
- **Affected ViewModels**: Baseline thumbnail gallery; regression history chart

## 24. Complexity Estimation

- **Implementation Complexity**: High
- **Estimated Refactoring Percentage**: 20% existing (Qdrant connector extension) / 80% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 7 (Memory, Evidence & Regression)
- **Prerequisites**: FEAT-061 (Evidence), FEAT-058 (Vision — screenshots), FEAT-057 (Memory Adapter)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| Where are visual artifacts stored? | `.agents/visual-runtime/artifacts/` filesystem |
| Structured metadata storage? | SQLite |
| Semantic memory? | Qdrant (embeddings only; no raw screenshots) |
| Long-term lessons? | Promoted to Knowledge Runtime / Obsidian |
| Baseline update approval? | Human confirmation for > 30% pixel change |

## 27. Requirement Readiness Score

- **Score**: 95/100
- **Status**: Ready ≥ 85

## 34. Acceptance Criteria

- [ ] AC-01 (FR-02): All required directories created at VIR first run
- [ ] AC-02 (FR-12): Known 10px layout shift classified as VISUAL_REGRESSION; identical pages as NO_CHANGE
- [ ] AC-03 (FR-14): Baseline update with 40% diff triggers human confirmation
- [ ] AC-04 (FR-21): Second investigation on same entity finds relevant past issue in < 500ms
- [ ] AC-05 (FR-18): LearningOutcome embedded in Qdrant; semantic search returns it for similar query

## 35. Final Planning Prompt

### Problem Statement
VIR needs hybrid memory architecture: filesystem artifacts, SQLite structured metadata, Qdrant semantic memory. Per-agent memory model (5 types). Regression Engine with baseline management. Continuous learning pipeline.

### Architectural Details
- `vir_runtime/memory/storage/` — filesystem, sqlite, qdrant adapters
- `vir_runtime/memory/agent_memory.py` — 5 memory type implementations
- `vir_runtime/memory/visual_memory.py` — baseline management
- `vir_runtime/engines/regression/regression_engine.py` — diff classification
- `vir_runtime/learning/learning_pipeline.py` — outcome extraction + promotion
- `vir_runtime/learning/knowledge_promoter.py` — Knowledge Runtime integration

### Verification Checklist
- [ ] docs/plans/FEAT-064_vir_memory_learning_plan.md generated and approved
- [ ] docs/designs/FEAT-064_vir_memory_learning_blueprint.md generated and approved
