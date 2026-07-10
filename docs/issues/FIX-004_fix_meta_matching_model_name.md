<!-- File path: docs/issues/FIX-004_fix_meta_matching_model_name.md -->

---
artifact_type: fix
issue_id: FIX-004
workflow: quick-fix
architecture_impact: low
adr_required: false
status: draft
---

# Fix Document – Fix Meta-Matching Model Name Bug

## 1. Issue
Giao diện Visualizer Extension hiển thị tên Model là `([^\` (một chuỗi biểu thức chính quy bị lỗi) thay vì tên Model thực tế của phiên trò chuyện.

## 2. Symptoms
- Mục `Model:` trong Workflow Usage hiển thị là `([^\`.
- Lỗi này xuất hiện sau khi hệ thống thực hiện thao tác hiển thị/đọc mã nguồn của tệp `context.py`.

## 3. Root Cause
- Trong tệp [context.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/context.py#L43), hàm `parse_transcript` quét qua toàn bộ tệp nhật ký `transcript.jsonl` để tìm các thay đổi cài đặt mô hình của người dùng thông qua chuỗi `"Model Selection"`.
- Khi tác nhân chạy lệnh xem tệp tin (`view_file`), toàn bộ mã nguồn của tệp `context.py` được ghi vào `transcript.jsonl` dưới dạng nội dung của bước xem tệp.
- Vì mã nguồn của `context.py` chứa chính biểu thức chính quy tìm kiếm `Model Selection` (tại dòng 44), trình phân tích cú pháp đã quét trúng dòng mã nguồn này và khớp nhầm với mẫu regex, khiến tên Model bị nhận diện sai thành chuỗi regex `([^\`.

## 4. Scope
- **In Scope**:
  - Sửa đổi tệp `skills/workflow-runtime/scripts/context.py` để giới hạn việc quét `"Model Selection"` chỉ trong các bước nhập liệu của người dùng (`type: USER_INPUT`).
  - Cập nhật tệp cài đặt thực thi `.agents/skills/workflow-runtime/scripts/context.py`.
- **Out of Scope**: Không thay đổi các phần logic nghiệp vụ khác của việc đếm token.

## 5. Expected Files
| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | [context.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/context.py) | Chỉ quét Model Selection trong `type: USER_INPUT` |
| Modify | [context.py](file:///Volumes/Kyle/AgentsProject/.agents/skills/workflow-runtime/scripts/context.py) | Chỉ quét Model Selection trong `type: USER_INPUT` |

## 6. Proposed Fix
Thay đổi dòng số 43 trong `context.py`:
```python
-                if content and "Model Selection" in content:
+                if line.get("type") == "USER_INPUT" and content and "Model Selection" in content:
```

## 7. Risks
- **Risk**: Nếu có loại bước khác đại diện cho nhập liệu người dùng, cấu hình mô hình có thể bị bỏ qua. → **Mitigation**: Cấu hình thay đổi cài đặt mô hình (`USER_SETTINGS_CHANGE`) luôn được hệ thống đóng gói bên trong bước nhập liệu có kiểu `USER_INPUT`, vì vậy không có rủi ro bỏ sót.

## 8. Acceptance Criteria
- [ ] Tên mô hình hiển thị đúng (ví dụ: `Gemini 3.5 Flash (Medium)` hoặc `auto`).
- [ ] Không còn hiện tượng hiển thị regex `([^\` khi đọc mã nguồn.

## 9. Test Plan
- **Verification**: Chạy kiểm thử đơn vị: `python3 -m pytest -k "not powershell" skills/workflow-runtime/tests/`.
- **Manual Check**: Đồng bộ hóa dữ liệu thông qua lệnh `python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py usage sync` và kiểm tra lại giá trị model hiển thị trong `.session.json`.
