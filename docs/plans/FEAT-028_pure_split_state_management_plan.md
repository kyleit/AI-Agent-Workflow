<!-- File path: docs/plans/FEAT-028_pure_split_state_management_plan.md -->

---
feature_id: FEAT-028
feature_name: Pure Split State Management
status: reviewed
stage: planning
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../brainstorming/FEAT-028_pure_split_state_management.md
next_artifact: ../designs/FEAT-028_pure_split_state_management_blueprint.md
---

# FEAT-028: Pure Split State Management

## Objective
- Loại bỏ hoàn toàn tệp tin trạng thái cồng kềnh `.agents/.session.json` trên đĩa và chuyển hoàn toàn sang sử dụng cơ chế lưu trữ phân tách (Pure Split State) trong thư mục `.agents/state/`.
- Định nghĩa thành công quy trình ghi và đọc trực tiếp các tệp nhỏ (`context.json`, `workflow.json`, `runtime.json`, `approvals.json`, `usage.json`, `agents.json`) cho cả AI Skills (Python) và Visualizer Extension (Typescript).
- Tăng hiệu năng hệ thống, giảm thiểu I/O đĩa thừa và ngăn chặn hoàn toàn lỗi tranh chấp ghi khóa tệp lớn.

## Scope
### Included
- Refactor tệp cấu hình Python CLI (`state_sync.py`, `session.py`) để loại bỏ logic ghi tệp `.session.json`.
- Refactor các CLI commands liên quan đến `init`, `start`, `step`, `complete`, `fail`, `blueprint`, `validate` để đảm bảo chúng làm việc trực tiếp trên thư mục `state/` và loại bỏ các thao tác thừa với `.session.json`.
- Cập nhật Visualizer Extension để chuyển cơ chế lắng nghe sự thay đổi tệp tin (file watcher) từ `.session.json` sang toàn bộ thư mục `.agents/state/`.
- Kiểm thử tích hợp toàn bộ quy trình để đảm bảo giao diện hiển thị chính xác mọi thông số mà không cần sự tồn tại của `.session.json`.

### Excluded
- Không thay đổi cấu trúc dữ liệu hoặc định nghĩa của các thuộc tính con bên trong các tệp nhỏ.
- Không thay đổi các tính năng nghiệp vụ của Visualizer Dashboard ngoài phần đọc và theo dõi tệp.
- Không thay đổi cơ chế cơ sở dữ liệu `project_runtime.db`.

## Project Impact
- **Modules & Services**:
  - `workflow-runtime` (Python helper scripts): Sửa đổi logic nạp và lưu trữ.
  - `aiwf` CLI: Đồng bộ hóa quá trình tương tác trạng thái.
- **Visualizer Extension**: Thay đổi file watcher và cơ chế nạp cấu hình ban đầu.
- **Workspace/Disk**: Xóa bỏ vĩnh viễn tệp `.agents/.session.json`.

## Dependencies
- Dự án phải đang chạy ở chế độ cấu hình trạng thái phân tách (state directory `.agents/state` khả dụng).
- Node.js và các công cụ biên dịch TypeScript hoạt động bình thường để đóng gói lại Visualizer Extension.

## Risks
- **Risk**: Một số tập lệnh dòng lệnh (PowerShell/Bash) cũ hoặc công cụ tích hợp ngoài có thể bị lỗi nếu chúng đang tìm kiếm trực tiếp tệp `.session.json`.
- **Mitigation**: Cung cấp lệnh CLI `aiwf state status` hoặc tài liệu hóa cách thức đọc trực tiếp từ thư mục `state/` cho lập trình viên.

## Acceptance Criteria
- [ ] Không còn tệp `.agents/.session.json` được tạo ra hoặc cập nhật trên đĩa trong toàn bộ vòng đời phát triển phần mềm (SDLC).
- [ ] Visualizer Dashboard hiển thị chính xác các thông tin (workspace, git branch, version, token usage, active checkpoint) khi thay đổi trạng thái và không gặp hiện tượng trễ hay không cập nhật.
- [ ] Tất cả 18+ bài test đơn vị của `test_runtime.py` đều vượt qua sau khi refactor.

## Deliverables
- Phiên bản cập nhật của các tệp Python quản lý trạng thái (`state_sync.py`, `session.py`, `workflow_runtime.py`).
- Phiên bản Visualizer Extension mới (`extension.ts` và `webviewHtml.ts` đã được build đồng bộ).
- Tài liệu hướng dẫn di trú hoặc lệnh thay thế cho tệp tin cũ.

## Estimated Complexity
- **Medium**: Cần refactor đồng thời cả mã nguồn Python (Skills) và TypeScript (Extension), đồng thời cần kiểm thử kỹ lưỡng để tránh mất mát trạng thái giữa chừng của quy trình.

## Recommended Blueprint Focus
- Tập trung thiết kế cơ chế theo dõi thư mục (directory file watcher) hiệu quả trong VS Code Extension đối với thư mục `state/` để tránh tải lại quá nhiều lần khi nhiều tệp nhỏ thay đổi liên tiếp (de-bouncing hoặc batch updates).
- Thiết kế cơ chế di trú tự động (migration fallback) trong `session.py` để xóa tệp `.session.json` cũ một cách an toàn khi chuyển đổi.

## Recommended Next Skill
/blueprint
