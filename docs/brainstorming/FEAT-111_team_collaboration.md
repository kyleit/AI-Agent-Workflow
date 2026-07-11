<!-- docs/brainstorming/FEAT-111_team_collaboration.md -->

---
feature_id: FEAT-111
feature_name: Collaboration & Knowledge Graph
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-111_team_collaboration_plan.md
---

# Master Requirement Document – Collaboration & Knowledge Graph

## Executive Summary
Hỗ trợ không gian làm việc chia sẻ (Shared Workspace), xác thực vai trò RBAC và liên kết đồ thị tri thức mã nguồn đa kho lưu trữ.

## Background
Môi trường v1 chỉ tối ưu cho một lập trình viên duy nhất trên một repo cục bộ độc lập.

## Current AIWF v1 Analysis
Cô lập thư mục dạng phẳng thông qua `ContextIsolationManager`.

## Gap Analysis
Thiếu mô hình phân quyền thao tác file chéo và đồng bộ hóa tri thức giữa nhiều dự án.

## Objectives
Xây dựng graph DB SQLite quan hệ đa chiều và cơ chế khóa file động phân tán.

## Scope
- Shared workspace locks.
- SQLite Graph DB.

## Out of Scope
- Tích hợp Git hosting server riêng.

## Functional Requirements
- **FR-01**: Khóa tệp tin khi có agent khác đang chỉnh sửa.
- **FR-02**: Truy vấn liên kết dependency chéo repo.

## Non-Functional Requirements
- **NFR-01**: Thời gian lock file dưới 10ms.

## Architecture Proposal
Sử dụng phân vùng cơ sở dữ liệu đồ thị phi tập trung tích hợp trong SQLite của Event Journal.

## Runtime Components
- `WorkspaceLockManager`
- `KnowledgeGraphEngine`

## Data Model
Bảng `edges` và `nodes` trong SQLite biểu diễn quan hệ import chéo repo.

## Runtime State
`LOCKING` -> `INDEXING` -> `RESOLVING`.

## Integration Points
Tích hợp với `EventJournal` để ghi nhận các giao dịch khóa file.

## Public APIs
- `acquire_file_lock(file_path: str, user_id: str) -> bool`

## Internal APIs
- `_build_cross_references() -> None`

## Event Model
- `file_locked`: Phát ra khi tệp tin bị khóa.

## State Machine
- `UNLOCKED` -> `LOCKED` -> `SYNCING`

## Sequence Flow
1. Agent A xin khóa tệp -> Thành công.
2. Agent B cố gắng ghi tệp -> Bị chặn cho đến khi Agent A release.

## Security
Chỉ cho phép sửa tệp nếu vai trò (RBAC) được cấu hình có quyền Write.

## Performance
Truy vấn đồ thị sâu 3 cấp dưới 20ms.

## Scalability
Hỗ trợ tới 50 repo liên kết cùng lúc.

## Fault Tolerance
Tự động nhả lock khi phát hiện agent bị crash hoặc mất heartbeat quá 30 giây.

## Disaster Recovery
Tự động tái lập cấu trúc lock trên RAM từ Event Journal khi khởi động lại.

## Multi-Tenant Considerations
Mỗi tenant sở hữu một keyspace đồ thị tri thức riêng biệt.

## Observability
Hiển thị đồ thị quan hệ phụ thuộc dạng trực quan hóa trên Visualizer.

## Risks
- Deadlock khóa file chéo. Giải pháp: Đặt thời gian timeout tự động nhả khóa.

## Trade-offs
- Tăng độ phức tạp quản trị tệp tin đổi lại tính an toàn khi cộng tác nhóm.

## Migration Strategy
Tự động chạy script migrate để tạo các bảng quan hệ SQLite mới.

## Backward Compatibility
Visualizer v1 hiển thị các tệp tin khóa dưới dạng read-only bình thường.

## Acceptance Criteria
- [ ] Khóa tệp hoạt động chính xác trên 2 session song song.
- [ ] Tìm liên kết dependency chéo dự án thành công.

## Estimated ADR Count
6 ADRs.

## Estimated Blueprint Count
3 Blueprints.

## Estimated Implementation Phases
3 Phases.
