---
artifact_type: fix-spec
issue_id: FIX-020
workflow: quick-fix
status: pending
---
# Fix Specification – Fix Visualizer Watcher for Dot Folders

## 1. Issue Description
Khi chạy workflow hoặc thay đổi các checkpoint, giao diện Visualizer Dashboard không tự động cập nhật để hiển thị tiến độ và số liệu thống kê mới. Nguyên nhân là do VS Code FileSystemWatcher mặc định bỏ qua các thư mục bắt đầu bằng dấu chấm (`.agents`). Điều này làm cho các sự kiện thay đổi trạng thái trong `.agents/state/*.json`, `.agents/project-profile.json` và `.agents/runtime/pending-choice*.json` không kích hoạt cập nhật giao diện, đồng thời giữ nguyên ID cuộc hội thoại và dữ liệu cũ trong bộ nhớ của Extension.

## 2. Scope
- **In Scope**:
  - Sửa đổi tệp `extensions/visualizer/src/extension.ts` để thay thế `vscode.workspace.createFileSystemWatcher` bằng `fs.watch` của Node.js đối với các thư mục nằm trong `.agents/`.
  - Đảm bảo các watcher được giải phóng (dispose) đúng cách khi extension bị deactivate.
- **Out of Scope**:
  - Không thay đổi bất kỳ code logic nào của Webview hiển thị (`webview.html`).
  - Không thay đổi cấu trúc hoặc logic lưu trữ trạng thái của Python CLI.
