<!-- docs/brainstorming/FEAT-113_microvm_isolation.md -->

---
feature_id: FEAT-113
feature_name: Hardware & Kernel MicroVM Isolation
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-113_microvm_isolation_plan.md
---

# Master Requirement Document – Hardware & Kernel MicroVM Isolation

## Executive Summary
Tăng cường bảo mật cấp hạt nhân (kernel-level) cho AIWF OS v2 bằng việc sử dụng Firecracker microVMs và WASM virtual machines để chạy các mã lệnh không đáng tin cậy.

## Background
Docker sandbox của v1 chia sẻ chung kernel của host OS, dẫn đến nguy cơ leo thang đặc quyền (privilege escalation) từ mã lệnh độc hại.

## Current AIWF v1 Analysis
Sử dụng Docker container thông qua `SandboxContainerProvider`.

## Gap Analysis
Thiếu khả năng cô lập tài nguyên phần cứng cứng và bảo mật cấp ảo hóa phần cứng (hypervisor-level).

## Objectives
Xây dựng lớp điều phối ảo hóa siêu nhẹ có thời gian khởi động dưới 100ms.

## Scope
- Firecracker microVM integration.
- WASM secure execution provider.

## Out of Scope
- Quản lý hạ tầng ảo hóa nặng như VMware hay Proxmox.

## Functional Requirements
- **FR-01**: Khởi chạy lệnh bash độc hại trong microVM cô lập hoàn toàn.
- **FR-02**: Giới hạn cứng số chu kỳ CPU và RAM khả dụng.

## Non-Functional Requirements
- **NFR-01**: Thời gian khởi động microVM dưới 150ms.

## Architecture Proposal
Sử dụng lớp bọc Firecracker CLI chạy song song. Các tác vụ script nhẹ được dịch chuyển sang WASM sandbox để tăng hiệu suất.

## Runtime Components
- `MicroVMOrchestrator`
- `WASMEngine`

## Data Model
Cấu hình cấp phát RAM/CPU dạng JSON tĩnh cho mỗi lớp session sandbox.

## Runtime State
`PROVISIONING` -> `BOOTING` -> `RUNNING` -> `DESTROYED`.

## Integration Points
Thay thế hoàn toàn hoặc chạy song song với `SandboxContainerProvider` của v1.

## Public APIs
- `spawn_secure_microvm(config: dict) -> str`

## Internal APIs
- `_compile_to_wasm(source_code: str) -> bytes`

## Event Model
- `vm_panic`: Phát ra khi máy ảo bị crash kernel.

## State Machine
- `DOWN` -> `BOOTING` -> `UP`

## Sequence Flow
1. Nhận mã nguồn cần thực thi -> Gửi tới microVM hoặc WASM engine.
2. Thực thi -> Trả stdout/stderr về host -> Hủy máy ảo.

## Security
Không chia sẻ chung bất kỳ socket hoặc tài nguyên đĩa nào với host OS.

## Performance
Băng thông I/O ảo đạt 80% hiệu suất đĩa vật lý.

## Scalability
Hỗ trợ khởi chạy đồng thời tới 100 microVMs trên một máy host.

## Fault Tolerance
Tự động ngắt kết nối và giải phóng tài nguyên khi phát hiện lỗi treo vòng lặp vô hạn (infinite loop).

## Disaster Recovery
Khởi tạo lại máy ảo sạch từ snapshot cơ sở trong trường hợp máy ảo cũ bị treo.

## Multi-Tenant Considerations
Mỗi session ID được ánh xạ trực tiếp tới một Firecracker VM riêng.

## Observability
Đo lường thời gian boot kernel của máy ảo và logs hệ thống.

## Risks
- Tăng overhead tài nguyên ram cho mỗi máy ảo. Giải pháp: Sử dụng kernel siêu nhỏ (micro-kernel).

## Trade-offs
- Tăng độ cô lập bảo mật đổi lấy trễ khởi động tăng nhẹ và tiêu thụ RAM nền lớn hơn.

## Migration Strategy
Adapter tự động chuyển cấu hình Docker cũ sang cấu hình microVM tương thích.

## Backward Compatibility
Tương thích ngược hoàn toàn với giao diện Sandbox của v1.

## Acceptance Criteria
- [ ] Chạy mã độc thử nghiệm không làm ảnh hưởng đến tệp tin của host OS.
- [ ] Khởi động máy ảo dưới 150ms.

## Estimated ADR Count
6 ADRs.

## Estimated Blueprint Count
2 Blueprints.

## Estimated Implementation Phases
3 Phases.
