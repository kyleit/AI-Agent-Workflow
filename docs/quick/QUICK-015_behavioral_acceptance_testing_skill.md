---
artifact_type: quick-feature-spec
feature_id: QUICK-015
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Behavioral Acceptance Testing (BAT) Skill

## 1. Feature Goal
Nâng cấp `skill-self-verification` từ việc phân tích cú pháp tĩnh và kiểm tra runtime thông thường thành một công cụ **Behavioral Acceptance Testing (BAT)** hoàn chỉnh. 
Mục tiêu cốt lõi của Skill này là hoạt động như một người dùng cuối giả lập (simulated end user) để trải nghiệm và đánh giá chất lượng hành vi, độ mượt mà của luồng nghiệp vụ, tokens tiêu thụ và chất lượng của bất kỳ Skill nào được tạo mới hoặc sửa đổi trước khi cho phép Release.

## 2. Scope
- **In Scope**:
  - Cải tiến tệp thực thi `verify_skill.py` (hoặc module liên quan) để tích hợp các bước BAT:
    - Đọc mục tiêu ban đầu (Original Goal) từ đặc tả/blueprint của skill cần verify.
    - Tạo các personas người dùng thực tế (realistic user personas).
    - Giả lập đầy đủ cuộc hội thoại (simulated user conversations) bao gồm: trả lời câu hỏi tương tác (interactive questions), lựa chọn options, chấp nhận/từ chối approval gates (accept/reject approval gates).
    - So sánh chi tiết hành vi thực tế (Actual Behaviour) với hành vi mong đợi (Expected Behaviour).
    - Tạo so sánh bắt buộc Trước vs Sau (Before vs After) nếu là Skill được chỉnh sửa.
    - Đánh giá định lượng về UX, chất lượng workflow, hiệu quả tokens sử dụng (token efficiency) và mức độ cải thiện năng suất (productivity improvement).
    - Tạo báo cáo nghiệm thu hoàn chỉnh:
      - Original Goal
      - Simulated User Sessions
      - Conversation Transcript
      - Expected Behaviour
      - Actual Behaviour
      - Before vs After
      - Improvements Achieved
      - Remaining Problems
      - UX Review
      - Productivity Impact
      - Token Impact
      - Final Recommendation (Chỉ PASS nếu người dùng giả lập nghiệm thu thành công về hành vi, không chỉ vì test pass hoặc code build thành công).
  - Cập nhật tài liệu `skills/skill-self-verification/SKILL.md` và index mô tả tương ứng.
- **Out of Scope**:
  - Không thay đổi các thuật toán RAG hoặc core state machine của framework.
