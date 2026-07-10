---
feature_id: FEAT-026
feature_name: AIWF Runtime Context Analytics & Optimization Dashboard
status: draft
stage: brainstorming
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: None
next_artifact: ../plans/FEAT-026_context_analytics_dashboard_plan.md
---

# Master Requirement Document – AIWF Runtime Context Analytics & Optimization Dashboard

## 1. Feature ID & Name
- **Feature ID**: FEAT-026
- **Feature Name**: AIWF Runtime Context Analytics & Optimization Dashboard

## 2. Original Idea
AIWF Runtime Context Analytics & Optimization Dashboard: Redesign the runtime usage panel to separate Active Context Window usage from Accumulated API usage (Input, Output, Cache, Thinking, Cost, request count, average input/output per request). Add Efficiency Metrics, Context Growth Graph (store history), Runtime Analyzer to detect duplicate reads (Skills, Rules, Plans, Memory) and provide optimization recommendations, Optimization Advisor with savings estimation, markdown report generation, Token Budget warnings, backward compatibility, and a simulation test generating 500 requests to verify the pipeline. Calculations must be performed in Python (Script-first).

## 3. Business Problem
- **Problem**: Users are confused by current token statistics where "Input tokens" represent accumulated sessions over many requests, causing them to worry that the 2M context window is almost full when it is not. Furthermore, there is no automatic diagnosis of duplicate context reads (which inflate cost) or warnings when approaching token budget limits.
- **Why it matters**: Unoptimized context usage leads to extremely high API bills (e.g., $97.15 for minor code changes) and limits conversation longevity due to redundant rule/file loading.
- **Who is affected**: AI Coding agents and users who want to control API costs.
- **Expected outcome**: Clear separation of metrics on the UI, automatic warnings before token exhaustion, and recommendations to save up to 80% on API costs.

## 4. Requirement Discovery
- **Functional Requirements**:
  - **FR-01 (Data Separation)**: Redesign `.session.json` state schema to house `active_context` (current request sizes) separately from `accumulated_api_usage` (all requests since session start).
  - **FR-02 (Efficiency Metrics)**: Track metrics: cache hit ratio, input-to-output ratio, context growth speed, workspace read count, memory hit count, RAG hit count, large file read counts.
  - **FR-03 (Time-Series Graph Data)**: Maintain a time-series log of context metrics inside `.agents/runtime/analytics_history.json` tracking timestamp, active context, input, output, cache, thinking, and request_number.
  - **FR-04 (Runtime Analyzer)**: Parse logs and session history to detect repetitive reads of static files: `AI_RULES.md`, `AGENTS.md`, design blueprints, implementation plans, and project memory.
  - **FR-05 (Optimization Advisor)**: Dynamically calculate and display estimated token/cost savings (e.g., "Estimated cost reduction: 85%") based on actual duplicate read sizes.
  - **FR-06 (Token Budget thresholds)**: Support configurable settings in `workflow.config.json` for warning/critical thresholds on context size, accumulated cost, and input/output ratios.
  - **FR-07 (Runtime Report CLI)**: Implement command `python3 skills/workflow-runtime/scripts/workflow_runtime.py release report` (or similar) to export a rich markdown analytics report.
  - **FR-08 (Simulation Validation)**: Develop a validation script that mock-generates 500 requests with various token profiles to verify that statistics, budgets, and advisor recommendations are calculated accurately.
- **Non-functional Requirements**:
  - **NFR-01 (Script-First)**: Visualizer code in `webview.html` only reads and renders JSON; it must contain no calculation logic.
  - **NFR-02 (Hi-Fi Performance)**: Analytical computations must run in less than 0.5 seconds on each CLI invocation.
  - **NFR-03 (Backward Compatibility)**: If session schema changes, the engine must support automatic schema migration of `.session.json` without failing.
- **Technical Constraints**:
  - **TC-01 (Visualizer Extensions)**: Modify [webview.html](../../extensions/visualizer/resources/webview.html) and build to `webviewHtml.ts` using `node build.js`.
  - **TC-02 (Absolute Path Prohibition)**: Never use absolute paths (e.g., `/Users/kyle/...`) anywhere in codebase, tests, or documentation.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Where should the budget thresholds be configured? | In `.agents/workflow.config.json` under a new `"token_budget"` object. |
| What visual components should be added to the Visualizer panel? | 1. Active Context gauge, 2. Accumulated usage card grid, 3. Line chart of context growth (using Chart.js in webview), 4. Analyzer recommendations & Advisor savings widget. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: `.agents/memory.config.json`, `MANIFEST.json`
- **Existing Architecture Summary**: AIWF session state is managed by `workflow_runtime.py` and `session.py` writing directly to `.session.json`. We need to introduce `analytics_engine.py` to offload analytical tasks and maintain `analytics_history.json`.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Runtime Engine CLI | [workflow_runtime.py](../../skills/workflow-runtime/scripts/workflow_runtime.py) | Needs to trigger analytics updates. |
| Session Handler | [session.py](../../skills/workflow-runtime/scripts/session.py) | Needs schema expansion for new metrics. |
| Webview Template | [webview.html](../../extensions/visualizer/resources/webview.html) | Main dashboard UI to be redesigned. |

## 9. Solution Options Evaluated

### Option A: In-line State Calculation
- **Overview**: Add analytical counters directly into the core `session.py` dict.
- **Architecture**: Changes `.session.json` properties directly in active memory.
- **Advantages**: Simple to write.
- **Disadvantages**: Bloats `.session.json` size on every turn, increasing Gemini input tokens.

### Option B: Separate Analytics Module & File (Recommended)
- **Overview**: Implement `analytics_engine.py` which computes metrics and saves history in a separate `.agents/runtime/analytics_history.json` file.
- **Architecture**: Runtime CLI triggers analytics calculation at the end of each command. Visualizer reads both files to render.
- **Advantages**: Prevents `.session.json` bloat, keeping session load operations token-efficient.
- **Disadvantages**: Requires managing multiple JSON files in Visualizer.

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Low | Medium |
| Risk | Low | Low |
| Performance | Medium (increases context size) | High (minimal context size) |
| Maintainability | Low | High |
| Compatibility | High | High |
| Future Scalability | Medium | High |
| Development Cost | Low | Medium |

## 11. Selected Solution
- **Choice**: Option B — Separate Analytics Module & File
- **Why Selected**: Tách biệt dữ liệu nén của phiên làm việc với dữ liệu phân tích chi tiết giúp giữ `.session.json` luôn gọn nhẹ, tối ưu hóa Input token cho các lượt chat tiếp theo của Agent.
- **Trade-offs Accepted**: Đòi hỏi webview Visualizer phải gọi API tải 2 file cấu hình thay vì 1.
- **Technical Debt**: Không.
- **Risk Mitigation**: Sử dụng cơ chế khóa ghi tệp nguyên tử (atomic write) để tránh tranh chấp dữ liệu khi cập nhật file lịch sử.

## 12. Risks & Assumptions
- **Risks**: 
  - Submodule hoặc IDE webview không nạp được Chart.js offline -> Giải pháp: Tích hợp thư viện Chart.js local hoặc dùng SVG thuần để vẽ đồ thị tăng trưởng context.
- **Assumptions**: 
  - Project memory có thể cung cấp các kích thước tệp tĩnh để so sánh.

## 13. Acceptance Criteria
- [ ] Tách biệt thành công Active Context và Accumulated API Usage trên `.session.json`.
- [ ] Module `analytics_engine.py` ghi nhận lịch sử tăng trưởng context vào `analytics_history.json`.
- [ ] Runtime Analyzer phát hiện đọc lặp lại Skill/Rules/Memory và in ra báo cáo/cảnh báo.
- [ ] Budget warnings xuất hiện khi vượt ngưỡng cấu hình trong `workflow.config.json`.
- [ ] Giao diện Visualizer [webview.html](../../extensions/visualizer/resources/webview.html) hiển thị đồ thị tăng trưởng context và advisor savings widget.
- [ ] Script giả lập chạy thành công 500 requests mô phỏng và sinh báo cáo BAT hoàn chỉnh.

## 14. Final Planning Prompt

### Purpose
Tạo kế hoạch triển khai chi tiết cho `FEAT-026` nhằm phân tách chỉ số token, đo lường hiệu năng và cải tiến giao diện Visualizer.

### Objectives & Selected Solution
Thực hiện Option B: Viết module Python độc lập `analytics_engine.py` để tính toán số liệu và ghi log lịch sử, cập nhật giao diện `webview.html` để vẽ đồ thị và hiển thị khuyến nghị tối ưu.

### Architectural Details
- **Python side**: Thêm `analytics_engine.py`, cập nhật `workflow_runtime.py` và `session.py`.
- **UI side**: Cập nhật [webview.html](../../extensions/visualizer/resources/webview.html) để hiển thị thông số và đồ thị.

### Verification Checklist
- [ ] docs/plans/FEAT-026_context_analytics_dashboard_plan.md generated and approved
- [ ] docs/designs/FEAT-026_context_analytics_dashboard_blueprint.md generated and approved
- [ ] All Acceptance Criteria mapped to implementation tasks
