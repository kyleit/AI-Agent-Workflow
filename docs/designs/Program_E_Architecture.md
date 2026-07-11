# Program E Architecture – Secure Execution Platform

## 1. Vision & Responsibilities
Ảo hóa cô lập tuyệt đối ở mức phần cứng/kernel bằng việc sử dụng Firecracker microVMs và WASM engines.

## 2. Scope & Out of Scope
- **Scope**: Firecracker virtualization, WASM compilation and execution.
- **Out of Scope**: OS hypervisor cluster administration.

## 3. Topologies (Runtime, Component, Service, Deployment)
- **Runtime Topology**: Kernel boots in microVM for executing untrusted code block.
- **Component Topology**: `MicroVMOrchestrator` ──> `Firecracker_CLI` ──> `WASM_Sandbox`.
- **Service Topology**: VM provisioning service, VM cleanup service.
- **Deployment Topology**: Hypervisor virtualization extensions required on host CPU.

## 4. Execution Flow & Lifecycle
`PROVISION` -> `BOOT` -> `RUN` -> `TEARDOWN`.

## 5. Interface & APIs
- `execute_in_microvm(script: str) -> str`
- `execute_wasm(bytecode: bytes) -> str`

## 6. Storage & Concurrency
- **Storage Model**: Ephemeral disk snapshots destroyed on VM shutdown.
- **Concurrency & Consistency**: Complete kernel separation; strong resource limit enforcement.

## 7. Fault Tolerance & Security
- **Fault Tolerance**: VM panic terminates process immediately.
- **Security**: Root file system mounted as read-only.

## 8. Observability & Risks
- **Observability**: Boot timing and memory consumption logs.
- **Risks**: Virtualization support missing on host CPU. Mitigated by running Docker fallback.
