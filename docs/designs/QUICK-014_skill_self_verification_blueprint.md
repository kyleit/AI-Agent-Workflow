<!-- File path: docs/designs/QUICK-014_skill_self_verification_blueprint.md -->
---
feature_id: QUICK-014
feature_name: Dedicated Skill Self-Verification
status: reviewed
stage: blueprint
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: docs/quick/QUICK-014_skill_self_verification.md
next_artifact: skills/skill-self-verification/SKILL.md
---

# Technical Design Blueprint - Dedicated Skill Self-Verification

## 0. Baseline Context & References
- **Memory Baseline**: Các AI Skill trong dự án hiện được khai báo trong `MANIFEST.json` và lưu trữ tại `skills/`.
- **RAG Query Summaries**: Đã phân tích cách đăng ký và gọi Skill thông qua orchestrator (`skills/orchestrator/SKILL.md`).
- **Inspected Source Files**:
  - `MANIFEST.json`
  - `SKILLS.md`
  - `skills/orchestrator/SKILL.md`

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/skill-self-verification/SKILL.md` | `NEW` | Định nghĩa Skill mới phục vụ cho chất lượng và xác thực, khai báo aliases, categories và input schema. | N/A | Rất thấp. |
| `skills/skill-self-verification/scripts/verify_skill.py` | `NEW` | Thực thi kiểm tra tĩnh cấu trúc Skill, mô phỏng động luồng tương tác người dùng, và ghi báo cáo chất lượng. | `workflow_runtime.py` | Rất thấp. |
| `MANIFEST.json` | `MODIFY` | Đăng ký Skill mới `skill-self-verification` trong registry của framework. | N/A | Rất thấp. |
| `SKILLS.md` | `MODIFY` | Thêm Skill mới vào danh mục catalog kỹ năng cho các AI Agent phát hiện. | N/A | Rất thấp. |
| `README.md` | `MODIFY` | Cập nhật hướng dẫn sử dụng và giới thiệu lệnh CLI `/verify-skill`. | N/A | Rất thấp. |
| `USAGE.md` | `MODIFY` | Cập nhật tài liệu hướng dẫn vận hành SDLC với bước verify skill. | N/A | Rất thấp. |
| `CHANGELOG.md` | `MODIFY` | Ghi nhận phiên bản cập nhật tính năng mới này. | N/A | Rất thấp. |
| `skills/orchestrator/SKILL.md` | `MODIFY` | Cập nhật hướng dẫn đề xuất chạy lệnh `/verify-skill <skill-name>` sau các bước sửa đổi skill. | N/A | Rất thấp. |

## 2. Target Folder Structure
```text
skills/
└── skill-self-verification/
    ├── SKILL.md
    └── scripts/
        └── verify_skill.py
```

## 3. Interface Contracts (Public & Internal)
- **Public CLI Commands**:
  - `/verify-skill <skill-name>`
  - `python skills/skill-self-verification/scripts/verify_skill.py verify --skill <skill-name>`
- **Inputs**:
  - `skill`: Tên của Skill cần xác thực (ví dụ: `brainstorming`, `quick-feature`, `project-rag-search`, `skill-self-verification`).
- **Outputs**:
  - File báo cáo markdown tại `docs/verification/SKILL-VERIFY_<skill-name>.md`.
  - Exit code `0` (PASS) hoặc `1` (FAIL / BLOCKED).

## 4. Algorithms & Logic Specifications

### 4.1. Thiết kế Script `verify_skill.py`
Script Python sẽ thực hiện 4 pha kiểm tra chính độc lập:
1. **Static Analysis (Phân tích tĩnh)**:
   - Đọc và kiểm tra sự tồn tại của `skills/<skill-name>/SKILL.md`.
   - Phân tích cú pháp YAML frontmatter để đảm bảo có đầy đủ trường: `name`, `description`, `command`.
   - Kiểm tra liên kết tương đối của các file scripts khai báo trong SKILL.md.
2. **Simulation Engine (Mô phỏng động)**:
   - Định nghĩa trước các kịch bản tương tác (Scenarios) của từng Skill mục tiêu:
     - `skill-self-verification`: Chạy kiểm tra tự xác thực của chính nó.
     - `brainstorming`: Giả lập luồng khởi tạo và ghi file đặc tả sản phẩm.
     - `quick-feature`: Giả lập các chốt chặn checkpoint từ 5 đến 7.
     - `project-rag-search`: Thực thi lệnh search mẫu xem có phản hồi kết quả hay không.
   - Giả lập dữ liệu đầu vào (stdin) hoặc các biến môi trường tương tác để mô phỏng sự lựa chọn của người dùng (ví dụ: gõ "1", "Y", "N" vào prompt chọn permission mode).
3. **Runtime & Boundary Validation**:
   - Xác thực sự tuân thủ các quy tắc trong `AI_RULES.md` (ví dụ: cấm dùng file:// tuyệt đối, cấm enum permission_mode không an toàn).
   - Kiểm tra xem Skill có tích hợp đầy đủ với state engine thông qua tệp `.agents/.session.json` và CLI `workflow_runtime.py` hay không.
4. **Retry & Fix Mechanism**:
   - Nếu phát hiện lỗi nhỏ (ví dụ: thiếu file MD tạm hoặc lỗi thư mục đầu ra), cho phép thực hiện sửa chữa tự động và thử lại tối đa 3 lần.

### 4.2. Mẫu Báo cáo Kết quả Xác thực
Báo cáo markdown được tạo tự động tại `docs/verification/SKILL-VERIFY_<skill-name>.md` với định dạng:
```markdown
# Skill Verification Report: <skill-name>

## Summary
- Date: <date>
- Status: <PASS/FAIL/BLOCKED>

## Design Extracted
- Command: <command>
- Purpose: <purpose>

## Test Matrix
- Happy Path: [x] Checked
- Invalid Input: [x] Checked
- Boundary Violations: [x] Checked

## Simulation Transcript
<nhật ký hội thoại giả lập>

## Expected vs Actual
- Expected: <behavior>
- Actual: <behavior>

## Final Result
PASS
```

## 5. Backward Compatibility & Migration Mapping

| Old Field | New File | New Field | Migration Rule | Recovery Rule |
| :--- | :--- | :--- | :--- | :--- |
| N/A | N/A | N/A | Không thay đổi dữ liệu cấu hình lưu trữ, do đó hoàn toàn tương thích ngược 100%. | N/A |

## 6. Disallowed Outputs Validation
- [x] Không sử dụng `file://` hoặc đường dẫn tuyệt đối.
- [x] Không sử dụng các placeholders `...` hay `etc.` trong code/sơ đồ.
- [x] Không sử dụng các giá trị `permission_mode` không an toàn.
- [x] Không sử dụng `TBD`.
- [x] Đã ánh xạ toàn bộ trường legacy (không có).

## 7. Implementation Checklist
- [ ] Tạo file `skills/skill-self-verification/SKILL.md`.
- [ ] Tạo file `skills/skill-self-verification/scripts/verify_skill.py` với CLI đầy đủ 6 subcommands.
- [ ] Tạo thư mục báo cáo `docs/verification/`.
- [ ] Đăng ký Skill mới trong `MANIFEST.json`.
- [ ] Cập nhật danh mục catalog trong `SKILLS.md`.
- [ ] Cập nhật tài liệu hướng dẫn `README.md`, `INSTALL.md`, `USAGE.md`, `CHANGELOG.md`.
- [ ] Cập nhật hướng dẫn orchestrator tại `skills/orchestrator/SKILL.md`.
- [ ] Chạy thử và xuất 4 báo cáo xác thực cho 4 skills: `skill-self-verification`, `brainstorming`, `quick-feature`, `project-rag-search`.

## 8. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Tạo thư mục `skills/skill-self-verification/` | Có thư mục và tệp tin đúng vị trí. | `ls skills/skill-self-verification/` | N/A (Kiểm thử thủ công) |
| `REQ-002` | Có tệp `SKILL.md` và kịch bản | Định nghĩa đầy đủ metadata, input schema. | Xem nội dung `SKILL.md`. | N/A (Kiểm thử thủ công) |
| `REQ-003` | Script Python `verify_skill.py` chạy độc lập | CLI hoạt động với subcommand `verify`. | Chạy `python skills/skill-self-verification/scripts/verify_skill.py --help`. | N/A (Kiểm thử thủ công) |
| `REQ-004` | Giả lập Simulator | Giả lập đầu vào và kiểm tra exit code. | Chạy thử xác thực với `--skill project-rag-search`. | N/A (Kiểm thử thủ công) |
| `REQ-005` | Xuất báo cáo markdown | Sinh tệp `.md` tại `docs/verification/`. | Kiểm tra sự tồn tại của file báo cáo. | N/A (Kiểm thử thủ công) |
| `REQ-006` | Đăng ký manifest & catalog | Skill mới hiển thị trong MANIFEST.json và SKILLS.md. | Kiểm tra nội dung registry. | N/A (Kiểm thử thủ công) |
| `REQ-007` | Hỗ trợ 4 skills mục tiêu | Tạo thành công 4 báo cáo cho 4 skills yêu cầu. | Chạy CLI verify cho cả 4 skill. | N/A (Kiểm thử thủ công) |
| `REQ-008` | Cập nhật điều phối Orchestrator | Hướng dẫn orchestrator đề xuất `/verify-skill`. | Xem nội dung `skills/orchestrator/SKILL.md`. | N/A (Kiểm thử thủ công) |
| `REQ-009` | Tương thích ngược & An toàn | Test suite của hệ thống vẫn hoạt động pass 100%. | Chạy `pytest skills/workflow-runtime/tests/`. | `test_refactoring.py` |
