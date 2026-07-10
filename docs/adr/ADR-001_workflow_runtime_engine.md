<!-- File path: docs/adr/ADR-001_workflow_runtime_engine.md -->

# ADR-001: Decoupling Workflow Runtime Logic into Executable CLI Engine

## Status
Proposed

## Related Feature
FEAT-010

## Context
Hiện tại, toàn bộ logic cập nhật trạng thái phiên chạy trong tệp `.session.json`, kiểm tra checkpoint, chẩn đoán lỗi git/workspace, tính toán token ngữ cảnh, và tạo báo cáo nhịp tim (heartbeat) đều được mô tả bằng ngôn ngữ tự nhiên trong phần chỉ dẫn prompt của 26 kỹ năng. 
Điều này dẫn đến các vấn đề nghiêm trọng:
1.  **Dung lượng Token quá lớn**: Các chỉ dẫn prompt lặp đi lặp lại hàng trăm dòng quy tắc ở mỗi kỹ năng làm phình to không gian ngữ cảnh (context window).
2.  **Khó bảo trì**: Mỗi lần cập nhật cấu trúc hoặc sửa đổi hành vi cập nhật của tệp `.session.json`, chúng ta phải sửa thủ công 26 kỹ năng, dễ gây ra sự không đồng bộ.
3.  **Hạn chế mở rộng**: Khó tích hợp trực tiếp các công cụ kiểm soát trạng thái này vào MCP Server hoặc các IDE Extensions (như VS Code API) do logic nằm hoàn toàn trong Claude prompt.

## Decision
Chúng ta sẽ tách biệt hoàn toàn phần xử lý logic điều khiển (Runtime engine) ra khỏi Claude prompt và đóng gói thành một công cụ dòng lệnh (CLI Runtime Engine) viết bằng Python nằm dưới `skills/workflow-runtime/scripts/`.

Các kỹ năng sẽ không còn mô tả cách chỉnh sửa tệp JSON, thay vào đó chỉ gọi trực tiếp các lệnh CLI:
*   `runtime start`
*   `runtime step`
*   `runtime complete`
*   `runtime fail`

Mã nguồn Python sẽ được chia nhỏ thành các mô-đun chuyên biệt (session, checkpoint, context, heartbeat, drift, validator, utils) với giới hạn tối đa 200 dòng/tệp.

## Alternatives Considered

### Option A: Giữ nguyên logic trong Claude Prompt
*   *Lý do bác bỏ*: Tốn token, khó nâng cấp, nguy cơ mô hình cập nhật sai cấu trúc tệp `.session.json` phá vỡ extension UI.

### Option B: Viết một tập lệnh Python đơn nhất (Monolith Script)
*   *Lý do bác bỏ*: Vi phạm nguyên tắc thiết kế mã sạch và quy tắc giới hạn tối đa 200 dòng mỗi tệp nguồn trong dự án.

## Trade-offs
*   **Điểm tốt (Pros)**:
    *   Tối ưu hóa token vượt trội (~3,000 tokens mỗi lần nạp kỹ năng).
    *   Kiểm soát lỗi tập trung, chống ghi lỗi tệp `.session.json`.
    *   Dễ dàng đóng gói thành MCP Tool hoặc Go/Node CLI trong tương lai nhờ giao diện CLI API độc lập ngôn ngữ.
*   **Điểm yếu (Cons)**:
    *   Đòi hỏi máy chạy phải cài đặt Python 3.9+ (đã được đảm bảo bằng quy tắc Bootstrap).

## Consequences
Tất cả các kỹ năng sẽ trở nên vô cùng gọn nhẹ, chỉ tập trung mô tả đặc tả pha (Inputs, Outputs, Checklists) và gọi CLI để quản lý phiên chạy.

## Risks
*   **Rủi ro**: Lỗi thực thi CLI Python trên môi trường Windows (do ký tự xuống dòng CRLF hoặc quyền thực thi tập lệnh).
*   **Mitigation**: Tích hợp các kiểm thử tự động (Unit Tests) chạy đa nền tảng và kiểm tra sức khỏe thông qua `doctor.ps1`.
