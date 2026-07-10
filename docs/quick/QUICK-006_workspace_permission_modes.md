<!-- File path: docs/quick/QUICK-006_workspace_permission_modes.md -->

---
artifact_type: quick-feature-spec
feature_id: QUICK-006
workflow: quick-feature
architecture_impact: high
adr_required: false
status: pending
---

# Mini Feature Specification – Workspace Permission Modes (Sandbox vs Full Access)

## 1. Feature Goal
Tích hợp cơ chế cấu hình chế độ phân quyền của không gian làm việc trong quá trình khởi tạo dự án. Hệ thống sẽ cung cấp 3 chế độ:
- **Sandbox Mode** (Mặc định): Yêu cầu người dùng phê duyệt lặp đi lặp lại đối với mọi hành động thay đổi trạng thái (sửa code, tạo file, chạy kiểm thử, git commit...).
- **Full Access Mode**: Cho phép Agent tự động thực hiện các tác vụ phát triển thông thường (sửa code, tạo tệp spec/blueprint, chạy build/test/lint, update memory...) mà không cần xác nhận nhiều lần. Tuy nhiên, các hành động phá hủy, phát hành, hoặc bảo mật (git push/tag/commit, release, delete file lớn, external command...) vẫn bắt buộc phải có sự xác nhận của người dùng (**Hard-gated actions**).
- **Unrestricted Mode**: Không cần bất kỳ xác nhận nào từ người dùng cho tất cả mọi hành động (kể cả git push, release). Khi người dùng lựa chọn chế độ này lúc khởi tạo, hệ thống phải in ra cảnh báo đỏ nguy hiểm và yêu cầu người dùng xác nhận lại một lần nữa bằng cách gõ `CONFIRM_UNRESTRICTED`. Nếu xác nhận sai hoặc bỏ qua, hệ thống tự động fallback về Sandbox Mode.

---

## 2. Business Value
- Tăng hiệu năng làm việc của Agent ở chế độ **Full Access Mode** nhờ giảm thiểu thời gian chờ Ba phê duyệt các hành động phụ trợ lành tính và không gây hại.
- Giữ vững mức độ an toàn mặc định ở chế độ **Sandbox Mode** để bảo vệ dự án khỏi các chỉnh sửa ngoài ý muốn.
- Cung cấp tùy chọn tự động hóa tối đa qua chế độ **Unrestricted Mode** cho các tác vụ tin cậy cao, có cảnh báo xác nhận hai lớp (Two-factor confirmation) để tránh kích hoạt ngoài ý muốn.

---

## 3. Session State Changes
Đồng bộ các thông số mới vào `.agents/.session.json`:
```json
{
  "permission_mode": "sandbox | full_access | unrestricted",
  "permission_mode_selected_at": "ISO8601",
  "permission_mode_selected_by": "user"
}
```

---

## 4. Expected Files

| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | [AI_RULES.md](file:///Volumes/Kyle/AgentsProject/AI_RULES.md) | Thêm chính sách Workspace Permission Mode Policy |
| Modify | [skills/workflow-runtime/scripts/session.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/session.py) | Khởi tạo cấu trúc permission_mode mặc định |
| Modify | [skills/workflow-runtime/scripts/workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) | Cung cấp helper CLI `permission` hoặc tham số `init --permission` |
| Modify | [skills/software-development-workflow/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/software-development-workflow/SKILL.md) | Định hướng luồng kiểm duyệt dựa trên phân quyền |
| Modify | [skills/initialize-workflow/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/initialize-workflow/SKILL.md) | Thêm bước lựa chọn mode khi khởi tạo |
| Modify | [skills/quick-fix/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/quick-fix/SKILL.md) | Kiểm tra Mode và giảm thiểu hỏi lặp |
| Modify | [skills/quick-feature/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/quick-feature/SKILL.md) | Kiểm tra Mode và giảm thiểu hỏi lặp |
| Modify | [skills/brainstorming/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming/SKILL.md) | Kiểm tra Mode và giảm thiểu hỏi lặp |
| Modify | [README.md](file:///Volumes/Kyle/AgentsProject/README.md), [USAGE.md](file:///Volumes/Kyle/AgentsProject/USAGE.md), [CHANGELOG.md](file:///Volumes/Kyle/AgentsProject/CHANGELOG.md) | Cập nhật hướng dẫn sử dụng Sandbox/Full Access |
| Modify | [skills/workflow-runtime/tests/test_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/tests/test_runtime.py) | Viết test suite xác thực 10 hành vi rẽ nhánh của phân quyền |

---

## 5. Security Guardrails
Chế độ **Full Access** tuyệt đối KHÔNG được bỏ qua:
- Phê duyệt Blueprint kỹ thuật trước khi sửa code.
- Phê duyệt Release thủ công.
- Các hành động phá hủy, đẩy Git (push, tag, commit).
- Mọi thay đổi về credential/secret hay thay đổi chính chế độ Permission.
