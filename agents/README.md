# AIWF Dynamic Agent Registry

Thư mục này chứa định nghĩa Agent động cho hệ thống **Resident Orchestrator** của AIWF.

## Cấu trúc thư mục

```text
agents/
├── agent.schema.json   # JSON Schema định nghĩa các trường metadata hợp lệ
├── registry.json       # Cơ sở dữ liệu tổng hợp của Agent Registry (tự động biên dịch)
├── README.md           # Tài liệu hướng dẫn này
├── validate_registry.py# Script xác thực và biên dịch tự động
└── [agent-name].md     # Tệp định nghĩa markdown cho từng Agent
```

## Các trường Metadata bắt buộc cho Agent
Mỗi file markdown định nghĩa agent phải bắt đầu bằng YAML frontmatter bao gồm các trường bắt buộc sau:
- `id`: Định danh duy nhất (ví dụ: `frontend-developer`).
- `name`: Tên canonical (trùng với `id`).
- `display_name`: Tên hiển thị thân thiện.
- `version`: Phiên bản định nghĩa.
- `capabilities`: Danh sách các capability được đăng ký (ví dụ: `["frontend"]`).
- `permissions.mode`: Chế độ ghi (`read-only`, `scoped-write`, `isolated-write`, `authoritative-write`).
- `write_mode`: Kiểu ghi (`none`, `single-writer`, `isolated-writer`, `integration-owner`).
- `allowed_reads` & `allowed_writes`: Các thư mục được phép đọc/ghi tương ứng.
- `handoff_targets`: Định tuyến handoff tiếp theo (ví dụ: `["qa-reviewer"]` hoặc `["done"]`).

## Cách thêm mới hoặc sửa đổi Agent
1. Tạo hoặc chỉnh sửa tệp tin markdown tương ứng tại thư mục `agents/` (ví dụ: `agents/my-custom-agent.md`).
2. Định nghĩa frontmatter của agent tuân thủ nghiêm ngặt JSON Schema.
3. Chạy script để tự động xác thực và cập nhật registry:
   ```bash
   python agents/validate_registry.py
   ```
4. Kiểm tra xem file `agents/registry.json` và thư mục tương thích ngược `.agents/agents/` đã được cập nhật thành công hay chưa.
