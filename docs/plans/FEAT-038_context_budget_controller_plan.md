<!-- File path: docs/plans/FEAT-038_context_budget_controller_plan.md -->

---
feature_id: FEAT-038
feature_name: Context Budget Controller
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-038_context_budget_controller.md
next_artifact: ../designs/FEAT-038_context_budget_controller_blueprint.md
---

# FEAT-038: Context Budget Controller

## Objective
- **Business Objective**: Chuyển đổi AIWF từ hệ thống giám sát thụ động thành bộ kiểm soát chủ động thời gian thực (active runtime controller) giúp ngăn chặn phình to context lãng phí thông qua các chính sách ngân sách cấu hình linh hoạt.
- **Expected Outcome**:
  - Tự động kiểm tra dự kiến tăng trưởng context trước khi gửi request.
  - Phê duyệt / Áp dụng tự động các hành động dọn dẹp file trùng, nén hội thoại.
  - Cung cấp Tab Budget Controller trên Webview.
  - CLI hỗ trợ các lệnh `usage budget`.

## Scope

### Included
- Thiết kế bảng SQLite `budget_policies` và `budget_history`.
- Phát triển module `budget_controller.py`.
- Tích hợp hook kiểm tra trước mỗi request LLM.
- Thiết kế Tab Budget Controller trên Dashboard.

### Excluded
- Không hỗ trợ tự động xóa mã nguồn của người dùng hoặc các thay đổi phá hủy (destructive action) mà không được người dùng phê duyệt rõ ràng.

## Project Impact
- **Database**: Thêm 2 bảng SQLite mới.
- **CLI**: Mở rộng các subcommands dòng lệnh của `workflow_runtime.py`.
- **Webview**: Thêm tab Budget và các thẻ giao diện điều khiển.

## Dependencies
- Dữ liệu lịch sử request từ `provider_requests`.

## Risks
- **Risk**: Chặn nhầm request cần thiết do cài đặt Emergency Protection quá thấp.
  - **Mitigation**: Để ngưỡng Emergency Protection mặc định ở mức cao (95% hoặc 1.9M tokens) và cho phép cấu hình ghi đè.

## Acceptance Criteria
- [ ] Chặn request thành công khi vượt quá ngưỡng bảo vệ Emergency Protection.
- [ ] Đề xuất đúng chiến lược tối ưu phù hợp với từng ngưỡng chính sách ngân sách.
- [ ] Tab Giao diện hiển thị trực quan cấu hình Auto/Manual và lịch sử tiết kiệm.

## Deliverables
- Module `budget_controller.py`.
- Bổ sung SQLite schema di trú trong `db.py`.
- Tích hợp CLI trong `workflow_runtime.py`.
- Bổ sung Tab Budget trong `webview.html` & `extension.ts`.

## Estimated Complexity
- **Medium-High**: Yêu cầu logic sắp xếp và ưu tiên các chiến lược tối ưu hóa an toàn.
