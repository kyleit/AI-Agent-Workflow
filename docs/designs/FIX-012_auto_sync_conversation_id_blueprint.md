<!-- File path: docs/designs/FIX-012_auto_sync_conversation_id_blueprint.md -->
---
artifact_type: blueprint
issue_id: FIX-012
workflow: quick-fix
status: draft
---
# Technical Design Blueprint – Auto-Sync Conversation ID on Rollover

## 1. Proposed Code Changes

### [MODIFY] [workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py)
Thực hiện bổ sung logic tự động lấy `conversationId` từ biến môi trường `ANTIGRAVITY_SOURCE_METADATA` khi bắt đầu hàm `update_context_health`. Việc parse JSON được làm an toàn, sử dụng `cast` từ `typing` và các phép kiểm tra `isinstance` để đảm bảo code sạch lints:

```python
from typing import cast, Any

def update_context_health(session: dict) -> None:
    # Auto-detect and sync current conversation_id from environment metadata
    metadata_str = os.environ.get("ANTIGRAVITY_SOURCE_METADATA")
    if metadata_str:
        try:
            metadata_raw = json.loads(metadata_str)
            if isinstance(metadata_raw, dict):
                metadata = cast(dict[str, object], metadata_raw)
                tool_data = metadata.get("tool")
                if isinstance(tool_data, dict):
                    tool_data_dict = cast(dict[str, object], tool_data)
                    env_conv_id = tool_data_dict.get("conversationId")
                    if isinstance(env_conv_id, str) and env_conv_id:
                        session["conversation_id"] = env_conv_id
        except Exception:
            pass

    if "suggestion_gate" not in session:
        # ... (giữ nguyên logic ban đầu)
```

## 2. Test Plan
- Thực hiện chạy lệnh `python skills/workflow-runtime/scripts/workflow_runtime.py usage sync` để kích hoạt hàm `update_context_health`.
- Kiểm tra file `.agents/.session.json` có tự động lưu đúng `conversation_id` hiện tại là `"d7e01795-e2ac-4e0a-945a-3e9c534b1d54"` không.
- Kiểm tra lượng token usage ước lượng (percentage) sau khi chạy sync chuyển về đúng dung lượng thực tế của hội thoại mới (~2.06%).
