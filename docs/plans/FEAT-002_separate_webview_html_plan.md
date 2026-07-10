<!-- File path: docs/plans/FEAT-002_separate_webview_html_plan.md -->

---
feature_id: FEAT-002
feature_name: Separate Webview HTML from extension.ts
status: reviewed
stage: planning
created_at: 2026-07-04
updated_at: 2026-07-04
previous_artifact: ../brainstorming/FEAT-002_separate_webview_html.md
next_artifact: ../designs/FEAT-002_separate_webview_html_blueprint.md
---

# Implementation Plan – Separate Webview HTML from extension.ts

## 1. Overview
- **Feature name**: FEAT-002: Separate Webview HTML from extension.ts
- **Business objective**: Improve code maintainability, readability, and ease of styling/UI updates for developers working on the Visualizer sidebar extension.
- **Technical objective**: Move the ~700 lines of HTML/CSS/JS template literal code out of `extensions/visualizer/src/extension.ts` into a resource template file, and statically inline it into compiled code at build-time.
- **Expected outcome**: A clean, TypeScript-only `extension.ts` file under 200 lines, with a standalone `resources/webview.html` template supported by full IDE syntax highlighting, auto-formatting, and autocomplete.

## 2. Memory Consultation Summary
- **Memory Confidence**: Low
- **Memory Documents Read**: None (Memory is not initialized locally in this workspace).
- **RAG Query Used**: None
- **RAG Results Summary**: None
- **Additional Source Files Inspected**:
  - `extensions/visualizer/src/extension.ts` (to analyze inline HTML structure and `getHtmlContent()`)
  - `extensions/visualizer/package.json` (to inspect compiler scripts and build pipeline)
  - `extensions/visualizer/Makefile` (to review packaging commands)
- **Key Architectural Findings**: The visualizer extension uses the standard TypeScript compiler (`tsc`) directly without bundlers like webpack or esbuild. Therefore, static inlining must happen before compile time using code-generation.

## 3. Current Architecture
- **Current modules**: Visualizer Extension sidebar provider in VS Code.
- **Current responsibilities**: Renders the active workflow session, estimates context token usage, handles state changes, and renders visual checklists.
- **Existing limitations**: HTML, CSS styles, and client JavaScript are all written as a giant template literal inside `src/extension.ts`, which prevents formatting, syntax highlighting, and makes edits highly prone to syntax errors.
- **Opportunities for reuse**: Reusing the existing `package.json` compile target by prefixing it with a Node.js generation script.

## 4. Scope
### In Scope
- Extracting the HTML content to `extensions/visualizer/resources/webview.html`.
- Creating `extensions/visualizer/build.js` to compile the HTML into a TypeScript file (`src/webviewHtml.ts`) at compile time.
- Modifying `extensions/visualizer/src/extension.ts` to import the generated template.
- Updating `package.json` to prepend the code-gen script execution to compile steps.

### Out of Scope
- Modifying the webview visual layout, color palette, or logic (refactoring structure only).
- Introducing bundlers like Webpack or Rollup to the extension.

### Assumptions
- Node.js runtime is present during project compilation.

## 5. Proposed Solution
We will implement a pre-build compilation script `build.js` that runs before `tsc`. It will read `resources/webview.html`, escape character literals (backticks, backslashes, dollar signs), wrap it in a TypeScript template export, and output it to `src/webviewHtml.ts`. The main `extension.ts` will import this hằng số string static.

## 6. Architecture Impact
- **Modules affected**: `visualizer` build configuration.
- **Storage/config changes**: Modified `package.json` scripts.
- **Deployment/security**: No change.

## 7. File Impact Analysis
- **[NEW]** `extensions/visualizer/resources/webview.html`
  - *Responsibility*: Store visualizer Webview UI template, CSS layout, and client-side message listeners.
  - *Complexity*: Low.
- **[NEW]** `extensions/visualizer/build.js`
  - *Responsibility*: Read HTML file, escape string characters, and write to `src/webviewHtml.ts`.
  - *Complexity*: Low.
- **[MODIFY]** `extensions/visualizer/src/extension.ts`
  - *Responsibility*: Import `webviewHtml` and return it.
  - *Complexity*: Low.
- **[MODIFY]** `extensions/visualizer/package.json`
  - *Responsibility*: Prepend `node build.js` to build compile targets.
  - *Complexity*: Low.

## 8. Implementation Phases
### Milestone 1: Extract HTML
- Copy inline HTML to `extensions/visualizer/resources/webview.html`.
- Double-check file contents.

### Milestone 2: Build Automation Script
- Create `extensions/visualizer/build.js`.
- Run `node build.js` manually and verify `src/webviewHtml.ts` is generated correctly.

### Milestone 3: Integrate and Verify
- Modify `extension.ts` to use `webviewHtml`.
- Update `package.json` compilation target.
- Run `npm run compile` and package extension via `make package` to verify everything packages correctly.

## 9. Testing Strategy
- **Automated Verification**: Run Visualizer compilation via `npm run compile` and check for TypeScript errors.
- **Manual Verification**: Run `make install` or install the generated VSIX, reload the window, and verify sidebar Webview renders and interacts correctly.

## 10. Risks
- **Risk**: Characters like backticks (\`) and backslashes (\\) inside HTML/JS template literals could cause syntax parsing issues when wrapped in TypeScript strings.
- **Mitigation**: The `build.js` script must replace `\` with `\\`, `\`` with `\``, and `$` with `\$` before wrapping.

## 11. Acceptance Criteria
- [ ] `npm run compile` completes with no compilation errors.
- [ ] `src/extension.ts` does not contain inline HTML string.
- [ ] The generated VSIX packages successfully.
- [ ] Webview UI displays correctly with dynamic state updates working.

## 12. Future Extensions
- HTML minification to reduce code size.
