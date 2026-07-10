<!-- File path: docs/quick/QUICK-021_upgrade_plan_to_blueprint_skill.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-021
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Upgrade plan-to-blueprint Skill

## 1. Feature Goal
Nâng cấp kỹ năng thiết kế kỹ thuật (plan-to-blueprint skill) để tệp tin Blueprint đầu ra trở thành một Hợp đồng triển khai (Implementation Contract) hoàn chỉnh, giúp subagent lập trình mã nguồn có thể thực thi ngay lập tức mà không cần suy luận thiết kế bổ sung. Ngoài ra, Architect cũng sẽ xuất thêm tệp JSON cấu trúc của bản thiết kế (`FEAT-XXX_blueprint.json`) để phục vụ các đại lý kiểm thử và triển khai hạ nguồn nạp nhanh.

## 2. Scope
- **In Scope**:
  - Cập nhật tệp [skills/plan-to-blueprint/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/plan-to-blueprint/SKILL.md):
    - Khai báo phiên bản nâng lên `3.2.0`.
    - Bổ sung vào khuôn mẫu đầu ra các phần phân tích bắt buộc mới:
      1. **Complete Class & Module Design**: Mô tả chi tiết trách nhiệm của class, public/internal methods, dependencies, constructor parameters, visibility, extension points.
      2. **Detailed Interface Contracts**: Tham số truyền vào, kiểu trả về, ngoại lệ (exceptions), quy tắc validation, và tính tương thích ngược.
      3. **Configuration Schema**: Schema hiện tại và mới, quy tắc di chuyển, mặc định, quy tắc validation, và tương thích ngược.
      4. **Database & Storage Design**: Chi tiết các bảng, chỉ mục, quan hệ, ràng buộc, chiến lược di chuyển và rollback dữ liệu.
      5. **Cache Architecture**: Khóa cache, quy tắc hủy bỏ (invalidation), TTL, thuật toán băm (hash strategy), phiên bản hóa nhà cung cấp, kiểm tra dữ liệu cũ, warmup, cleanup.
      6. **Error Model**: Định nghĩa các exceptions dự kiến, trigger, chiến lược khôi phục, retry policy, fallback và ghi log.
      7. **Skill Integration Contracts**: Định nghĩa rõ các before/after hooks, runtime calls, cấu trúc trao đổi dữ liệu, và kết quả mong đợi.
      8. **CLI & Runtime Contracts**: Mô tả cú pháp CLI, tham số truyền vào, dữ liệu trả về, exit codes, và hành vi lỗi.
      9. **Sequence Flows**: Mô tả luồng chạy thông thường, cache miss, nhà cung cấp không sẵn sàng, di chuyển chỉ mục bằng chuỗi văn bản (tránh vẽ Mermaid).
      10. **Security & Safety**: Ranh giới thư mục làm việc (workspace boundary), xác thực đường dẫn, giới hạn ghi file, an toàn rollback, và quy tắc hộp cát.
      11. **Complete Test Matrix**: Áp dụng ma trận ánh xạ từ yêu cầu → các loại test (unit, integration, compatibility, regression, performance, stress, end-to-end tests).
      12. **Requirement Traceability**: Mở rộng truy vết Requirement → Planning Task → Blueprint Component → Implementation Module → Tests → Verification → Release.
      13. **File-Level Implementation Contracts**: Purpose, owner, inputs, outputs, dependencies, implementation notes, risks cho mỗi file.
    - Hướng dẫn Architect tự động tạo thêm tệp tin có cấu trúc máy đọc `docs/designs/FEAT-XXX_feature_slug_blueprint.json` chứa các thông số: `modules`, `classes`, `interfaces`, `files`, `dependencies`, `sequence_flows`, `configuration`, `database`, `tests`, `risks`, `implementation_contracts`.
  - Cập nhật tệp `skills/blueprint-to-implementation/SKILL.md` và các Skill hạ nguồn để ưu tiên nạp và đọc tệp `FEAT-XXX_blueprint.json` thay vì tệp Markdown khi triển khai để giảm token và tăng tốc độ xử lý.
- **Out of Scope**: Thay đổi logic validation checkpoint trong mã nguồn CLI `workflow_runtime.py`.
