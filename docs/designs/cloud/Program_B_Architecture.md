# Program B Architecture – Distributed Scheduling

## 1. Vision & Responsibilities
Lập lịch tối ưu hóa chi phí token và phân chia Task Graph chéo các vùng NodeAgent.

## 2. Scope & Out of Scope
- **Scope**: Multi-cluster scheduler, queue priority routes.
- **Out of Scope**: Node local process management.

## 3. Topologies & Services
- **Service Topology**: GlobalScheduler, TaskRouter, CapacityEstimator.
- **Deployment Topology**: Deploy active-active across 3 AWS AZs.

## 4. Interface & APIs
- `POST /api/v1/scheduler/dispatch`
