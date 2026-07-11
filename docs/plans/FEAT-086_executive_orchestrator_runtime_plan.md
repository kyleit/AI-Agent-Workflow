<!-- File path: docs/plans/FEAT-086_executive_orchestrator_runtime_plan.md -->

---
feature_id: FEAT-086
feature_name: Executive Orchestrator Runtime
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-086_executive_orchestrator_runtime.md
next_artifact: ../designs/FEAT-086_executive_orchestrator_runtime_blueprint.md
---

# FEAT-086: Executive Orchestrator Runtime

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | State Machine loop logic | [x] |
| FR-02 | Phase 1 | Task 1.2 | Loop evaluation metrics | [x] |
| FR-03 | Phase 1 | Task 1.3 | Snapshot persistence controller | [x] |
| FR-04 | Phase 2 | Task 2.1 | Auto-resume & crash recovery | [x] |

## 2. Task Ownership & Roles
Phân bổ người chịu trách nhiệm thực thi các tác vụ:
- **Task 1.1**: [Architect] - Thiết kế máy trạng thái vòng lặp thực thi.
- **Task 1.2**: [Coder] - Triển khai loop logic trong `runtime.py`.
- **Task 1.3**: [Coder] - Triển khai cơ chế snapshot nguyên tử trong `state_sync.py`.
- **Task 2.1**: [Coder] - Triển khai logic auto-resume trong `session.py`.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3
- **Parallel Tasks**: None.
- **Blocking Tasks**: Task 1.3 (blocks Task 2.1)
- **Independent Tasks**: None.
- **Recommended Execution Groups**:
  - Group 1: Task 1.1
  - Group 2: Task 1.2, Task 1.3
  - Group 3: Task 2.1

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.2 | `skills/workflow-runtime/scripts/runtime.py` | Create | Tạo nhân loop controller |
| Task 1.3 | `skills/workflow-runtime/scripts/state_sync.py` | Modify | Thêm hàm ghi snapshot nguyên tử |
| Task 2.1 | `skills/workflow-runtime/scripts/session.py` | Modify | Tích hợp phục hồi session từ snapshot |

## 5. Blueprint Preparation Inputs
Cung cấp định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces**: Lớp `ExecutiveLoopController` quản lý vòng lặp thực thi và chuyển trạng thái.
- **Provider Pattern**: Sử dụng `StateStoreProvider` để quản lý các snapshot vật lý.
- **Sequence Flow**: Khởi chạy -> Quét Snapshot -> Tải trạng thái -> Bắt đầu vòng lặp thực thi.

## 6. Verification Strategy & Test Mapping
- **Unit Tests**: Kiểm thử máy trạng thái `runtime.py` (Mapped to Task 1.2).
- **Integration Tests**: Kiểm thử ghi/đọc snapshot trên đĩa (Mapped to Task 1.3).
- **Compatibility Tests**: Xác nhận định dạng snapshot hoạt động bình thường với Visualizer.

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] 100% Unit Tests máy trạng thái vượt qua (Pass).
  - [ ] File snapshot JSON ghi xuống đĩa đúng định dạng.
- **Phase 2 Exit Criteria**:
  - [ ] Phục hồi trạng thái loop thành công sau khi giả lập lỗi tắt tiến trình đột ngột.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Gặp lỗi kiểm thử hệ thống nghiêm trọng hoặc làm hỏng session hiện có.
  - Steps: Revert git commit của Sprint 1, khôi phục `session.py` cũ.
  - Recovery: Trả về trạng thái hoạt động bình thường trên nhánh main.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.2 | Yes | Yes | Yes | No | Yes | Yes | No |
| Task 1.3 | Yes | Yes | Yes | No | No | No | No |
| Task 2.1 | Yes | Yes | Yes | No | Yes | Yes | No |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: docs/designs/FEAT-086_executive_orchestrator_runtime_blueprint.md
- **Phase 2 Artifacts**: docs/adr/ADR-007_loop_recovery.md

## 11. Token & Execution Optimization
- **Sequential execution cost**: Mỗi vòng lặp tốn từ 100ms - 200ms CPU overhead.
- **Expected token savings**: Tiết kiệm 30% lượng token gửi lên LLM nhờ nạp cache nóng trạng thái.

## Recommended Next Skill
/blueprint
