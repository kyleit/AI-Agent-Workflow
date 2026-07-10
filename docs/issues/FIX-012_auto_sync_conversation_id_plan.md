# Plan - Auto-Sync Conversation ID on Workflow Actions

## Goal Description
Sửa lỗi dung lượng context không tự động cập nhật (hoặc hiển thị sai 85% do fallback) khi người dùng đổi sang cuộc hội thoại mới.
Hệ thống sẽ tự động trích xuất `Conversation ID` hiện tại từ biến môi trường `ANTIGRAVITY_SOURCE_METADATA` và cập nhật trực tiếp vào `.agents/.session.json` bất cứ khi nào bất kỳ thao tác nào của `workflow_runtime.py` được thực thi.

## Proposed Changes

### Centralized CLI Runtime

#### [MODIFY] [workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py)
Tự động lấy `conversationId` từ biến môi trường `ANTIGRAVITY_SOURCE_METADATA` và ghi đè vào `session["conversation_id"]` ngay tại đầu hàm `update_context_health`. Điều này đảm bảo tất cả các lệnh của runtime (như `init`, `start`, `step`, `complete`, `heartbeat`) đều tự động cập nhật chính xác Conversation ID của thread mới nhất, tránh tình trạng tính toán fallback ra 85% của thread cũ.

```python
def update_context_health(session: dict) -> None:
    # Auto-detect and sync current conversation_id from environment metadata
    metadata_str = os.environ.get("ANTIGRAVITY_SOURCE_METADATA")
    if metadata_str:
        try:
            import json
            metadata = json.loads(metadata_str)
            env_conv_id = metadata.get("tool", {}).get("conversationId")
            if env_conv_id:
                session["conversation_id"] = env_conv_id
        except Exception:
            pass
```

## Verification Plan

### Manual Verification
1. Chạy lệnh `python skills/workflow-runtime/scripts/workflow_runtime.py usage sync`.
2. Kiểm tra xem file `.agents/.session.json` có tự động đồng bộ đúng `conversation_id` hiện tại là `d7e01795-e2ac-4e0a-945a-3e9c534b1d54` hay không.
3. Kiểm tra xem lượng token usage hiển thị trên Dashboard Visualizer có tự động chuyển về đúng tỷ lệ thực tế (~2.06%) mà không cần phải can thiệp thủ công hay không.
