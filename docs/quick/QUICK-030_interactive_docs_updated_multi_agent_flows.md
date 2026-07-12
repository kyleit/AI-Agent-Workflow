<!-- File path: docs/quick/QUICK-030_interactive_docs_updated_multi_agent_flows.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-030
workflow: quick-feature
status: pending
---
# Mini Plan & Feature Specification - Interactive Docs Updated Multi-Agent Flows

## 1. Feature Goal
Rewrite the existing static `interactive-docs/` content so it reflects the current AIWF runtime model, updated workflow rules, and the multi-agent/subagent flows already introduced in the framework. The update preserves the current static site UI and route structure while refreshing the Vietnamese documentation copy, workflow simulator data, and skills catalog descriptions.

## 2. Quick Feature Justification
- **Estimated Complexity**: Low to Medium
- **Implementation Scope**: Local documentation website content and simulator data only.
- **Architectural Impact**: Low / purely additive content refresh within the existing static site.
- **Risk Level**: Low
- **Justification**: The change does not modify Runtime API v1, Python workflow runtime logic, provider behavior, database schema, or Visualizer extension runtime code. It updates static documentation files already dedicated to interactive docs.

## 3. Scope Boundary
- **In Scope**:
  - Refresh overview content to describe the current AIWF model: approval gates, blueprint gate, split-state runtime, knowledge runtime, orchestrator-first workflow, resident runtime concepts, and explicit release.
  - Refresh workflow guide copy while keeping the current tab layout.
  - Refresh simulator scenarios in `interactive-docs/docs-assets/app.js` to show current standard, quick-feature, quick-fix, and orchestrated flows.
  - Refresh skill catalog entries in `interactive-docs/docs-assets/skills-data.js` for newly updated runtime and multi-agent behavior.
- **Out of Scope**:
  - Redesigning the static site UI layout.
  - Adding new backend services, build tooling, or external dependencies.
  - Modifying core Python runtime, Runtime API v1, orchestration engine, Visualizer extension, or provider manager code.
  - Changing frozen architecture decisions.
- **Not Modified**:
  - Runtime API v1 behavior.
  - `.agents/state/` runtime schema beyond normal workflow tracking.
  - Any `skills/*/scripts` implementation.
- **Future Work**:
  - A later visual redesign may add a dedicated Multi-Agent Runtime tab, diagrams, or screenshots.

## 4. Trigger / Execution Flow
- **Entry Point**: User request to rewrite `interactive-docs/`.
- **Trigger Source**: Manual documentation update through quick-feature workflow.
- **Execution Order**: Specification approval -> Blueprint approval -> implementation -> static verification.
- **Completion Condition**: Interactive docs open successfully, existing tabs continue to work, simulator scenarios run, and updated content describes the current multi-agent/subagent workflow accurately.

## 5. Runtime Sequence
User request
-> Quick-feature specification
-> Technical design blueprint
-> Blueprint approval
-> Static docs content update
-> Browser/static verification
-> Summary and recommendation for release if desired

## 6. Dependency Contract
- **Required Dependencies**: Existing browser runtime for static HTML/CSS/JS.
- **Optional Dependencies**: None.
- **External Runtime**: None.
- **Expected Contracts**:
  - `skillsData` remains a JavaScript array consumed by `app.js`.
  - `simStepsData` remains keyed by current workflow selector values.
  - Existing DOM ids/classes remain compatible with current router and simulator.
- **Detection Method**: Open local static HTML and verify JavaScript console/runtime behavior.
- **Failure Behavior**: If a tab, search, or simulator interaction fails, fix only the changed docs-site files.

## 7. Error Matrix
| Condition | Expected Behavior | User Visibility | Recovery Action |
|---|---|---|---|
| JavaScript syntax error | Site interaction fails | Browser console error | Fix changed JS file |
| Missing DOM selector | A tab or simulator field does not update | Broken UI section | Preserve selector or update matching markup |
| Content overflow on mobile | Text/cards overflow viewport | Visual layout defect | Adjust copy length or existing responsive CSS only |
| Broken copy button text | Clipboard command is stale or invalid | Wrong command copied | Update command text in HTML |
| Outdated workflow statement | Documentation contradicts AI_RULES | Misleading docs | Correct text to match AI_RULES |

## 8. Non-functional Requirements
- **Performance Expectations**: Static page remains client-only and loads without new network/API dependencies.
- **Blocking vs Asynchronous**: No async runtime work beyond existing browser events.
- **Timeouts**: Not applicable.
- **Retry Policy**: Not applicable.
- **Resource Usage**: No meaningful increase beyond existing static assets.
- **Thread Safety**: Not applicable for static docs.
- **Idempotency**: Re-opening the page shows the same content and simulator initial state.
- **User Interaction**: Existing tabs, filters, copy buttons, and simulator buttons remain familiar.

## 9. Logging Requirements
- **Start**: No runtime logging required for static docs.
- **Progress**: Browser interactions remain visible through UI state changes.
- **Warning**: Simulator may show warning-style terminal lines for approval gates.
- **Skipped**: Not applicable.
- **Success**: Simulator prints success-style terminal lines for completed steps.
- **Failure**: Browser console errors should be absent after verification.
- **Completion**: Final agent summary lists modified files and verification performed.

## 10. Configuration Impact
- **Existing Configs Reused**: Existing static site file layout.
- **New Configs Required**: None.
- **Migration Required**: None.
- **Default Behavior**: Site opens from `interactive-docs/index.html`.
- **Backward Compatibility**: Existing sidebar tabs, search, and simulator interaction model remain intact.

## 11. Design Constraints
- **CLI/API Constraints**: No new CLI commands and no Runtime API v1 modifications.
- **Database Constraints**: No database schema changes or data restructuring.
- **Architectural Constraints**: Preserve frozen runtime architecture and use only the existing static docs structure.

## 12. Blast Radius
- **Affected Skills**: None directly; skills are documented only.
- **Affected Runtime**: None directly; runtime is documented only.
- **Affected Extension**: None.
- **Affected Memory**: None, except normal project-memory update after implementation if requested.
- **Affected Documentation**: `interactive-docs/` static documentation site.
- **Affected Scripts**: Browser-side docs script only.
- **Impact Level**: Low.

## 13. File Change Scope
- **Modify**:
  - `interactive-docs/index.html`
  - `interactive-docs/docs-assets/app.js`
  - `interactive-docs/docs-assets/skills-data.js`
- **Optional**:
  - `interactive-docs/docs-assets/style.css`
- **Do Not Modify**:
  - `skills/workflow-runtime/**`
  - `.agents/skills/**/scripts/**`
  - `extensions/visualizer/**`
  - Runtime API v1 implementation files

## 14. Success Metrics
- **Regression free**: Yes.
- **Backward compatible**: Yes.
- **Token reduction**: Not applicable.
- **Latency improvement**: Not applicable.
- **Implementation completeness**: 100% of selected Option 1 content refresh.

## 15. Rollback Strategy
- **Files Affected**: The files listed in File Change Scope.
- **Safe Rollback Steps**: Revert the modified static docs files with Git if needed.
- **Migration Rollback**: Not applicable.
- **Behavior After Rollback**: Interactive docs return to the previous static content.

## 16. Expanded Acceptance Criteria
- [ ] AC-01 (Success Path): Overview explains updated AIWF guardrails and runtime concepts without changing layout.
- [ ] AC-02 (Success Path): Workflow tabs describe current standard, quick-feature, quick-fix, and orchestrated flows.
- [ ] AC-03 (Success Path): Simulator data includes multi-agent/subagent constraints: analysis-only agents, implementation-only workers, file locks, execution mode choice, and explicit release.
- [ ] AC-04 (Backward Compatibility): Existing sidebar navigation, inner workflow tabs, skill search/filter, copy buttons, and simulator controls still work.
- [ ] AC-05 (Regression): No runtime/skill implementation files are modified.
- [ ] AC-06 (No behavior change outside scope): Static docs update does not alter Runtime API v1, Visualizer extension, or provider behavior.
- [ ] AC-07 (Documentation Accuracy): Content does not claim automatic release, unrestricted parallelism, or code modification without an approved blueprint.

## 17. Self Verification
- [ ] Before vs after review of changed docs-site content.
- [ ] Static browser verification of tabs/search/simulator.
- [ ] Search for forbidden absolute local paths in changed docs files.
- [ ] Confirm no source runtime files changed.

## 18. Open Questions
None. User selected Option 1: rewrite content while keeping the current UI.

## 19. Blueprint Handoff
The technical blueprint must define exact file-by-file changes for `interactive-docs/index.html`, `interactive-docs/docs-assets/app.js`, and `interactive-docs/docs-assets/skills-data.js`, and must keep `interactive-docs/docs-assets/style.css` optional. It must explicitly preserve existing route/tab behavior and document that Runtime API v1 and frozen architecture are out of scope.
