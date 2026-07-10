# Nhật Ký Thay Đổi Sản Phẩm (Product Changelog)

Tất cả các tính năng mới, cải tiến và sửa lỗi quan trọng của **AI Skill Framework** và **Visualizer Extension** sẽ được cập nhật tại đây theo góc nhìn trải nghiệm người dùng.

---

## [6.5.5] - 2026-07-10

### Tính Năng Mới & Cải Tiến
- **Hiệu ứng tải dữ liệu Shimmer Loader mới**:
  - Giao diện Project và Global Usage trên Dashboard khi chưa tải xong dữ liệu SQLite sẽ hiển thị hiệu ứng vệt sáng quét mượt mà (Shimmer skeleton text loader) cao cấp, không bị chồng đè số liệu workflow hiện tại như trước.
- **Khóa an toàn chống xung đột trạng thái (QUICK-029)**:
  - Bổ sung cơ chế khóa an toàn nguyên tử `state.lock` đa tiến trình kết hợp khả năng tự động giải phóng khóa hết hạn, tránh hoàn toàn lỗi tranh chấp ghi file giữa CLI và Visualizer Extension.
  - Tối ưu hóa ghi file granular: Chỉ cập nhật các tệp tin trạng thái con có sự thay đổi dữ liệu thực sự giúp giảm I/O ổ đĩa và ngăn ngừa ghi đè nhầm lẫn dữ liệu tiến trình song song.

## [6.5.4] - 2026-07-10

### Tính Năng Mới & Cải Tiến
- **Kiểm soát quy trình phê duyệt nghiêm ngặt (Strict Approval Gates)**:
  - Bổ sung cơ chế khóa an toàn: Bắt buộc Agent phải dừng thực thi ngay lập tức và kết thúc lượt làm việc sau mỗi bước khởi chạy (start), tạo bản đặc tả yêu cầu (Spec) hoặc tạo bản thiết kế kỹ thuật (Design Blueprint).
  - Agent sẽ hiển thị rõ thông tin và chỉ được phép tiếp tục khi có phản hồi phê duyệt trực tiếp từ bạn trong chat.

### Sửa Lỗi Quan Trọng
- **Khắc phục lỗi treo dòng lệnh (Deadlock)**:
  - Giải quyết triệt để lỗi thỉnh thoảng bị treo (hang) khi chạy CLI đồng thời với các hoạt động đọc/ghi dữ liệu của Visualizer Extension.
  - Tối ưu hóa cơ chế kết nối cơ sở dữ liệu giúp tăng tốc độ phản hồi và hoạt động mượt mà hơn.

## [6.5.3] - 2026-07-10

### Tính Năng Mới & Cải Tiến
- **Quản lý phiên làm việc thông minh (Split State)**:
  - Thiết kế lại cấu trúc lưu trữ dữ liệu giúp tăng tốc độ đồng bộ hóa real-time giữa các công cụ, giảm thiểu tối đa độ trễ hiển thị tiến trình của Agent.
- **Tự động hóa kiểm soát chất lượng (Quality Gates)**:
  - Tích hợp chốt chặn thông minh giúp tự động quét và kiểm tra chất lượng mã nguồn, tài liệu trước khi xuất bản, ngăn ngừa việc phát hành các phiên bản lỗi.
- **Hệ thống điều phối Agent thông minh**:
  - Tự động phân chia công việc và điều phối các AI Agent lập trình phối hợp nhịp nhàng, đảm bảo sinh mã nguồn đúng cấu trúc nghiệp vụ của dự án.
- **Tối ưu hóa hiệu năng & độ ổn định**:
  - Cải tiến hiệu suất ghi chép dữ liệu của hệ thống, giúp chạy mượt mà ổn định ngay cả dưới tần suất làm việc cao liên tục.
- **Nâng cấp bảo mật đầu vào**:
  - Tự động xác thực mã token bảo mật của từng phiên làm việc để ngăn chặn các yêu cầu AI không hợp lệ hoặc không được cấp phép.
- **Cô lập dữ liệu dự án độc lập**:
  - Lưu trữ dữ liệu lịch sử sử dụng của từng dự án vào cơ sở dữ liệu riêng, tự động gom nhóm và dọn dẹp lịch sử cũ để các dự án không gây ảnh hưởng lẫn nhau.
- **Ràng buộc mã nguồn sạch**:
  - Tự động kiểm tra và giới hạn độ dài của các tệp mã nguồn cốt lõi (dưới 500 dòng) để đảm bảo hệ thống luôn ngắn gọn, dễ nâng cấp và bảo trì.

### Trải Nghiệm Giao Diện (Visualizer Extension v1.0.40)
- **Giao diện Tab hiện đại**:
  - Chia tách rõ ràng giữa màn hình theo dõi tiến độ (Stepper) và màn hình phân tích số liệu API, giúp người dùng dễ dàng bao quát thông tin.
- **Cải thiện hiệu năng vượt trội**:
  - Loại bỏ các tính năng chạy ngầm không sử dụng để giải phóng tài nguyên CPU và RAM cho máy tính của bạn.
  - Sửa lỗi hiển thị trùng lặp, phân tách rõ ràng chi phí của dự án hiện tại (Project Usage) và tổng lịch sử sử dụng (Global Usage).
- **Trải nghiệm cuộn và chọn văn bản mượt mà (Anti-flicker)**:
  - Khắc phục hoàn toàn hiện tượng chớp tắt màn hình khi dữ liệu logs cập nhật liên tục.
  - Tích hợp tính năng **Tự động đóng băng cập nhật UI khi tương tác**: Giúp Ba thoải mái cuộn xem log cũ hoặc bôi đen chọn văn bản (select text) mà không sợ giao diện tự render lại làm mất focus.
  - Tự động lưu và khôi phục chính xác vị trí thanh cuộn.

---

## [6.5.0] - 2026-07-09

### Tính Năng Mới & Cải Tiến
- **Công cụ dòng lệnh tiện ích**:
  - Hỗ trợ gọi nhanh các tính năng đồng bộ hóa dữ liệu trực tiếp từ CLI.
  - Hỗ trợ phím tắt và lệnh viết tắt giúp đồng bộ hóa tài liệu dự án sang Obsidian một cách nhanh chóng.
- **Mini-Plan Đặc Tả Yêu Cầu**:
  - Nâng cấp các mẫu đặc tả tính năng mới và sửa lỗi thành các bản kế hoạch mini hoàn chỉnh, tự động cảnh báo các rủi ro kiến trúc và kiểm tra phụ thuộc.
- **Bắt buộc cấu trúc Skill chuẩn**:
  - Áp dụng quy tắc tự động từ chối các thiết kế sinh kỹ năng (Skill) mới nếu không định nghĩa đầy đủ tệp hướng dẫn sử dụng tiêu chuẩn.

---

## [6.4.0] - 2026-07-09

### Tính Năng Mới & Cải Tiến
- **Bản Thiết Kế Kỹ Thuật Đồng Bộ (Design Blueprint)**:
  - Tự động xuất bản thiết kế hệ thống dưới dạng Markdown và tệp dữ liệu JSON đồng bộ để các Agent lập trình hạ nguồn đọc và triển khai chính xác 100%.
  - Mở rộng chi tiết thiết kế lớp, thiết kế lưu trữ và tích hợp hệ thống.
- **Hỗ trợ tự động hóa hạ nguồn**:
  - Định nghĩa sẵn cấu trúc gói thực thi lập trình giúp các Agent triển khai code tự động hiểu rõ phạm vi chỉnh sửa.

---

## [6.3.0] - 2026-07-08

### Tính Năng Mới & Cải Tiến
- **Hệ thống Quản lý Tri Thức Dự Án (Project Memory)**:
  - Tự động hóa việc phân tích toàn bộ cấu trúc dự án và tạo sơ đồ tri thức tổng quan ngay trong lần chạy đầu tiên.
  - Hỗ trợ cập nhật tri thức gia tăng theo lịch sử thay đổi mã nguồn (Git diff).
- **Bộ máy Tìm kiếm Semantic (RAG Search)**:
  - Tích hợp bộ tìm kiếm ngữ nghĩa giúp các AI Agent truy xuất tài liệu nội bộ cực nhanh và chính xác mà không cần đọc lại toàn bộ mã nguồn.
