<!-- File path: docs/quick/QUICK-022_upgrade_plan_to_blueprint_skill_v3_2.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-022
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Upgrade plan-to-blueprint Skill to v3.2

## 1. Feature Goal
Nâng cấp kỹ năng thiết kế kỹ thuật (plan-to-blueprint skill) để đồng bộ hóa 100% thông tin giữa hai định dạng Markdown và JSON. Tệp tin thiết kế sẽ chứa đầy đủ thông tin chi tiết về hợp đồng thiết kế lớp, thiết kế kho lưu trữ, các lệnh CLI, tích hợp, đặc tả file, ma trận kiểm thử tự động, và đặc biệt là sinh gói triển khai thực thi có cấu trúc JSON (`implementation_packages` trong `blueprint.json`) để các đại lý lập trình có thể thực thi ngay lập tức mà không cần tự suy luận thiết kế.

## 2. Scope
- **In Scope**:
  - Cập nhật tệp [skills/plan-to-blueprint/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/plan-to-blueprint/SKILL.md):
    - Khai báo phiên bản nâng lên `3.2.0` (giữ nguyên để hoàn tất đặc tả).
    - Thắt chặt tính đồng bộ thông tin (Blueprint JSON Parity): tệp `blueprint.json` phải chứa đầy đủ mọi thông tin cấu trúc biểu diễn trong Markdown (modules, classes, methods, configuration, database, cache, error model, sequence flows, skill integration, CLI, files, risks, tests, traceability, artifacts).
    - Bổ sung chỉ dẫn sinh Class Contracts hoàn chỉnh cho tất cả các lớp cốt lõi: responsibilities, constructor, public/internal methods, dependencies, extension points, lifecycle, state ownership.
    - Mở rộng thiết kế Storage Design: tables, indexes, relationships, constraints, migrations, rollback, data ownership, expected growth, maintenance strategy.
    - Mở rộng đặc tả CLI: syntax, arguments, examples, outputs, exit codes, failure modes.
    - Mở rộng Skill Integration: before/after hooks, runtime API calls, data exchanged, expected side effects, rollback behavior.
    - Bổ sung File-Level Contracts: purpose, owner, inputs, outputs, dependencies, implementation notes, risks, validation checklist.
    - Mở rộng Test Matrix: Unit, Integration, Compatibility, Regression, Performance, Stress, End-to-End.
    - Hướng dẫn tự động tạo gói triển khai thực thi `implementation_packages` trong tệp JSON chứa: task id, module, read_set, write_set, dependencies, implementation notes, verification, rollback, expected outputs.
- **Out of Scope**: Thay đổi logic CLI Python của `workflow_runtime.py`.
