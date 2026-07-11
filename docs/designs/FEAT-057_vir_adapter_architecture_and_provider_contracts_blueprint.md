<!-- File path: docs/designs/FEAT-057_vir_adapter_architecture_and_provider_contracts_blueprint.md -->

---
feature_id: FEAT-057
feature_name: Visual Intelligence Runtime — Adapter Architecture & Provider Contracts
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-057_vir_adapter_architecture_and_provider_contracts_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Adapter Architecture & Provider Contracts

## 0. Baseline Context & References
- **Memory Baseline**: Memory of Playwright page bindings and dynamic modules load schemas.
- **RAG Query Summaries**: `project-profile.json` specifies Node/Python environment requirements for loading external libraries.
- **Inspected Source Files**:
  - [FEAT-057 Plan](file:///e:/AgentsProject/docs/plans/FEAT-057_vir_adapter_architecture_and_provider_contracts_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/adapters/base.py` | Create | Abstract Protocol contracts defining adapter interfaces | None | High. Contract must remain unchanged. |
| `vir_runtime/adapters/registry.py` | Create | Dynamic module loader and plugin registration broker | `base.py` | Medium. Resolves adapter dependencies. |
| `vir_runtime/adapters/playwright.py` | Create | Default web browser automation controller adapter | `base.py` | High. Core driver for DOM and screenshot captures. |
| `vir_runtime/adapters/fallback.py` | Create | Fallback manager that downgrades capabilities on provider errors | `base.py` | Medium. Ensures execution continuity. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── adapters/
    ├── base.py
    ├── fallback.py
    ├── playwright.py
    └── registry.py
```

---

## 3. Complete Class & Module Design

### 3.1 BrowserAdapter (Protocol)
- **Class / Module Name**: `vir_runtime.adapters.base.BrowserAdapter`
  - **Responsibilities**: Define standard browser lifecycle capabilities (Navigate, Screenshot, Fetch DOM).
  - **Public Methods**:
    - `async def open(url: str) -> None`
    - `async def capture_screenshot(path: str) -> None`
    - `async def get_dom_content() -> str`
    - `async def close() -> None`

### 3.2 AdapterRegistry
- **Class / Module Name**: `vir_runtime.adapters.registry.AdapterRegistry`
  - **Responsibilities**: Register, instantiate, and manage life spans of provider plugins dynamically.
  - **Constructor Parameters**:
    - `config_path: str` - Path to `adapters.yaml`.
  - **Public Methods**:
    - `def register_adapter(name: str, adapter_cls: Type[BrowserAdapter]) -> None`
    - `def get_adapter(name: str) -> BrowserAdapter`
    - `def load_from_config() -> None`
  - **Internal Methods**:
    - `def _import_module(module_path: str) -> Type`

### 3.3 PlaywrightAdapter
- **Class / Module Name**: `vir_runtime.adapters.playwright.PlaywrightAdapter`
  - **Responsibilities**: Wrap Playwright python libraries to implement the BrowserAdapter interface.
  - **Constructor Parameters**:
    - `headless: bool`
    - `viewport: dict`
  - **Public Methods**: Implements all `BrowserAdapter` APIs.

---

## 4. Detailed Interface Contracts

- **API Signature**: `async def capture_screenshot(path: str) -> None`
  - **Parameters**:
    - `path` (file system target folder location path, e.g. `.agents/visual-runtime/current.png`)
  - **Return Types**: None.
  - **Exceptions**:
    - `BrowserNotOpenedError` - If navigate() hasn't been called.
    - `ScreenshotFailedError` - If OS screenshot capturing fails.

---

## 5. Configuration Schema

- **Target Schema (`adapters.yaml`)**:
```yaml
adapters:
  browser:
    provider: "playwright"
    headless: true
    viewports:
      desktop: { width: 1920, height: 1080 }
      mobile: { width: 375, height: 812 }
```

---

## 6. Database & Storage Design
- No database tables allocated. The Registry stores instantiated classes in RAM hash tables.

---

## 7. Cache Architecture
- No cache mechanisms defined for provider adapters layer.

---

## 8. Error Model

- **Exception Class**: `ProviderFallbackTriggered`
  - **Trigger Condition**: Playwright browser crashes or fails to launch due to missing OS graphics drivers.
  - **Recovery Strategy**: Degrade features to DOM-only analysis (skip image comparing), routing to `FallbackAdapter`.
  - **Logging Requirements**: WARNING level alerting fallback conditions.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None. (Adapters load dynamically based on YAML config settings).

---

## 11. Sequence Flows

- **Dynamic Provider Loading Flow**:
  1. Registry reads `adapters.yaml`.
  2. Sub-module `playwright.py` imported.
  3. Class instantiated and cached inside `AdapterRegistry`.
  4. Core calls `registry.get_adapter("browser")`.

---

## 12. Security & Safety
- **Sandbox Boundary**: Adapters are blocked from calling absolute file system targets outside the workspace workspace directories.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `tests/unit/test_adapter_registry.py` | `registry.py` | `self.assertIsInstance(adapter, BrowserAdapter)` |
| `FR-12` | Integration Test | `tests/integration/test_playwright_screenshots.py` | `playwright.py` | `self.assertTrue(path.exists())` |

---

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Interface `BrowserAdapter` -> `base.py` -> `test_adapter_registry.py` -> Verified.
- `FR-12` -> Task 1.10 -> Class `PlaywrightAdapter` -> `playwright.py` -> `test_playwright_screenshots.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/adapters/registry.py`
  - **Purpose**: Dynamic plugin provider manager.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on `adapters.yaml`.
