<!-- File path: docs/designs/FEAT-098_virtual_filesystem_overlay_blueprint.md -->

---
feature_id: FEAT-098
feature_name: Virtual Filesystem (VFS) Overlay
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-098_virtual_filesystem_overlay_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint – Virtual Filesystem (VFS) Overlay

## Executive Summary
Bản thiết kế kỹ thuật chi tiết dành cho Virtual Filesystem (VFS) Overlay tuân thủ nghiêm ngặt các ADR và chính sách quản trị của AIWF OS.

## Objective
Xây dựng đặc tả chi tiết và giao diện hợp đồng sẵn sàng cho quá trình triển khai mã nguồn.

## Scope
- Triển khai nhân xử lý cốt lõi của Virtual Filesystem (VFS) Overlay.
- Tích hợp vào hệ thống vòng lặp chung.

## Out of Scope
- Các dịch vụ mở rộng bên ngoài nền tảng.

## Responsibilities
- **Architect**: Giám sát tuân thủ thiết kế.
- **Coder**: Triển khai mã nguồn.

## Runtime Layer
Services Layer

## Related ADRs
ADR-026, ADR-030

## Related FEATs
FEAT-098

## Dependencies
Không có phụ thuộc vòng lặp ngoài các phụ thuộc đã định nghĩa tại Master Roadmap.

## Public APIs
- `def init_virtual_filesystem_overlay() -> bool`: Khởi tạo và liên kết module.

## Internal APIs
- `def _execute_virtual_filesystem_overlay_task() -> None`: Xử lý luồng cục bộ.

## Events
- `event_virtual_filesystem_overlay_complete`: Phát hành khi hoàn thành xử lý.

## Commands
- `python workflow_runtime.py execution --feature FEAT-098`

## Runtime Components
- `Virtual Filesystem (VFS) OverlayModule`

## Data Structures
- Định nghĩa schema JSON cấu hình nội bộ.

## State Model
Trạng thái tĩnh được lưu trữ cục bộ dưới cache session.

## State Machine
- `STANDBY` -> `PROCESSING` -> `FINISHED`

## Sequence Diagrams
1. Khởi chạy command
2. Tải cấu hình và khởi tạo module
3. Trả kết quả và thoát tiến trình

## Interaction Diagrams
Tương tác trực tiếp với Event Bus và Observability Module.

## Runtime Flow
- Đọc trạng thái.
- Xử lý tác vụ.
- Ghi log sự kiện.

## Failure Handling
Ném ngoại lệ trực tiếp về máy trạng thái trung tâm để kích hoạt rollback.

## Retry Strategy
Không thử lại trực tiếp; chuyển quyền phục hồi cho lỗi cấp cao.

## Recovery Strategy
Khôi phục dữ liệu từ snapshot session gần nhất.

## Rollback Strategy
Git stash revert và phục hồi SQLite WAL.

## Security Considerations
Chỉ đọc ghi trong thư mục con của session cô lập.

## Performance Considerations
Độ trễ khởi tạo nhỏ hơn 5ms.

## Scalability Considerations
Hỗ trợ mở rộng độc lập qua RPC.

## Observability
Tích hợp nhật ký sự kiện thông qua SQLite Event Journal.

## Logging Requirements
Ghi log định dạng JSONL chuẩn.

## Metrics
- Khởi chạy latency
- Lượng bộ nhớ RAM tiêu thụ

## Configuration
Lưu tại `workflow.config.json`.

## Storage Design
Lưu trữ bảng dữ liệu tương ứng trong SQLite.

## Testing Strategy
- Viết 100% unit tests cho các hàm công khai.

## Acceptance Criteria
- [ ] Chạy thành công test case chuẩn.
- [ ] Phản hồi sự kiện đúng thời gian quy định.

## Definition of Done
- Mã nguồn qua được các Quality Gates và phân tích tĩnh.

## Risks
- Rủi ro trôi lệch biến. Giải pháp: Validate nghiêm ngặt bằng schema.

## Migration Notes
Tự động migrate dữ liệu SQLite.

## Traceability Matrix (ADR → Blueprint)
- ADR liên quan: ADR-026, ADR-030
