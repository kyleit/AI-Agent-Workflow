# ADR-052: Cross-Program Shared Contracts

- **Status**: Proposed
- **Program**: Cross-Program
- **Domain**: Governance
- **Related FEATs**: FEAT-109, FEAT-110, FEAT-111, FEAT-112, FEAT-113
- **Related Initiatives**: All
- **Related Capabilities**: All
- **Related AIWF v1 ADRs**: ADR-028, ADR-046

## Context & Problem
Cần một giao thức bao bì chung (message envelope) và mã lỗi thống nhất cho toàn bộ các giao tiếp chéo giữa 5 chương trình của AIWF v2.

## Decision
Mọi thông điệp RPC đều được bọc trong cấu trúc Correlation ID chung. Mã lỗi sử dụng chung namespace lỗi từ Core của v1.

## Consequences
- **Positive**: Giảm tải việc tự định nghĩa cấu trúc dữ liệu và dễ dàng debug phân tán chéo node.
- **Negative**: Yêu cầu tất cả các bên tuân thủ schema nghiêm ngặt.

## Backward Compatibility
Tương thích ngược với các mã lỗi tiêu chuẩn của AIWF v1.
