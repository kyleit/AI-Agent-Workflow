<!-- File path: docs/implementation-governance/IMP-QUALITY-GATES.md -->

# IMP-QUALITY-GATES: Implementation Quality Gates & Matrices

Tài liệu này định nghĩa các chốt chặn chất lượng kiểm soát mã nguồn thực thi, ma trận truy vết và đặc tả runtime cho AIWF OS.

## 1. Traceability Matrices (Ma trận truy vết)

### FEAT → Blueprint → Implementation Matrix

| FEAT ID | Blueprint File | Target Implementation File | Owner |
| :--- | :--- | :--- | :--- |
| **FEAT-086** | `FEAT-086_blueprint.md` | `skills/workflow-runtime/scripts/runtime.py` | Coder |
| **FEAT-087** | `FEAT-087_blueprint.md` | `skills/workflow-runtime/scripts/dag.py` | Coder |
| **FEAT-088** | `FEAT-088_blueprint.md` | `skills/workflow-runtime/scripts/registry_sdk.py` | Coder |

---

## 2. Runtime Execution Contracts (Hợp đồng thực thi)

- **Subagent spawning**: Mọi subagent phải được kích hoạt thông qua cơ chế Sandbox cô lập, cấm gọi trực tiếp shell host.
- **Handoff rules**: Quá trình bàn giao lock tài nguyên giữa các agent phải được lưu log trong SQLite Event Journal.
- **VFS usage**: Các tiến trình test bắt buộc phải ghi dữ liệu thông qua VFS memory-overlay để tránh thay đổi trực tiếp file hệ thống khi chưa được duyệt.

---

## 3. Implementation Checklists (Danh sách kiểm tra)

- [ ] Không có thay đổi nào làm thay đổi kiến trúc core đã đóng băng.
- [ ] 100% mã nguồn được format theo tiêu chuẩn PEP8.
- [ ] Báo cáo bằng chứng (evidence bundle) được tạo và ký số tự động.
- [ ] Không rò rỉ cổng mạng hay PID zombie sau khi chạy xong.
