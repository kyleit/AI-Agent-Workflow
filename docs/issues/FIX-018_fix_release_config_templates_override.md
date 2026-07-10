<!-- File path: docs/issues/FIX-018_fix_release_config_templates_override.md -->
---
artifact_type: fix-spec
issue_id: FIX-018
workflow: quick-fix
status: pending
---
# Fix Specification – Fix Release Config Templates Hardcoding

## 1. Issue Description
Tệp tin cấu hình mẫu `templates/release.config.json` và `.agents/templates/release.config.json` hiện tại đang bị fix cứng các mô-đun riêng biệt của dự án `ai-workflow-skills` (gồm `framework-core` và `visualizer-extension`). 
Khi người dùng chạy cài đặt/cập nhật (`install.sh`/`update.sh`) trên một dự án khác (như `acoms`), hệ thống copy nguyên bản tệp mẫu này sang dự án đích, khiến quy trình release của dự án đó bị lỗi vì cố gắng quét các mô-đun không tồn tại.

## 2. Scope
- **In Scope**: 
  - Khai báo lại nội dung của `templates/release.config.json` và `.agents/templates/release.config.json` thành dạng cấu hình dự án đơn lẻ chuẩn hóa và tổng quát (`single` project type).
  - Tự động fallback về cấu hình tổng quát này thay vì cấu hình hardcode cụ thể.
- **Out of Scope**: 
  - Thay đổi logic phát hiện ngôn ngữ tự động trong code của `project_discovery.py`.
