<!-- File path: docs/plans/FEAT-116_autonomous_delivery_after_brainstorming_plan.md -->

---
feature_id: FEAT-116
feature_name: Autonomous Delivery After Brainstorming
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT_autonomous_delivery_after_brainstorming.md
next_artifact: ../designs/FEAT-116_autonomous_delivery_after_brainstorming_blueprint.md
---

# FEAT-116: Autonomous Delivery After Brainstorming

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Add `autonomous_delivery` flag to Session schema and parser | [x] |
| FR-02 | Phase 1 | Task 1.2 | Implement `--autonomous` CLI flag in workflow CLI | [x] |
| FR-03 | Phase 1 | Task 1.3 | Sync `autonomous_delivery` status in `context.json` | [x] |
| FR-04 | Phase 2 | Task 2.1 | Implement automatic phase transition logic bypassing approval gates | [x] |
| FR-05 | Phase 2 | Task 2.2 | Implement Resource Circuit Breaker in runtime manager | [x] |
| FR-06 | Phase 2 | Task 2.3 | Implement Debug Loop Throttle (Max 5 retries per failure) | [x] |
| FR-07 | Phase 3 | Task 3.1 | Implement progress percentage computation of the DAG lifecycle | [x] |
| FR-08 | Phase 3 | Task 3.2 | Update `webview.html` to display autonomous progress bar | [x] |
| FR-09 | Phase 4 | Task 4.1 | Implement Shadow Mode verification configuration | [x] |

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ:
- **Task 1.1 - 1.3**: [Coder] - Cập nhật cấu trúc trạng thái và cấu hình CLI.
- **Task 2.1 - 2.3**: [Architect / Coder] - Thiết kế và xây dựng luồng chuyển tiếp tự động, bộ ngắt mạch an toàn, và điều phối vòng lặp debug.
- **Task 3.1 - 3.2**: [Frontend Developer / Designer] - Cập nhật giao diện Visualizer và hiển thị thanh tiến trình động.
- **Task 4.1**: [Verifier] - Triển khai chế độ chạy ẩn (Shadow mode) và kiểm thử liên kết.

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3 -> Task 2.1 -> Task 2.2 -> Task 2.3
- **Parallel Tasks**: [Task 3.1, Task 3.2] (Sau khi hoàn tất Phase 2)
- **Blocking Tasks**: Task 2.1 (bắt buộc hoàn thành trước khi triển khai Task 3.1)
- **Independent Tasks**: Task 4.1
- **Recommended Execution Groups**:
  - Group 1: Task 1.1, Task 1.2, Task 1.3 (Tuần tự cấu hình hệ thống)
  - Group 2: Task 2.1, Task 2.2, Task 2.3 (Tuần tự lõi điều phối tự động)
  - Group 3: Task 3.1, Task 3.2 (Song song hiển thị Visualizer)
  - Group 4: Task 4.1 (Kiểm thử độc lập)

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/workflow-runtime/scripts/session.py` | Modify | Thêm trường cấu hình `autonomous_delivery` vào schema |
| Task 1.2 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Thêm tham số `--autonomous` và xử lý cờ CLI |
| Task 1.3 | `skills/workflow-runtime/scripts/state_sync.py` | Modify | Đồng bộ cờ tự động hóa vào tệp trạng thái context |
| Task 2.1 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Bỏ qua các gate thủ công nếu cờ tự động hóa bật |
| Task 2.2 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Giám sát tài nguyên CPU/RAM và ngắt mạch nếu quá tải |
| Task 3.1 | `skills/workflow-runtime/scripts/state_sync.py` | Modify | Tính toán phần trăm tiến độ DAG |
| Task 3.2 | `extensions/visualizer/resources/webview.html` | Modify | Hiển thị thanh tiến trình động trên UI |
| Task 3.2 | `extensions/visualizer/src/webviewHtml.ts` | Modify (via build) | Được tự động sinh thông qua `node build.js` |

## 5. Blueprint Preparation Inputs

Định hướng thiết kế chi tiết:
- **Interfaces**: API kiểm tra trạng thái tự động (`is_autonomous_delivery_enabled()`).
- **Data Flow**: `User request` -> `RRS Calculation` -> `Autonomous Session Start` -> `Orchestrator loop` -> `Auto transition gates` -> `Final Release Gate` -> `User confirm`.
- **Migration Strategy**: Triển khai trước Shadow Mode để kiểm chứng độ chính xác trước khi bật Opt-in Mode.

## 6. Verification Strategy & Test Mapping

- **Unit Tests**: Kiểm thử việc parse cờ session và cấu hình CLI (Ánh xạ vào Task 1.1, 1.2).
- **Integration Tests**: Kiểm thử luồng chuyển tiếp tự động chạy qua các phase giả lập mà không dừng (Ánh xạ vào Task 2.1).
- **Compatibility / Regression Tests**: Đảm bảo chế độ thường (Manual approvals) hoạt động chính xác khi cờ tắt.

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] Schema session được cập nhật thành công và không lỗi biên dịch.
  - [ ] CLI nhận diện đúng cờ `--autonomous`.
- **Phase 2 Exit Criteria**:
  - [ ] Luồng chạy nền tự động chuyển phase trơn tru.
  - [ ] Circuit breaker ngắt mạch chính xác khi giả lập lỗi tài nguyên.

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - Trigger: Gặp lỗi đọc/ghi schema session làm hỏng việc đọc file cũ.
  - Steps: Revert git commit liên quan đến `session.py`, khôi phục tệp context cũ từ backup.
- **Phase 2 Rollback**:
  - Trigger: Luồng chạy nền bị deadlock hoặc treo vô hạn.
  - Steps: Dừng daemon orchestrator, xóa file lock và phục hồi phiên hoạt động thủ công.

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | Yes | No |
| Task 2.1 | Yes | Yes | Yes | No | No | Yes | No |
| Task 3.2 | Yes | No | No | Yes | Yes | No | No |

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: `docs/designs/FEAT-116_autonomous_delivery_after_brainstorming_blueprint.md`
- **Phase 2 Artifacts**: `docs/designs/FEAT-116_autonomous_delivery_after_brainstorming_blueprint.json`

## 11. Token & Execution Optimization

- **Sequential execution cost**: Luồng chạy nền giảm thiểu 100% chi phí tokens chờ phản hồi từ người dùng giữa các bước.
- **Parallel execution**: Triển khai song song frontend và backend tiết kiệm 30% thời gian thực thi của Coder.

## Recommended Next Skill
/blueprint
