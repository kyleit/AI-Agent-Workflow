<!-- File path: docs/plans/FEAT-046_upgrade_brainstorming_skill_to_v3_plan.md -->

---
feature_id: FEAT-046
feature_name: Upgrade Brainstorming Skill to v3
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-046_upgrade_brainstorming_skill_to_v3.md
next_artifact: ../designs/FEAT-046_upgrade_brainstorming_skill_to_v3_blueprint.md
---

# FEAT-046: Upgrade Brainstorming Skill to v3

## Objective
- **Business objective**: Cải tiến kỹ năng Động não (Brainstorming) từ một công cụ phát hiện yêu cầu đơn thuần thành một bộ máy phân tích tri thức chủ chốt (Master Requirement Discovery). Giảm thiểu tối đa việc lặp lại phân tích kiến trúc, rủi ro, và phạm vi tại các pha lập kế hoạch (Plan) và thiết kế kỹ thuật (Blueprint) ở hạ nguồn.
- **Expected outcome**: Tiết kiệm tối thiểu 15-25% số lượng mã thông báo (tokens) tiêu thụ cho toàn chu trình SDLC của mỗi tính năng thông qua việc tái sử dụng tri thức có cấu trúc đã phân tích ở pha đầu.

## Scope
### Included
- Nâng cấp tệp hướng dẫn [skills/brainstorming/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming/SKILL.md) bổ sung 14 mục phân tích mới bao gồm phạm vi, phân tích tài sản có sẵn, vùng ảnh hưởng, nguyên tắc thiết kế, KPIs, ma trận rủi ro, khuyến nghị ADR và kiểm thử sơ bộ.
- Tinh giản tệp hướng dẫn [skills/brainstorming-to-plan/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming-to-plan/SKILL.md) để Planner chỉ tập trung vào phân chia giai đoạn, lập lịch trình và ước lượng nguồn lực.
- Tinh giản tệp hướng dẫn [skills/plan-to-blueprint/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/plan-to-blueprint/SKILL.md) để Architect thừa hưởng trực tiếp các thiết lập và nguyên tắc kiến trúc từ tài liệu Brainstorming v3.
- Tạo mẫu (Template) và ví dụ tài liệu đầu ra so sánh Trước vs Sau để hướng dẫn mô hình.

### Excluded
- Không sửa đổi mã nguồn CLI của `workflow_runtime.py`.
- Không thay đổi mã nguồn giao diện Visualizer Extension của VS Code.

## Project Impact
- **Modules**: `skills/brainstorming/`, `skills/brainstorming-to-plan/`, `skills/plan-to-blueprint/` (Thay đổi hướng dẫn hoạt động của các agent).
- **APIs**: Không thay đổi.
- **Database**: Không thay đổi.
- **Documentation**: Cập nhật danh sách mô tả kỹ năng trong `SKILLS.md` và `CHANGELOG.md`.

## Dependencies
- Phụ thuộc vào cơ chế nạp và thực thi kỹ năng mặc định của AIWF CLI.

## Risks
- **Risk**: Mô hình AI đời cũ hoặc nhỏ có thể gặp hiện tượng ảo tưởng hoặc bỏ sót các phần phân tích mới do hướng dẫn `SKILL.md` quá dài.
- **Mitigation**: Thiết lập các chỉ dẫn theo bảng cấu trúc ngắn gọn và cung cấp mẫu few-shot ví dụ đầu ra cực kỳ rõ ràng.

## Acceptance Criteria
- [ ] Tệp `skills/brainstorming/SKILL.md` được cập nhật thành công hỗ trợ đầy đủ 14 phần phân tích mới.
- [ ] Tệp `skills/brainstorming-to-plan/SKILL.md` và `skills/plan-to-blueprint/SKILL.md` được tinh giản và loại bỏ phân tích lặp lại thành công.
- [ ] Kiểm thử biên dịch tài liệu brainstorming cũ và mới không bị sập cú pháp.
- [ ] Tài liệu `CHANGELOG.md` được cập nhật.

## Deliverables
- [skills/brainstorming/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming/SKILL.md) (v3 nâng cấp)
- [skills/brainstorming-to-plan/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming-to-plan/SKILL.md) (v3 tối ưu)
- [skills/plan-to-blueprint/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/plan-to-blueprint/SKILL.md) (v3 tối ưu)
- [CHANGELOG.md](file:///Volumes/Kyle/AgentsProject/CHANGELOG.md) cập nhật phiên bản.

## Estimated Complexity
- **Hiệu năng**: Thấp (chỉ thay đổi tệp tin hướng dẫn kỹ năng dạng Markdown, không sửa đổi mã nguồn chạy nền).
- **Phức tạp**: Low-Medium.

## Recommended Blueprint Focus
- Tập trung thiết lập sơ đồ cấu trúc tệp mẫu Brainstorming v3 mới và hướng dẫn các biểu thức regex cho Planner/Architect để kế thừa các phần này một cách hiệu quả nhất.

## Recommended Next Skill
/blueprint
