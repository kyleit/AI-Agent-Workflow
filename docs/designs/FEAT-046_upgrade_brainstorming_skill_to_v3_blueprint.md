<!-- File path: docs/designs/FEAT-046_upgrade_brainstorming_skill_to_v3_blueprint.md -->

---
feature_id: FEAT-046
feature_name: Upgrade Brainstorming Skill to v3
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-046_upgrade_brainstorming_skill_to_v3_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Upgrade Brainstorming Skill to v3

## 0. Baseline Context & References
- **Memory Baseline**: FRESH — Tài liệu bộ nhớ và chỉ mục tri thức ổn định.
- **RAG Query Summaries**: Không yêu cầu gọi RAG do thiết kế tập trung điều chỉnh hướng dẫn kỹ năng.
- **Inspected Source Files**:
  - `skills/brainstorming/SKILL.md`
  - `skills/brainstorming-to-plan/SKILL.md`
  - `skills/plan-to-blueprint/SKILL.md`

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/brainstorming/SKILL.md` | `MODIFY` | Thêm đặc tả và mẫu phân tích v3 (14 mục phân tích mới) vào quy trình và mẫu đầu ra của Brainstorming. | Không | Thấp - Chỉ bổ sung chỉ dẫn văn bản cho mô hình AI. |
| `skills/brainstorming-to-plan/SKILL.md` | `MODIFY` | Điều chỉnh quy trình lập kế hoạch để loại bỏ các bước bắt buộc Planner phân tích lại kiến trúc, rủi ro, scope vốn đã được Brainstorming thực hiện. | `skills/brainstorming/SKILL.md` | Thấp. |
| `skills/plan-to-blueprint/SKILL.md` | `MODIFY` | Điều chỉnh quy trình để bắt buộc Architect kế thừa trực tiếp các nguyên tắc kiến trúc và ADR detection từ tài liệu brainstorm v3. | `skills/brainstorming/SKILL.md` | Thấp. |

## 2. Target Folder Structure
```text
.
└── skills
    ├── brainstorming
    │   └── SKILL.md
    ├── brainstorming-to-plan
    │   └── SKILL.md
    └── plan-to-blueprint
        └── SKILL.md
```

## 3. Interface Contracts (Public & Internal)
- **Frontmatter Version**: Cả 3 kỹ năng được cập nhật phiên bản lên `3.0.0` trong tệp cấu hình frontmatter.
- **Backward Compatibility**: Tương thích ngược với các tài liệu cũ bằng cách sử dụng cấu trúc khoá/giá trị cũ không đổi trong Markdown header, chỉ bổ sung các phần mới vào cuối tệp Markdown đầu ra.

## 4. Algorithms & Logic Specifications
- Luồng dữ liệu mới giảm số bước lặp phân tích:
  ```text
  [Brainstorming v3]
         │ (Tạo đầy đủ 14 phân tích phạm vi, rủi ro, nguyên tắc, ADR)
         ▼
  [Planning v3]
         │ (Chỉ phân chia phase, ước lượng, lên lịch - KHÔNG phân tích lại)
         ▼
  [Blueprint v3]
         │ (Kế thừa trực tiếp nguyên tắc thiết kế, ADR từ Brainstorming)
         ▼
  [Implementation]
  ```

## 5. State Machine & Transitions
Không thay đổi trạng thái checkpoint hoặc máy trạng thái của `workflow-runtime`. Vẫn giữ nguyên Checkpoint 3 cho Động não thành công, và Checkpoint 4 cho Thiết kế thành công.

## 6. Validation and Safety Constraints
- Xác thực cú pháp tệp `SKILL.md` phải tuân thủ nghiêm ngặt chuẩn YAML frontmatter để tránh sập CLI parser khi nạp kỹ năng.

## 7. Backward Compatibility & Migration Mapping
| Old Field | New File | New Field | Migration Rule | Recovery Rule |
| :--- | :--- | :--- | :--- | :--- |
| `legacy_field` | `skills/brainstorming/SKILL.md` | `legacy_field` | Giữ nguyên tất cả các khoá YAML cũ ở đầu tài liệu. | Revert về phiên bản git trước đó. |

## 8. Implementation Checklist
- [ ] Cập nhật mẫu tài liệu đầu ra trong `skills/brainstorming/SKILL.md` thêm 14 phần phân tích mới.
- [ ] Cập nhật chỉ dẫn cho Planner trong `skills/brainstorming-to-plan/SKILL.md`.
- [ ] Cập nhật chỉ dẫn cho Architect trong `skills/plan-to-blueprint/SKILL.md`.
- [ ] Chạy thử nghiệm quy trình với cả tài liệu brainstorming cũ và mới để xác minh.

## 9. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Hỗ trợ 14 mục phân tích tri thức mới | Tệp đầu ra chứa đầy đủ các bảng và phần phân tích như Scope Boundary, Asset Analysis, Blast Radius, v.v. | Tạo tệp và kiểm tra thủ công nội dung tệp sinh ra. | `skills/workflow-runtime/tests/test_validation.py` |
| `REQ-002` | Tối ưu hóa Planning | Planner không sinh ra phần phân tích kiến trúc mà sử dụng trực tiếp bối cảnh từ brainstorming. | So sánh độ dài và chi phí token của pha Planning. | `skills/workflow-runtime/tests/test_scoping.py` |
| `REQ-003` | Tối ưu hóa Blueprint | Blueprint kế thừa trực tiếp ADR recommendations. | Kiểm tra tham chiếu chéo tệp thiết kế với tệp spec gốc. | `skills/workflow-runtime/tests/test_refactoring.py` |
