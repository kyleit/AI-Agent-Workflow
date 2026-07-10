---
feature_id: FEAT-029
feature_name: Project/Global Usage Scope Aggregation Fix
status: draft
stage: brainstorming
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: None
next_artifact: ../plans/FEAT-029_project_global_usage_scope_aggregation_fix_plan.md
---

# Master Requirement Document – Project/Global Usage Scope Aggregation Fix

## 1. Feature ID & Name
- **Feature ID**: FEAT-029
- **Feature Name**: Project/Global Usage Scope Aggregation Fix

## 2. Original Idea
Investigate and fix a suspected bug where Project Usage and Global Usage show unrealistically high and identical values, while Active Context and Workflow Accumulated Usage look reasonable.
Do NOT start by changing the Visualizer UI. Treat the UI as a passive renderer until proven otherwise.

## 3. Business Problem
- **Problem**: Giao diện hiển thị số liệu thống kê sử dụng token của Dự án (Project Usage) và Toàn cầu (Global Usage) hiển thị giá trị khổng lồ giống nhau hoàn toàn (ví dụ: 282.3M tokens), mặc dù lượng token của Active Context và Workflow chỉ khoảng vài trăm nghìn.
- **Why it matters**: Làm giảm tính tin cậy của telemetry hệ thống, khiến lập trình viên lo lắng về chi phí API và giới hạn ngữ cảnh khi thực tế mức tiêu thụ thấp hơn rất nhiều.
- **Who is affected**: Lập trình viên và agents theo dõi ngân sách token và hiệu năng context.
- **Expected outcome**: Hiển thị chính xác lượng token tiêu thụ theo đúng phạm vi:
  - Active Context: Kích thước của lượt hội thoại hiện tại.
  - Workflow: Lượng tích lũy của phiên làm việc hiện tại.
  - Project: Tổng lượng tiêu thụ của riêng dự án hiện tại (được lọc chính xác theo `project_id`).
  - Global: Tổng lượng tiêu thụ của tất cả các dự án đã đăng ký.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01 (Lọc Project ID): Cập nhật hàm `get_project_summary()` để lọc dữ liệu theo `project_id` hiện tại (`WHERE project_id = ?`).
  - FR-02 (Tính tuần tự và Idempotent): Đảm bảo các lần đồng bộ lại (sync) không ghi đè hoặc cộng dồn trùng lặp bản ghi cho cùng một phiên hội thoại, trừ khi có thông số lượt chạy mới.
  - FR-03 (Dọn dẹp dữ liệu rác cũ): Triển khai tập lệnh chuẩn hóa/đặt lại dữ liệu lịch sử bị phình to trong tệp cơ sở dữ liệu dự án (`project_runtime.db`) và toàn cầu (`global_runtime.db`).
  - FR-04 (CLI Diagnostics): Cập nhật CLI lệnh `diagnose` hiển thị so sánh chính xác giữa số liệu thực tế trong transcript, số liệu lưu trong DB và hiển thị trên UI.
- **Non-functional Requirements**:
  - NFR-01 (Idempotency): Chạy lệnh `aiwf usage sync` nhiều lần liên tiếp không làm tăng số liệu Project/Global.
  - NFR-02 (Zero-overhead): Việc lọc và truy vấn tính tổng trên SQLite không gây trễ khi cập nhật trạng thái Visualizer.
- **Technical Constraints**:
  - TC-01: Truy vấn SQLite trực tiếp trên tệp `project_runtime.db` và `global_runtime.db`.
  - TC-02: Không sử dụng đường dẫn tuyệt đối ở bất kỳ tài liệu hay tệp kiểm thử nào.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Làm thế nào để xác định duy nhất một lượt chạy (request) nhằm tránh double-counting? | Sử dụng khóa chính gồm `conversation_id` để cập nhật/thay thế bản ghi tích lũy của phiên hiện tại thay vì chèn bản ghi mới liên tục. |
| Nếu dữ liệu lịch sử bị phình to (283M tokens) do lỗi phiên bản cũ, ta xử lý thế nào? | Cần viết hàm `normalize_database_records` thực hiện quét lại các log file transcript để tính toán chính xác lại và ghi đè lên hàng tương ứng trong DB. Nếu log file không tồn tại, điều chỉnh số liệu về giới hạn hợp lý dựa trên ước lượng logic. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: Cấu trúc telemetry của hệ thống lưu trữ bản ghi vào `usage_records` SQLite. Hàm `get_project_summary` trong `db.py` hiện tại truy vấn `SUM(total_tokens) FROM usage_records` mà không lọc theo `project_id`.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Database Management | [.agents/skills/workflow-runtime/scripts/db.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/db.py) | Cần cập nhật các câu lệnh truy vấn SUM và hàm lưu dữ liệu để lọc đúng project. |
| Workflow CLI | [.agents/skills/workflow-runtime/scripts/workflow_runtime.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/workflow_runtime.py) | Cần truyền tham số `project_id` hiện tại từ session vào hàm gọi của `db.py`. |

## 9. Solution Options Evaluated

### Option A: Lọc theo Project ID, Idempotency & Chạy dọn dẹp dữ liệu cũ (Khuyên dùng)
- **Overview**: Cập nhật hàm `get_project_summary` nhận `project_id` làm tham số và thêm điều kiện `WHERE project_id = ?`. Viết hàm dọn dẹp dữ liệu rác lịch sử trong SQLite và đảm bảo idempotency khi đồng bộ dữ liệu.
- **Architecture**: Thay đổi trực tiếp tại `db.py` và `workflow_runtime.py`.
- **Advantages**: Sửa tận gốc lỗi rác dữ liệu cũ, tách biệt hoàn toàn phạm vi Project và Global.
- **Disadvantages**: Cần thêm mã lệnh để di trú và dọn dẹp dữ liệu.
- **Complexity**: Medium
- **Risk**: Low

### Option B: Chỉ thêm điều kiện lọc Project ID
- **Overview**: Thêm tham số `project_id` vào query của `get_project_summary`. Không làm sạch dữ liệu cũ.
- **Advantages**: Cực kỳ nhanh, ít thay đổi code.
- **Disadvantages**: Lượng token rác khổng lồ (283M) vẫn sẽ hiển thị trong Project Usage của dự án này.
- **Complexity**: Low
- **Risk**: Low

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Medium | Low |
| Risk | Low | Low |
| Performance | High | High |
| Maintainability | High | Medium |
| Compatibility | High | High |
| Future Scalability | High | Low |
| Development Cost | Medium | Low |

## 11. Selected Solution
- **Choice**: Option A — Lọc theo Project ID, Idempotency & Chạy dọn dẹp dữ liệu cũ
- **Why Selected**: Đây là giải pháp triệt để nhất để đưa hệ thống telemetry về trạng thái hoạt động chính xác, đáng tin cậy. Việc dọn dẹp dữ liệu rác đảm bảo giao diện hiển thị đúng các giá trị thực tế của dự án.
- **Trade-offs Accepted**: Chấp nhận công sức viết thêm hàm dọn dẹp DB.
- **Technical Debt**: Không.

## 12. Risks & Assumptions
- **Risks**: Việc sửa đổi cơ sở dữ liệu có thể gây lỗi khóa dữ liệu nếu có tiến trình khác đang ghi. -> *Mitigation*: Sử dụng cơ chế đóng kết nối an toàn trong khối `finally`.

## 13. Acceptance Criteria
- [ ] Hàm `get_project_summary()` lọc chính xác theo `project_id`.
- [ ] Số liệu hiển thị của Project Usage khác biệt với Global Usage (khi có nhiều dự án trong database toàn cầu).
- [ ] Dữ liệu rác lịch sử (283M) được dọn dẹp thành công về giá trị thực tế.
- [ ] Đồng bộ hóa dữ liệu nhiều lần liên tiếp không làm tăng số liệu Project/Global.

---

## 14. Final Planning Prompt

### Purpose
Lời gọi thiết kế chi tiết tiếp theo cho Skill `brainstorming-to-plan`.

### Objectives & Selected Solution
Thực hiện Option A: Sửa câu lệnh truy vấn lọc Project ID, viết cơ chế đồng bộ an toàn và hàm di trú/dọn dẹp dữ liệu rác trong `db.py`.

### Functional Requirements
- Truyền `project_id` vào `get_project_summary()` từ `workflow_runtime.py`.
- Viết hàm `normalize_database_records()` hoặc query tương tự để làm sạch và tính toán lại các dòng token bị phình to trong DB.
- Kiểm thử idempotency với lệnh sync liên tục.

### Verification Checklist
- [ ] docs/plans/FEAT-029_project_global_usage_scope_aggregation_fix_plan.md được phê duyệt.
