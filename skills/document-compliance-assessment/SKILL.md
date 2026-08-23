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
version: 1.1.0
license: MIT
repository: https://gitlab.com/your-org/ai-workflow-skills
created_at: 2026-07-17
updated_at: 2026-08-18
description: Use when reviewing workflow artifacts, upstream consistency, relative-path compliance, and pre-approval document quality before a phase can pass.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
---

# Skill: document-compliance-assessment (Đánh giá tuân thủ tài liệu & Thẩm tra ngược đầu vào)

---

## 🔒 GLOBAL POLICY REFERENCES

Tác nhân sử dụng Skill này bắt buộc phải tuân thủ nghiêm ngặt các chính sách toàn cục được định nghĩa trong [AI_RULES.md](../../AI_RULES.md):
- **Documentation Policy** (Section 7) - Tài liệu rõ ràng, cấu trúc chuẩn mực.
- **Absolute Path Prohibition Policy** (Section 15 & Section 28) - Tuyệt đối cấm sử dụng đường dẫn tuyệt đối (Absolute Path) hoặc URL tệp cục bộ (`file:///`) trong bất kỳ tài liệu hay mã nguồn nào.
- **Artifact Governance Policy** (Section 28) - Lưu trữ tài liệu đúng vị trí quy định theo chuẩn Feature Family (`docs/features/<feature-family>/<stage>/`).

---

## 🎯 Mục đích

Skill này cung cấp quy trình và bộ tiêu chuẩn thống nhất để đánh giá điểm tuân thủ tài liệu (**Documentation Traceability Score**), chất lượng các artifacts bàn giao, và **ngăn chặn triệt để lỗi dây chuyền (Anti-Cascading Error Propagation)** từ các giai đoạn trước sang các giai đoạn sau.

---

## 🛡️ Upstream Consistency & Anti-Cascading Review Gate (Thẩm định ngược đầu vào)

> [!CRITICAL]
> **NGĂN CHẶN LỖI LAN TRUYỀN DÂY CHUYỀN (CASCADING DEFECT PREVENTION)**:
> Mọi giai đoạn SDLC kế tiếp (Plan, Blueprint, Implementation) **BẮT BUỘC** phải thẩm định lại toàn bộ tài liệu đầu vào trước khi tiến hành viết:
> 1. **Tính Toàn Vẹn Đầu Vào**: Xác thực tệp đầu vào (`Spec`, `Brainstorming`, hoặc `Plan`) không chứa bất kỳ lỗ hổng ranh giới, giả định sai lệch hay vi phạm quy tắc đường dẫn.
> 2. **Phát Hiện Mâu Thuẫn (Contradiction Interception)**: Nếu tài liệu giai đoạn hiện tại mâu thuẫn hoặc không thể triển khai do tài liệu giai đoạn trước thiết kế sai, Agent **BẮT BUỘC PHẢI DỪNG LẠI (HALT)** và gửi yêu cầu sửa đổi (Needs Changes) ngược lên giai đoạn trước.
> 3. **Cấm Vá Cháy Tạm Bợ**: Tuyệt đối cấm viết tiếp tài liệu hoặc mã nguồn dựa trên một tài liệu đầu vào có lỗi.

---

## 📋 Thang điểm đánh giá chất lượng tài liệu (Documentation Traceability Score - Thang 100)

Việc đánh giá điểm số phải dựa trên bằng chứng thực tế có trong tài liệu hoặc các tệp tin kết quả kiểm thử. Không được chấm điểm theo cảm giác.

| # | Thành phần đánh giá | Điểm tối đa | Tiêu chuẩn đạt đủ điểm & Bằng chứng cần thiết |
|---|---|---:|---|
| 1 | **Upstream Consistency & Trace** | 20 | Mỗi yêu cầu chính từ spec/brainstorming/plan đầu vào được rà soát không mâu thuẫn, không thiếu sót, và ánh xạ chính xác sang artifact hiện tại. |
| 2 | **Blueprint to implementation trace** | 20 | Mỗi file/command/API thay đổi hoặc thêm mới đều phải truy xuất ngược lại được về phần thiết kế hoặc quyết định liên quan trong blueprint. |
| 3 | **Implementation to test trace** | 20 | Mỗi hành vi/tính năng chính được triển khai phải đi kèm bằng chứng kiểm thử (test evidence) hoặc lý do tại sao chưa test rõ ràng trong tài liệu. |
| 4 | **Report/result evidence** | 20 | Báo cáo kết quả (như `audit_report.md` hoặc `release_notes.md`) phải viết rõ ràng, nêu rõ điểm số (score) của các hạng mục, kết quả PASS/FAIL, các lệnh đã chạy, danh sách artifact được tạo và các rủi ro còn lại. |
| 5 | **Known risks (Rủi ro đã biết)** | 10 | Các rủi ro còn lại của hệ thống phải được liệt kê và phân loại rõ ràng theo mức độ nghiêm trọng (severity), tầm ảnh hưởng (impact) và hành động giảm thiểu tiếp theo. |
| 6 | **Relative artifact links** | 10 | Mọi liên kết dẫn tới tài liệu/mã nguồn (artifacts) phải sử dụng đường dẫn tương đối (Relative Path). Tuyệt đối không có đường dẫn tuyệt đối hoặc URL tệp cục bộ (`file:///`, `C:\`, `E:\`). |
| | **TỔNG ĐIỂM TÀI LIỆU** | **100** | **Điểm đạt tối thiểu để Release: 95/100** |

---

## ⛔ Điều kiện bắt buộc đánh FAIL lập tức (NO-GO)

Tài liệu hoặc giai đoạn sẽ bị đánh FAIL (NO-GO) ngay lập tức nếu vi phạm bất kỳ điều nào dưới đây:
1. Có bất kỳ đường dẫn tuyệt đối nào (`file:///...`, `E:\...`, `C:\...`) trong tài liệu hoặc mã nguồn (Policy 11).
2. Phát hiện tài liệu đầu vào của giai đoạn trước có sai sót nghiêm trọng mà giai đoạn này vẫn tiếp tục thực thi làm lan truyền lỗi dây chuyền.
3. Có luồng rò rỉ thông tin bí mật (mã xác thực, token, khóa API, cookie) trong tài liệu hoặc log kiểm thử.
4. Báo cáo đạt nhưng chưa đủ bằng chứng thực tế ghi nhận trong tệp tin kết quả.
5. Tổng điểm chất lượng tài liệu đánh giá dưới **95/100**.
6. Thiếu bảng `Internal Review Evidence` hoặc `CODE_BLOCK_GATE` không đạt `PASS`.
7. Sử dụng các từ khóa lười biếng / giữ chỗ (`// TODO`, `...`, `tương tự như trên`, `generic modify`).
8. Lưu tài liệu sai vị trí cấu trúc Feature Family (`docs/features/<feature-family>/<stage>/`).

---

## Strict Pre-Approval Artifact Review Rules

For roadmap/discovery, Specification, Implementation Plan, and Technical Blueprint artifacts:

- A score of `100/100` is allowed only when every scoring row cites concrete evidence from the artifact by section heading, table row, or checklist item.
- Missing evidence MUST subtract points. Do not infer compliance from intent.
- Any no-go condition above overrides the numeric score and produces `FAIL`.
- If review FAILS, output an exact failed-point list. Each item must name the violated rule, the artifact section, the required correction, and the scope boundary that must not be changed.
- The authoring agent must revise only those failed points, then rerun the same review. The re-review must increment `Re-review Count`.
- The workflow cannot advance to the next phase until the current artifact has review result `PASS`, score `>=95/100`, and zero no-go findings.
