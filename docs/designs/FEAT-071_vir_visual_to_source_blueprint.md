<!-- File path: docs/designs/FEAT-071_vir_visual_to_source_blueprint.md -->

---
feature_id: FEAT-071
feature_name: Visual Intelligence Runtime — Visual-to-Source Code Mapper
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-071_vir_visual_to_source_code_mapper_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Visual-to-Source Code Mapper

## 0. Baseline Context & References
- **Memory Baseline**: Memory of React virtual DOM structures and sourcemap line-by-line parsing models.
- **RAG Query Summaries**: Mapper injects scraping queries via the `BrowserAdapter` defined in Phase 1, using workspace path lookups to filter out-of-bounds library files.
- **Inspected Source Files**:
  - [FEAT-071 Plan](file:///e:/AgentsProject/docs/plans/FEAT-071_vir_visual_to_source_code_mapper_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/mapper/scraper.py` | Create | Inject JS snippets to query framework metadata from DOM nodes | None | High. Core metadata scraper. |
| `vir_runtime/mapper/sourcemaps.py` | Create | Translate minified JS coordinates back to TS/Svelte files | None | High. Resolves sourcemap details. |
| `vir_runtime/mapper/css.py` | Create | Map active CSS class declarations back to stylesheets files | None | Medium. Resolves stylesheet paths. |
| `vir_runtime/mapper/fallback.py` | Create | Execute structural DOM text grep searches when sourcemaps are missing | None | Low. Fallback scanner engine. |
| `vir_runtime/mapper/ranker.py` | Create | Score and sort candidates files list based on metadata matching levels | None | Medium. Computes candidate confidences. |
| `vir_runtime/mapper/scope_gate.py` | Create | Verify mapped source paths fit within approved workspace and blueprint scopes | None | High. Safety boundaries checker. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── mapper/
    ├── css.py
    ├── fallback.py
    ├── ranker.py
    ├── scope_gate.py
    ├── scraper.py
    └── sourcemaps.py
```

---

## 3. Complete Class & Module Design

### 3.1 SourceLinker
- **Class / Module Name**: `vir_runtime.mapper.scraper.SourceLinker`
  - **Responsibilities**: Orchestrate framework scraper scripts execution, query sourcemaps, rank targets, and verify scopes.
  - **Constructor Parameters**:
    - `adapter: BrowserAdapter`
  - **Public Methods**:
    - `async def resolve_source_coordinates(element_id: str) -> List[SourceCoordinate]`
  - **Dependencies**: `sourcemaps`, `css`, `fallback`, `ranker`, `scope_gate`

### 3.2 SourcemapResolver
- **Class / Module Name**: `vir_runtime.mapper.sourcemaps.SourcemapResolver`
  - **Responsibilities**: Load local `.map` files, parse minified bundle line/column coordinates, and translate to source workspace files.
  - **Constructor Parameters**:
    - `sourcemap_dir: str`
  - **Public Methods**:
    - `def resolve_coordinates(bundle_js_path: str, line: int, col: int) -> Optional[SourceCoordinate]`
  - **Dependencies**: python `sourcemap` libraries.

---

## 4. Detailed Interface Contracts

- **API Signature**: `async def resolve_source_coordinates(element_id: str) -> List[SourceCoordinate]`
  - **Parameters**:
    - `element_id` (string DOM selector identifier)
  - **Return Types**: Returns a list of `SourceCoordinate` dataclasses sorted by confidence score.
  - **Exceptions**:
    - `SourceResolutionFailedError` - If element is missing or maps return invalid files.

---

## 5. Configuration Schema

- **Target Schema**:
```yaml
mapper:
  sourcemaps:
    enabled: true
    lookup_directories: ["dist/", "build/"]
  scope_gate:
    block_node_modules: true
    authorized_workspace_prefix: "e:/AgentsProject"
```

---

## 6. Database & Storage Design
- Mapped source files references (file, line number) are saved as attributes of Evidence records in the SQLite tables.

---

## 7. Cache Architecture
- **Sourcemap Files Cache**:
  - Memory dictionary caches parsed sourcemap objects to prevent reloading map files on consecutive resolutions.

---

## 8. Error Model

- **Exception Class**: `SourceResolutionFailedError`
  - **Trigger Condition**: Input JS map files are missing or corrupted.
  - **Recovery Strategy**: Degrade to `FallbackGrepChecker` querying unique text strings, returning candidates with lower confidence.
  - **Logging Requirements**: WARNING log highlighting target DOM class names.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **Source Code Mapping Flow**:
  1. `SourceLinker` receives DOM element selector.
  2. Scraper injects JS querying React Fiber properties.
  3. Bundle source file path and line returned.
  4. `SourcemapResolver` translates coordinates back to workspace JSX file.
  5. `ScopeGate` verifies target file sits inside current git workspace bounds.
  6. Ranked candidate coordinate list returned.

---

## 12. Security & Safety
- **Workspace Boundary Safety**: `ScopeGate` checks resolved path strings. If mapped coordinates target folders outside the active workspace (e.g. library node modules), the engine marks coordinates as out-of-scope, protecting codebase files.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-02` | Unit Test | `tests/unit/test_react_fiber.py` | `scraper.py` | `self.assertIn("jsx_source", metadata)` |
| `FR-14` | Unit Test | `tests/unit/test_scope_enforcement.py` | `scope_gate.py` | `self.assertFalse(is_allowed)` |

---

## 14. Requirement Traceability Matrix
- `FR-02` -> Task 1.2 -> Class `ReactScraper` -> `scraper.py` -> `test_react_fiber.py` -> Verified.
- `FR-14` -> Task 1.9 -> Class `ScopeGate` -> `scope_gate.py` -> `test_scope_enforcement.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/mapper/sourcemaps.py`
  - **Purpose**: Low-level sourcemap resolver using standard Python mapping libraries.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on python `sourcemap` libraries.
