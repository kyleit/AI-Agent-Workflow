---
name: document-compliance-assessment
command: verify-doc
aliases:
  - doc-assess
  - check-doc
category: review
tags:
  - documentation
  - compliance
  - quality
  - audit
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-17
updated_at: 2026-07-17
description: Use when reviewing workflow artifacts, traceability, relative-path compliance, and pre-approval document quality before a phase can pass.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
---

# Skill: document-compliance-assessment (Đánh giá tuân thủ tài liệu)

---

## 🔒 GLOBAL POLICY REFERENCES

Tác nhân sử dụng Skill này bắt buộc phải tuân thủ nghiêm ngặt các chính sách toàn cục được định nghĩa trong [AI_RULES.md](../../AI_RULES.md):
- **Documentation Policy** (Section 7) - Tài liệu rõ ràng, cấu trúc chuẩn mực.
- **Absolute Path Prohibition Policy** (Section 15 & Section 28) - Tuyệt đối cấm sử dụng đường dẫn tuyệt đối (Absolute Path) hoặc URL tệp cục bộ (`file:///`) trong bất kỳ tài liệu hay mã nguồn nào.
- **Artifact Governance Policy** (Section 28) - Lưu trữ tài liệu đúng vị trí quy định, không lưu rác ở root hay Desktop.

---

## 🎯 Mục đích

Skill này cung cấp quy trình và bộ tiêu chuẩn thống nhất để đánh giá điểm tuân thủ tài liệu (**Documentation Traceability Score**) và chất lượng các artifacts bàn giao, đảm bảo đạt yêu cầu nghiệm thu giai đoạn (Phase Release).

---

## 📋 Thang điểm đánh giá chất lượng tài liệu (Documentation Traceability Score - Thang 100)

Việc đánh giá điểm số phải dựa trên bằng chứng thực tế có trong tài liệu hoặc các tệp tin kết quả kiểm thử. Không được chấm điểm theo cảm giác.

| # | Thành phần đánh giá | Điểm tối đa | Tiêu chuẩn đạt đủ điểm & Bằng chứng cần thiết |
|---|---|---:|---|
| 1 | **Requirement to plan/blueprint trace** | 20 | Mỗi yêu cầu chính từ brainstorming/yêu cầu ban đầu đều phải được ánh xạ (mapping) rõ ràng tới plan, blueprint, hoặc decision (ADR) tương ứng. |
| 2 | **Blueprint to implementation trace** | 20 | Mỗi file/command/API thay đổi hoặc thêm mới đều phải truy xuất ngược lại được về phần thiết kế hoặc quyết định liên quan trong blueprint. |
| 3 | **Implementation to test trace** | 20 | Mỗi hành vi/tính năng chính được triển khai phải đi kèm bằng chứng kiểm thử (test evidence) hoặc lý do tại sao chưa test rõ ràng trong tài liệu. |
| 4 | **Report/result evidence** | 20 | Báo cáo kết quả (như `walkthrough.md` hoặc `verify.md`) phải viết bằng tiếng Việt, nêu rõ điểm số (score) của các hạng mục, kết quả PASS/FAIL, các lệnh đã chạy, danh sách artifact được tạo và các rủi ro còn lại. |
| 5 | **Known risks (Rủi ro đã biết)** | 10 | Các rủi ro còn lại của hệ thống phải được liệt kê và phân loại rõ ràng theo mức độ nghiêm trọng (severity), tầm ảnh hưởng (impact) và hành động giảm thiểu tiếp theo. |
| 6 | **Relative artifact links** | 10 | Mọi liên kết dẫn tới tài liệu/mã nguồn (artifacts) phải sử dụng đường dẫn tương đối (Relative Path). Tuyệt đối không có đường dẫn tuyệt đối hoặc URL tệp cục bộ. |
| | **TỔNG ĐIỂM TÀI LIỆU** | **100** | **Điểm đạt tối thiểu để Release: 95/100** |

---

## ⛔ Điều kiện bắt buộc đánh FAIL lập tức (NO-GO)

Tài liệu hoặc giai đoạn sẽ bị đánh FAIL (NO-GO) ngay lập tức nếu vi phạm bất kỳ điều nào dưới đây:
1. Có bất kỳ đường dẫn tuyệt đối thật nào (ví dụ bắt đầu bằng `file:///` hoặc `/Volumes/...` hoặc Windows tương ứng `C:\...`) trong tài liệu, mã nguồn, script hoặc tệp tin kết quả.
2. Có luồng rò rỉ thông tin bí mật (mã xác thực, token, khóa API, khóa proxy, cookie) hoặc thông tin cá nhân (PII) trong tài liệu hoặc log kiểm thử.
3. Báo cáo đạt nhưng chưa đủ bằng chứng thực tế ghi nhận trong tệp tin kết quả.
4. Tổng điểm chất lượng tài liệu đánh giá dưới **95/100**.
5. A pre-approval artifact is missing an `Internal Review Evidence` section.
6. The review says PASS but does not list reviewer roles, source artifacts, checklist rows, failed-point repair history, document-compliance score, and relative-path scan result.
7. The final Blueprint Approval gate is requested through plain chat instead of `workflow_runtime.py prompt select`, unless the runtime prompt bridge is explicitly reported unavailable.
8. The artifact uses vague placeholders such as `TBD`, `...`, `etc.`, `modify related files`, or generic implementation instructions where concrete file-by-file evidence is required.
9. A new FEAT/FIX/QUICK workflow artifact is written as a flat file directly under `docs/brainstorming/`, `docs/plans/`, `docs/blueprints/`, `docs/issues/`, `docs/quick/`, `docs/debug/`, `docs/verification/`, or `docs/reports/` instead of under `docs/features/<feature-family>/<stage>/`.
10. A new FEAT/FIX/QUICK workflow artifact is stored in a folder copied from the work item ID, such as `docs/work-items/FEAT-XXX_*` or `docs/<stage>/FEAT-XXX_*`, instead of a semantic feature family folder.
11. A new FEAT/FIX/QUICK workflow artifact lacks a matching `docs/features/<feature-family>/README.md` cross-artifact index, unless the artifact is a legacy file being migrated and the migration report explicitly explains it.
12. A documentation migration groups artifacts by `FEAT-*`, `FIX-*`, or `QUICK-*` ID without reading content evidence from frontmatter, title, headings, summary/problem statement, and linked artifacts.

---

## Strict Pre-Approval Artifact Review Rules

For roadmap/discovery, Specification, Implementation Plan, and Technical Blueprint artifacts:

- A score of `100/100` is allowed only when every scoring row cites concrete evidence from the artifact by section heading, table row, or checklist item.
- Missing evidence MUST subtract points. Do not infer compliance from intent.
- Any no-go condition above overrides the numeric score and produces `FAIL`.
- If review FAILS, output an exact failed-point list. Each item must name the violated rule, the artifact section, the required correction, and the scope boundary that must not be changed.
- The authoring agent must revise only those failed points, then rerun the same review. The re-review must increment `Re-review Count`.
- The workflow cannot advance to the next phase until the current artifact has review result `PASS`, score `>=95/100`, and zero no-go findings.

Required `Internal Review Evidence` block:

```markdown
## Internal Review Evidence

| Field | Evidence |
|---|---|
| Reviewer Roles | Planner / Architect / Reviewer / QA / QC / Specialist roles used |
| Source Artifacts Reviewed | `relative/path.md`, user request summary, active Skill, `AI_RULES.md` |
| Checklist Result | PASS/FAIL rows with concrete evidence |
| Failed Points | `None` or exact failed-point list |
| Revision Scope | `None` or exact sections revised |
| Re-review Count | `0` for first-pass PASS, otherwise number of repeated reviews |
| Document Compliance Score | `NN/100` |
| Relative Path Scan | PASS only when no `file:///`, `/Users/`, `/Volumes/`, drive-letter paths, or local absolute links exist |
| Semantic Feature Folder Compliance | PASS only when new FEAT/FIX/QUICK artifacts live under `docs/features/<feature-family>/<stage>/`, `<feature-family>` is semantic rather than ID-derived, classification evidence is recorded, and the feature index exists |
| Final Result | `PASS` or `FAIL` |
```

---

## 🔄 Quy trình thực hiện tự đánh giá tài liệu

### Bước 1: Thu thập Artifacts và Tài liệu liên quan
- Định vị tất cả các tệp tài liệu được tạo/chỉnh sửa trong giai đoạn hiện tại (ví dụ: `implementation_plan.md`, `walkthrough.md`, `ADR-XXX.md`, `verify.md`).
- Xác định mã nguồn và các file kiểm thử thực tế.

### Bước 2: Chạy kiểm tra quy tắc đường dẫn tương đối
- Sử dụng công cụ grep hoặc quét qua các tệp tin để đảm bảo không có chuỗi tuyệt đối như `/Users/`, `/Volumes/`, `file:///`.

### Bước 3: Tính toán điểm số theo thang 100
- Điền bảng điểm chi tiết dựa trên bằng chứng cụ thể.
- Báo cáo rõ ràng lý do đạt hoặc trừ điểm đối với từng hạng mục.

### Bước 4: Tạo báo cáo Compliance Report
- Ghi nhận kết quả đánh giá tài liệu vào báo cáo nghiệm thu cuối cùng.

---

## 📊 Mẫu báo cáo kết quả (Document Compliance Report)

Báo cáo phải được ghi vào phần cuối của báo cáo nghiệm thu (`walkthrough.md` hoặc tệp báo cáo nghiệm thu tương ứng):

```markdown
## Đánh giá tuân thủ tài liệu (Document Compliance Report)

- **Documentation Traceability Score**: <diem>/100
- **Trạng thái**: [ĐẠT | KHÔNG ĐẠT]

### Bảng chi tiết điểm số:
1. **Requirement to plan/blueprint trace** (<diem>/20): [Bằng chứng chi tiết]
2. **Blueprint to implementation trace** (<diem>/20): [Bằng chứng chi tiết]
3. **Implementation to test trace** (<diem>/20): [Bằng chứng chi tiết]
4. **Report/result evidence** (<diem>/20): [Bằng chứng chi tiết]
5. **Known risks** (<diem>/10): [Mô tả rủi ro & giải pháp giảm thiểu]
6. **Relative artifact links** (<diem>/10): [Trạng thái đường dẫn tương đối]

- **Rủi ro còn lại**: [Liệt kê rủi ro hoặc ghi "Không có"]
```

---

## 🔒 WORKFLOW RUNTIME INTERFACE

- **Start**: `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "document-compliance-assessment" --command "verify-doc" --checkpoint 9 --step "Starting document assessment..."`
- **Step Updates**: `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<desc>" --log "<msg>"`
- **Completion**: `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 9 --step "Document Assessment Complete" --next-skill "software-development-workflow" --next-command "workflow"`
- **Failure**: `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"`
