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
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
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
  usage: none
---

# Skill: Frontend Visual Debug

## Purpose

Validate frontend implementation visually. This Skill is invoked to confirm that the UI:
- matches the expected design and layout
- satisfies frontend requirements
- loads successfully in the browser with no console or network errors
- has correct responsive behavior and spacing/alignment
- has no broken key interactions or visual regressions

This Skill must run after `blueprint-to-implementation` or after `implementation-to-debug` when the feature affects frontend/UI. If the feature does not affect frontend/UI, this Skill may be skipped.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 7"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "frontend-visual-debug" --command "visual-debug" --checkpoint 8 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 8 --step "Step Complete" --next-skill "debug-to-verify" --next-command "verify"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

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
- `docs/designs/` (Technical Blueprint)
- `docs/brainstorming/` (Requirements)
- `docs/plans/` (Implementation Plan)

---

## Browser Tool Policy

*   **If Browser Tools are Available**:
    The agent MUST use them.
    1. Open the browser using available tools (e.g., `browser_subagent`).
    2. Navigate to the local development server URL.
    3. Inspect the page DOM, layout, spacing, alignment, and responsiveness.
    4. Check console logs for errors, warnings, or hydration mismatches.
    5. Check the network tab for failed asset downloads or failed API requests.
    6. Take screenshots of key states (standard layout, responsive breakpoints, modals, hover states) and review them.
    7. Verify core frontend interactions (e.g., button clicks, form submissions, dropdowns).
*   **If Browser Tools are NOT Available**:
    1. Explain clearly to the user that browser automation tools are unavailable.
    2. Fall back to static inspection of frontend source code (components, markup, CSS styles).
    3. Perform dry-run code reviews against the blueprint and responsive guidelines.
    4. Recommend manual visual verification to the user.
    5. **Strict Rule**: Under no circumstances can the visual debug report be marked as `PASS` without browser automation inspection. The status MUST be set to `PARTIAL`.

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
    - Generate the report at `docs/verification/FEAT-XXX_visual_debug.md` matching the layout below.

---

## Output Template

Generate `docs/verification/FEAT-XXX_visual_debug.md` in the following format:

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
- Browser tools were used to verify the page visually.

If browser tools are unavailable, the status MUST be set to `PARTIAL`.
If critical visual or interaction bugs remain, set to `FAILED`.
