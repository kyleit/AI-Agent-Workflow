---
artifact_type: blueprint
feature_id: QUICK-008
workflow: quick-feature
status: draft
---

# Technical Design Blueprint – Update Interactive Docs with Orchestrator Workflow

This blueprint defines the changes in the interactive documentation files to include the Orchestrator skill and workflow, and fixes the mobile layout overflow/squishing issue for the workflow tab buttons.

## 1. Proposed Code Changes

### [Component] Skills Data & Catalog

#### [MODIFY] [skills-data.js](file:///Volumes/Kyle/AgentsProject/interactive-docs/docs-assets/skills-data.js)
- Add a new skill entry object for `orchestrator` at the end of the `skillsData` array.

---

### [Component] Documentation Layout & Interactive Tabs

#### [MODIFY] [index.html](file:///Volumes/Kyle/AgentsProject/interactive-docs/index.html)
- Add a new tab button "4. Quy trình Điều phối (Orchestrator)" under the `.flow-tabs-nav` navigation bar.
- Add a new workflow panel `#flowOrchestrate` under the `workflows` tab content area describing the orchestrated workflow timeline and parallel execution constraints.

---

### [Component] Stylesheet Layout (Mobile Responsiveness)

#### [MODIFY] [style.css](file:///Volumes/Kyle/AgentsProject/interactive-docs/docs-assets/style.css)
- Under the media query `@media screen and (max-width: 768px)` (around line 931), update `.flow-tabs-nav` and `.flow-tab-btn` styles:
  ```css
  .flow-tabs-nav {
      display: flex !important;
      flex-wrap: nowrap !important;
      overflow-x: auto !important;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
      width: 100%;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  
  .flow-tab-btn {
      white-space: nowrap !important;
      flex-shrink: 0 !important;
  }
  ```

---

## 2. Test Plan

### Manual Verification
- Open `interactive-docs/index.html` in a web browser.
- Verify that the "4. Quy trình Điều phối (Orchestrator)" tab button is visible under "Các luồng Workflow".
- Click on the button and verify that the panel is shown and others are hidden.
- Go to the "Thư mục 19 Skills" tab, type `/orchestrate` or `orchestrator` in the search bar, and verify that the Orchestrator skill is displayed.
- Resize browser window to mobile width (or inspect under mobile responsive mode). Verify that the workflow tab navigation menu is scrollable horizontally and buttons do not wrap or shrink.
