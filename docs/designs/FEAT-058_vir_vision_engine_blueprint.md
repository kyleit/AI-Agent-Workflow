<!-- File path: docs/designs/FEAT-058_vir_vision_engine_blueprint.md -->

---
feature_id: FEAT-058
feature_name: Visual Intelligence Runtime — Vision Engine (5-Layer Architecture)
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-058_vir_vision_engine_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Vision Engine (5-Layer Architecture)

## 0. Baseline Context & References
- **Memory Baseline**: Baseline parameters mapping to WCAG standards and local PIL image manipulations.
- **RAG Query Summaries**: Vision engine relies on `BrowserAdapter` signatures established in Phase 1 to capture page states.
- **Inspected Source Files**:
  - [FEAT-058 Plan](file:///e:/AgentsProject/docs/plans/FEAT-058_vir_vision_engine_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/sensory/vision/engine.py` | Create | Manage sequential evaluation loops across 5 vision inspection layers | None | High. Orchestrates sensory vision logic. |
| `vir_runtime/sensory/vision/dom_inspector.py` | Create | Extract element bounds, offsets, z-indexes, and computed styles | None | Medium. Layer 1 DOM inspector. |
| `vir_runtime/sensory/vision/pixel_comparer.py` | Create | Compare active page screenshots to stored visual baselines | None | High. Layer 2 pixel comparer (PIL-backed). |
| `vir_runtime/sensory/vision/ignore_regions.py` | Create | Resolve dynamic selectors or coordinate boxes ignored during pixel runs | None | Low. Coordinates masking selector checks. |
| `vir_runtime/sensory/vision/annotator.py` | Create | Draw highlight overlays marking coordinates of visual errors on output images | None | Low. Renders red box borders on PNGs. |
| `vir_runtime/sensory/vision/ocr_reader.py` | Create | Extract embedded textual labels inside canvas contexts (Layer 3) | None | Medium. Integrates OCR engines. |
| `vir_runtime/sensory/vision/vlm_analyser.py` | Create | Run semantic visual review prompts against cloud or local VLMs (Layer 4) | None | Medium. Communicates visual states to LLMs. |
| `vir_runtime/sensory/vision/a11y_contrast.py` | Create | Calculate color contrast values of text coordinates (WCAG 2.1) | None | Low. Audits text accessibility levels. |
| `vir_runtime/sensory/vision/cv_yolo.py` | Create | Apply YOLO object classifiers over custom canvas widgets (Layer 5) | None | Low. Classifies dynamic canvas buttons. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── sensory/
    └── vision/
        ├── a11y_contrast.py
        ├── annotator.py
        ├── cv_yolo.py
        ├── dom_inspector.py
        ├── engine.py
        ├── ignore_regions.py
        ├── ocr_reader.py
        ├── pixel_comparer.py
        └── vlm_analyser.py
```

---

## 3. Complete Class & Module Design

### 3.1 VisionEngine
- **Class / Module Name**: `vir_runtime.sensory.vision.engine.VisionEngine`
  - **Responsibilities**: Dispatch execution across the 5 vision layers, exit early if findings confidence satisfies thresholds.
  - **Constructor Parameters**:
    - `adapter: BrowserAdapter` - Target browser driver interface.
  - **Public Methods**:
    - `async def run_vision_audit(feature_id: str, url: str) -> List[Evidence]` - Triggers observation loop.
  - **Dependencies**: `dom_inspector`, `pixel_comparer`, `ocr_reader`, `vlm_analyser`, `cv_yolo`

### 3.2 PixelComparer
- **Class / Module Name**: `vir_runtime.sensory.vision.pixel_comparer.PixelComparer`
  - **Responsibilities**: Apply structural pixel comparison on page screenshots using custom tolerance configs.
  - **Constructor Parameters**:
    - `tolerance: float`
  - **Public Methods**:
    - `def compare(current_png: bytes, baseline_png: bytes, ignore_masks: List[Tuple[int,int,int,int]]) -> Tuple[float, bytes]` - Returns diff ratio and diff image bytes.

---

## 4. Detailed Interface Contracts

- **API Signature**: `def compare(current_png: bytes, baseline_png: bytes, ignore_masks: List[Tuple[int,int,int,int]]) -> Tuple[float, bytes]`
  - **Parameters**:
    - `current_png` (raw bytes data of captured screenshot)
    - `baseline_png` (raw bytes data of matching baseline template)
    - `ignore_masks` (coordinate bounds array describing pixel regions to skip comparing)
  - **Return Types**: Returns a tuple of `(diff_ratio: float, diff_image_bytes: bytes)`.

---

## 5. Configuration Schema

- **Target Schema**:
```yaml
vision:
  layers:
    layer1_active: true
    layer2_active: true
    layer3_active: false
    layer4_active: false
    layer5_active: false
  pixel_comparison:
    tolerance: 0.05
    ignore_selectors: [".dynamic-timestamp", "#ad-banner"]
```

---

## 6. Database & Storage Design
- Baseline paths, diff ratio percentages, and visual findings metadata are saved to the `vir_evidence` table (Phase 3).

---

## 7. Cache Architecture
- No caching is defined at the sensory engine layer.

---

## 8. Error Model

- **Exception Class**: `VisualComparisonError`
  - **Trigger Condition**: Input PNG resolutions do not match, or image buffers are corrupted.
  - **Recovery Strategy**: Flag the run as inconclusive, return error ratios, post diagnostic info.
  - **Logging Requirements**: WARNING level logs containing input image sizes.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **Vision Audit Flow**:
  1. `VisionEngine` launches browser page navigation.
  2. `DOMInspector` captures layouts, bounding box lists.
  3. `PixelComparer` runs pixel diff sweeps.
  4. Red overlays drawn on matching error zones via `VisualAnnotator`.
  5. Auditing results are packaged as `Evidence` objects.

---

## 12. Security & Safety
- **Pixel boundaries checks**: Ignore coordinates values are validated to ensure they fit inside the active screenshot dimensions, protecting against memory index overflows.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `tests/unit/test_dom_inspector.py` | `dom_inspector.py` | `self.assertIn("z-index", style)` |
| `FR-02` | Unit Test | `tests/unit/test_pixel_match.py` | `pixel_comparer.py` | `self.assertGreater(diff_ratio, 0.0)` |

---

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `DOMInspector` -> `dom_inspector.py` -> `test_dom_inspector.py` -> Verified.
- `FR-02` -> Task 1.2 -> Class `PixelComparer` -> `pixel_comparer.py` -> `test_pixel_match.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/sensory/vision/pixel_comparer.py`
  - **Purpose**: Low-level image diffing algorithms.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on Pillow library functions.
