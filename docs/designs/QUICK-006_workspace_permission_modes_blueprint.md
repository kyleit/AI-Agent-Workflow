<!-- File path: docs/designs/QUICK-006_workspace_permission_modes_blueprint.md -->

---
artifact_type: design-blueprint
feature_id: QUICK-006
workflow: quick-feature
adr_required: false
status: pending
---

# Technical Design Blueprint – Workspace Permission Modes (Sandbox vs Full Access)

## 1. Context & Architecture Decisions
Để tối ưu hóa trải nghiệm nhà phát triển và an toàn thông tin, hệ thống thiết lập cơ chế phân quyền hai mức độ. 

---

## 2. Policy Definitions in AI_RULES.md
Thêm mục `15. Workspace Permission Mode Policy`:
- Mặc định: `sandbox`.
- Phải được chọn khi chạy `/init` (hoặc initialize-workflow).
- `full_access` chỉ bỏ qua các thao tác phát triển thông thường (normal file write, build, test, lint, local updates).
- Tuyệt đối cấm tự động hóa các hành vi nguy hiểm, phát hành, hoặc bảo mật (git push, git commit, git tag, release, delete file lớn, thay đổi credential...).

---

## 3. Session Schema Updates
Tệp `.session.json` bổ sung:
```json
{
  "permission_mode": "sandbox",
  "permission_mode_selected_at": "2026-07-07T10:08:00Z",
  "permission_mode_selected_by": "user"
}
```

---

## 4. Runtime Helpers
Trong `workflow_runtime.py`:
- `get_permission_mode() -> str`: Đọc từ session, fallback là `sandbox`.
- `requires_approval(action_type: str) -> bool`:
  - `sandbox` mode: Luôn trả về `True` cho mọi action_type.
  - `full_access` mode: Trả về `False` cho `normal_file_write`, `source_code_change`, `test_command`, `build_command`, `memory_update`, `blueprint_generation`. Trả về `True` cho `release`, `git_commit`, `git_tag`, `git_push`, `git_merge`, `destructive_delete`, `external_command`, `secret_change`.
  - `unrestricted` mode: Luôn trả về `False` cho mọi action_type (không cần phê duyệt cho bất kỳ hành động nào).
- **Two-Factor CLI Confirmation**:
  - Khi người dùng chọn `--permission 3` (hoặc unrestricted) trong `init`, hệ thống hiển thị cảnh báo đỏ và yêu cầu người dùng nhập `"CONFIRM_UNRESTRICTED"` để xác nhận. Nếu người dùng nhập không đúng, hệ thống fallback về `sandbox`.

---

## 5. Skills Interactions
Các tệp Kỹ năng (`SKILL.md`) cập nhật bước kiểm duyệt:
- Bổ sung bước kiểm tra phân quyền:
  `If requires_approval("action_type") or permission_mode == "sandbox": Ask user approval.`
  `Else: Proceed automatically.`

---

## 6. Test Suite Cases
Tích hợp các trường hợp kiểm thử tự động trong `test_runtime.py` kiểm tra:
1. `init` mặc định.
2. Ghi nhận `sandbox` khi chọn 1.
3. Ghi nhận `full_access` khi chọn 2.
4. Chọn 3 nhưng nhập sai hoặc không nhập mã xác nhận -> fallback về `sandbox`.
5. Chọn 3 và nhập đúng mã xác nhận `CONFIRM_UNRESTRICTED` -> lưu `unrestricted`.
6. Trả về `True` cho mọi action khi mode là `sandbox`.
7. Bỏ qua yêu cầu kiểm duyệt đối với normal file write khi mode là `full_access`.
8. Giữ nguyên kiểm duyệt đối với git push trong `full_access`.
9. Bỏ qua hoàn toàn mọi kiểm duyệt (kể cả git push, release) khi mode là `unrestricted`.
10. Fallback khi giá trị mode rác.
11. Đổi mode cần phê duyệt.
12. Kiểm tra đồng bộ time khi chọn mode.
