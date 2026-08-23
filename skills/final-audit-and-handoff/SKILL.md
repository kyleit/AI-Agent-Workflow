---
name: final-audit-and-handoff
description: Final audit and handoff governance skill for the AI Engineering Workflow framework. Audits all 18 preceding implementation phases, validates final artifact index, verifies end-to-end traceability, validates operational closure decision, and executes formal redesign project closure.
role: FINAL_AUDIT_AND_HANDOFF_GOVERNANCE
version: 3.15.0
canonical_entrypoint: false
on_demand: true
---

# Final Audit and Handoff Governance Skill

## 1. Overview
Skill này chịu trách nhiệm kiểm tra thẩm định cuối cùng (Final Audit), tạo chỉ mục bằng chứng hoàn chỉnh (Final Artifact Index), xác minh tính toàn vẹn truy vết và ban hành Quyết định Đóng Dự án Tái thiết kế Luồng làm việc AIWF (Final Project Closure).

---

## 2. Core Capabilities
1. **Full Phase-Chain Audit**: Kiểm tra trạng thái PASS & REVIEWED của toàn bộ 18 Phase triển khai từ Phase 01 tới Phase 18.
2. **Artifact & Traceability Audit**: Xác minh 100% tệp bằng chứng machine-readable, chuỗi Full SHA-256 identity và liên kết truy vết từ Raw Intent tới Handoff.
3. **Operational Status Validation**: Đánh giá trạng thái vận hành `OPERATIONAL_ACTIVE_WITH_CONDITIONS` và xác nhận rào cản dừng sự cố không bị kích hoạt.
4. **Maintenance Backlog Aggregation**: Tổng hợp danh mục các hạng mục bảo trì không cản trở vận hành (MB-001, MB-002).
5. **Final Project Closure Execution**: Thực thi việc đóng chính thức dự án Tái thiết kế AIWF (`workflow_redesign_closed: true`, `final_project_closure_performed: true`).

---

## 3. Governance Standards
- Dynamic discovery via authoritative `skills/` directory.
- Strictly read-only static validation & final audit aggregation (`NOT_A_TEST`).
- Zero automated test runner triggers without `TEST_EXECUTION_APPROVAL`.
