<!-- File path: docs/issues/FIX-002_fix_hardcoded_brain_root.md -->

---
artifact_type: fix
issue_id: FIX-002
workflow: quick-fix
architecture_impact: low
adr_required: false
status: PASS
---

# Fix Document – Fix Hardcoded Brain Root Path

## 1. Issue
Người dùng báo cáo rằng sau khi chạy đến Step 5, các thống kê về lượng token và chi phí của workflow (Workflow Usage) và dự án (Project Usage) hiển thị là N/A hoặc $0.00 (0 tokens), đồng thời thông tin Global Usage hiển thị sai lệch.

## 2. Symptoms
- Giao diện Visualizer mở rộng hiển thị Workflow Usage là `N/A` ("Waiting for workflow usage data...").
- Project Usage hiển thị `0.00 USD` (Tokens: 0).
- Tập tin `.session.json` có các trường thống kê lượng token đều bằng 0, mặc dù tệp nhật ký giao thoại `transcript.jsonl` thực tế có dung lượng lớn hơn 0.

## 3. Root Cause
- Trong tệp [context.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/context.py#L13), biến `BRAIN_ROOT` đang bị hardcode cứng đường dẫn của Windows: `BRAIN_ROOT = r"C:\Users\Kyle\.gemini\antigravity-ide\brain"`.
- Trên hệ điều hành macOS của Ba, đường dẫn này không tồn tại, khiến hàm `parse_transcript(log_file)` luôn trả về kết quả rỗng `{}`, từ đó dẫn đến việc các thống kê token sử dụng luôn bằng 0.

## 4. Scope
- **In Scope**: Thay đổi cách khởi tạo biến `BRAIN_ROOT` trong `skills/workflow-runtime/scripts/context.py` và phiên bản cài đặt `.agents/skills/workflow-runtime/scripts/context.py` để sử dụng hàm `os.path.expanduser` động và tương thích đa nền tảng.
- **Out of Scope**: Không thay đổi bất kỳ logic tính toán token hay hành vi lưu trữ của cơ sở dữ liệu SQLite.

## 5. Expected Files
| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | [context.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/context.py) | Sửa biến `BRAIN_ROOT` thành động |
| Modify | [context.py](file:///Volumes/Kyle/AgentsProject/.agents/skills/workflow-runtime/scripts/context.py) | Sửa biến `BRAIN_ROOT` trong thư mục cài đặt thực thi |

## 6. Proposed Fix
Thay đổi dòng số 13 trong `context.py`:
```python
-BRAIN_ROOT = r"C:\Users\Kyle\.gemini\antigravity-ide\brain"
+BRAIN_ROOT = os.path.expanduser("~/.gemini/antigravity-ide/brain")
```

## 7. Risks
- **Risk**: Một số hệ thống Windows có cấu hình đặc biệt có thể không giải quyết ký tự `~` chính xác. → **Mitigation**: Python hỗ trợ `os.path.expanduser` hoàn toàn chuẩn xác trên cả Windows (tự động trỏ về `C:\Users\Username`) nên rủi ro này là cực kỳ thấp.

## 8. Acceptance Criteria
- [ ] Biến `BRAIN_ROOT` được chuyển thành động bằng cách sử dụng `os.path.expanduser("~/.gemini/antigravity-ide/brain")`.
- [ ] Chạy lệnh `python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py usage report` trả về đúng thống kê số lượng token lớn hơn 0.
- [ ] Tập tin `.session.json` đồng bộ và cập nhật chính xác các thông tin Workflow, Project và Global Usage.

## 9. Test Plan
- **Verification**: Run unit tests of workflow runtime: `pytest .agents/skills/workflow-runtime/tests/` (nếu có).
- **Manual Check**: Chạy `python3 .agents/migrate_session_to_db.py` và kiểm tra lại giá trị trong `.session.json`.
