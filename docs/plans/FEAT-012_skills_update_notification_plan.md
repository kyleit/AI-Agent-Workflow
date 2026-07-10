<!-- File path: docs/plans/FEAT-012_skills_update_notification_plan.md -->

---
feature_id: FEAT-012
feature_name: Skills Auto-Update Notification
status: reviewed
stage: planning
created_at: 2026-07-06
updated_at: 2026-07-06
previous_artifact: ../brainstorm/FEAT-012_skills_update_notification.md
next_artifact: ../designs/FEAT-012_skills_update_notification_blueprint.md
---

# FEAT-012: Skills Auto-Update Notification

## Objective
- **Mục tiêu doanh nghiệp**: Giúp các nhà phát triển sử dụng công cụ luôn nhận biết được khi nào có phiên bản Kỹ năng AI (AI Skills) hoặc biểu mẫu CLI (CLI templates) mới được phát hành để cập nhật kịp thời, tránh các lỗi cũ đã sửa.
- **Định nghĩa thành công**: 
  - Visualizer Extension tự động kiểm tra phiên bản bất đồng bộ ngay khi panel mở ra.
  - Hiển thị thông báo (sticky banner) thân thiện ở góc trên giao diện Webview Dashboard nếu phiên bản cục bộ cũ hơn phiên bản phát hành trên GitHub.
  - Hỗ trợ nút nhấn cập nhật nhanh để chạy lệnh cập nhật tự động trong Terminal mà người dùng không phải gõ lệnh thủ công.

## Scope

### Included
- **Đọc phiên bản cục bộ**: Đọc tệp `.agents/MANIFEST.json` trong thư mục làm việc hiện tại khi VS Code Extension được kích hoạt.
- **Truy vấn phiên bản từ xa**: Thực hiện gọi API HTTP GET bất đồng bộ (không chặn luồng chính) tới địa chỉ GitHub chứa tệp `MANIFEST.json` gốc:
  `https://raw.githubusercontent.com/kyleit/AI-Agent-Workflow/main/MANIFEST.json`
- **So sánh phiên bản**: So sánh cú pháp SemVer của phiên bản từ xa với phiên bản cục bộ.
- **Thiết kế Giao diện Thông báo (Frontend Webview)**:
  - Thiết kế một Sticky Warning Banner màu vàng premium/glassmorphism nằm ở trên cùng của Dashboard.
  - Hiển thị thông điệp dạng: `✨ Có phiên bản AI Skill Framework mới: vX.Y.Z (Hiện tại: vA.B.C). [Cập nhật ngay]`
- **Hành động cập nhật nhanh**:
  - Khi nhấn `[Cập nhật ngay]`, Webview gửi tin nhắn (postMessage) về VS Code Extension.
  - Extension tự động mở một VS Code Integrated Terminal và chạy lệnh `./update.sh` (trên macOS/Linux) hoặc `.\update.ps1` (trên Windows).

### Excluded
- Không tự động cập nhật code ngầm mà không có sự đồng ý hoặc click chuột của lập trình viên (vi phạm chính sách Approval Gate).
- Không thực hiện các cuộc gọi mạng đồng bộ làm đơ hoặc chậm quá trình khởi động Panel Dashboard của Visualizer Extension.

## Project Impact
- **Modules ảnh hưởng**:
  - **Visualizer Extension** (`extensions/visualizer/`): Thêm cơ chế kiểm tra mạng và giao diện hiển thị banner.
- **Tác động chéo**: Không làm ảnh hưởng đến hiệu năng hoạt động của các CLI command độc lập (`aiwf`).

## Dependencies
- Phụ thuộc vào kết nối Internet để fetch thông tin từ GitHub (cần có cơ chế timeout hợp lý là 3 giây để tránh treo khi offline).
- Yêu cầu cài đặt Visualizer Extension của IDE.

## Risks
- **Rủi ro**: Lỗi mạng hoặc bị chặn tường lửa/proxy khi gọi API GitHub raw content làm đơ giao diện.
- **Giảm thiểu**: Thiết lập giới hạn thời gian chờ (Timeout) tối đa 3 giây, bỏ qua thông báo lỗi mạng một cách êm thấm (silent catch) và không hiển thị banner nếu kết nối thất bại.

## Acceptance Criteria
- Khi mở panel Visualizer:
  - Nếu phiên bản cục bộ nhỏ hơn phiên bản trên GitHub (ví dụ local là `2.12.5` và GitHub là `2.13.0`), Dashboard phải hiển thị banner thông báo.
  - Nếu phiên bản cục bộ bằng hoặc lớn hơn phiên bản trên GitHub, Dashboard hoàn toàn không hiển thị banner.
- Khi click vào liên kết hoặc nút `[Cập nhật ngay]`, VS Code Terminal phải được tạo ra và chạy đúng lệnh `./update.sh` hoặc `.\update.ps1`.
- Quá trình kiểm tra phiên bản phải chạy bất đồng bộ hoàn toàn, không làm trễ việc hiển thị các chỉ số Token/Checkpoint hiện tại trên Dashboard.

## Deliverables
- Sửa đổi `extensions/visualizer/src/extension.ts` để đọc manifest và fetch github raw metadata.
- Sửa đổi `extensions/visualizer/resources/webview.html` & `extensions/visualizer/src/webviewHtml.ts` để hiển thị sticky banner và đăng ký cơ chế gửi/nhận message cập nhật.
- Viết test case giả lập (Mocking) dữ liệu manifest mạng để xác minh logic.

## Estimated Complexity
- **Low**: Tác vụ chủ yếu liên quan đến thao tác gọi HTTP GET trong Node.js và render thêm một phần tử HTML trên Webview của Extension.

## Recommended Next Skill
/blueprint
