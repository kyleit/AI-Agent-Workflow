<!-- docs/brainstorming/FEAT-109_distributed_runtime.md -->

---
feature_id: FEAT-109
feature_name: Distributed Runtime & Operations
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-109_distributed_runtime_plan.md
---

# Master Requirement Document – Distributed Runtime & Operations

## Executive Summary
Hệ thống AIWF v2 mở rộng khả năng điều phối tác vụ phân tán trên nhiều cụm máy (multi-node), quản lý GPU pools và chạy qua Kubernetes.

## Background
AIWF v1 chỉ hỗ trợ thực thi trên máy local đơn lẻ, giới hạn khả năng scale tài nguyên khi chạy các tác vụ phân tích lớn.

## Current AIWF v1 Analysis
Nhân Executive Runtime của v1 quản lý tiến trình local độc quyền qua `VirtualProcessManager`.

## Gap Analysis
Thiếu cơ chế liên lạc gRPC và quản lý trạng thái cluster tập trung (fleet management).

## Objectives
Xây dựng nền tảng điều phối cụm máy ảo và phân bổ tiến trình con từ xa.

## Scope
- Điều phối tác vụ qua gRPC.
- Quản lý node registry.

## Out of Scope
- Tự động mua/bán tài nguyên cloud.

## Functional Requirements
- **FR-01**: Đăng ký và theo dõi node remote.
- **FR-02**: Phân bổ tác vụ từ xa theo độ ưu tiên.

## Non-Functional Requirements
- **NFR-01**: Thời gian phản hồi heartbeat node dưới 50ms.

## Architecture Proposal
Sử dụng mô hình Master-Worker. Master điều phối Task Graph và phân phối sang các Remote gRPC Worker Nodes.

## Runtime Components
- `FederationMaster`
- `NodeAgent`

## Data Model
`NodeRegistry` bảng SQLite lưu giữ danh sách IP và trạng thái Node.

## Runtime State
`CLUSTER_INITIALIZING` -> `ACTIVE` -> `FAILOVER`.

## Integration Points
Tích hợp với `VirtualProcessManager` cục bộ của v1 để làm backend cho NodeAgent.

## Public APIs
- `register_node(node_info: dict) -> bool`

## Internal APIs
- `_send_heartbeat() -> None`

## Event Model
- `node_disconnected`: Phát đi khi mất liên lạc node.

## State Machine
- `STANDBY` -> `ACTIVE` -> `UNREACHABLE`

## Sequence Flow
1. Worker đăng ký -> Master chấp thuận.
2. Master phân bổ task -> Worker báo cáo kết quả.

## Security
Mã hóa giao thức gRPC bằng mTLS và xác thực khóa chứng chỉ.

## Performance
Trễ phân phối task nhỏ hơn 15ms.

## Scalability
Hỗ trợ tối đa 100 node chạy song song.

## Fault Tolerance
Tự động chuyển tiếp task sang node backup khi phát hiện node chết.

## Disaster Recovery
Master tự động đồng bộ Task Graph sang node phụ để sẵn sàng tiếp quản (failover).

## Multi-Tenant Considerations
Mỗi tenant được giới hạn số node tối đa có thể thuê thông qua quota.

## Observability
Theo dõi CPU/RAM và băng thông mạng thông qua Prometheus metrics.

## Risks
- Rủi ro mất kết nối mạng giữa chừng. Giải pháp: Queue đệm lưu giữ trạng thái.

## Trade-offs
- Tăng chi phí truyền thông qua mạng đổi lấy khả năng tính toán vượt trội.

## Migration Strategy
AIWF v2 tương thích ngược hoàn toàn bằng cách xem máy local đơn lẻ như Node mặc định.

## Backward Compatibility
Visualizer v1 tiếp tục kết nối trực tiếp với Master thông qua WebSocket.

## Acceptance Criteria
- [ ] Dispatch tác vụ tới Worker thành công.
- [ ] Failover tự động chạy khi tắt Worker.

## Estimated ADR Count
5 ADRs.

## Estimated Blueprint Count
2 Blueprints.

## Estimated Implementation Phases
3 Phases.
