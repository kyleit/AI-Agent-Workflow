# ADR-047: Program A Distributed Runtime Topology

- **Status**: Proposed
- **Program**: Program A
- **Domain**: Distributed Runtime
- **Related FEATs**: FEAT-109
- **Related Initiatives**: Initiative A1, A2
- **Related Capabilities**: Cap-001
- **Related AIWF v1 ADRs**: ADR-002, ADR-010

## Context & Problem
AIWF v1 chỉ hỗ trợ máy trạng thái đơn node cục bộ. Để thực thi song song đa node, cần một giao thức liên thông Master-Worker đồng bộ đáng tin cậy.

## Decision
Sử dụng mTLS gRPC làm giao tiếp chính. Master duy trì Task Graph và phân phối task sang các NodeAgent từ xa, theo dõi trạng thái qua Heartbeat định kỳ.

## Consequences
- **Positive**: Khả năng mở rộng ngang tốt, phân tách rõ ràng control plane và data plane.
- **Negative**: Tăng overhead truyền thông qua mạng.
- **Risks & Mitigations**: Mất kết nối mạng. Giảm thiểu bằng cách lưu cache local task buffer trên Node.

## Backward Compatibility
Hoàn toàn tương thích ngược bằng cách xem node cục bộ như Node mặc định.
