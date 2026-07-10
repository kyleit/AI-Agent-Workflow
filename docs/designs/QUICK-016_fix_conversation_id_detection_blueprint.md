<!-- File path: docs/designs/QUICK-016_fix_conversation_id_detection_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-016
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – Fix Conversation ID Detection and Context Usage Reset

## 1. Proposed Code Changes

### `skills/workflow-runtime/scripts/context.py`
- **Operation**: MODIFY
- **Responsibility**: Khai báo và xuất các hàm:
  - `detect_active_conversation_id() -> str`: Phát hiện conversation ID hiện tại từ biến môi trường `ANTIGRAVITY_SOURCE_METADATA`.
  - `sync_conversation_id(session: dict) -> bool`: So sánh conversation ID trong session với conversation ID hoạt động hiện tại. Nếu khác nhau, cập nhật và thêm log.
  - `refresh_context_usage_for_active_conversation(session: dict) -> dict`: Đồng bộ conversation ID, tính toán lại context usage và cập nhật `session["context_usage"]`.
- **Changes**:
  - Cập nhật `estimate_context_usage(conversation_id: str = None)` để nhận `conversation_id` cụ thể, tránh tải session từ đĩa làm ghi đè giá trị cũ.
  - Cập nhật hàm `estimate_context_usage` để xử lý Case C (thiếu transcript), trả về kết quả rỗng (tính toán token = 0) và tránh gây lỗi crash.

### `skills/workflow-runtime/scripts/workflow_runtime.py`
- **Operation**: MODIFY
- **Responsibility**: Cập nhật hàm `update_context_health(session)` để gọi `refresh_context_usage_for_active_conversation(session)` trước khi tính toán các chỉ số khác.
- **Changes**: Sửa logic gán và tính toán context usage thông qua hàm tập trung mới.

### `skills/workflow-runtime/scripts/workflow_state.py`
- **Operation**: MODIFY
- **Responsibility**: Cập nhật hàm `resume_session()` để đồng bộ conversation ID và làm mới context usage khi người dùng tiếp tục session trong một cửa sổ chat mới.
- **Changes**: Import `refresh_context_usage_for_active_conversation` từ `context` và gọi nó trước khi gọi `save_session_atomic`.

### `skills/workflow-runtime/tests/test_conversation_id_detection.py`
- **Operation**: NEW
- **Responsibility**: Bổ sung bộ unit test tự động bao quát cả 4 kịch bản Case A, B, C, D.

### `skills/initialize-workflow/SKILL.md`
- **Operation**: MODIFY
- **Responsibility**: Cập nhật hướng dẫn về việc tự động kiểm tra và đồng bộ conversation ID khi bắt đầu khởi tạo.

### `skills/resume-workflow/SKILL.md`
- **Operation**: MODIFY
- **Responsibility**: Cập nhật hướng dẫn về việc tự động kiểm tra và đồng bộ conversation ID khi tiếp tục.

### `skills/workflow-runtime/SKILL.md`
- **Operation**: MODIFY
- **Responsibility**: Cập nhật thông tin tài liệu.

## 2. Target Folder Structure
```text
.
├── .agents
│   ├── state
│   │   ├── context.json
│   │   └── workflow.json
│   └── skills
│       ├── initialize-workflow
│       │   └── SKILL.md
│       ├── resume-workflow
│       │   └── SKILL.md
│       └── workflow-runtime
│           ├── SKILL.md
│           └── scripts
│               ├── context.py
│               ├── workflow_runtime.py
│               └── workflow_state.py
```

## 3. Interface & Data Contracts
- `detect_active_conversation_id() -> str`
- `sync_conversation_id(session: dict) -> bool`
- `refresh_context_usage_for_active_conversation(session: dict) -> dict`
- Cấu trúc `session["context_usage"]` không thay đổi để duy trì khả năng tương thích ngược của Visualizer Sidebar:
  ```json
  "context_usage": {
    "total_tokens": 12345,
    "limit_tokens": 2000000,
    "percentage": 0.62
  }
  ```

## 4. Algorithms & Key Logic
### Đồng bộ Conversation ID hoạt động
```python
def detect_active_conversation_id() -> str:
    metadata_str = os.environ.get("ANTIGRAVITY_SOURCE_METADATA")
    if metadata_str:
        try:
            metadata = json.loads(metadata_str)
            if isinstance(metadata, dict):
                tool_data = metadata.get("tool")
                if isinstance(tool_data, dict):
                    env_conv_id = tool_data.get("conversationId")
                    if isinstance(env_conv_id, str) and env_conv_id:
                        return env_conv_id
        except Exception:
            pass
    return ""
```

## 5. Validation Rules
- Không cho phép cập nhật `conversation_id` thành chuỗi rỗng nếu `detect_active_conversation_id()` không tìm thấy giá trị hợp lệ (bảo toàn ID cũ).
- Nếu tệp transcript của cuộc hội thoại mới chưa được tạo (Case C), context usage sẽ trả về giá trị mặc định là 0 và ghi lại một dòng cảnh báo vào nhật ký session.

## 6. Implementation Checklist
- [ ] Triển khai các hàm trong `context.py`.
- [ ] Tích hợp `refresh_context_usage_for_active_conversation` vào `workflow_runtime.py`.
- [ ] Tích hợp vào `workflow_state.py` để xử lý sự kiện `resume`.
- [ ] Sửa đổi tài liệu hướng dẫn Skill trong các tệp SKILL.md.
- [ ] Tạo tệp kiểm thử `test_conversation_id_detection.py` và chạy xác thực.

## 7. Verification & Test Plan
### Acceptance Assertions
- **Case A**: So sánh cùng một ID hội thoại, kết quả không thay đổi, dữ liệu context usage được giữ nguyên.
- **Case B**: Khác ID hội thoại, cập nhật ID hội thoại, tính toán lại context usage và ghi nhận log chuyển đổi.
- **Case C**: Hội thoại mới chưa có transcript, không crash, cảnh báo ghi nhận trong logs, token tính toán = 0.
- **Case D**: Session mới hoàn toàn/rỗng, khởi tạo thành công với ID mới.
