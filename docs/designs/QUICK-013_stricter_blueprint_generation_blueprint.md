<!-- File path: docs/designs/QUICK-013_stricter_blueprint_generation_blueprint.md -->
---
feature_id: QUICK-013
feature_name: Stricter Blueprint Generation
status: reviewed
stage: blueprint
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: docs/quick/QUICK-013_stricter_blueprint_generation.md
next_artifact: skills/plan-to-blueprint/SKILL.md
---

# Technical Design Blueprint – Stricter Blueprint Generation

## 0. Baseline Context & References
- **Memory Baseline**: Đã tham chiếu `skills/plan-to-blueprint/SKILL.md` hiện tại và hiểu rõ cấu trúc mẫu Blueprint.
- **RAG Query Summaries**: Không cần RAG bổ sung vì các yêu cầu được định nghĩa rõ ràng trong yêu cầu của người dùng.
- **Inspected Source Files**: [skills/plan-to-blueprint/SKILL.md](skills/plan-to-blueprint/SKILL.md)

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/plan-to-blueprint/SKILL.md` | `MODIFY` | Cập nhật cấu trúc mẫu Blueprint và bổ sung các quy tắc kiểm tra nghiêm ngặt, bao gồm cả mục Tương thích ngược và Disallowed Outputs. | Không có | Thấp. Chỉ thay đổi chỉ dẫn cho AI, không ảnh hưởng đến logic chạy runtime. |

## 2. Target Folder Structure
```text
.
└── skills
    └── plan-to-blueprint
        └── SKILL.md
```

## 3. Interface Contracts (Public & Internal)
- **Public Interface Contracts**:
  - Không có CLI command mới. Lệnh `aiwf blueprint` giữ nguyên cú pháp.
- **Internal Component Contracts**:
  - Cấu trúc tài liệu Technical Design Blueprint được xuất ra phải tuân thủ nghiêm ngặt định dạng mẫu mới cập nhật.

## 4. Algorithms & Logic Specifications
Mẫu cấu trúc Technical Design Blueprint trong `skills/plan-to-blueprint/SKILL.md` sẽ được thiết kế lại như sau:

### Quy định tự kiểm tra (Self-review Checklist) trước khi xuất Blueprint:
1. Không có link `file://` hay đường dẫn tuyệt đối nào xuất hiện.
2. Có bảng tương thích ngược chỉ rõ cách di trú cấu trúc cũ.
3. enum `permission_mode` chỉ chứa `sandbox` hoặc `full_access`.
4. pseudo-code paths được validate đầy đủ (sử dụng đường dẫn tương đối chính xác).
5. acceptance criteria liệt kê tường minh toàn bộ số lượng test cases.
6. Mô tả đầy đủ ViewModel schema, watch strategy, debounce, fallback, UI error state khi thay đổi extension.

## 5. Backward Compatibility & Migration Mapping

| Old Field | New File | New Field | Migration Rule | Recovery Rule |
| :--- | :--- | :--- | :--- | :--- |
| N/A | N/A | N/A | Không có sự thay đổi cấu trúc dữ liệu lưu trữ (state), đây chỉ là thay đổi định dạng tài liệu hướng dẫn. | N/A |

## 6. Disallowed Outputs Validation
- Không sử dụng `file://` trong thiết kế.
- Không sử dụng đường dẫn tuyệt đối.
- Không sử dụng `...` hoặc `etc.` trong biểu đồ thư mục hoặc pseudo-code.
- Không sử dụng `TBD` trong các mô tả thiết kế.
- Không sử dụng các giá trị `permission_mode` không an toàn.
- Không có trường legacy nào chưa được ánh xạ.

## 7. Implementation Checklist
- [ ] Cập nhật tệp `skills/plan-to-blueprint/SKILL.md` với template mới và 8 quy tắc validation.
- [ ] Đồng bộ hóa sang `.agents/skills/plan-to-blueprint/SKILL.md`.

## 8. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Cấm sinh `file://` và đường dẫn tuyệt đối | Mẫu Blueprint mới chỉ dùng đường dẫn tương đối. | Kiểm tra thủ công tệp `SKILL.md`. | N/A |
| `REQ-002` | Tương thích ngược với `.session.json` | Mẫu Blueprint có phần Backward Compatibility & Migration Mapping. | Kiểm tra thủ công tệp `SKILL.md`. | N/A |
| `REQ-003` | Enum an toàn cho `permission_mode` | Cấm `unrestricted`, chỉ cho phép `sandbox` và `full_access`. | Kiểm tra thủ công tệp `SKILL.md`. | N/A |
| `REQ-004` | Xác thực đường dẫn pseudo-code | Pseudo-code sử dụng `.agents/.session.json` thay vì `.agents/session.json`. | Kiểm tra thủ công tệp `SKILL.md`. | N/A |
| `REQ-005` | Acceptance Criteria không được rút gọn | Yêu cầu liệt kê đầy đủ tất cả các test case, không dùng dấu ba chấm. | Kiểm tra thủ công tệp `SKILL.md`. | N/A |
| `REQ-006` | Extension changes phải đầy đủ | Có mô tả về ViewModel, watch strategy, debounce, fallback, UI hỏng, partial refresh. | Kiểm tra thủ công tệp `SKILL.md`. | N/A |
| `REQ-007` | Mục Backward Compatibility bắt buộc | Có bảng di trú với các cột được chỉ định. | Kiểm tra thủ công tệp `SKILL.md`. | N/A |
| `REQ-008` | Mục Disallowed Outputs bắt buộc | Có mục Disallowed Outputs ở cuối mẫu Blueprint. | Kiểm tra thủ công tệp `SKILL.md`. | N/A |
