# ADR-051: Program E Secure MicroVM Sandboxing

- **Status**: Proposed
- **Program**: Program E
- **Domain**: Security
- **Related FEATs**: FEAT-113
- **Related Initiatives**: Initiative E1, E2
- **Related Capabilities**: Cap-002
- **Related AIWF v1 ADRs**: ADR-037, ADR-043

## Context & Problem
Docker container dùng chung kernel của host OS dễ bị leo thang quyền hạn từ mã nguồn không đáng tin cậy.

## Decision
Triển khai ảo hóa cấp hypervisor siêu nhẹ thông qua Firecracker microVMs và WASM virtual machines cho các tác vụ script.

## Consequences
- **Positive**: Cô lập tuyệt đối phần cứng và an toàn cho máy host.
- **Negative**: Tăng lượng tiêu thụ tài nguyên RAM.

## Backward Compatibility
Fallback về Docker sandbox của v1 nếu CPU host không hỗ trợ công nghệ ảo hóa phần cứng.
