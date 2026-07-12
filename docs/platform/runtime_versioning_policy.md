# AIWF Runtime Versioning Policy

Chính sách cập nhật phiên bản đảm bảo tính tương thích ngược cho hệ sinh thái.

## 1. Định dạng phiên bản (Semantic Versioning)
Tuân thủ chuẩn `MAJOR.MINOR.PATCH`:
- **MAJOR**: Thay đổi cấu trúc cơ sở dữ liệu hoặc giao diện Named Pipes phá vỡ tương thích.
- **MINOR**: Thêm tính năng mới không phá vỡ logic cũ.
- **PATCH**: Sửa các lỗi bảo mật hoặc tranh chấp Windows File Locks.
