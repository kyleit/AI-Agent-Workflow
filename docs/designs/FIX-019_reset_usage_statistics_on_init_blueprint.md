---
artifact_type: blueprint
issue_id: FIX-019
workflow: quick-fix
status: draft
---
# Technical Design Blueprint – Reset Usage Statistics on Init

## 1. Proposed Code Changes

### [.agents/skills/workflow-runtime/scripts/db.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/db.py)
- **Operation**: MODIFY
- **Responsibility**: Cho phép ghi nhận số liệu thống kê mã thông báo (token usage) mới vào cơ sở dữ liệu khi lệnh thực thi là `init`, ngay cả khi số lượng mã thông báo ước tính mới nhỏ hơn hoặc bằng số lượng hiện tại đã lưu.
- **Changes**: 
  - Sửa đổi hàm `save_usage_to_dbs(conversation_id, project_id, skill, command, usage)`:
    Thêm điều kiện kiểm tra biến `command` phải khác `"init"` trước khi chặn ghi đè thống kê nhỏ hơn.
    ```python
    if command != "init" and new_total <= existing_total and existing_total > 0:
        # Keep existing record if new estimate is smaller or equal
        return
    ```

## 2. Target Folder Structure
Cấu trúc thư mục không thay đổi:
```text
.agents/
└── skills/
    └── workflow-runtime/
        └── scripts/
            └── db.py
```

## 3. Interface & Data Contracts
Không có sự thay đổi về giao diện hay định dạng payload.

## 4. Algorithms & Key Logic
Trong hàm `save_usage_to_dbs`:
1. Kiểm tra nếu `command` khác `"init"`, đồng thời `new_total <= existing_total` và `existing_total > 0`, thì trả về mà không ghi đè dữ liệu cũ.
2. Nếu `command` bằng `"init"`, bỏ qua bước trả về sớm và tiến hành thay thế bản ghi cũ trong cả `PROJECT_DB` và `global_runtime.db` với số liệu thống kê mới từ transcript hiện tại.

## 5. Validation Rules
- Dữ liệu `command` là chuỗi văn bản.
- Hoạt động cập nhật cơ sở dữ liệu SQLite thông qua `INSERT OR REPLACE` vẫn giữ nguyên.

## 6. Implementation Checklist
- [ ] Chỉnh sửa tệp `.agents/skills/workflow-runtime/scripts/db.py`.

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Chạy lại lệnh khởi tạo `init` trong khi cơ sở dữ liệu có sẵn giá trị thống kê lớn hơn. Xác minh số liệu trong cơ sở dữ liệu được cập nhật về giá trị thực tế của transcript hiện tại.
