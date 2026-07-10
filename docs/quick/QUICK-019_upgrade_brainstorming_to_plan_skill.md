<!-- File path: docs/quick/QUICK-019_upgrade_brainstorming_to_plan_skill.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-019
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Upgrade brainstorming-to-plan Skill

## 1. Feature Goal
Nâng cấp kỹ năng Lập kế hoạch (planning skill) từ một công cụ tạo lịch trình dự án đơn thuần thành một Bộ máy hoạch định thực thi (Execution Planning Engine) mạnh mẽ. Tài liệu Kế hoạch thực hiện mới sẽ cung cấp đầy đủ thông tin chi tiết về độ bao phủ yêu cầu, vai trò thực thi, thứ tự chạy song song/tuần tự, vùng ảnh hưởng tập tin, sự chuẩn bị cho Blueprint, chiến lược test/rollback, và đặc biệt là sinh thêm định dạng JSON có cấu trúc (`FEAT-XXX_plan.json`) để các đại lý hạ nguồn đọc hiểu tức thì với chi phí token tối thiểu.

## 2. Scope
- **In Scope**:
  - Cập nhật tệp [skills/brainstorming-to-plan/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming-to-plan/SKILL.md):
    - Khai báo phiên bản nâng lên `3.2.0`.
    - Bổ sung chỉ dẫn sinh tài liệu Kế hoạch thực hiện Markdown mới với 11 phần phân tích tri thức:
      1. **Requirement Coverage Matrix**: Áp dụng ánh xạ Requirement ID → Phase → Task → Deliverable để đảm bảo mọi FR được cài đặt chính xác 1 lần và phát hiện yêu cầu bị bỏ sót.
      2. **Task Ownership**: Phân bổ từng Task cụ thể cho các vai trò: Architect, Coder, Reviewer, Verifier, Documentation, Runtime.
      3. **Parallel Execution Plan**: Phân loại các tác vụ tuần tự, song song, blocking, độc lập, và nhóm chúng lại thành các nhóm thực thi khuyến nghị.
      4. **File Change Plan**: Định vị biên giới tác động cho mỗi tác vụ: Create, Modify, Delete, Do Not Modify.
      5. **Blueprint Preparation**: Định nghĩa trước các Interfaces, Classes, Modules, Provider Pattern, Data Flow, Sequence Flow, Migration Strategy, và Testing Architecture cho pha Blueprint kế thừa.
      6. **Verification Strategy**: Xác định Unit Tests, Integration Tests, Compatibility Tests, Regression Tests, Performance Tests cho từng giai đoạn và map tới từng task.
      7. **Exit Criteria**: Đặt các cổng hoàn thành đo lường được cho mỗi phase (tests pass, memory updated, v.v.).
      8. **Rollback Strategy**: Định nghĩa rollback trigger, rollback steps, recovery method cho mỗi phase lớn.
      9. **Change Impact Matrix**: Ma trận ánh xạ từ Task → Files → Modules → Runtime → Extension → Documentation → Memory → Database.
      10. **Artifact Production Plan**: Chỉ định rõ các artifact sinh ra sau mỗi phase (Blueprint, ADR, Memory, Release Notes, CHANGELOG).
      11. **Token & Execution Optimization**: Ước tính chi phí chạy tuần tự, cơ hội chạy song song, số lượng token tiết kiệm được và chiến lược thực thi tối ưu.
    - Hướng dẫn Planner tự động tạo thêm tệp tin có cấu trúc máy đọc [docs/plans/FEAT-XXX_feature_slug_plan.json](file:///Volumes/Kyle/AgentsProject/docs/plans/) chứa các thông số: `phases`, `tasks`, `dependencies`, `parallel_groups`, `owners`, `files`, `risks`, `tests`, `artifacts`.
  - Cập nhật tệp [skills/plan-to-blueprint/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/plan-to-blueprint/SKILL.md) và các Skill hạ nguồn để ưu tiên nạp và đọc tệp `FEAT-XXX_plan.json` thay vì tệp Markdown khi phân tích kế hoạch để giảm token và tăng tốc độ xử lý.
- **Out of Scope**: Thay đổi logic validation checkpoint trong mã nguồn CLI `workflow_runtime.py`.
