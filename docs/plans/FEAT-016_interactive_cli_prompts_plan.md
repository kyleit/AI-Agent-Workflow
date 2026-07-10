<!-- File path: docs/plans/FEAT-016_interactive_cli_prompts_plan.md -->

---
feature_id: FEAT-016
feature_name: Interactive CLI Prompts via IDE UI
status: reviewed
stage: planning
created_at: 2026-07-07
updated_at: 2026-07-07
previous_artifact: ../brainstorming/FEAT-016_interactive_cli_prompts.md
next_artifact: ../designs/FEAT-016_interactive_cli_prompts_blueprint.md
---

# FEAT-016: Interactive CLI Prompts via IDE UI

## Objective
- **Mục tiêu**: Nâng cấp toàn bộ trải nghiệm tương tác giữa Ba và quy trình AI bằng cách thay thế việc gõ văn bản/số thủ công tại các trạm kiểm duyệt thành việc click chọn trực quan qua giao diện hộp thoại (`ask_question` modal UI) của IDE.
- **Kết quả mong đợi**: Tự động hóa việc chọn nhánh Git, chọn Skill, phê duyệt hành động (Y/N) và tích hợp cơ chế cầu nối tương tác (Interactive Prompts Bridge) cho Python CLI mà không làm thay đổi tính năng nền tảng.

## Scope
### Included
- **Cập nhật chính sách trung tâm**: Sửa đổi cổng phê duyệt (Approval Gate) và cổng phân loại Skill (Skill Suggestion Gate) trong `AI_RULES.md` để buộc Agent dùng `ask_question`.
- **Cập nhật thư viện Skill**: Tích hợp hướng dẫn gọi công cụ `ask_question` cho các bước tương tác trung gian (chọn nhánh Git, chạy kiểm thử).
- **Xây dựng cầu nối tương tác CLI**: CLI in ra định dạng XML/JSON có cấu trúc đặc biệt để báo hiệu Agent mở giao diện UI.
- **Đồng bộ phản hồi ngược**: Agent bắt kết quả Ba chọn và gửi vào luồng đầu vào tiêu chuẩn (`stdin`) để CLI tiếp tục chạy.
- **Cơ chế dự phòng (Fallback)**: Tự động phát hiện nếu IDE/Client không hỗ trợ `ask_question` để chuyển sang chế độ hỏi bằng văn bản truyền thống.

### Excluded
- Giao diện chọn nhiều phương án cùng lúc (Multi-select / Checkbox).
- Thay đổi cấu trúc Webview Sidebar của Visualizer Extension.

## Project Impact
- **Modules**: `workflow-runtime`, `initialize-workflow`, `software-development-workflow`, và tài liệu hướng dẫn Skill.
- **Config & Policies**: Sửa đổi trực tiếp chính sách toàn cục `AI_RULES.md`.

## Dependencies
- Phối hợp chặt chẽ giữa CLI Python (`workflow_runtime.py`) và cơ chế lắng nghe đầu ra (stdout listener) của Agent.

## Risks
- **Nghẽn tiến trình (Stdin Deadlock)**: Nếu CLI đang block chờ stdin nhưng Agent gặp lỗi không thể ghi kết quả -> *Mitigation*: Thiết lập cơ chế timeout hoặc fallback tự động sau một khoảng thời gian chờ không có tương tác.
- **Không hỗ trợ công cụ**: Chạy trên CLI thuần/IDE cũ không hỗ trợ `ask_question` -> *Mitigation*: Tự động phát hiện lỗi và chuyển đổi sang text input truyền thống.

## Acceptance Criteria
- Cổng phê duyệt (Y/N) của tất cả các Skill được hiển thị dưới dạng Modal lựa chọn trực quan.
- Bước chọn nhánh Git liệt kê đầy đủ danh sách nhánh và cho phép Ba click chọn.
- CLI Python có thể kích hoạt thành công hộp thoại chọn trên IDE và nhận lại kết quả qua stdin.
- Quy trình tự động fallback mượt mà về dạng hỏi đáp text cũ nếu chạy trên môi trường không hỗ trợ.

## Deliverables
- Kế hoạch triển khai `docs/plans/FEAT-016_interactive_cli_prompts_plan.md`.
- Bản vẽ thiết kế kỹ thuật `docs/designs/FEAT-016_interactive_cli_prompts_blueprint.md`.

## Estimated Complexity
- **Medium**: Đòi hỏi sửa đổi đồng bộ cả tệp chính sách `AI_RULES.md`, kịch bản Python CLI và luồng đọc ghi stdin/stdout của Agent.

## Recommended Blueprint Focus
- **Thiết kế**: Tập trung chi tiết vào cấu trúc định dạng thẻ XML/JSON của CLI, cơ chế kiểm tra tính khả dụng của công cụ (Tool Availability Detection) trên Agent, và kịch bản bắt lỗi/phục hồi khi stdin bị nghẽn.

## Recommended Next Skill
/blueprint
