<!-- docs/brainstorming/FEAT-071_vir_visual_to_source_code_mapper.md -->

---
feature_id: FEAT-071
feature_name: Visual Intelligence Runtime — Visual-to-Source Code Mapper
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-070_vir_target_lifecycle_and_sandbox_orchestrator.md
next_artifact: ../plans/FEAT-071_vir_visual_to_source_plan.md
---

# Master Requirement Document – VIR Visual-to-Source Code Mapper

## 1. Feature ID & Name
- **Feature ID**: FEAT-071
- **Feature Name**: Visual Intelligence Runtime — Visual-to-Source Code Mapper

## 2. Original Idea
Design the visual-to-source mapping layer (Source Linker) for VIR. It translates visual components, DOM coordinates, computed styles, and framework elements back to specific codebase files, component templates, styling declarations, and lines of code.

## 3. Business Problem
- **Problem**: When a visual issue (e.g. style bug, layout overlap) is detected, VIR only has browser-level DOM elements or coordinate boundaries. The Coder Agent must search through component directories to locate the file rendering that element.
- **Why it matters**: Direct correlation of runtime UI elements to codebase coordinates (file, line number) eliminates search loops, lowers context token usage, and increases code patch precision.
- **Who is affected**: Coder Agent, RCA Engine, Visualizer extension, and developers reviewing findings.
- **Expected outcome**: A Source Linker that maps DOM elements and styles directly back to their source code location with high confidence.

## 4. Requirement Discovery

### Functional Requirements
- **FR-01: DOM Node to Component Mapping:** Extract internal framework descriptors from runtime DOM nodes.
- **FR-02: React Fiber Inspection:** Extract Fiber node metadata (`__reactFiber$`) to retrieve component names, source files, and lines of code.
- **FR-03: Vue VNode Inspection:** Extract Vue virtual DOM node metadata (`__vnode`) to trace back to single-file components (`.vue`).
- **FR-04: Svelte Component Inspection:** Parse Svelte element markers to locate origin `.svelte` files.
- **FR-05: Angular Component Inspection:** Query Angular element debug context (`ng.getComponent`) to locate backing component classes.
- **FR-06: Source Map Integration:** Parse source maps (`.map` files) to translate bundled, minified JS coordinates back to TS/Svelte/JSX files in the workspace.
- **FR-07: CSS & Styling Mapper:** Trace computed CSS style declarations, Tailwind utility classes, or CSS Modules back to their origin files (e.g. tracking CSS class `.cart-item` back to `Cart.module.css:L12`).
- **FR-08: Event-Handler & Event Tracer:** Map DOM event listeners back to their JS/TS function source code blocks (e.g. trace click action back to `onCheckout()` function declaration).
- **FR-09: Store & Subscription Trace:** Trace reactive data bindings (e.g. Redux selectors, Pinia stores) back to their state store files.
- **FR-10: Template & Render Function Mapping:** Translate virtual DOM structures back to physical file templates or render functions.
- **FR-11: Build-tool & Bundler Adapters:** Abstract mapping extraction to support Webpack, Vite, Rollup, and Esbuild output structures.
- **FR-12: Production-Minified Limitations & Fallbacks:** If debug indicators or source maps are missing, fall back to structural DOM grep search, unique text nodes, class names, or data attributes.
- **FR-13: Multiple Candidate Ranking:** When mapping is ambiguous, return a list of candidate source coordinates ranked by confidence.
- **FR-14: Safe-Edit Scope Generation:** Enforce file boundaries based on the approved blueprint scope; flag code changes targeting files outside the authorized boundary.
- **FR-15: Source Code Access & Privacy Boundaries:** Limit source mapping to the current workspace paths; block mapping into external libraries or global node modules unless explicitly configured.

### Non-functional Requirements
- **NFR-01: Lookup Speed:** Node-to-source resolution completed in under 150ms per element.
- **NFR-02: Accuracy Rate:** > 90% resolution accuracy for dev/debug builds.
- **NFR-03: Thread Safety:** Support thread-safe file lookups during concurrent mapping requests.

### Technical Constraints
- **TC-01:** Framework scraping queries run inside page contexts via the Browser Adapter.
- **TC-02:** Source map resolution uses the Python `sourcemap` package.
- **TC-03:** Local workspace file lookups verified against the git workspace path structure.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | DOM to component | BP-VIR-019 | Click element in test page | Returns file path and line |
| FR-02 | Must | React Fiber tracing | BP-VIR-019 | Query element in React page | Mapped to component source JSX |
| FR-06 | Must | Source map parsing | BP-VIR-019 | Parse bundle location | Matches exact typescript line |
| FR-07 | Must | CSS tracing | BP-VIR-019 | Map Tailwind class | Pinpoints styled element JSX line |
| FR-08 | Should | Event tracer | BP-VIR-019 | Trace click handler | Locates target click function |
| FR-12 | Must | Fallback mechanism | BP-VIR-019 | Map element without maps | Returns best match using text grep |
| FR-13 | Must | Candidate ranking | BP-VIR-019 | Multi-match selector | Returns ranked list with confidence |
| FR-14 | Must | Scope enforcement | BP-VIR-019 | Map element outside blueprint | Flagged as out-of-scope |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Coder Agent | Primary | Critical | Critical | Direct file/line access for fixes, zero directory grep loops |
| RCA Engine | Internal | High | High | Knows exactly which component triggered the exception |
| Visualizer Extension | Secondary | Medium | Medium | Developer clicks bug visual in dashboard to open file in editor |

## 7. Scope Boundary

### In Scope
- React Fiber, Vue vnode, Svelte, Angular DOM meta scrapers.
- Source map parsers, CSS modules, inline styles, Tailwind tracer.
- Code snippet extraction, workspace file path validation.
- Safe-edit scope check.

### Out of Scope
- Actually editing source code files (handled by Coder Agent).
- Non-web desktop/mobile mapping in MVP (delegated to future adapters).

### Deferred Scope
- Canvas coordinate-to-element mapping.

## 8. Dependency Graph Preview
- FEAT-071: Visual-to-Source Mapper
  - FEAT-057: Adapters (prerequisite — uses BrowserAdapter)
  - FEAT-058: Vision Engine Layer 1 (feeds DOM computed style data)
  - FEAT-061: Evidence Domain (uses SourceLink objects in evidence)
  - FEAT-062: Thinking Pipeline (RCA uses code links to target bug origins)

## 9. Data Flow Preview
- Visual defect found: button text overlapping
  └── Cognitive Engine requests source map for selector `.btn-primary`
      └── SourceLinker queries page for DOM metadata
          └── Fiber scraper retrieves file metadata: `Button.tsx`, Line 15
              └── SourceLinker parses source map to confirm original line
                  └── Returns `SourceLink` object
                      └── RCA Engine uses object to document root cause
                          └── Coder Agent uses link to apply CSS fix directly to Card.tsx:15

## 10. Existing Asset Analysis
- Reuses page runtime JavaScript execution patterns from `frontend-visual-debug`.
- Integrates with standard workspace file loaders from `db.py`.

## 11-13. Implementation Details
- **Contracts:** `SourceLinker(Protocol)` interface.
- **Privacy:** Rejects resolution of files outside the git repository directory tree.
- **Failures:** Fallback locator searches for unique DOM IDs or class groupings if metadata is stripped.

## 14-16. Metrics & Business Value
- **Token savings**: Up to 40% reduction in debug discussion logs.
- **Efficacy**: 100% of visual bugs have corresponding code location references.

## 17. Risk Matrix
- *Risk:* Production build strips source maps. *Mitigation:* Sandbox Orchestrator configures source maps in dev builds (FEAT-070).
- *Risk:* Dynamic CSS-in-JS hashes. *Mitigation:* Fallback ast-matching on surrounding layout tree.

## 34. Acceptance Criteria
- [ ] AC-01: Returns React component name, file, and line for DOM node.
- [ ] AC-02: Resolves bundle coordinates to original workspace files using source maps.
- [ ] AC-03: Traces Tailwind CSS utility class back to JSX render line.
- [ ] AC-04: Blocks and flags mapping results pointing outside authorized blueprint boundaries.

## 35. Final Planning Prompt
Provide design blueprints for React Fiber and Vue vnode scrapers, source map AST parsers, Tailwind class tracing, and JSX component line resolution.
