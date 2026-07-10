<!-- File path: docs/issues/FIX-013_add_docs_button_to_extension.md -->
---
artifact_type: fix-spec
issue_id: FIX-013
workflow: quick-fix
status: pending
---
# Fix Specification – Add Docs Button to Extension Webview

## 1. Issue Description
Người dùng muốn tích hợp một nút liên kết trực tiếp trên giao diện của VS Code Extension (Visualizer Sidebar) dẫn tới trang tài liệu tương tác vừa triển khai: `https://kyleit.github.io/AI-Agent-Workflow/`. Nút này cần được đặt cạnh nút GitHub ở thanh tiêu đề trên cùng để tăng tính tiện dụng.

## 2. Scope
- **In Scope**:
  - Sửa đổi tệp `extensions/visualizer/src/webviewHtml.ts` tại phần đầu đề `session-header` để bọc nút GitHub hiện tại và nút Docs mới trong một div flex xếp ngang.
  - Sử dụng biểu tượng SVG quyển sách mở và nhãn "Docs" trỏ tới `https://kyleit.github.io/AI-Agent-Workflow/`.
  
- **Out of Scope**:
  - Thay đổi cấu trúc điều hành lõi của Extension.
  - Thêm các lệnh command palette mới vào VS Code.
