# Technical Blueprint — FEAT-110 Multi-Agent Operations Dashboard and Recovery Center

## 1. Multi-Agent Team and Write Scopes
Hệ thống sử dụng tổ hợp 8 tác nhân chuyên biệt điều phối phát triển dự án:
- **AGENT-DISCOVERY-001** (Discovery): Chỉ đọc, phát hiện ranh giới dự án.
- **AGENT-PROD-001** (Product): Quản lý tài liệu yêu cầu.
- **AGENT-ARCH-001** (Architecture): Chịu trách nhiệm viết tài liệu thiết kế. Write scope: `docs/designs/`.
- **AGENT-RUNTIME-001** (Runtime): Quản lý tích hợp bộ điều phối. Write scope: `skills/workflow-runtime/scripts/`.
- **AGENT-BACKEND-001** (Backend API): Triển khai router và CLI subcommand. Write scope: `skills/workflow-runtime/scripts/workflow_runtime.py`.
- **AGENT-FRONTEND-001** (Frontend Dashboard): Giao diện HTML. Write scope: `extensions/visualizer/resources/webview.html`.
- **AGENT-TEST-001** (Test): Viết unit tests. Write scope: `skills/workflow-runtime/tests/`.
- **AGENT-VERIFY-001** (Verification): Kiểm tra tính đúng đắn và phát hành báo cáo. Write scope: `docs/verification/`, `reports/`, `artifacts/`.

## 2. 25-Task Graph Structure (DAG)
Thiết lập đồ thị phụ thuộc gồm 25 tác vụ song song và nối tiếp:
```text
TASK-001 (workspace discovery) -> TASK-002 (architecture analysis) -> TASK-003 (requirement validation)
-> TASK-004 (planning) -> TASK-005 (blueprint)
-> [TASK-006 (backend contract design), TASK-007 (runtime adapter design), TASK-008 (frontend data model)]
-> [TASK-009 (backend implementation), TASK-010 (runtime integration), TASK-011 (frontend dashboard), TASK-012 (graph visualization)]
-> [TASK-013 (real-time updates), TASK-014 (recovery controls), TASK-015 (audit trail)]
-> [TASK-016 (unit tests), TASK-017 (integration tests), TASK-018 (UI tests)]
-> TASK-019 (build) -> TASK-020 (debug) -> TASK-021 (independent verification)
-> TASK-022 (concurrency validation) -> TASK-023 (evidence collection) -> TASK-024 (compliance report) -> TASK-025 (final verification)
```

## 3. False Completion Protection
Mã nguồn backend và giao diện Visualizer bắt buộc thẩm định tính toàn vẹn:
- Trạng thái Objective chỉ được phép hoàn thành khi toàn bộ 25 tác vụ bắt buộc (required) trong đồ thị có trạng thái `completed` hoặc `passed`.
- Nếu Objective.status = `completed` nhưng tồn tại bất kỳ tác vụ bắt buộc nào chưa kết thúc, giao diện Visualizer bắt buộc phải kích hoạt khối cảnh báo màu đỏ chói hiển thị `INTEGRITY ERROR: Unfinished required tasks detected!`.
