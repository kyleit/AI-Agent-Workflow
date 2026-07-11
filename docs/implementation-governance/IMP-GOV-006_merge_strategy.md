<!-- File path: docs/implementation-governance/IMP-GOV-006_merge_strategy.md -->

# IMP-GOV-006: Merge Strategy

## Quy chuẩn Triển khai
Tài liệu này thiết lập các ràng buộc kỹ thuật đối với quá trình phát triển mã nguồn dự án.

## 1. Mục tiêu
Quy định chi tiết về Chiến lược gộp code an toàn và tránh gây xung đột để đảm bảo tính an toàn, bảo mật và khả năng phục hồi.

## 2. Nguyên tắc bắt buộc
- Tri triển khai mã nguồn phải bám sát tuyệt đối đặc tả Blueprint của tính năng tương ứng.
- Không tự ý thay đổi API signature hay cấu trúc cơ sở dữ liệu mà chưa được duyệt Design Change Proposal.
- Mọi thay đổi mã nguồn phải đi kèm với unit test bổ sung tương ứng.

## 3. Đánh giá kiểm soát
Tất cả các thay đổi sẽ được chạy qua hệ thống tự động đối soát Quality Gates trước khi gộp vào nhánh chính.
