<!-- File path: docs/quick/QUICK-018_upgrade_brainstorming_skill_to_v3_1.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-018
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Upgrade Brainstorming Skill to v3.1

## 1. Feature Goal
Nâng cấp kỹ năng Động não (Brainstorming Skill) lên phiên bản v3.1. Tính năng này bổ sung thêm các phần phân tích cấu trúc nâng cao để biến tài liệu Động não thành tài liệu tri thức chủ chốt có thẩm quyền duy nhất (single authoritative requirement document), giúp Planner và Architect ở hạ nguồn kế thừa trực tiếp mà không cần phân tích lại. Đồng thời, áp dụng chính sách cấm tuyệt đối sinh ra đường dẫn tuyệt đối (absolute paths) trong mẫu tài liệu Động não để tuân thủ AI_RULES.md.

## 2. Scope
- **In Scope**:
  - Bổ sung các mục phân tích mới vào `skills/brainstorming/SKILL.md`:
    1. **Requirement Traceability Matrix**: Bảng ma trận ánh xạ Requirement ID, Priority, Related Blueprint Section, Expected Tests, và Acceptance Criteria.
    2. **Stakeholder Analysis**: Xác định Stakeholders chính/phụ, hệ thống nội bộ/tích hợp ngoài, impact, priority, benefits.
    3. **Requirement Prioritization (MoSCoW)**: Phân loại Must, Should, Could, Won't cho từng yêu cầu.
    4. **Dependency Graph Preview**: Biểu diễn thứ tự thực hiện bằng cấu trúc Markdown phân tầng thô (không dùng Mermaid).
    5. **Data Flow Preview**: Biểu diễn luồng dữ liệu logic bằng Markdown tương tự.
    6. **Open Decision Register**: Ghi nhận và phân loại các chủ đề chưa giải quyết (Resolved, Pending, ADR Required, Prototype Required, Research Required).
    7. **ROI Analysis**: Tính toán chi phí thực thi ước tính, runtime savings, token reduction, API cost savings, dự kiến điểm hòa vốn và ROI dài hạn.
    8. **Knowledge Update Impact**: Dự báo các phân lớp Project Memory nào sẽ bị thay đổi (summary, architecture, lessons, v.v.).
    9. **Existing Module Analysis**: Mở rộng bảng phân tích mô-đun hiện hành với các cột: Owner, Public APIs, Estimated reuse %, Estimated modifications, và Breaking risk.
    10. **Acceptance Traceability**: Mỗi Acceptance Criterion phải tham chiếu rõ ràng tới Requirement ID tương ứng và các kịch bản test dự kiến.
  - Cập nhật quy tắc mẫu tài liệu Động não: Cấm tuyệt đối sinh ra các đường dẫn tuyệt đối (ví dụ `file:///`, `/Users/`, `C:\`). Mọi liên kết tài liệu trong tệp Markdown đầu ra bắt buộc phải dùng đường dẫn tương đối (relative paths).
  - Tối ưu hóa tệp hướng dẫn `skills/brainstorming-to-plan/SKILL.md` và `skills/plan-to-blueprint/SKILL.md` để đảm bảo nạp trực tiếp dữ liệu v3.1.
- **Out of Scope**:
  - Chỉnh sửa mã nguồn CLI Python của `workflow_runtime.py` hoặc giao diện Extension UI.
