<!-- File path: docs/designs/FEAT-109_distributed_runtime_blueprint.md -->

---
feature_id: FEAT-109
feature_name: Distributed Runtime Platform
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-109_distributed_runtime_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Distributed Runtime Platform

## 0. Baseline Context & References
- **Memory Baseline**: Baseline v1 architecture frozen.
- **RAG Query Summaries**: Found gRPC client-server patterns in knowledge runtime.
- **Inspected Source Files**: Checked `remote_execution_federation_platform.py` and `virtual_process_manager.py`.

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation (Create/Modify/Delete/Rename) | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/remote_execution_federation_platform.py` | MODIFY | Coder | ADR-047 | Thấp. Không phá vỡ giao tiếp cục bộ |
| `skills/workflow-runtime/scripts/node_agent_registry.py` | NEW | Architect | ADR-047 | Không có rủi ro chéo |

## 2. Target Folder Structure
```text
.
└── skills
    └── workflow-runtime
        └── scripts
            ├── remote_execution_federation_platform.py
            └── node_agent_registry.py
```

## 3. Complete Class & Module Design
- **Class / Module Name**: `NodeAgentRegistry`
  - **Responsibilities**: Quản lý ghi nhận trạng thái và địa chỉ các remote workers.
  - **Constructor Parameters**: `db_path: str`
  - **Public Methods**: `def register_worker(self, worker_id: str, capacity: int) -> bool`
  - **Internal Methods**: `def _verify_mtls_cert(self) -> bool`

## 4. Detailed Interface Contracts
- **API Signature**: `register_worker(worker_id: str, capacity: int) -> bool`
  - **Parameters**: `worker_id` (string định danh duy nhất), `capacity` (số lượng slots tối đa)
  - **Return Types**: `bool` (Thành công/Thất bại)

## 5. Configuration Schema
- **Defaults & Validation**: `{"port": 8765, "mtls_enabled": true}`.

## 6. Database & Storage Design
- **Tables**: Bảng `nodes` trong database SQLite `.agents/runtime/nodes.db`.

## 7. Cache Architecture
- **Cache Keys**: `worker_node:{worker_id}`.
- **TTL**: 60 giây.

## 8. Error Model
- **Exception Class**: `ConnectionError`
  - **Trigger Condition**: Mất kết nối gRPC quá 3 lần heartbeat.
  - **Recovery Strategy**: Gọi hàm reschedule các task sang Node dự phòng.

## 9. Skill Integration Contracts
- **Skill Name**: `workflow-runtime`
  - **Runtime Calls**: Gọi registry mỗi khi scheduler DAG phân bổ tác vụ.

## 10. CLI & Runtime Contracts
- **Command Syntax**: `python workflow_runtime.py register-node --ip 127.0.0.1`

## 11. Sequence Flows
1. Worker Agent kích hoạt -> Gửi gRPC request `register_worker`.
2. Master xác thực mTLS -> Lưu vào Registry -> Phản hồi kết quả.

## 12. Security & Safety
- **Workspace Boundary**: Chỉ ghi nhận cấu hình thuộc thư mục `.agents/runtime/`.
- **Path Validation**: Chặn mọi ký tự escape `../` trong tên node.

## 13. Complete Test Matrix
| Requirement ID | Test Type (Unit/Integration/Compatibility/Regression/Performance/Stress/E2E) | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Unit Test | `skills/workflow-runtime/tests/unit/test_node_agent_registry.py` | `node_agent_registry.py` | `self.assertTrue(res)` |

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `NodeAgentRegistry` -> `node_agent_registry.py` -> `test_node_agent_registry.py` -> Verified -> Released.

## 15. File-Level Implementation Contracts
- **File**: `skills/workflow-runtime/scripts/node_agent_registry.py`
  - **Purpose**: Lưu trữ danh sách worker node và sức chứa tác vụ.
