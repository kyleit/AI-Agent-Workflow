<!-- File path: docs/plans/FEAT-109_distributed_runtime_plan.md -->

---
feature_id: FEAT-109
feature_name: Distributed AI Runtime Platform
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-109_distributed_runtime.md
next_artifact: ../designs/FEAT-109_distributed_runtime_blueprint.md
---

# FEAT-109: Distributed AI Runtime Platform

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Thiết lập gRPC Client/Server và mô hình Master-Worker | [x] |
| FR-02 | Phase 1 | Task 1.2 | Đăng ký Node Registry cục bộ và từ xa | [x] |
| FR-03 | Phase 2 | Task 2.1 | Phân bổ tác vụ chéo node sử dụng Task Graph v1 | [x] |

## 2. Task Ownership & Roles
- **Task 1.1**: [Coder] - Phát triển gRPC worker agent.
- **Task 1.2**: [Architect] - Định nghĩa cấu trúc Registry trong SQLite.
- **Task 2.1**: [Reviewer] - Đánh giá luồng truyền tải Task Graph phân tán qua mTLS.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2
- **Parallel Tasks**: [Task 2.1]
- **Recommended Execution Groups**:
  - Group 1: Task 1.1, Task 1.2
  - Group 2: Task 2.1

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation (Create/Modify/Delete/Do Not Modify) | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/workflow-runtime/scripts/remote_execution_federation_platform.py` | Modify | Nâng cấp API gRPC |
| Task 1.2 | `skills/workflow-runtime/scripts/node_agent_registry.py` | Create | Tạo Registry lưu trữ danh sách Node |

## 5. Blueprint Preparation Inputs
- **Interfaces / Classes / Modules**: `FederationMaster`, `NodeAgent`.
- **Data Flow / Sequence Flow**: Client đăng ký -> Master chấp thuận -> Lưu trạng thái Node -> Chạy Heartbeat.

## 6. Verification Strategy & Test Mapping
- **Unit Tests**: `test_remote_execution_federation_platform.py` (Mapped to Task 1.1)
- **Integration Tests**: `test_node_agent_registry.py` (Mapped to Task 1.2)

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] 100% các ca kiểm thử kết nối gRPC thành công.
  - [ ] Khóa chứng chỉ SSL được trao đổi hợp lệ qua mTLS.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Lỗi timeout truyền tin mTLS không khắc phục được.
  - Steps: Revert git commit của gRPC, khôi phục cấu hình cổng kết nối mạng cũ.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | Yes | Yes | Yes |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: docs/designs/FEAT-109_distributed_runtime_blueprint.md

## 11. Token & Execution Optimization
- **Sequential execution cost**: Thấp nhờ mô phỏng node giả lập tại máy cục bộ trong pha phát triển.
