<!-- File path: docs/issues/FIX-010_fix_session_loss_atomic_writes.md -->

---
artifact_type: issue-spec
feature_id: FIX-010
workflow: quick-fix
architecture_impact: medium
adr_required: false
status: pending
---

# Issue Specification – Session Data Loss on High-Frequency Writes

## 1. Problem Statement
Trong các chu trình đọc ghi nhanh liên tục (High-Frequency Read/Write), tệp cấu hình session `.session.json` có thể bị lỗi, trống (corrupted / size 0) dẫn đến mất mát dữ liệu hoặc làm sập luồng phát triển.

## 2. Root Cause Analysis
1. **Lỗi Ghi Dang Dở**: Mặc dù hệ thống đã có Atomic Write nhưng nếu tiến trình bị kill giữa chừng trong lúc thay thế, tệp có thể bị mất.
2. **Không có file dự phòng (Backup)**: Khi file chính bị lỗi đọc JSON (JSONDecodeError), hệ thống chỉ trả về `{}` dẫn đến ghi đè dữ liệu mới làm mất sạch dữ liệu cũ.

## 3. Proposed Fix
1. **Thêm cơ chế file dự phòng (`.session.json.bak`)**: Trước mỗi lần ghi đè, hệ thống tự động backup file chính sang `.bak`.
2. **Cơ chế Tự Phục Hồi (Self-Healing)**: Khi hàm `load_session()` phát hiện file chính tồn tại nhưng bị lỗi (JSONDecodeError/IOError/trống), hệ thống tự động phục hồi dữ liệu từ file backup `.bak`.
3. **Giữ nguyên khả năng ghi đè độc lập**: Để tương thích hoàn toàn với toàn bộ unit tests, `save_session_atomic` sẽ ghi đè toàn bộ (không tự động merge ngầm) nhưng luôn tạo bản sao backup và khôi phục khi lỗi.
4. **CLI Subcommand `permission`**: Thêm lệnh `python3 workflow_runtime.py permission` để người dùng/nhà phát triển thật có thể dễ dàng in ra bảng kiểm tra xem hành động nào được cho phép (ALLOWED/Bypass) và hành động nào bị chặn phê duyệt (REQUIRED_APPROVAL/Hard-gated) đối với chế độ phân quyền hiện tại của session.

## 4. Expected Files

| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | [skills/workflow-runtime/scripts/session.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/session.py) | Tích hợp cơ chế Backup và Self-healing cho session |
| Modify | [skills/workflow-runtime/scripts/workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) | Thêm subcommand `permission` hiển thị bảng kiểm tra quyền |
| Modify | [skills/workflow-runtime/tests/test_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/tests/test_runtime.py) | Cập nhật dọn dẹp thêm file backup trong setUp/tearDown |
