# ADR-050: Program D Plugin Signature Verification & MCP

- **Status**: Proposed
- **Program**: Program D
- **Domain**: Ecosystem
- **Related FEATs**: FEAT-112
- **Related Initiatives**: Initiative D1, D2
- **Related Capabilities**: Cap-005
- **Related AIWF v1 ADRs**: ADR-034, ADR-035

## Context & Problem
Quy trình cài đặt kỹ năng của v1 thiếu tính bảo mật chữ ký số và chưa tương thích giao tiếp với các tool ngoài qua Model Context Protocol (MCP).

## Decision
Đóng gói Plugin dưới dạng ZIP có kèm chữ ký số SHA-256. MCP Runtime chạy qua Stdpipe làm cầu nối tích hợp các công cụ bên ngoài.

## Consequences
- **Positive**: Đảm bảo an toàn mã nguồn gói tải về và mở rộng thư viện tool dễ dàng.
- **Negative**: Quy trình đóng gói phức tạp hơn.

## Backward Compatibility
Plugin cũ v1 không có chữ ký số sẽ chạy dưới quyền hạn tối thiểu (legacy isolation mode).
