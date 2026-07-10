<!-- File path: docs/issues/FIX-005_fix_fallback_token_estimation.md -->

---
artifact_type: fix
issue_id: FIX-005
workflow: quick-fix
architecture_impact: low
adr_required: false
status: PASS
---

# Fix Document – Fix Fallback Token Estimation on Fresh Workspaces

## 1. Issue
Một số thiết bị vẫn gặp hiện tượng phần trăm ngữ cảnh (Context) hiển thị `0%` và thống kê usage bị trống (N/A) ở lần đầu khởi chạy phiên làm việc hoặc khi chưa có tệp nhật ký trò chuyện.

## 2. Symptoms
- Giao diện Visualizer hiển thị `0% Context` và các thông số token/cost đều bằng `0` hoặc trống.
- Lỗi này xuất hiện trên các máy trạm mới thiết lập dự án mà chưa có tệp nhật ký `transcript.jsonl` hoặc chưa lưu trường `conversation_id` trong `.session.json`.

## 3. Root Cause
- Trong tệp [context.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/context.py#L123), nếu không tìm thấy `conversation_id` hoặc tệp nhật ký `transcript.jsonl`, hàm `estimate_context_usage` sẽ trả về toàn bộ giá trị mặc định bằng `0` (`input_tokens: 0`, `active_tokens: 0`, `percentage: 0.0`).
- Khi CLI của bộ chạy (`workflow_runtime.py`) ghi đè các giá trị bằng `0` này vào `.session.json`, nó sẽ vô hiệu hóa hoàn toàn cơ chế ước lượng dựa trên checkpoint (fallback) của Visualizer Extension, dẫn đến giao diện hiển thị trắng/0%.

## 4. Scope
- **In Scope**:
  - Cập nhật tệp `skills/workflow-runtime/scripts/context.py` để bổ sung hàm sinh ước lượng dự phòng (`get_fallback_usage`) dựa trên mức độ checkpoint hiện tại của session nếu thiếu `conversation_id` hoặc tệp nhật ký.
  - Cập nhật tệp cài đặt thực thi `.agents/skills/workflow-runtime/scripts/context.py`.
- **Out of Scope**: Không thay đổi cấu trúc bảng SQLite hay logic khác.

## 5. Expected Files
| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | [context.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/context.py) | Bổ sung fallback ước lượng dựa trên checkpoint |
| Modify | [context.py](file:///Volumes/Kyle/AgentsProject/.agents/skills/workflow-runtime/scripts/context.py) | Bổ sung fallback ước lượng dựa trên checkpoint |
| Modify | [db.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/db.py) | Ngăn chặn ghi đè dữ liệu cũ bằng ước lượng nhỏ hơn |
| Modify | [db.py](file:///Volumes/Kyle/AgentsProject/.agents/skills/workflow-runtime/scripts/db.py) | Ngăn chặn ghi đè dữ liệu cũ bằng ước lượng nhỏ hơn |

## 6. Proposed Changes

### [context.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/context.py)
(Bổ sung hàm `get_fallback_usage` và cập nhật `estimate_context_usage` như cũ)

### [db.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/db.py)
Cập nhật hàm `save_usage_to_dbs` để kiểm tra `total_tokens` hiện tại trong DB. Nếu giá trị mới nhỏ hơn hoặc bằng giá trị đã lưu, bỏ qua không ghi đè:
```python
def save_usage_to_dbs(conversation_id: str, project_id: str, skill: str, command: str, usage: dict) -> None:
    new_total = usage.get("total_tokens", 0)
    
    # Read existing total_tokens from Project DB if it exists
    existing_total = 0
    if os.path.exists(PROJECT_DB):
        conn = sqlite3.connect(PROJECT_DB)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usage_records'")
            if cursor.fetchone():
                cursor.execute("SELECT total_tokens FROM usage_records WHERE conversation_id = ?", (conversation_id,))
                row = cursor.fetchone()
                if row:
                    existing_total = row[0]
        except Exception:
            pass
        finally:
            conn.close()
            
    if new_total <= existing_total and existing_total > 0:
        # Keep existing record if new estimate is smaller or equal
        return

    record = (
        conversation_id,
        project_id,
        skill,
        command,
        usage.get("input_tokens", 0),
        usage.get("output_tokens", 0),
        usage.get("cache_tokens", 0),
        usage.get("thinking_tokens", 0),
        usage.get("active_tokens", 0),
        usage.get("total_tokens", 0),
        usage.get("estimated_cost_usd", 0.0),
        usage.get("provider", "unknown"),
        usage.get("model", "unknown"),
        usage.get("accuracy", "unknown"),
        datetime.now().astimezone().isoformat()
    )
    
    # Save to Project DB
    _save_record(PROJECT_DB, record)
    
    # Save to Global DB
    global_db = get_global_db_path()
    _save_record(global_db, record)
```

## 7. Risks
- **Risk**: Dự đoán không chính xác tuyệt đối như quét log thực tế. → **Mitigation**: Gán nhãn `accuracy: "estimated"` để người dùng nhận diện đây là số liệu ước tính, sẽ tự động chuẩn hóa khi có log thực tế.

## 8. Acceptance Criteria
- [ ] Khi chưa có `conversation_id` hoặc tệp logs, giao diện Visualizer vẫn hiển thị phần trăm context ước lượng tương ứng với checkpoint hiện tại thay vì `0%`.
- [ ] Chạy bộ test hệ thống thành công.

## 9. Test Plan
- **Verification**: Chạy kiểm thử: `python3 -m pytest -k "not powershell" skills/workflow-runtime/tests/`.
- **Manual Check**: Tạo một tệp `.session.json` trống không có `conversation_id` và chạy `workflow_runtime.py usage sync` xem thông số context có tự động điền theo checkpoint hay không.
