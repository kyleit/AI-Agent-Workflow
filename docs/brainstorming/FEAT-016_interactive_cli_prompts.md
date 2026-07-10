<!-- File path: docs/brainstorming/FEAT-016_interactive_cli_prompts.md -->

---
artifact_type: brainstorm
feature_id: FEAT-016
feature_name: Interactive CLI Prompts via IDE UI
status: active
---

# Feature Brainstorming – Tương Tác CLI & Quy Trình Qua Giao Diện IDE (FEAT-016)

## 1. Bối cảnh & Vấn đề
Hiện tại, trong toàn bộ quy trình phát triển phần mềm AI, việc tương tác giữa AI Agent và Ba tại các "cổng duyệt" (Approval Gates) hoặc chuyển đổi Skill (Skill Suggestion Gates) chủ yếu dựa trên giao diện dòng lệnh văn bản:
- AI Agent in ra `Confirm to continue? Y / N` hoặc liệt kê các lựa chọn `Option 1, 2, 3` và bắt Ba phải gõ chữ/số để phản hồi.
- Khi chạy các kịch bản CLI (`workflow_runtime.py`), việc nhập liệu qua `input()` của Python rất dễ gây nghẽn tiến trình của Agent và không tận dụng được giao diện trực quan của IDE.

## 2. Mục tiêu & Phạm vi (Scope)
- **Mục tiêu**: Thay thế toàn bộ các thông báo nhập liệu thủ công (Y/N, chọn nhánh, chọn Skill, xác nhận code...) bằng giao diện bảng chọn trực quan (`ask_question` modal UI) của IDE trên toàn bộ các Skill và chính sách cốt lõi của dự án.
- **Phạm vi (Scope)**:
  - **Trong phạm vi (In Scope)**:
    - Chỉ hỗ trợ chế độ chọn duy nhất một phương án (Single-select) cho tất cả các câu hỏi tương tác (như Y/N, chọn nhánh Git, chọn Skill tiếp theo).
    - Thiết lập cơ chế tự động phát hiện tính khả dụng của công cụ `ask_question` và tự động chuyển đổi dự phòng (fallback) về văn bản chat truyền thống nếu chạy trên client/IDE cũ hoặc terminal thuần.
  - **Ngoài phạm vi (Out of Scope)**: Hỗ trợ chọn nhiều phương án cùng lúc (Multi-select / Checkbox) cho các tác vụ phức tạp (như tích chọn nhiều tệp tin để commit).

## 3. Giải pháp Kỹ thuật Lựa chọn: Giải pháp A (Chặn đầu ra CLI)

Sau khi thảo luận và thống nhất với Ba, chúng ta sẽ chọn **Giải pháp A (Chặn đầu ra CLI và chuyển đổi sang công cụ IDE)** vì tính chất gọn nhẹ, an toàn và không yêu cầu mở cổng kết nối mạng.

### A. Định dạng thông điệp tương tác từ CLI (Structured Output)
Khi CLI Python (`workflow_runtime.py`) cần người dùng chọn, nó sẽ xuất ra stdout một định dạng có cấu trúc XML/JSON đặc biệt:
```xml
<interactive_prompt type="select">
  {
    "question": "Chọn chế độ cấp quyền không gian làm việc:",
    "options": ["Sandbox Mode", "Full Access Mode", "Unrestricted Mode"]
  }
</interactive_prompt>
```

### B. Cơ chế bắt sự kiện của AI Agent (IDE Agent Bridge)
- Khi AI Agent chạy CLI và nhận diện thẻ `<interactive_prompt>`, Agent sẽ tạm dừng phân tích thông tin thông thường.
- Agent phân tách nội dung JSON bên trong thẻ và tự động thực hiện gọi công cụ native `ask_question` của IDE.

### C. Cơ chế phản hồi kết quả vào CLI (Response Loop)
- Sau khi Ba click chọn phương án trên giao diện và nhấn **Submit**, Agent nhận được giá trị kết quả.
- Agent sẽ truyền kết quả đó trở lại cho tiến trình CLI thông qua luồng `stdin` (Sử dụng công cụ `manage_task` với action `send_input` to feed input to the CLI process).

### D. Các giải pháp thay thế đã xem xét (Alternative Solutions)
* **Giải pháp B (Local API Server)**: Thiết lập WebSocket/REST API Server trong CLI để trao đổi với Extension của VS Code.
  - *Lý do loại bỏ*: Quá phức tạp và yêu cầu mở cổng kết nối trên máy tính, tăng rủi ro bảo mật.
* **Giải pháp C (File Watching)**: CLI ghi câu hỏi ra file tạm và IDE theo dõi file để hiển thị giao diện.
  - *Lý do loại bỏ*: Có độ trễ nhất định khi đọc/ghi đĩa và dễ bị xung đột file tạm nếu chạy song song.

## 4. Kịch bản Áp Dụng (Use Cases)
- **Git Branch Select**: Ba click chọn nhánh muốn làm việc từ danh sách hiển thị (Single-select).
- **Verify / Go-No-Go Gate**: Ba chọn `Proceed` để phát hành phiên bản mới hoặc chọn `Abort` để hủy.
- **Skill Suggestion Gate**: Sau khi kết thúc một Skill, Agent gợi ý các Skill tiếp theo dưới dạng bảng chọn để Ba click chạy tiếp.

## 5. Câu hỏi thảo luận đã làm rõ
1. **Có cần hỗ trợ Multi-select không?**
   - *Trả lời*: Không, hiện tại chỉ cần Single-select để giải quyết các cổng rẽ nhánh quy trình.
2. **Trải nghiệm gõ tay dự phòng**:
   - *Trả lời*: Bảng chọn trực quan của IDE đã hỗ trợ sẵn tùy chọn "Other (write your answer)" để Ba gõ nội dung tùy chỉnh khi cần thiết.
3. **Quản lý trạng thái CLI**:
   - *Trả lời*: CLI Python sẽ ở trạng thái chờ nhập dữ liệu (blocking stdin read) cho đến khi Agent nhận được phản hồi từ Ba và gửi nó thông qua `send_input`.
4. **Trường hợp IDE không hỗ trợ công cụ `ask_question` (ví dụ: client cũ hoặc terminal thuần)?**
   - *Trả lời*: Hệ thống sẽ tự động phát hiện việc không hỗ trợ tool và kích hoạt cơ chế fallback. Agent sẽ in câu hỏi dưới dạng văn bản thuần trong khung chat như trước đây, Ba nhập tay câu trả lời, và Agent sẽ gửi câu trả lời đó vào CLI. Quy trình vẫn tiếp tục trôi chảy không bị báo lỗi hay gián đoạn.
