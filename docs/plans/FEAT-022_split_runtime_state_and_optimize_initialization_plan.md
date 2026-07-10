<!-- File path: docs/plans/FEAT-022_split_runtime_state_and_optimize_initialization_plan.md -->

---
feature_id: FEAT-022
feature_name: Split Runtime State, Optimize Initialize Workflow, and Update Extension
status: reviewed
stage: planning
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../brainstorming/FEAT-022_split_runtime_state_and_optimize_initialization.md
next_artifact: ../designs/FEAT-022_split_runtime_state_and_optimize_initialization_blueprint.md
---

# FEAT-022: Split Runtime State, Optimize Initialize Workflow, and Update Extension

## Objective
- Thiết kế lại và tái cấu trúc hệ thống quản lý trạng thái của AI Workflow Framework nhằm chia nhỏ tệp tin `.session.json` monolit hiện tại thành các tệp tin trạng thái con chuyên biệt trong `.agents/state/`.
- Tối ưu hóa hiệu năng khởi động `initialize-workflow` thông qua cơ chế lưu bộ đệm Project Fingerprint.
- Cập nhật VS Code Extension để hỗ trợ watch thư mục trạng thái con và thực hiện cập nhật giao diện cục bộ (Live UI Update), loại bỏ hiện tượng nhấp nháy hoặc lag.
- Đảm bảo an toàn dữ liệu và tính tương thích ngược hoàn toàn với phiên bản cũ.

## Scope
### Included
- Tạo thư mục `.agents/state/` chứa 8 file JSON con (`context.json`, `workflow.json`, `runtime.json`, `approvals.json`, `usage.json`, `agents.json`, `rules.json`, `recovery.json`).
- Triển khai cơ chế đồng bộ hai chiều (Aggregate & Deconstruct) bảo đảm tương thích ngược với `.agents/.session.json`.
- Cấu hình Project Fingerprint để lưu cache thông tin tĩnh vào `context.json`, tăng tốc khởi tạo.
- Cập nhật phần TypeScript/webview của VS Code Extension để watch thư mục `state/` và ghép ViewModel động.
- Triển khai 5 lệnh CLI mới cho `workflow_runtime.py`.
- Viết 11 kịch bản unit tests phủ đầy đủ các tình huống nghiệp vụ mới.
- Cập nhật 5 file tài liệu hướng dẫn (`AI_RULES.md`, `AGENTS.md`, `README.md`, `USAGE.md`, `CHANGELOG.md`).

### Excluded
- Không chỉnh sửa logic lập lịch tác vụ đa tác nhân (Multi-agent scheduling) bên ngoài việc cập nhật trạng thái runtime.
- Không thay đổi các Skill nghiệp vụ khác không liên quan trực tiếp đến quản lý trạng thái.

## Project Impact
- **Modules & Services**: CLI Engine (`workflow_runtime.py`) và Visualizer Extension.
- **Database & Cache**: Cập nhật cách thức cache và ghi đĩa trạng thái, không thay đổi cấu trúc bảng SQLite.
- **UI**: Visualizer Dashboard Extension (webview).
- **Configuration**: Cấu trúc thư mục `.agents/state/`.

## Dependencies
- POSIX `rename` và cơ chế file lock hiện tại trên hệ thống để đảm bảo ghi nguyên tử.
- Node.js/VS Code API hỗ trợ watch thư mục.

## Risks
- **Tranh chấp ghi (Concurrent Write)**: Nhiều tiến trình ghi đè cùng lúc -> *Biện pháp giảm thiểu*: Sử dụng cơ chế File locking (`SessionLock`) độc quyền khi thay đổi trạng thái.
- **Lệch trạng thái (State Drift)**: File session.json và các file con bị mất đồng bộ -> *Biện pháp giảm thiểu*: Kích hoạt cơ chế kiểm tra Timestamp/Hash tự động sửa ngược khi có sự thay đổi ngoài luồng.

## Acceptance Criteria
- [ ] Thư mục `.agents/state/` chứa đủ 8 file JSON sau khi chạy khởi tạo thành công.
- [ ] Xoá `.session.json` và chạy lệnh CLI bất kỳ sẽ tự động khôi phục lại `.session.json` chính xác.
- [ ] Thời gian chạy khởi tạo lần 2 mất dưới 50ms khi fingerprint không đổi.
- [ ] Visualizer UI tự cập nhật live progress mà không cần load lại thông tin metadata tĩnh của dự án.
- [ ] Bộ 11 unit tests chạy thành công 100%.

## Deliverables
1. Tệp mã nguồn cập nhật cho `workflow_runtime.py` (CLI subcommands & state sync engine).
2. Thư mục mã nguồn cập nhật cho Visualizer Extension (`extensions/visualizer/src/`).
3. Bộ unit tests mới trong `skills/workflow-runtime/tests/`.
4. Tài liệu hướng dẫn cập nhật (`AI_RULES.md`, `AGENTS.md`, `README.md`, `USAGE.md`, `CHANGELOG.md`).

## Estimated Complexity
- **Medium**: Đòi hỏi sửa đổi đồng thời cả CLI Python và TypeScript Extension, đảm bảo đồng bộ hoàn hảo giữa hai môi trường.

## Recommended Blueprint Focus
- Chú trọng thiết kế chi tiết thuật toán Đồng bộ hai chiều (Bi-directional Sync Algorithm) và cách tính Project Fingerprint trong Blueprint.
- Đặc tả chi tiết cơ chế watch folder và ghép ViewModel của Extension.

## Recommended Next Skill
/blueprint
