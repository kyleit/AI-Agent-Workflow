---
name: cross-skill-validation
description: Direct cross-skill validation governance skill for the AI Engineering Workflow framework. Validates end-to-end integration, schema compatibility, enum alignment, authority matrix, artifact identity propagation, and invalidation rules across all AIWF skills.
role: CROSS_SKILL_VALIDATION_GOVERNANCE
version: 3.15.0
canonical_entrypoint: false
on_demand: true
---

# Cross-Skill Validation Governance Skill

## 1. Overview
Skill này chịu trách nhiệm quản trị và thực thi kiểm tra tính tương thích liên Skill (Cross-Skill Validation) cho toàn bộ 45 Skills thuộc hệ thống AI Engineering Workflow Framework (AIWF v3.15.0).

---

## 2. Core Capabilities
1. **Producer/Consumer Inventory Validation**: Đảm bảo 100% tệp đầu ra (output artifacts) của Skill producer đều có Skill consumer tiếp nhận và xử lý hợp lệ.
2. **Schema & Field Compatibility**: Kiểm tra tính khớp kiểu dữ liệu, bắt buộc/tùy chọn, định dạng và enum giữa các schema.
3. **Authority & Gate Alignment**: Xác minh 9 loại phê duyệt độc lập và 23 cổng đánh giá (readiness gates) được duy trì đúng tên gọi và ranh giới thẩm quyền.
4. **Artifact Identity & Invalidation Propagation**: Đảm bảo chuỗi định danh mã Full SHA-256 và tín hiệu hủy hiệu lực (invalidation) được truyền xuyên suốt qua toàn bộ 14 phase canonical.
5. **Cross-Skill Route Simulations**: Thực hiện 9 bài mô phỏng luồng xuôi không có tác dụng phụ (no-side-effect dry-runs) và 20 bài kiểm tra luồng cấm (negative-path cases).

---

## 3. Governance Standards
- Dynamic discovery via authoritative `skills/` directory.
- Strictly read-only static validation & no-side-effect simulations (`NOT_A_TEST`).
- Zero automated test runner triggers without `TEST_EXECUTION_APPROVAL`.
