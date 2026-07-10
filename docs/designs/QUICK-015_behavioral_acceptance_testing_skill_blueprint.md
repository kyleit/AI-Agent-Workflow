---
artifact_type: blueprint
feature_id: QUICK-015
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – Behavioral Acceptance Testing (BAT) Skill

## 1. Proposed Code Changes

### [skills/skill-self-verification/scripts/verify_skill.py](file:///Volumes/Kyle/AgentsProject/skills/skill-self-verification/scripts/verify_skill.py)
- **Operation**: MODIFY
- **Responsibility**: Nâng cấp toàn diện bộ giả lập tương tác BAT và định dạng xuất báo cáo.
- **Changes**:
  - **Persona Generation**: Tích hợp hàm `generate_personas(skill_name)` để tạo ra các personas người dùng mô phỏng thực tế.
  - **Conversation Simulation**: Xây dựng kịch bản hội thoại động chân thực (Simulated User Sessions & Conversation Transcript), mô phỏng cách người dùng đặt câu hỏi, trả lời prompt, gate đồng ý/từ chối.
  - **Before vs After Detection**: 
    - Dùng `git diff` hoặc phân tích `git log` để tự động phát hiện xem Skill có bị sửa đổi hay không.
    - Nếu có sửa đổi, trích xuất sự thay đổi chính để tạo mục so sánh "Before vs After" chi tiết.
  - **Metrics Evaluation**:
    - **UX Review**: Đánh giá trải nghiệm tương tác của Skill.
    - **Productivity Impact**: Ước tính thời gian tiết kiệm (ví dụ: 15-30 phút).
    - **Token Impact**: Ước tính input/output tokens và chi phí.
  - **Report Generation**: Định dạng lại báo cáo markdown xuất ra để chứa đầy đủ các chương mục bắt buộc:
    - *Original Goal*
    - *Simulated User Sessions*
    - *Conversation Transcript*
    - *Expected Behaviour*
    - *Actual Behaviour*
    - *Before vs After*
    - *Improvements Achieved*
    - *Remaining Problems*
    - *UX Review*
    - *Productivity Impact*
    - *Token Impact*
    - *Final Recommendation*

### [skills/skill-self-verification/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/skill-self-verification/SKILL.md)
- **Operation**: MODIFY
- **Responsibility**: Cập nhật mô tả hoạt động BAT của Skill trong catalog tài liệu.
- **Changes**:
  - Sửa đổi phần Mục tiêu & Trách nhiệm để nhấn mạnh vai trò thực hiện Behavioral Acceptance Testing.
  - Cập nhật định dạng báo cáo đầu ra mong đợi.

---

## 2. Target Folder Structure
Không thay đổi cấu trúc thư mục hiện tại.

---

## 3. Interface & Data Contracts
Không thay đổi giao diện CLI của script `verify_skill.py`. Vẫn giữ nguyên lệnh:
`python skills/skill-self-verification/scripts/verify_skill.py verify --skill <skill-name>`

---

## 4. Algorithms & Key Logic

### BAT Simulation Algorithm:
1. Đọc metadata từ `SKILL.md` để trích xuất `name` và `description`.
2. Tạo 2-3 personas phù hợp (ví dụ: Dev, Lead Architect, QA).
3. Sử dụng mẫu hội thoại động để mô phỏng tương tác:
   - Bước 1: Người dùng gõ lệnh gọi skill.
   - Bước 2: Skill phản hồi và đưa ra các câu hỏi/lựa chọn.
   - Bước 3: Người dùng chọn các options và phản hồi gates.
   - Bước 4: Skill hoàn thành và xuất kết quả.
4. Chạy `git diff` đối với thư mục `skills/<skill_name>` để lấy thông tin Before vs After.
5. Tính toán các chỉ số Token/UX/Productivity dựa trên độ phức tạp của Skill.
6. Kết xuất báo cáo markdown hoàn chỉnh.

---

## 5. Validation Rules
- Báo cáo xác thực được lưu tại `docs/verification/SKILL-VERIFY_<skill_name>.md`.
- Báo cáo bắt buộc phải chứa cụm từ `# Skill Verification Report:` ở dòng đầu và có đầy đủ tất cả các chương mục BAT.
- Chỉ PASS khi hành vi giả lập nghiệm thu thành công.

---

## 6. Implementation Checklist
- [ ] Cập nhật tệp `verify_skill.py` với logic BAT hoàn chỉnh.
- [ ] Cập nhật tệp `SKILL.md` của `skill-self-verification`.

---

## 7. Verification & Test Plan

### Automated Tests
- Chạy unit tests:
  `PYTHONPATH=skills/workflow-runtime/scripts pytest skills/workflow-runtime/tests/`

### Manual Verification
- Chạy thử:
  `python3 skills/skill-self-verification/scripts/verify_skill.py verify --skill skill-self-verification`
- Kiểm tra báo cáo được tạo ra tại [SKILL-VERIFY_skill-self-verification.md](file:///Volumes/Kyle/AgentsProject/docs/verification/SKILL-VERIFY_skill-self-verification.md) để verify đầy đủ các chương mục BAT.
