<!-- File path: docs/plans/FEAT-055_project_context_isolation_plan.md -->

---
feature_id: FEAT-055
feature_name: Project Context Isolation System
status: reviewed
stage: planning
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../brainstorming/FEAT-055_project_context_isolation.md
next_artifact: ../designs/FEAT-055_project_context_isolation_blueprint.md
---

# FEAT-055: Project Context Isolation System

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Mở rộng schema `.session.json` lưu trữ cấu hình Project Scope | [x] |
| FR-02 | Phase 1 | Task 1.2 | Lớp `ContextFirewall` trung tâm xử lý lọc dữ liệu lệch dự án | [x] |
| FR-03 | Phase 1 | Task 1.3 | Bộ lọc 10 bước kiểm tra workspace, git, vector, database | [x] |
| FR-04 | Phase 1 | Task 1.4 | Cơ chế cách ly lịch sử hội thoại và sinh thông báo cảnh báo mismatch | [x] |
| FR-05 | Phase 1 | Task 1.5 | Cập nhật Skill `project-rag-search` để chèn bộ lọc phạm vi dự án | [x] |
| FR-06 | Phase 2 | Task 2.1 | Cập nhật Visualizer Extension Dashboard hiển thị trạng thái cô lập | [x] |
| FR-08 | Phase 2 | Task 2.2 | Quản lý và cách ly tệp SQLite metadata và collection vector | [x] |

## 2. Task Ownership & Roles
Phân bổ người chịu trách nhiệm thực thi các tác vụ:
- **Task 1.1**: [Runtime Developer] - Mở rộng schema session và cập nhật hàm khởi tạo.
- **Task 1.2**: [Architect] - Thiết kế kiến trúc lớp `ContextFirewall`.
- **Task 1.3**: [Runtime Developer] - Cài đặt logic lọc 10 bước.
- **Task 1.4**: [Runtime Developer] - Lọc và hiển thị cảnh báo hội thoại mismatch.
- **Task 1.5**: [RAG Specialist] - Tích hợp bộ lọc vào truy vấn vector database.
- **Task 2.1**: [Frontend Developer] - Phát triển widget trạng thái trên Visualizer.
- **Task 2.2**: [Database Developer] - Thiết lập cấu hình cách ly cơ sở dữ liệu SQLite và vector index.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3 -> Task 1.5
- **Parallel Tasks**: [Task 1.4, Task 2.1]
- **Blocking Tasks**: Task 1.3 (blocks Task 2.2)
- **Independent Tasks**: Task 2.1
- **Recommended Execution Groups**:
  - Group 1: Task 1.1, Task 1.2, Task 1.3
  - Group 2: Task 1.4, Task 1.5
  - Group 3: Task 2.1, Task 2.2

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Thêm cấu hình Project Scope vào session |
| Task 1.2 | `skills/workflow-runtime/scripts/context_firewall.py` | Create | Tạo mới tệp mã nguồn xử lý Firewall |
| Task 1.3 | `skills/workflow-runtime/scripts/context_firewall.py` | Modify | Triển khai logic lọc 10 bước |
| Task 1.4 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Xử lý nạp lịch sử chat và cảnh báo mismatch |
| Task 1.5 | `skills/project-rag-search/scripts/search_client.py` | Modify | Chèn project scope vào truy vấn vector |
| Task 2.1 | `extensions/visualizer/resources/webview.html` | Modify | Thêm HTML hiển thị trạng thái cách ly |
| Task 2.2 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Định tuyến đường dẫn SQLite và vector collection |

## 5. Blueprint Preparation Inputs
Cung cấp định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Định nghĩa lớp `ContextFirewall` với các hàm `validate_request()`, `filter_history()`.
- **Provider Pattern details**: Định tuyến linh hoạt giữa các dịch vụ vector (Qdrant).
- **Data Flow / Sequence Flow**: Vẽ đồ thị dòng chảy của ngữ cảnh qua Firewall.
- **Migration Strategy & Testing Architecture**: Cách gán giá trị mặc định cho session cũ và mô phỏng RAG chéo.

## 6. Verification Strategy & Test Mapping
- **Unit Tests**: Viết unit test cho lớp `ContextFirewall` (Mapped to Task 1.3).
- **Integration Tests**: Kiểm tra RAG search với collection của dự án khác bị chặn thành công (Mapped to Task 1.5 & Task 2.2).
- **Compatibility / Regression Tests**: Chạy các Skill cũ và kiểm tra xem có bị ảnh hưởng bởi firewall hay không (Mapped to Task 1.1).

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] Context Firewall lọc chính xác và từ chối 100% ngữ cảnh lệch dự án.
  - [ ] Hiển thị thông báo cảnh báo mismatch ra console khi phát hiện chéo dự án.
- **Phase 2 Exit Criteria**:
  - [ ] Dashboard hiển thị chính xác số lượng context bị chặn.
  - [ ] Visualizer và webviewHtml.ts được đồng bộ đầy đủ sau khi build.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Lỗi sập luồng tìm kiếm RAG của tất cả các Skill do lỗi lọc Firewall.
  - Steps: Xóa tệp `context_firewall.py`, revert thay đổi tại `workflow_runtime.py` và `project-rag-search`.
  - Recovery: Khôi phục cấu hình và kiểm tra RAG chạy lại bình thường.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | Yes | No |
| Task 1.2 | Yes | Yes | Yes | No | No | No | No |
| Task 1.3 | Yes | Yes | Yes | No | No | No | No |
| Task 1.4 | Yes | Yes | Yes | No | Yes | No | No |
| Task 1.5 | Yes | Yes | Yes | No | No | Yes | Yes |
| Task 2.1 | Yes | No | No | Yes | Yes | No | No |
| Task 2.2 | Yes | Yes | Yes | No | No | Yes | Yes |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: docs/designs/FEAT-055_project_context_isolation_blueprint.md
- **Phase 2 Artifacts**: docs/adr/ADR-055_context_firewall.md

## 11. Token & Execution Optimization
- **Sequential execution cost**: Các lõi lọc phải chạy tuần tự.
- **Expected token savings**: Tiết kiệm hàng ngàn token mỗi phiên nhờ ngăn chặn nạp lịch sử chat chéo dài dòng không liên quan.

## Recommended Next Skill
/blueprint
