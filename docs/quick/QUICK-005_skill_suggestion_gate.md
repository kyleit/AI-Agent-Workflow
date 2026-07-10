<!-- File path: docs/quick/QUICK-005_skill_suggestion_gate.md -->

---
artifact_type: quick-feature-spec
feature_id: QUICK-005
workflow: quick-feature
architecture_impact: high
adr_required: false
status: approved
---

# Mini Feature Specification – Skill Suggestion Gate for Unclassified User Requests

## 1. Feature Goal
Tích hợp một chốt chặn phân loại và gợi ý Kỹ năng tự động (**Skill Suggestion Gate**) đối với tất cả các yêu cầu bằng ngôn ngữ tự nhiên chưa được gắn lệnh hoặc Kỹ năng tường minh của người dùng. AI Agent sẽ dừng lại, gợi ý luồng phù hợp nhất và chờ người dùng xác nhận trước khi thực hiện bất kỳ hành động sửa đổi code hay tạo tài liệu nào.

---

## 2. Business Value
- Tránh việc AI Agent tự ý phỏng đoán và khởi chạy sai Kỹ năng hoặc tự động chỉnh sửa code một cách bừa bãi khi người dùng chỉ muốn đặt câu hỏi khảo sát hoặc thảo luận.
- Định hướng người dùng sử dụng đúng Kỹ năng cho đúng tác vụ (sửa lỗi nhỏ -> quick-fix, tính năng nhỏ -> quick-feature, hệ thống lớn -> brainstorming...).

---

## 3. Existing Context
- Luật toàn cầu: `AI_RULES.md`
- CLI Runtime: `skills/workflow-runtime/scripts/workflow_runtime.py`, `session.py`
- Kỹ năng điều phối chính: `skills/software-development-workflow/`
- Kỹ năng SDLC khác: `quick-fix`, `quick-feature`, `brainstorming`, `blueprint-to-implementation`, `implementation-to-release`, `resume-workflow`

---

## 4. Scope

### In Scope:
- **Chính sách**: Bổ sung chính sách `14. Skill Suggestion Gate Policy` vào `AI_RULES.md` định nghĩa rõ các quy tắc phân loại dựa trên loại yêu cầu (lỗi -> quick-fix/brainstorm, tính năng nhỏ -> quick-feature, hệ thống lớn -> brainstorming, tìm kiếm -> project-rag-search...).
- **Định dạng phản hồi**:
  - Gợi ý đơn lẻ: Hiển thị phân loại, Kỹ năng/Lệnh đề xuất, lý do, các bước xử lý và dừng lại chờ xác nhận (`Y/N`).
  - Đa gợi ý: Hiển thị bảng lựa chọn (Option 1, 2, 3...) và dừng chờ chọn số.
- ** CLI Runtime**: Tích hợp trường `"suggestion_gate"` vào tệp `.session.json` để lưu trữ vết của yêu cầu gốc, các option đề cử và trạng thái chờ xác nhận.
- **Orchestrator**: Cập nhật `software-development-workflow` để làm nhiệm vụ phân loại chính khi người dùng gõ văn bản thuần.
- **Cập nhật các Kỹ năng**: Sửa đổi các Skill để kiểm tra nếu nhận được yêu cầu thô thì phải dừng và chạy qua Suggestion Gate trước.
- **Tests**: Thêm 12 test case tương ứng để xác minh toàn bộ các hành vi rẽ nhánh của Suggestion Gate.

---

## 5. Expected Files

| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | [AI_RULES.md](file:///Volumes/Kyle/AgentsProject/AI_RULES.md) | Thêm chính sách Skill Suggestion Gate |
| Modify | [skills/workflow-runtime/scripts/session.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/session.py) | Hỗ trợ cấu trúc lưu trữ suggestion_gate |
| Modify | [skills/workflow-runtime/scripts/workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) | Hỗ trợ lệnh CLI lưu trữ/xác nhận gợi ý |
| Modify | [skills/software-development-workflow/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/software-development-workflow/SKILL.md) | Tích hợp ma trận phân loại (Classification Matrix) |
| Modify | [skills/quick-fix/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/quick-fix/SKILL.md) | Chặn chạy thẳng từ văn bản thô |
| Modify | [skills/quick-feature/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/quick-feature/SKILL.md) | Chặn chạy thẳng từ văn bản thô |
| Modify | [skills/blueprint-to-implementation/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/blueprint-to-implementation/SKILL.md) | Kiểm tra suggestion gate |
| Modify | [skills/implementation-to-release/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/implementation-to-release/SKILL.md) | Kiểm tra suggestion gate |
| Modify | [README.md](file:///Volumes/Kyle/AgentsProject/README.md) | Cập nhật hướng dẫn sử dụng chốt chặn |
| Modify | [USAGE.md](file:///Volumes/Kyle/AgentsProject/USAGE.md) | Cập nhật ví dụ phân loại và phê duyệt |
| Modify | [skills/workflow-runtime/tests/test_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/tests/test_runtime.py) | Viết thêm test suite xác thực 12 kịch bản phân loại |

---

## 6. Risks & Mitigation
- **Risk**: Người dùng gõ lệnh tường minh nhưng vẫn bị chặn hỏi gợi ý.
- **Mitigation**: CLI và Agent luôn ưu tiên kiểm tra xem người dùng có truyền prefix lệnh (ví dụ `/workflow`, `/quick-fix`,...) hay không. Nếu có lệnh tường minh thì bỏ qua Suggestion Gate hoàn toàn.

---

## 7. Acceptance Criteria
- [ ] Mọi yêu cầu thô không có lệnh sẽ kích hoạt chốt gợi ý và dừng lại.
- [ ] Trạng thái chốt gợi ý được đồng bộ chính xác trong `.session.json`.
- [ ] Giao diện Webview/Console hiển thị đúng format gợi ý đơn lẻ hoặc đa gợi ý.
- [ ] Vượt qua toàn bộ bộ tests tích hợp.
