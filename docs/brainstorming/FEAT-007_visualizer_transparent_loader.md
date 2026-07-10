<!-- docs/brainstorming/FEAT-007_visualizer_transparent_loader.md -->

---
feature_id: FEAT-007
feature_name: Visualizer Non-Blocking Loader Overlay
status: draft
stage: brainstorming
created_at: 2026-07-04
updated_at: 2026-07-04
previous_artifact: None
next_artifact: ../plans/FEAT-007_visualizer_transparent_loader_plan.md
---

# Master Requirement Document – Visualizer Non-Blocking Loader Overlay

## 1. Feature ID & Name
- **Feature ID**: FEAT-007
- **Feature Name**: Visualizer Non-Blocking Loader Overlay

## 2. Original Idea
Waiting loader overlay covers the checkpoints; make it transparent so we can see the checkpoints list underneath.

## 3. Business Problem
- **Problem**: When the companion extension is waiting for a workflow session to start, a dark blur overlay covers the entire stepper, blocking the checklist view. Developers cannot see the upcoming checkpoint sequence.
- **Why it matters**: Blocking workflow checklist details before execution harms developers' understanding of the incoming workflow tasks.
- **Who is affected**: Developers who want to preview checkpoints while the session initializes.
- **Expected outcome**: Transparent loader overlay showing disabled checkpoints list clearly in the background.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Checkpoint list must be visible in a "pending/disabled" state under the loading screen.
  - FR-02: Loader spinner and connection message must remain visible and legible on top.
- **Non-functional Requirements**:
  - NFR-01: Visual feedback must clearly indicate that the visualizer is "Waiting" (inactive state).
- **Technical Constraints**:
  - TC-01: Must only modify `webview.html` styling rules.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Should checkpoints be clickable during load? | No, they remain non-interactive. |
| Is backdrop filter needed? | Use minimal/no blur so elements are fully legible. |

## 6. Requirement Readiness Score
- **Score**: 96/100
- **Status**: Ready (>= 85)

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///e:/Cloud/_protected/agents/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: Stepper overlays are rendered inside `resources/webview.html`. The webview renders standard checkpoints by default at start.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Webview Template | [webview.html](file:///e:/Cloud/_protected/agents/extensions/visualizer/resources/webview.html) | Style overrides for `.stepper-overlay`. |

## 9. Solution Options Evaluated

### Option A: Semi-transparent overlay with light blur
- **Overview**: Modify `.stepper-overlay` css properties to use `background: rgba(6, 11, 20, 0.45);` and reduce blur `backdrop-filter: blur(1px);`.
- **Advantages**: Checkpoints are visible underneath, loading feedback is maintained, clean styling.
- **Disadvantages**: Minor CSS change.
- **Complexity**: Low
- **Risk**: Low
- **Performance**: High
- **Maintainability**: High
- **Compatibility**: High

### Option B: Spinner Banner (no overlay)
- **Overview**: Delete the overlay completely, replacing it with a loading progress bar at the top header of the stepper.
- **Advantages**: Complete visibility.
- **Disadvantages**: Loading status is less prominent.
- **Complexity**: Medium

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Low | Medium |
| Risk | Low | Low |
| Performance | High | High |
| Maintainability | High | High |
| Compatibility | High | High |
| Future Scalability | High | High |
| Development Cost | Low | Low |

## 11. Selected Solution
- **Choice**: Option A — Semi-transparent overlay with light blur
- **Why Selected**: Very simple to implement, maintains visual connection status cleanly, while keeping the background checkpoints legible.

## 12. Risks & Assumptions
- **Assumptions**: Checkpoint list is populated before session connection (which it is, since webview renders it at startup).

## 13. Acceptance Criteria
- [ ] Checklist is visible under loading overlay.
- [ ] Backdrop blur is set to <= 1px.
- [ ] Overlay background transparency is set to <= 0.5.

---

## 14. Final Planning Prompt

### Purpose
Input for `brainstorming-to-plan` to design non-blocking visual progress list.

### Problem Statement
Loader overlay obscures checkpoints sequence before active connection.

### Objectives & Selected Solution
Modify CSS rules of `.stepper-overlay` to make it semi-transparent and reduce blur backdrop.

### Verification Checklist
- [ ] Verify legibility of checkpoints during loading state.
