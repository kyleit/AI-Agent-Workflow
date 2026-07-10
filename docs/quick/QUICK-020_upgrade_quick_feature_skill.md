<!-- File path: docs/quick/QUICK-020_upgrade_quick_feature_skill.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-020
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Upgrade quick-feature Skill

## 1. Feature Goal
Nâng cấp kỹ năng phát triển nhanh (quick-feature skill) dựa trên đánh giá từ QUICK-018. Mục tiêu là nâng cao chất lượng của tài liệu Đặc tả Mini Spec (Quick Feature specification) để sẵn sàng triển khai ngay lập tức, nhưng vẫn đảm bảo tính gọn nhẹ, tránh biến nó thành một tài liệu Động não cồng kềnh.

## 2. Scope
- **In Scope**:
  - Cập nhật tệp [skills/quick-feature/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/quick-feature/SKILL.md):
    - Khai báo phiên bản nâng lên `3.2.0`.
    - Bổ sung vào khuôn mẫu đầu ra các phần bắt buộc mới:
      1. **Backward Compatibility**: Mô tả hành vi hiện tại được bảo toàn, yêu cầu tương thích, và lưu ý di chuyển.
      2. **Blast Radius**: Xác định các Kỹ năng, Runtime, Extension, Memory, Tài liệu, và Scripts bị ảnh hưởng cùng mức độ tác động.
      3. **File Change Scope**: Phân nhóm rõ ràng các file thành: Modify, Create, Optional, Do Not Modify để thiết lập biên giới thực thi.
      4. **Acceptance Criteria**: Sinh các tiêu chí nghiệm thu có thể truy vết, mỗi tiêu chí tham chiếu tới Requirement ID và Expected test.
      5. **Success Metrics**: Các chỉ số đo lường (không lỗi hồi quy, tương thích ngược, token tiết kiệm, độ trễ tối ưu).
      6. **Self Verification**: Quy định xác minh tự động bắt buộc sau triển khai (so sánh Trước vs Sau, regression test, downstream workflow check).
      7. **Quick Feature Justification**: Giải thích lý do tác vụ đủ điều kiện phát triển nhanh thay vì chu trình SDLC đầy đủ (complexity, scope, risk).
    - Cải tiến phần phân định Scope rõ ràng: In Scope, Out of Scope, Not Modified, Future Work.
    - Quy tắc tương thích hạ nguồn: Khi nhắc tới Lập kế hoạch, Thiết kế, Kiểm thử, không mặc định bắt buộc chúng phải thay đổi, mà cần xác minh độ tương thích trước và chỉ cập nhật khi cần thiết.
- **Out of Scope**: Sửa đổi logic CLI Python của `workflow_runtime.py`.
