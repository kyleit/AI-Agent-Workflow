<!-- File path: docs/plans/FEAT-025_project_workflow_templates_plan.md -->

---
feature_id: FEAT-025
feature_name: Project-specific Workflow Templates & Release Configuration
status: reviewed
stage: planning
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../brainstorming/FEAT-025_project_workflow_templates.md
next_artifact: ../designs/FEAT-025_project_workflow_templates_blueprint.md
---

# FEAT-025: Project-specific Workflow Templates & Release Configuration

## Objective
- Cung cấp cơ chế cho phép người dùng định nghĩa và tự động hóa quy trình Git Flow (checkout, merge, rebase) và pipeline phát hành (release commands) tùy biến riêng biệt cho từng dự án.
- Giúp AI Agent tự động thích ứng với cấu trúc nhánh Git và cách đóng gói/phát hành cụ thể của mọi dự án thực tế mà không cần sửa đổi mã nguồn khung lõi (core framework).

## Scope
### Included
- Tạo tệp cấu hình mới `.agents/workflow.config.json` để khai báo nhánh phát triển (`development_branch`), nhánh phát hành (`release_branch`), cấu trúc tiền tố nhánh tính năng (`feature_prefix`), và các lệnh phát hành tùy biến (`custom_release_commands`).
- Cập nhật CLI `workflow_runtime.py` để đọc và phân tích cấu hình quy trình tùy chỉnh này.
- Cập nhật logic checkout/init/resume của các Skills để tự động điều phối Git Flow dựa trên cấu hình dự án.
- Cập nhật `release_manager.py` để chạy tuần tự các lệnh release tùy chỉnh được cấu hình trước thay vì chạy mock.
- Đảm bảo tương thích ngược: Fallback về quy trình mặc định (`main`/`master` và mock release) nếu tệp cấu hình không tồn tại.

### Excluded
- Tự động giải quyết các xung đột code (conflict merge/rebase). Nếu gặp conflict, Agent bắt buộc phải dừng và nhờ người dùng hỗ trợ.
- Tự động tạo hoặc sinh ra các câu lệnh Makefile/npm build nếu dự án chưa thiết lập sẵn.

## Project Impact
- **Modules**: `workflow-runtime` (CLI scripts) và `release_manager` (trực tiếp chịu ảnh hưởng).
- **Git Flow**: Thay đổi linh hoạt các nhánh gốc và đích khi checkout và release.
- **Config**: Tạo thêm cấu hình mới `.agents/workflow.config.json`.

## Dependencies
- Phụ thuộc vào các lệnh Git tiêu chuẩn trên môi trường hệ thống.
- Yêu cầu cấu hình Choice Protocol để người dùng phê duyệt trước khi chạy các lệnh shell custom.

## Risks
- **Xung đột Code (Git Conflict)**: Việc tự động merge/rebase giữa các nhánh `dev` và `master` có thể phát sinh conflict.
  - *Mitigation*: CLI kiểm tra trạng thái lệnh Git sau khi chạy, dừng lại lập tức nếu phát hiện lỗi hoặc conflict, đảm bảo không làm mất mát code chưa commit (sử dụng stash).
- **Rủi ro Bảo mật (Command Injection)**: Người dùng có thể vô tình hoặc cố ý cài cắm lệnh nguy hại trong file cấu hình JSON.
  - *Mitigation*: Luôn bắt buộc hiển thị rõ nội dung lệnh tùy biến và yêu cầu phê duyệt thông qua Approval Gate trước khi thực thi.

## Acceptance Criteria
- [ ] Agent nạp và hiển thị cấu hình Git Flow tùy chỉnh của dự án thành công khi chạy khởi động.
- [ ] Khi bắt đầu một tính năng mới, Agent tự động checkout nhánh từ nhánh phát triển tùy chỉnh (`dev`/`develop`) thay vì mặc định `main`.
- [ ] Khi chạy `/release`, Agent thực thi rebase/merge và chạy các lệnh shell custom (như `make publish-github`) theo đúng cấu hình tuần tự đã khai báo trong JSON.
- [ ] Các tác vụ release custom luôn hiển thị cảnh báo phê duyệt và chỉ chạy khi được đồng ý.
- [ ] Hệ thống tương thích ngược hoàn hảo với các dự án cũ không có tệp cấu hình tùy chỉnh.

## Deliverables
- Tệp đặc tả cấu hình mẫu `.agents/templates/workflow.config.json.template`.
- Cập nhật kịch bản Python CLI `session.py`, `workflow_runtime.py` và `release_manager.py`.
- Tệp đặc tả thiết kế kỹ thuật `docs/designs/FEAT-025_project_workflow_templates_blueprint.md`.

## Estimated Complexity
- **Medium**: Cần sửa đổi luồng Git cốt lõi trong CLI và lớp quản lý phiên (`session`) để đảm bảo không làm gãy các quy trình SDLC tiêu chuẩn, đồng thời bảo mật tuyệt đối cho việc chạy shell command tùy biến.

## Recommended Blueprint Focus
- Thiết kế chính xác lược đồ (schema) của tệp cấu hình `workflow.config.json`.
- Thiết kế luồng xử lý ngoại lệ Git (Stash -> Rebase -> Abort/Resolve) khi gặp xung đột.
- Thiết kế giao thức bảo mật duyệt lệnh CLI tùy chỉnh.

## Recommended Next Skill
/blueprint
