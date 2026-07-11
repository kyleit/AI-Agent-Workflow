<!-- docs/brainstorming/FEAT-058_vir_vision_engine.md -->

---
feature_id: FEAT-058
feature_name: Visual Intelligence Runtime — Vision Engine (5-Layer Architecture)
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-057_vir_adapter_architecture_and_provider_contracts.md
next_artifact: ../plans/FEAT-058_vir_vision_engine_plan.md
---

# Master Requirement Document – VIR Vision Engine (5-Layer Architecture)

## 1. Feature ID & Name
- **Feature ID**: FEAT-058
- **Feature Name**: Visual Intelligence Runtime — Vision Engine (5-Layer Architecture)

## 2. Original Idea
Design and implement the VIR Vision Engine using a layered strategy: Layer 1 (DOM/Computed Style), Layer 2 (Screenshot/Pixel Analysis), Layer 3 (OCR), Layer 4 (VLM Semantic Analysis), and Layer 5 (Optional CV Models). The Vision Engine transforms raw browser observations into structured visual evidence.

## 3. Business Problem
- **Problem**: No single vision technique is sufficient for comprehensive UI quality assessment. Pixel diff misses semantic errors; DOM inspection misses visual rendering bugs; OCR misses layout composition issues; deterministic rules miss aesthetic quality. A layered approach combining all techniques is required.
- **Why it matters**: The Vision Engine is the primary sensory input for VIR. Poor vision = blind runtime. The 5-layer design ensures coverage from deterministic structure to semantic understanding.
- **Who is affected**: VIR Orchestrator, Cognitive Engines, Evidence Engine, Design Authority Agent, Quality Gate.
- **Expected outcome**: A pluggable, layered Vision Engine that produces structured visual evidence at multiple confidence levels, from deterministic DOM facts to semantic VLM insights.

## 4. Requirement Discovery

### Functional Requirements
- FR-01: Layer 1 (DOM & Computed Style): inspect bounding boxes, computed styles, z-index, visibility, opacity, overflow, clipping, positioning, font sizes, line heights, color values, contrast, component dimensions, layout shifts, element overlap, hidden elements, off-screen elements, focus indicators, responsive breakpoints.
- FR-02: Layer 2 (Screenshot & Pixel Analysis): capture screenshots, compare against baseline using configurable tolerance, detect regressions, misalignment, broken layout, missing elements, incorrect colors, rendering differences, cross-browser differences.
- FR-03: Layer 3 (OCR): extract text from canvas, images-with-text, PDF viewers, virtualized rendering, remote desktop surfaces when DOM text extraction fails. Not used for standard HTML text.
- FR-04: Layer 4 (VLM Semantic Analysis): analyze visual hierarchy, composition, balance, whitespace, information density, design consistency, aesthetic quality, component relationships, confusing interactions, poor UX presentation. VLM findings must be corroborated by at least one additional signal.
- FR-05: Layer 5 (Optional CV Models): YOLO or specialized object detection for canvas applications, game interfaces, complex visual editors, video frames. Not required for default VIR implementation.
- FR-06: Vision Engine must execute layers in priority order; stop after first layer that provides sufficient confidence for the requested observation type.
- FR-07: Vision Engine must publish all findings as structured Evidence domain objects to the event bus.
- FR-08: Each vision layer must declare its confidence score (0.0–1.0) for each finding.
- FR-09: VLM must never make final decisions alone; all VLM findings flagged as requiring corroboration.
- FR-10: Vision Engine must support multi-viewport capture: desktop, tablet, mobile breakpoints.
- FR-11: Pixel comparison must support configurable tolerance (threshold, ignore regions, anti-aliasing compensation).
- FR-12: Vision Engine must produce annotated screenshots highlighting detected issues.
- FR-13: Vision Engine must detect and report visual accessibility violations (contrast ratio, focus indicator visibility, text size).

### Non-functional Requirements
- NFR-01: Layer 1 (DOM) inspection: < 500ms per page for standard complexity.
- NFR-02: Layer 2 (Pixel diff): < 2s per viewport comparison.
- NFR-03: Layer 3 (OCR): < 3s per canvas element; only invoked when needed.
- NFR-04: Layer 4 (VLM): configurable timeout (default 15s); skipped in Lightweight profile.
- NFR-05: Layer 5 (CV): optional; timeout configurable; not in default profiles.
- NFR-06: Vision Engine must support incremental observation (re-check only changed regions when possible).
- NFR-07: All screenshots stored in `.agents/visual-runtime/artifacts/` with structured naming.

### Technical Constraints
- TC-01: Layer 1 uses Browser Adapter (Playwright CDP / JavaScript evaluation).
- TC-02: Layer 2 uses Vision Adapter (Pixelmatch default).
- TC-03: Layer 3 uses Vision Adapter (OCR adapter; Tesseract or cloud OCR).
- TC-04: Layer 4 uses Vision Adapter (VLM adapter; local Ollama or cloud API).
- TC-05: Layer 5 uses Vision Adapter (CV adapter; YOLO or custom model).
- TC-06: Confidence threshold configuration in `adapters.yaml`.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | DOM inspection Layer 1 | BP-VIR-004 | 20 DOM properties extracted correctly | All properties match browser DevTools |
| FR-02 | Must | Pixel diff Layer 2 | BP-VIR-004 | Compare identical screenshots → 0% diff; inject 5px shift → detected | Regression detected with correct bounding box |
| FR-03 | Should | OCR Layer 3 | BP-VIR-004 | Extract text from canvas element | Text matches expected content |
| FR-04 | Should | VLM semantic analysis Layer 4 | BP-VIR-004 | VLM evaluates misaligned layout | Finding corroborated by DOM layer data |
| FR-06 | Must | Layer priority execution | BP-VIR-004 | Configure confidence threshold; Layer 1 high confidence stops execution | Layer 2+ not invoked when Layer 1 sufficient |
| FR-07 | Must | Evidence published to bus | BP-VIR-007 | Vision finding received by Evidence Engine | Evidence object has all required fields |
| FR-09 | Must | VLM cannot make final decision alone | BP-VIR-004 | VLM finding without corroboration | Finding marked as `requires_corroboration` |
| FR-10 | Must | Multi-viewport capture | BP-VIR-004 | Capture 3 viewports (1920, 768, 375px) | 3 separate evidence records produced |
| FR-12 | Should | Annotated screenshots | BP-VIR-004 | Issue detected; annotated screenshot produced | Bounding box overlay visible on issue area |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Evidence Engine | Internal | Critical | Critical | Structured visual evidence input |
| Design Authority Agent | Internal | High | High | Visual findings for design compliance review |
| Cognitive Engines | Internal | High | High | Visual observations for contradiction/investigation |
| Digital Twin | Internal | High | High | Visual state dimension fed by Layer 1 |
| Regression Engine | Internal | High | High | Layer 2 pixel diff powers regression detection |
| Accessibility Engine | Internal | Medium | High | Layer 1 contrast/focus findings |

## 7. Scope Boundary

### In Scope
- All 5 vision layers (Layer 5 as optional/pluggable)
- Confidence scoring per layer
- Evidence publication to event bus
- Multi-viewport capture
- Annotated screenshot generation
- Layer priority execution
- Pixel diff with configurable tolerance
- Accessibility visual checks (Layer 1)

### Out of Scope
- Hearing Engine (FEAT-059)
- Accessibility Engine detailed logic (FEAT-067)
- Regression Engine baseline management (FEAT-064)
- VLM provider implementation (FEAT-057 adapter)

### Deferred Scope
- Video frame analysis (Layer 5 advanced)
- Remote desktop capture
- Cross-browser parallel capture

### Future Scope
- Real-time visual monitoring (continuous observation mode)
- Visual A/B testing comparison

## 8. Dependency Graph Preview

- FEAT-058: Vision Engine (Must)
  - FEAT-057: Vision Adapters (prerequisite)
  - FEAT-056: Event Bus (prerequisite — evidence publication)
  - FEAT-061: Evidence Domain (consumer of Vision output)
  - FEAT-064: Memory Engine (baseline storage for Layer 2)
  - FEAT-067: Accessibility Engine (consumes Layer 1 output)

## 9. Data Flow Preview

- Orchestrator triggers Visual Observation
  └── Vision Engine receives `observe.visual` event
      └── Layer 1 (DOM): Browser Adapter extracts computed styles → DOM Evidence published
          └── If confidence < threshold → activate Layer 2
              └── Layer 2 (Pixel): Browser Adapter takes screenshot → Vision Adapter diffs vs baseline → Diff Evidence published
                  └── If regression detected → activate Layer 4 (Standard+Deep profiles)
                      └── Layer 4 (VLM): Vision Adapter sends screenshot to VLM → Semantic Evidence published
                          └── Corroboration check: VLM finding + DOM/Pixel findings linked
                              └── All evidence published to `vir.evidence.vision.*` topic
                                  └── Evidence Engine aggregates; Digital Twin updated (visual state)

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| frontend-design SKILL.md | `.agents/skills/frontend-design/` | Consume | Design rules used as Vision evaluation criteria |
| Pixelmatch (external) | pip/npm | Wrap in adapter | Layer 2 default pixel diff engine |
| Playwright CDP | Playwright API | Use via Browser Adapter | Layer 1 DOM extraction |

## 11. Dependency & Blast Radius Analysis

- **Affected Agents**: Evidence Engine, Cognitive Engines, Digital Twin, Regression Engine, Accessibility Engine
- **Affected Adapters**: Vision Adapter (all layers), Browser Adapter (Layer 1 + screenshot)
- **Affected Storage**: baseline screenshots, current screenshots, diff images, annotated screenshots
- **Impact Level**: High — Vision is the primary sensory input

## 12. Migration Strategy

- **Backward Compatibility**: Vision Engine replaces existing screenshot checks in frontend-visual-debug
- **Migration Phases**: Phase 2 delivers Layer 1+2; Phase 4 adds Layer 3+4; Phase 10 adds Layer 5

## 13. Architecture Principles

- **API First**: Vision Engine publishes Evidence events before downstream consumers built
- **Provider First**: All layers use Vision/Browser Adapters; no direct provider calls
- **Memory First**: Layer 2 loads baseline from Memory before taking new screenshot
- **Incremental Updates**: Layers added incrementally; existing layers stable

## 14. Non Goals

- Vision Engine does not make pass/fail decisions (that is Consensus Engine + Quality Gate)
- Vision Engine does not fix code (that is Coder Agent)
- Vision Engine does not analyze audio/network (Hearing Engine)

## 15. ROI Analysis

- **Estimated Implementation Cost**: High (Layer 1+2 in Phase 2; Layer 3+4 in Phase 4)
- **Regression Detection Savings**: Automated pixel regression replaces manual screenshot review per PR
- **Semantic Analysis Value**: VLM layer catches aesthetic issues before human design review
- **Long-Term ROI**: Vision Engine becomes the eyes of the AIWF for all visual quality work

## 16. Success Metrics

- **Layer 1 Accuracy**: > 99% DOM property extraction accuracy vs DevTools
- **Layer 2 Recall**: > 95% visual regression detection rate on known test cases
- **Layer 2 Precision**: < 5% false positive rate with properly configured tolerance
- **VLM Corroboration**: 100% of VLM findings have at least one supporting signal
- **Annotated Screenshot**: Issue bounding box within 5px of actual problem area
- **Multi-viewport**: All 3 standard breakpoints captured in Standard+ profiles

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| High false positive rate in pixel diff | High | High | Configurable tolerance; anti-aliasing compensation; ignore regions | Vision Engineer |
| VLM hallucination produces incorrect findings | High | Medium | Corroboration requirement; VLM confidence threshold | AI Engineer |
| Layer 1 fails on shadow DOM / web components | Medium | Medium | Deep DOM traversal; slot extraction; Shadow DOM pierce mode | Frontend Engineer |
| OCR accuracy poor on low-contrast canvas | Medium | Medium | Pre-processing; contrast enhancement before OCR | Vision Engineer |
| VLM timeout degrades page review latency | Medium | High | Per-VLM-call timeout; async; non-blocking for other layers | Backend Engineer |

## 18. Technical Questions

- Should Layer 1 use Playwright `evaluate()` + custom JS extractor or CDP directly?
- How should ignored regions be defined for pixel diff (CSS selectors, coordinates, element references)?
- Should the Vision Engine cache Layer 1 results for reuse within the same investigation?
- What VLM prompt template should be used for UI quality assessment?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Layer 1: evaluate() vs CDP | Pending | CDP preferred for performance; fallback to evaluate(); decide in BP-VIR-004 |
| Ignore regions format | Pending | CSS selector format recommended; specify in BP-VIR-004 |
| VLM prompt template | Pending | Template library in Design Knowledge Base; define in FEAT-065 |
| Layer 1 result caching | Pending | Cache per URL+DOM-hash within investigation; define in BP-VIR-004 |

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: ADR-VIR-004: VLM corroboration requirement (prevents AI-only visual decisions)

## 21. Knowledge Update Impact

- **patterns**: Yes — 5-layer vision analysis pattern; VLM corroboration pattern
- **architecture**: Yes — Vision Engine architecture
- **ADR**: Yes — ADR-VIR-004
- **modules**: Yes — vir_runtime/engines/vision/ module tree
- **vector metadata**: Yes — VLM visual finding embeddings stored in Qdrant

## 22. Test Strategy Preview

- **Unit Tests**: Each layer independently testable with stub adapters; confidence scoring; evidence schema
- **Integration Tests**: Full 5-layer pipeline on sample page; baseline comparison with known regressions
- **Visual Regression Tests**: Pixel diff on known good vs deliberately broken UI
- **VLM Tests**: VLM findings on design-correct vs design-incorrect layouts; corroboration validation

## 23. Extension Impact

- **Extension UI Changes**: Screenshots visible in Visualizer VIR panel; annotated screenshots overlaid on issues
- **Affected ViewModels**: Image viewer component needed in extension

## 24. Complexity Estimation

- **Implementation Complexity**: High
- **Estimated Refactoring Percentage**: 0% existing (Vision Engine is new); Layer 2 replaces existing screenshot capture in frontend-visual-debug

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 2 (Sensory) + Phase 4 (Vision & Design)
- **Milestones**: Phase 2: Layer 1+2 MVP; Phase 4: Layer 3+4; Phase 10: Layer 5 optional
- **Prerequisites**: FEAT-056 (Event Bus), FEAT-057 (Adapters)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| Vision technology stack? | 5-layer: DOM → Pixel → OCR → VLM → CV (optional) |
| Pixel diff tool? | Pixelmatch default; configurable tolerance |
| VLM decisions alone? | Never; always requires corroboration |
| Multi-viewport? | Yes; desktop/tablet/mobile per Standard+ profile |
| Annotated screenshots? | Yes; issue bounding box overlaid |

## 27. Requirement Readiness Score

- **Score**: 95/100
- **Status**: Ready ≥ 85

## 28. Existing Project Context

- **Memory Source**: Clarification answers Q2 (Vision Engine); FEAT-045 (VLM patterns)
- **Existing Architecture Summary**: AIWF already uses Qdrant for vector storage; VLM patterns established in knowledge-runtime

## 29. Existing Modules & Services

| Module | Location | Owner | Reuse % | Mod. % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|
| frontend-visual-debug | `.agents/skills/frontend-visual-debug/` | Skill | 5% | 95% | Low | Screenshot capture replaced by Layer 2 |
| connectors/qdrant.py | scripts/connectors/ | Runtime | 70% | 30% | Low | VLM embedding storage |

## 30-31. Solution Comparison & Selection
*(Covered in FEAT-055 Section 30-31 — Option B Event-Driven selected; Vision layers implemented as independent agent subscriptions on the event bus.)*

## 32. Selected Solution

- **Architecture**: Layer 1–4 implemented as cascading async stages within VisionAgent; each stage publishes intermediate evidence; final consolidated evidence published after all required layers complete.
- **Execution**: Sequential by default; concurrent in Deep profile with result aggregation.
- **Trade-offs**: Sequential is simpler and cheaper; concurrent needed only for multi-viewport Deep Review.

## 33. Risks & Assumptions

- **Risks**: R-01 through R-05 listed in Section 17 Risk Matrix above.
- **Assumptions**:
  - A-01: Pixelmatch sufficient for pixel diff without GPU
  - A-02: Playwright CDP gives reliable computed style extraction
  - A-03: A local VLM (Ollama + LLaVA or equivalent) is available for Layer 4 in Standard+ profiles

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): 20 DOM properties extracted and match browser DevTools for test page
- [ ] AC-02 (FR-02): Known 5px layout shift detected with < 5% false positive rate on 10 test pages
- [ ] AC-03 (FR-04): VLM finding without DOM/pixel corroboration flagged as `requires_corroboration=True`
- [ ] AC-04 (FR-07): All vision findings published as Evidence objects with all required fields
- [ ] AC-05 (FR-10): 3 viewport screenshots captured in single Standard profile run
- [ ] AC-06 (FR-12): Annotated screenshot shows issue bounding box within 5px accuracy
- [ ] AC-07 (NFR-01): Layer 1 DOM inspection < 500ms on standard page complexity

## 35. Final Planning Prompt

### Problem Statement
VIR needs a 5-layer Vision Engine that transforms browser visual observations into structured evidence. Layer priority: DOM (deterministic) → Pixel (regression) → OCR (text extraction) → VLM (semantic) → CV (optional).

### Objectives
Implement all 5 layers via adapter interfaces; publish structured Evidence to event bus; support multi-viewport; produce annotated screenshots; enforce VLM corroboration rule.

### Architectural Details
- `vir_runtime/engines/vision/vision_engine.py` — Layer orchestration
- `vir_runtime/engines/vision/layers/dom_inspector.py` — Layer 1
- `vir_runtime/engines/vision/layers/pixel_diff.py` — Layer 2
- `vir_runtime/engines/vision/layers/ocr_extractor.py` — Layer 3
- `vir_runtime/engines/vision/layers/vlm_analyzer.py` — Layer 4
- `vir_runtime/engines/vision/layers/cv_model.py` — Layer 5 (optional)
- `vir_runtime/engines/vision/annotator.py` — Screenshot annotator

### Verification Checklist
- [ ] docs/plans/FEAT-058_vir_vision_engine_plan.md generated and approved
- [ ] docs/designs/FEAT-058_vir_vision_engine_blueprint.md generated and approved
