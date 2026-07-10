<!-- File path: docs/designs/QUICK-005_skill_suggestion_gate_blueprint.md -->

---
artifact_type: design-blueprint
feature_id: QUICK-005
workflow: quick-feature
adr_required: false
status: pending
---

# Technical Design Blueprint – Skill Suggestion Gate for Unclassified User Requests

## 1. Context & Architecture Decisions
Yêu cầu thiết lập chốt chặn Suggestion Gate bắt buộc đối với tất cả các câu hỏi/yêu cầu ngôn ngữ tự nhiên không có prefix command từ người dùng. AI Agent sẽ dừng lại, đề cử Kỹ năng phù hợp và chỉ tiếp tục thực hiện khi nhận được xác nhận từ người dùng.

---

## 2. Session Schema Integration
Tệp `.session.json` được cập nhật thêm trường cấu trúc `"suggestion_gate"`:
```json
"suggestion_gate": {
    "active": true,
    "raw_request": "Tôi bị lỗi crash khi bấm submit form",
    "classification": "quick-fix",
    "recommended_skill": "quick-fix",
    "options": ["quick-fix", "brainstorming"],
    "status": "waiting_for_user_confirmation"
}
```

---

## 3. CLI Subcommand "suggest" Specs
Lệnh CLI runtime hỗ trợ quản lý trạng thái gợi ý:
- `workflow_runtime.py suggest --request "..." --recommend "..."` : Đăng ký yêu cầu thô và đề xuất Kỹ năng.
- `workflow_runtime.py suggest --choose "Y"` : Người dùng phê duyệt lựa chọn để chuyển đổi `status: confirmed` và tắt `active: false`.
- `workflow_runtime.py suggest --choose "1"` : Người dùng chọn phương án 1 trong danh sách options.

---

## 4. Verification & Testing Matrix

### Automated Tests
Tất cả 12 kịch bản rẽ nhánh đã được kiểm chứng tự động trong `test_runtime.py` bao gồm:
1. Gợi ý `quick-fix` khi gặp bug.
2. Gợi ý `quick-feature` khi gặp tính năng nhỏ.
3. Gợi ý `brainstorming` khi gặp thiết kế lớn.
4. Gợi ý đa lựa chọn khi gặp yêu cầu mơ hồ.
5. Duyệt bằng `choose 1`.
6. Duyệt bằng `choose 2`.
7. Duyệt bằng `choose 3`.
8. Đề cử release chỉ khi có yêu cầu tường minh.
9. Đăng ký complete không tự ý gợi ý auto-release.
10. Lệnh explicit `/quick-fix` bỏ qua suggestion gate.
11. Lệnh explicit `/brainstorm` bỏ qua suggestion gate.
12. Lệnh explicit `/release` hoạt động bình thường.
