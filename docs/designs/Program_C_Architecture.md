# Program C Architecture – Collaboration & Knowledge Platform

## 1. Vision & Responsibilities
Quản lý khóa tệp tin phân tán chéo dự án và liên kết đồ thị tri thức mã nguồn đa kho lưu trữ.

## 2. Scope & Out of Scope
- **Scope**: File locks, dependency mapping, SQLite Graph schema.
- **Out of Scope**: Third-party VCS Hosting services.

## 3. Topologies (Runtime, Component, Service, Deployment)
- **Runtime Topology**: Graph database processes file change events from Event Journal.
- **Component Topology**: `LockManager` ──> `KnowledgeGraph` ──> `EventJournal`.
- **Service Topology**: Lock sync service, Graph query service.
- **Deployment Topology**: Embedded SQLite running locally on workspace.

## 4. Execution Flow & Lifecycle
`ACQUIRE_LOCK` -> `SYNC_GRAPH` -> `RELEASE_LOCK`.

## 5. Interface & APIs
- `lock_file(path: str, agent: str) -> bool`
- `query_dependencies(module: str) -> list`

## 6. Storage & Concurrency
- **Storage Model**: SQLite tables `nodes` and `edges` in CodeDB.
- **Concurrency & Consistency**: Strong consistency for file locks; eventual consistency for graph indexes.

## 7. Fault Tolerance & Security
- **Fault Tolerance**: Hard timeout release of file locks if heartbeats fail.
- **Security**: RBAC verification before lock acquisition.

## 8. Observability & Risks
- **Observability**: Visualizer shows dynamic dependency graphs.
- **Risks**: Circular locks (deadlocks). Mitigated by lock sorting.
