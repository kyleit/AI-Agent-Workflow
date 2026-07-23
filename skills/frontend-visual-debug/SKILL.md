---
name: frontend-visual-debug
command: visual-debug
aliases:
  - ui-debug
  - visual-qa
  - browser-debug
category: workflow
tags:
  - frontend
  - ui
  - browser
  - visual
  - debug
  - qa
version: 2.5.0
license: MIT
created_at: 2026-07-05
updated_at: 2026-07-05
description: Validate frontend implementation visually. Uses browser tools when available to debug and verify frontend UI against the expected design and requirements.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: none
  version: none
  provider: optional
  usage: none---

# Skill: Frontend Visual Debug (VIR Entry-Point)

## Purpose

Validate frontend implementation visually. This Skill acts as the entry-point coordinator for the Visual Intelligence Runtime (VIR).

### 🚀 VIR Canonical Invocation Chain
Every frontend visual debugging action follows this routing path:
1. `frontend-visual-debug` loads the active context plan.
2. Invokes `frontend-design` to act as the Design Authority.
3. Invokes `vir-investigate` to compile the investigation plan.
4. Requests observations from `vir-runtime` (referencing the canonical runtime `skills/vir-runtime/scripts/vir.py`).
5. After resolving any root causes, runs `vir-verify` to apply final quality gates.
6. Invokes `vir-memory-update` to store baseline/lessons updates.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the aiwf Go Native CLI Engine (`aiwf`):
- **Validate Checkpoint**: Run `aiwf validate --checkpoint "exactly 7"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `aiwf start --skill "frontend-visual-debug" --command "visual-debug" --checkpoint 8 --step "Starting execution..."`
  - *Step Updates*: Run `aiwf step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `aiwf complete --checkpoint 8 --step "Step Complete" --next-skill "debug-to-verify" --next-command "verify"` when execution finishes successfully.
  - *Failure*: Run `aiwf fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.

## Inputs

The Skill may receive:
```text
Feature ID
Blueprint file
Design screenshot
Expected UI description
Target route
Local dev URL
```

If these inputs are missing, infer them by scanning:
- `docs/features/<feature-family>/blueprints/` (Technical Blueprint — `<WORK_ITEM_ID>_<slug>_blueprint.md`, or the multi-phase `phase-NN-<phase-slug>/phase-blueprint.md` + companions for the relevant frontend phase; legacy flat or former work-item files may be read only for older work)
- `docs/brainstorming/` (Requirements)
- `docs/plans/` (Implementation Plan)

---

## Browser Tool Policy

*   **If IDE Browser Tools are Available**:
    The agent MUST use them.
    1. Open the browser using available tools (e.g., `browser_subagent`).
    2. Navigate to the local development server URL.
    3. Inspect the page DOM, layout, spacing, alignment, and responsiveness.
    4. Check console logs for errors, warnings, or hydration mismatches.
    5. Check the network tab for failed asset downloads or failed API requests.
    6. Take screenshots of key states (standard layout, responsive breakpoints, modals, hover states) and review them.
    7. Verify core frontend interactions (e.g., button clicks, form submissions, dropdowns).
*   **If IDE Browser Tools are NOT Available**:
    1. Attempt a real browser path through Chrome DevTools Protocol (CDP) or an equivalent browser automation surface before falling back to static inspection.
    2. Start or reuse the local dev server, launch/connect a browser with a debug port, navigate to the target URL, inspect DOM/layout, console, network, responsive breakpoints, and affected interactions, then capture screenshots.
    3. If CDP/equivalent browser automation is unavailable, explain the missing capability clearly, perform static inspection only as supporting analysis, and mark the status `PARTIAL` or `FAILED`.
    4. **Strict Rule**: Under no circumstances can the visual debug report be marked as `PASS` without real browser or CDP/equivalent browser automation evidence.

Opening a browser once is not evidence. A screenshot without inspection is not evidence. PASS requires the Agent to compare the rendered UI against the Blueprint, user request, and `frontend-design` acceptance criteria.

## Visual PASS Evidence Contract

The report may mark `PASS` only when every affected UI criterion has concrete evidence:
- Desktop and mobile screenshots, plus tablet when the layout materially changes.
- Screenshots for affected states such as modal, drawer, menu, hover/focus, loading, empty, error, form validation, and disabled states when applicable.
- DOM/layout inspection notes for spacing, alignment, clipping, overflow, z-index, text wrapping, and visual hierarchy.
- Console and network inspection results, including blocking errors, failed assets, failed API calls, hydration mismatches, or uncaught promises.
- Interaction evidence for affected buttons, forms, navigation, menus, toggles, dialogs, and keyboard/focus paths.
- Responsive evidence for the required breakpoints.
- Explicit comparison against Blueprint and `frontend-design` acceptance criteria.

Automatic FAIL conditions:
- No real browser/CDP evidence.
- Missing required screenshots.
- Only static/source inspection was performed.
- Known visual mismatch remains unfixed.
- Text overlaps, clips, or overflows its container.
- Layout breaks at required breakpoints.
- Blocking console/network errors exist.
- Required interaction, keyboard, focus, or navigation path fails.
- The rendered UI conflicts with explicit user requirements, Blueprint decisions, or `frontend-design` criteria.

If any automatic FAIL condition is present, apply the smallest in-scope fix, rerun browser/CDP inspection, update screenshots, and repeat until PASS or a real blocker is documented.

---

## Supported Frontend Stacks

The Skill must detect the workspace technology stack:
- Vite
- React
- Vue
- Svelte / SvelteKit
- Next.js
- Nuxt
- Angular
- Wails frontend
- Plain HTML/CSS/JS

---

## Execution Workflow

1.  **Framework & Dev Command Detection**:
    - Scan package manifests (e.g. `package.json`) or script files.
    - Identify the start/dev server command (e.g. `npm run dev`, `vite`, `next dev`).
2.  **Dev Server Launch**:
    - Start the local dev server using `run_command` in the background (if not already running).
    - Wait for the dev server to start and retrieve its local URL (e.g., `http://localhost:5173`).
3.  **Visual and Interaction Audit (via Browser Subagent when available)**:
    - Open browser and navigate to the target route/URL.
    - **Layout checks**: Spacing, alignment, clipping, overflows, scrollbars, z-index, responsive behavior across breakpoints (mobile, tablet, desktop).
    - **Styling checks**: Colors, borders, shadows, hover/focus states, dark/light mode toggle.
    - **Interaction checks**: Test buttons, navigation links, modal popups, dropdown toggles, fullscreen behavior, loading state, empty state, and error handling.
    - **Runtime checks**: Read console outputs to ensure zero runtime exceptions, uncaught promises, broken assets, or asset load failures.
4.  **UI Bug Fixing (Scope Protection)**:
    - If layout, styling, or console errors are detected:
      - **Allowed**: Fix CSS, layout properties, HTML/component markup, frontend state management, local interactions, and responsive CSS.
      - **Forbidden**: Redesign requirements, refactor unrelated modules, modify backend API architecture, or skip failing verification.
      - Apply minimal, precise fixes to the affected components in the active feature scope.
      - Re-run browser checks to confirm the fix succeeded.
5.  **Report Generation**:
    - Generate the report at `docs/features/<feature-family>/verification/<WORK_ITEM_ID>_<slug>_visual_debug.md` (or `docs/features/<feature-family>/verification/phase-NN-<phase-slug>/phase-visual-debug.md` when debugging one phase of a multi-phase feature) matching the layout below.

---

## Output Template

Generate `docs/features/<feature-family>/verification/FEAT-XXX_slug_visual_debug.md` (or the phase variant above) in the following format:

```markdown
# Visual Debug Report

## Feature
- ID: [FEAT-XXX]
- Title: [Feature Title]

## Target Route
- Route: [e.g., /settings, /dashboard, /]
- Local dev URL: [e.g., http://localhost:5173]

## Browser Tool Used
- [Yes / No]

## Dev Server
- Command: [e.g., npm run dev]
- URL: [e.g., http://localhost:5173]

## Screenshots Reviewed
- [List screenshots taken, e.g. Desktop dashboard view, Mobile menu drawer open]

## Console Errors
- [None | List of warnings/exceptions captured]

## Network Errors
- [None | List of failed network requests or asset loading failures]

## Visual Findings
- [Document layout, spacing, alignment, alignment to design requirements]

## Interaction Findings
- [Document button click test, input forms, modals, toggles]

## Responsive Findings
- [Document mobile layout, tablet layout, breakpoint behavior]

## Fixes Applied
- [None | List of CSS/component fixes applied during debug]

## Remaining Issues
- [None | List of minor items for future tickets]

## Visual Status
- [PASS / PARTIAL / FAILED]
- *Note: Must be FAILED if critical visual bugs remain. Must be PARTIAL if browser tools are unavailable and static check was used.*

## Recommended Next Skill
- /verify
```

---

## Completion Rule

The Skill may report `PASS` only when:
- Page loads successfully with no blocking console/network errors.
- The design layout and responsive checks pass.
- Core interactions are fully functional.
- Real browser or CDP/equivalent browser automation was used to verify the page visually.
- Required screenshots and inspection evidence are included in the report.

If no real browser or CDP/equivalent automation path is available, the status MUST be set to `PARTIAL` or `FAILED`, never `PASS`.
If critical visual or interaction bugs remain, set to `FAILED`.
