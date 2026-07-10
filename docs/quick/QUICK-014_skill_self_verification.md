<!-- File path: docs/quick/QUICK-014_skill_self_verification.md -->
# Feature Specification: QUICK-014 Dedicated Skill Self-Verification

## 1. Context & Objective
Hiện tại, khi các Skill của framework được tạo mới hoặc chỉnh sửa, chưa có một cơ chế tự động, chuẩn hóa để xác thực (verify) hành vi của chúng một cách động (mô phỏng tương tác của người dùng, kiểm tra chốt chặn runtime, kiểm tra checkpoint, v.v.).
Tính năng này yêu cầu tạo một Skill độc lập mới chuyên biệt mang tên `skill-self-verification` để tự kiểm thử và xuất báo cáo chất lượng cho các Skill khác.

## 2. Requirements & Capabilities
1. **Skill Folder**:
   - Vị trí: `skills/skill-self-verification/`
   - Chứa `SKILL.md` định nghĩa siêu dữ liệu, aliases (`verify-skill`, `skill-verify`, `self-verify`), categories, input schema, completion report và failure behaviors.
2. **Deterministic Script**:
   - Vị trí: `skills/skill-self-verification/scripts/verify_skill.py`
   - Cung cấp CLI: `python skills/skill-self-verification/scripts/verify_skill.py verify --skill <skill-name>`
   - Các subcommands đề xuất: `analyze`, `generate-tests`, `simulate`, `compare`, `report`, `verify`.
3. **Mô phỏng tương tác người dùng (Real User Simulator)**:
   - Script phải hoạt động như một simulator giả lập input của người dùng (happy path, sai input, từ chối/đồng ý approval gate, sai checkpoint, boundary violations).
   - Có khả năng xử lý tương tác qua luồng hỏi-đáp (mock user response).
4. **Báo cáo xác thực (Verification Report)**:
   - Ghi báo cáo tại `docs/verification/SKILL-VERIFY_<skill-name>.md`.
   - Kết quả cuối cùng phải thuộc một trong các giá trị: `PASS`, `FAIL`, `BLOCKED`.
5. **Đồng bộ hóa & Phát hiện**:
   - Đăng ký Skill mới trong `MANIFEST.json`.
   - Liệt kê trong `SKILLS.md`, `README.md`, `USAGE.md`, `CHANGELOG.md`.
   - Cập nhật điều phối orchestrator giới thiệu lệnh `/verify-skill <skill-name>` sau khi hoàn thành tạo/sửa đổi skill.

## 3. Scope Boundaries
- **In-Scope**:
  - Viết đầy đủ logic kiểm tra tĩnh (quét `SKILL.md`, `AI_RULES.md`) và logic kiểm tra động (giả lập chạy thử hoặc kiểm tra cấu trúc).
  - Tự động chạy thử tự kiểm tra (self-verify) đối với 4 skills mục tiêu: `skill-self-verification`, `brainstorming`, `quick-feature`, `project-rag-search`.
- **Out-of-Scope**:
  - Không thay đổi hành vi nghiệp vụ của các Skill khác ngoài việc thêm dòng khuyến nghị chạy `/verify-skill` vào cuối luồng xử lý hoặc orchestrator.

## 4. Verification & Testing Target
- Chạy lệnh tự kiểm thử cho 4 skills:
  ```bash
  python skills/skill-self-verification/scripts/verify_skill.py verify --skill skill-self-verification
  python skills/skill-self-verification/scripts/verify_skill.py verify --skill brainstorming
  python skills/skill-self-verification/scripts/verify_skill.py verify --skill quick-feature
  python skills/skill-self-verification/scripts/verify_skill.py verify --skill project-rag-search
  ```
- Toàn bộ test suite `pytest skills/workflow-runtime/tests/` phải tiếp tục pass 100%.
