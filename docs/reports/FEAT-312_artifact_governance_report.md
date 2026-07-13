# FEAT-312 Artifact Governance & Documentation Structure Report

Báo cáo chi tiết về việc triển khai hệ thống quản trị tài liệu (Artifact Governance) tập trung cho AIWF nhằm tổ chức chặt chẽ và chuẩn hóa toàn bộ các tài liệu sinh ra bởi workflow.

---

## 1. Vấn đề Hiện tại (Current Problem)
Trước đây, các Agent hoặc Skills có thể tự ý tạo các tài liệu Markdown (`.md`) ở bất kỳ đâu trong dự án, bao gồm cả thư mục gốc (project root). Điều này gây lộn xộn và thiếu nhất quán trong cấu trúc thư mục của dự án (Ví dụ: `FEAT-310_extension_workflow_observatory_migration_report.md` được sinh ra ngay tại thư mục root).

---

## 2. Quy tắc Quản trị Mới (New Rules)
- **Quy tắc 1**: Nghiêm cấm tuyệt đối việc tạo bất kỳ tài liệu Markdown (`.md`) nào trực tiếp ở project root ngoại trừ các tệp tin hệ thống chuẩn (`README.md`, `CHANGELOG.md`, `AGENTS.md`, `AI_RULES.md`, `SKILLS.md`, `USAGE.md`, `INSTALL.md`, `LICENSE`).
- **Quy tắc 2**: Toàn bộ tài liệu do workflow tạo ra bắt buộc phải được lưu trữ trong các thư mục con tương ứng của `docs/` dựa theo cấu trúc ánh xạ tiêu chuẩn.
- **Quy tắc 3**: Tên tệp tin phải tuân thủ nghiêm ngặt định dạng đặt tên (định dạng prefix `FEAT-xxx` hoặc `FIX-xxx` đi kèm hậu tố thích hợp).

---

## 3. Bảng Ánh xạ Thư mục Tài liệu (Directory Mapping)

| Loại Tài liệu | Thư mục Đích | Định dạng Tên Tệp |
| :--- | :--- | :--- |
| **Brainstorming** | `docs/brainstorming/` | `FEAT-xxx.md` / `FIX-xxx.md` |
| **Planning** | `docs/planning/` | `FEAT-xxx_plan.md` / `FEAT-xxx_plan.json` |
| **Architecture Review** | `docs/architecture/` | `FEAT-xxx_architecture.md` |
| **Blueprint** | `docs/blueprints/` | `FEAT-xxx_blueprint.md` / `FEAT-xxx_blueprint.json` |
| **Implementation** | `docs/implementation/` | `FEAT-xxx_implementation.md` / `_report.md` |
| **Verification** | `docs/verification/` | `FEAT-xxx_verification.md` / `_report.md` |
| **Release** | `docs/release/` | `FEAT-xxx_release.md` / `_candidate_report.md` |
| **Reports** | `docs/reports/` | `FEAT-xxx_report.md` / `_migration_report.md` |
| **Operations** | `docs/operations/` | Hướng dẫn vận hành & bảo trì |

---

## 4. Thiết kế Bộ Xác thực & Tích hợp Supervisor (Validation Design)

### Bộ Xác thực `ArtifactGovernance`:
- Triển khai lớp `ArtifactGovernance` trong [artifact_governance.py](file://./skills/workflow-runtime/scripts/artifact_governance.py) để tự động chuẩn hóa đường dẫn, kiểm tra sự tồn tại của tệp, xác minh sự phù hợp với cấu trúc thư mục con và định dạng tên tệp.
- Hỗ trợ hàm `scan_root_violations` để tự động quét tìm các file Markdown mồ côi nằm ở project root.

### Tích hợp vào Workflow Supervisor:
- Trong [workflow_supervisor.py](file://./skills/workflow-runtime/scripts/workflow_supervisor.py), trước khi hoàn tất tiến trình của bất kỳ phase nào, Supervisor sẽ gọi `ArtifactGovernance.validate_artifact_path` để xác thực toàn bộ các tài liệu evidence/artifact được khai báo trong cấu hình phase.
- Nếu phát hiện vi phạm, Supervisor sẽ:
  1. Ghi nhận sự kiện lỗi `workflow.artifact.violation` vào lịch sử trace event.
  2. Phát cảnh báo và tự động chuyển trạng thái sang `BLOCKED`.
  3. Chặn đứng (không cho phép) việc chuyển đổi sang phase tiếp theo.

---

## 5. Kết quả Di trú (Migration Result)
Con đã quét và di chuyển thành công các tài liệu báo cáo mồ côi ở project root vào đúng thư mục quy định:
- `FEAT-310_extension_workflow_observatory_migration_report.md` -> [FEAT-310_extension_workflow_observatory_migration_report.md](file://./docs/reports/FEAT-310_extension_workflow_observatory_migration_report.md)
- `AIWF_Workflow_Enforcement_Rules_Update_Report.md` -> [AIWF_Workflow_Enforcement_Rules_Update_Report.md](file://./docs/reports/AIWF_Workflow_Enforcement_Rules_Update_Report.md)

---

## 6. Kết quả Kiểm thử (Test Results)
Tệp kiểm thử [test_artifact_governance.py](file://./skills/workflow-runtime/tests/test_artifact_governance.py) đã xác thực:
- 6/6 test cases chạy thành công (**PASSED**).
- Xác thực thành công cơ chế chặn (blocking) của Supervisor khi nhận diện đường dẫn hoặc định dạng tên tệp vi phạm quy tắc.

---

## 7. Trạng thái Nghiệm thu Cuối cùng

```text
AIWF_ARTIFACT_GOVERNANCE_READY
```
