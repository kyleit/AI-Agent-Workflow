# AIWF Runtime Versioning Policy

Chính sách kiểm soát phiên bản và tương thích ngược của Runtime.

## 1. Nguyên tắc Semantic Versioning
- **Major (X.0.0)**: Thay đổi phá vỡ cấu trúc hợp đồng API v1 (đòi hỏi nâng cấp toàn bộ các Skills).
- **Minor (1.X.0)**: Bổ sung thêm API phụ trợ hoặc tối ưu hoá hiệu năng, giữ nguyên tương thích ngược.
- **Patch (1.0.X)**: Sửa lỗi bảo mật hoặc vá lỗi tranh chấp locks.

## 2. Quy trình Deprecation
Mọi API bị thay thế phải được duy trì cảnh báo `@deprecated` trong ít nhất một phiên bản Minor trước khi bị loại bỏ ở phiên bản Major tiếp theo.
