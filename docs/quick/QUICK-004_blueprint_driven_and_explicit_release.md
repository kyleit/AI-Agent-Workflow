<!-- File path: docs/quick/QUICK-004_blueprint_driven_and_explicit_release.md -->

---
artifact_type: quick-feature
feature_id: QUICK-004
workflow: quick-feature
architecture_impact: high
adr_required: false
status: approved
---

# Mini Feature Specification – Blueprint-Driven Development & Explicit Release Control

## 1. Feature Goal
Tái cấu trúc toàn bộ AI Workflow Framework để thiết lập hai nguyên tắc kỹ thuật tuyệt đối:
1. **Blueprint là đầu vào duy nhất hợp lệ cho việc triển khai mã nguồn**: Không cho phép bất kỳ Kỹ năng (Skill) nào sửa đổi mã nguồn nếu không có tài liệu Blueprint thiết kế kỹ thuật (`docs/designs/`) đã được người dùng phê duyệt rõ ràng.
2. **Quy trình Phát hành (Release) chỉ được kích hoạt khi có yêu cầu tường minh từ người dùng**: Loại bỏ hoàn toàn mọi cơ chế tự động chuyển tiếp hoặc tự ý sửa đổi phiên bản, commit, tag, push của AI Agent.

---

## 2. Business Value
- Tăng cường 100% độ an toàn và kiểm soát của người dùng đối với các hành vi thay đổi mã nguồn và phát hành của Agent.
- Chuẩn hóa quy trình SDLC chuyên nghiệp, loại bỏ rủi ro Agent tự ý chỉnh sửa code lung tung dựa trên các tài liệu thảo luận, spec sơ sài hoặc tự ý release mã nguồn chưa qua kiểm duyệt.

---

## 3. Existing Context
- Tệp chính sách cốt lõi: `AI_RULES.md`
- Kỹ năng điều phối chính: `skills/software-development-workflow/`
- Kỹ năng triển khai: `skills/blueprint-to-implementation/`, `skills/quick-fix/`, `skills/quick-feature/`
- Kỹ năng release: `skills/implementation-to-release/`
- Bộ chạy CLI runtime: `skills/workflow-runtime/scripts/workflow_runtime.py`, `validator.py`, `session.py`
- Tài liệu hướng dẫn: `README.md`, `INSTALL.md`, `USAGE.md`, `CHANGELOG.md`

---

## 4. Scope

### In Scope:
- **Chính sách toàn cầu**: Thêm chính sách `13. Blueprint Mandatory Execution Policy` và cập nhật `9. Release Policy` thành `Explicit Release Policy` trong `AI_RULES.md`.
- **Nâng cấp Quick Fix & Quick Feature (3 Giai đoạn)**:
  - Giai đoạn 1: Tạo tài liệu Đặc tả (`docs/issues/FIX-XXX.md` hoặc `docs/quick/QUICK-XXX.md`) và **DỪNG** chờ phê duyệt.
  - Giai đoạn 2: Tạo tệp Thiết kế kỹ thuật Blueprint tương ứng (`docs/designs/FIX-XXX_blueprint.md` hoặc `docs/designs/QUICK-XXX_blueprint.md`) và **DỪNG** chờ phê duyệt.
  - Giai đoạn 3: Triển khai mã nguồn (Implementation) chỉ sau khi kiểm tra Blueprint đã được duyệt.
- **Quy trình SDLC chuẩn**: Cập nhật Orchestrator (`software-development-workflow`) để chèn chốt chặn bắt buộc trước Release.
- **Cập nhật Runtime**:
  - Bổ sung trường cấu trúc `"blueprint"` vào `.session.json` để lưu vết trạng thái và đường dẫn thiết kế.
  - Sửa đổi CLI `workflow_runtime.py` để hỗ trợ lưu và xác thực trạng thái Blueprint được duyệt.
- **Cập nhật các Kỹ năng**: Thêm logic xác thực Blueprint tồn tại & được duyệt trước khi cho phép sửa đổi tệp tin.
- **Tài liệu & Tests**: Cập nhật toàn bộ tài liệu hướng dẫn và bộ test tự động tương ứng.

### Out of Scope:
- Thay đổi cấu trúc cơ sở dữ liệu SQLite bên ngoài session tracking.

---

## 5. Expected Files

| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | [AI_RULES.md](file:///Volumes/Kyle/AgentsProject/AI_RULES.md) | Bổ sung chính sách Blueprint bắt buộc và Explicit Release |
| Modify | [skills/workflow-runtime/scripts/workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) | Cập nhật CLI lưu trữ và kiểm tra trạng thái phê duyệt Blueprint |
| Modify | [skills/workflow-runtime/scripts/session.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/session.py) | Hỗ trợ cấu trúc lưu trữ blueprint mới trong session |
| Modify | [skills/software-development-workflow/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/software-development-workflow/SKILL.md) | Định nghĩa lại luồng điều phối SDLC mới |
| Modify | [skills/blueprint-to-implementation/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/blueprint-to-implementation/SKILL.md) | Thêm logic kiểm soát nghiêm ngặt đầu vào Blueprint |
| Modify | [skills/quick-fix/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/quick-fix/SKILL.md) | Refactor thành quy trình 3 giai đoạn |
| Modify | [skills/quick-feature/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/quick-feature/SKILL.md) | Refactor thành quy trình 3 giai đoạn |
| Modify | [skills/implementation-to-release/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/implementation-to-release/SKILL.md) | Chặn tự động hóa, yêu cầu lệnh Release tường minh |
| Modify | [README.md](file:///Volumes/Kyle/AgentsProject/README.md) | Cập nhật sơ đồ và hướng dẫn quy trình SDLC mới |
| Modify | [USAGE.md](file:///Volumes/Kyle/AgentsProject/USAGE.md) | Hướng dẫn cách thức chạy các lệnh và duyệt Blueprint/Release |
| Modify | [skills/workflow-runtime/tests/test_project_memory.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/tests/test_project_memory.py) | Cập nhật và bổ sung test suites kiểm tra chốt chặn |

---

## 6. Risks & Mitigation
- **Risk**: Làm phức tạp hóa các thay đổi nhỏ (như sửa lỗi typo).
- **Mitigation**: Quy trình Quick Fix và Quick Feature 3 giai đoạn vẫn nhanh gọn hơn Standard SDLC (không cần bước Brainstorm/Plan) nhưng đảm bảo tính an toàn tối đa vì bắt buộc phải viết thiết kế kỹ thuật Blueprint ra để người dùng phê duyệt trước khi chạm vào mã nguồn.

---

## 7. Acceptance Criteria
- [ ] Không có Skill nào được phép sửa đổi code nếu không có Blueprint được duyệt.
- [ ] Trạng thái Blueprint được lưu trữ động trong `.session.json`.
- [ ] CLI `workflow_runtime.py` hỗ trợ lệnh kiểm tra và cập nhật Blueprint phê duyệt.
- [ ] Quy trình Release yêu cầu từ khóa tường minh, không tự động chuyển tiếp.
- [ ] Toàn bộ bộ test suites chạy vượt qua thành công.
