<!-- File path: docs/quick/QUICK-029_granular_state_backup_and_lock_protection.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-029
workflow: quick-feature
status: pending
---
# Mini Plan & Feature Specification – Granular State Backup-Restore & Lock-Protected Writes

## 1. Feature Goal
Khắc phục hiện tượng xung đột và đè dữ liệu trạng thái giữa các tiến trình chạy song song (CLI và Visualizer Extension) bằng hai cơ chế:
1.  **Ghi rã và khôi phục thông minh (Granular Write/Backup/Restore)**: Chỉ tiến hành ghi đè/sao lưu các tệp trạng thái phân rã (`context.json`, `workflow.json`, v.v.) thực sự có thay đổi dữ liệu, thay vì ghi đè toàn bộ thư mục gây mất mát dữ liệu của các file khác.
2.  **Khóa đồng bộ (File Lock Protection)**: Tích hợp cơ chế khóa vật lý `state.lock` để đảm bảo tại một thời điểm chỉ có một tiến trình được quyền ghi/sửa đổi thư mục trạng thái `.agents/state/`.

---

## 2. Quick Feature Justification
*   **Estimated Complexity**: Thấp (chỉ chỉnh sửa logic đọc/ghi tệp tin trong module `state_sync.py` và `session.py`).
*   **Implementation Scope**: Giới hạn trong các hàm `deconstruct_state`, `aggregate_state` và các thao tác ghi của runtime.
*   **Architectural Impact**: Không ảnh hưởng đến các interface bên ngoài, tương thích ngược hoàn toàn.
*   **Risk Level**: Thấp.

---

## 3. Scope Boundary
*   **In Scope**:
    *   Tích hợp context manager `StateLock` sử dụng tệp tin khóa `.agents/state/state.lock` với cơ chế retry (thử lại tối đa 5 giây) để bảo vệ các thao tác đọc/ghi trong `deconstruct_state` và `aggregate_state`.
    *   Cải tiến `deconstruct_state` để so sánh dữ liệu mới với dữ liệu hiện tại trên đĩa. Chỉ ghi đè lên các tệp JSON thực sự có nội dung thay đổi.
    *   Cập nhật cơ chế `snapshot` để cho phép sao lưu/khôi phục chính xác các tệp thay đổi thay vì copy mù quáng.
*   **Out of Scope**:
    *   Thay đổi định dạng lưu trữ SQLite hoặc tri thức Obsidian.
    *   Thay đổi logic nghiệp vụ của các Skill khác.

---

## 4. Proposed Changes

### Component: Runtime State Management

#### [MODIFY] [state_sync.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/state_sync.py)
*   Thêm lớp `StateLock` quản lý khóa tệp tin `state.lock` dạng an toàn (blocking/non-blocking với timeout).
*   Sửa đổi hàm `deconstruct_state` để:
    1.  Lấy khóa `StateLock` trước khi thực hiện ghi rã.
    2.  Đọc nội dung các file hiện có trên đĩa lên để so sánh. Chỉ ghi đè các file có nội dung dữ liệu khác biệt so với session mới.
*   Sửa đổi hàm `aggregate_state` để lấy khóa `StateLock` khi đọc tổng hợp dữ liệu, tránh đọc đúng lúc tiến trình khác đang ghi dở dang.

#### [MODIFY] [session.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/session.py)
*   Sửa đổi hàm `save_session_atomic` để sử dụng khóa bảo vệ khi gọi ghi rã trạng thái.

---

## 5. Verification Plan

### Automated Tests
*   Viết unit test giả lập 2 tiến trình đồng thời ghi đè trạng thái (stress test với luồng song song) để xác minh cơ chế `StateLock` hoạt động chính xác và không gây deadlock hay corrupted file.
*   Chạy bộ test kiểm tra: `pytest skills/workflow-runtime/tests/test_state_aggregator.py` và các test liên quan để đảm bảo không có regressions.

### Manual Verification
*   Mở Visualizer Extension song song với việc chạy CLI `aiwf step` liên tục để kiểm tra xem có còn hiện tượng xung đột ghi đè hoặc mất dữ liệu tệp tin trạng thái hay không.
