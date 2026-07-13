<!-- File path: docs/designs/FEAT-056_update_global_architecture_policy_blueprint.md -->

---
feature_id: FEAT-056
feature_name: Update Global Architecture Policy
status: reviewed
stage: blueprint
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../plans/FEAT-056_update_global_architecture_policy_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Update Global Architecture Policy

## 0. Baseline Context & References
- **Memory Baseline**: `AI_RULES.md` là nguồn chính sách trung tâm ("Single Source of Truth") của dự án. Tất cả các Skill khi được gọi đều phải đọc tệp tin này trước để làm cơ sở ra quyết định.
- **RAG Query Summaries**: Các Skill thiết kế và triển khai (như `plan-to-blueprint`, `blueprint-to-implementation`) đang tự định nghĩa các logic kiến trúc tẻ nhạt riêng lẻ gây lãng phí token.
- **Inspected Source Files**:
  - `AI_RULES.md`
  - `.agents/skills/brainstorming-to-plan/SKILL.md`
  - `.agents/skills/plan-to-blueprint/SKILL.md`
  - `.agents/skills/blueprint-to-implementation/SKILL.md`

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `AI_RULES.md` | MODIFY | Chèn phần chính sách "Architecture & Code Organization Policy" chi tiết vào cuối phần chính sách toàn cục | None | Thấp - Rủi ro phá vỡ định dạng Markdown |
| `.agents/skills/brainstorming-to-plan/SKILL.md` | MODIFY | Bổ sung câu chỉ thị tham chiếu đến Architecture Policy trong `AI_RULES.md` | AI_RULES.md | Thấp - Tối ưu hóa dung lượng token |
| `.agents/skills/plan-to-blueprint/SKILL.md` | MODIFY | Bổ sung chỉ thị đánh giá rủi ro kích thước tệp tin (soft lines limits) | AI_RULES.md | Thấp |
| `.agents/skills/blueprint-to-implementation/SKILL.md` | MODIFY | Bổ sung chỉ thị xác thực ranh giới Clean Architecture trước khi code | AI_RULES.md | Thấp |
| `README.md`, `USAGE.md`, `INSTALL.md`, `AGENTS.md` | MODIFY | Cập nhật tài liệu hướng dẫn giới thiệu về chuẩn kiến trúc DDD của dự án | AI_RULES.md | Thấp - Chỉ ảnh hưởng tài liệu |

## 2. Target Folder Structure
```text
.
├── .agents
│   └── skills
│       ├── brainstorming-to-plan
│       │   └── SKILL.md
│       ├── blueprint-to-implementation
│       │   └── SKILL.md
│       └── plan-to-blueprint
│           └── SKILL.md
├── AGENTS.md
├── AI_RULES.md
├── INSTALL.md
├── README.md
└── USAGE.md
```

## 3. Complete Class & Module Design
- Không bổ sung lớp lập trình mới. Đây là thay đổi cấu trúc tài liệu chính sách và hướng dẫn của Skill.

## 4. Detailed Interface Contracts
- Không áp dụng.

## 5. Configuration Schema
- Không áp dụng.

## 6. Database & Storage Design
- Không áp dụng.

## 7. Cache Architecture
- Không áp dụng.

## 8. Error Model
- Không áp dụng.

## 9. Skill Integration Contracts
- Các Skill thiết kế và viết code khi bắt đầu chạy sẽ tự động đối chiếu các đề xuất cấu trúc thư mục với quy định phân lớp DDD tại `AI_RULES.md` (Domain -> Application -> Infrastructure -> Transport).

## 10. CLI & Runtime Contracts
- Không áp dụng.

## 11. Sequence Flows
- **Architecture Validation Flow during Blueprint**:
  1. Skill `plan-to-blueprint` phân tích tệp tin nguồn.
  2. Đọc chính sách `AI_RULES.md` -> Quét bảng Soft Limits dòng code.
  3. Đối chiếu danh sách tệp đề xuất thay đổi.
  4. Nếu một tệp mới/sửa đổi vượt quá giới hạn soft limit (ví dụ: entity > 150 dòng, service > 250 dòng) hơn 20%:
     - Thêm phần "File size risk assessment" vào Blueprint.
     - Đề xuất phương án refactor/tách nhỏ cấu trúc.
  5. Xuất file blueprint.

## 12. Security & Safety
- **No Force Migration**: Tuyệt đối không tự ý ép buộc cấu trúc DDD lên các dự án cũ đã có kiến trúc ổn định khác (như MVC, Monolith truyền thống) để đảm bảo tính an toàn hệ thống và tránh lỗi biên dịch.

## 13. Complete Test Matrix
- Do đây là tài liệu chính sách, phương thức kiểm tra chủ yếu là chạy kiểm thử chất lượng liên kết tài liệu (broken links check) và kiểm tra tính nhất quán bằng kịch bản chạy thử Skill.
- **Verification Assertion**:
  - `AI_RULES.md` chứa chính xác từ khóa "Architecture & Code Organization Policy".
  - Các Skill chứa liên kết hợp lệ đến `AI_RULES.md`.

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Tệp `AI_RULES.md` -> Verified -> Released.
- `FR-04` -> Task 1.4 -> Tệp `AI_RULES.md` (Soft Limits) -> Verified -> Released.
- `FR-05` -> Task 1.5 -> Các tệp `SKILL.md` -> Verified -> Released.

## 15. File-Level Implementation Contracts
- **File**: `AI_RULES.md`
  - **Purpose**: Lưu trữ toàn bộ quy định an toàn và kiến trúc toàn cục cho dự án.
  - **Owner**: Architect.
  - **Inputs / Outputs**: Không áp dụng.
  - **Risks**: Trùng lặp chính sách gây loãng ngữ cảnh. -> Cách giảm thiểu: Xóa bỏ các định nghĩa kiến trúc nhỏ lẻ rải rác ở các file Skill khác sau khi đã tích hợp vào tệp quy tắc trung tâm.
