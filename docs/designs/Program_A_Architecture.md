# Program A Architecture – Distributed Runtime Platform

## 1. Vision & Responsibilities
Xây dựng nền tảng điều phối cụm máy ảo thực thi phân tán phục vụ chạy song song đa tác nhân qua gRPC.

## 2. Scope & Out of Scope
- **Scope**: mTLS gRPC communication, local & remote Node agent setup.
- **Out of Scope**: Public cloud instance autoscaling.

## 3. Topologies (Runtime, Component, Service, Deployment)
- **Runtime Topology**: Master coordinates Task Graph. Worker agents download tasks, execute locally, and stream logs back.
- **Component Topology**: `FederationMaster` ──[gRPC]──> `NodeAgent`.
- **Service Topology**: Heartbeat service, Task dispatch service, Metric streaming service.
- **Deployment Topology**: Master deployed on primary node; Workers deployed on peripheral worker instances.

## 4. Execution Flow & Lifecycle
`REGISTERING` -> `HEARTBEATING` -> `DISPATCHING` -> `EXECUTING` -> `REPORTING`.

## 5. Interface & APIs
- `register_worker_node(ip: str, capacity: int) -> str`
- `stream_worker_logs(worker_id: str) -> Stream`

## 6. Storage & Concurrency
- **Storage Model**: SQLite DB local storage for Node Agent state.
- **Concurrency & Consistency**: Local task locks via SQLite WAL; eventual consistency for node cluster states.

## 7. Fault Tolerance & Security
- **Fault Tolerance**: Automatic task rescheduling to active worker when a heartbeat times out.
- **Security**: Strict mTLS encryption with custom certificate authority.

## 8. Observability & Risks
- **Observability**: Prometheus metrics for CPU/RAM usage and round-trip network latency.
- **Risks**: Network split partition. Mitigated by keeping local offline task buffers.
