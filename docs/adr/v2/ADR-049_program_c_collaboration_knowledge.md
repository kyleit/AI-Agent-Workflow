# ADR-049: Program C Distributed File Locking & Knowledge Graph

- **Status**: Proposed
- **Program**: Program C
- **Domain**: Collaboration
- **Related FEATs**: FEAT-111
- **Related Initiatives**: Initiative C1, C2
- **Related Capabilities**: Cap-004
- **Related AIWF v1 ADRs**: ADR-025, ADR-027

## Context & Problem
Môi trường đa tác nhân cộng tác song song dễ gây tranh chấp ghi đè tệp tin và thiếu mô hình liên kết dependency chéo repo.

## Decision
Thiết lập WorkspaceLockManager lưu trữ danh sách khóa tệp trên SQLite và đồ thị quan hệ CodeDB lưu trữ edges/nodes phụ thuộc chéo.

## Consequences
- **Positive**: Ngăn chặn hoàn toàn xung đột ghi đè tệp tin và hiển thị dependency trực quan.
- **Negative**: Nguy cơ deadlock khóa tệp chéo.

## Backward Compatibility
Visualizer v1 hiển thị các tệp bị khóa dưới dạng read-only.
