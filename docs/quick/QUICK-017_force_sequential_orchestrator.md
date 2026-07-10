<!-- File path: docs/quick/QUICK-017_force_sequential_orchestrator.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-017
workflow: quick-feature
status: pending
---

# Mini Feature Specification – Force Sequential Orchestrator

## 1. Feature Goal
Khống chế Orchestrator của AIWF chỉ hoạt động ở chế độ chạy tuần tự (Sequential Mode), loại bỏ mọi cơ chế chạy song song để đảm bảo tính toàn vẹn trạng thái và loại bỏ xung đột ghi cơ sở dữ liệu/tệp tin. Thiết lập cơ chế khóa độc quyền `.agents/runtime/orchestrator.lock` có kiểm tra timeout 60 giây và tự động làm mới thời gian lock (heartbeat) định kỳ khi thực hiện bước chạy workflow.

## 2. Scope
- **In Scope**:
  - Buộc `execution_mode` và `recommended_mode` luôn mặc định và chuẩn hóa về `"sequential"`.
  - Giữ các trường tương thích ngược (`parallel_groups`, `running_agents`, v.v.) nhưng giữ `parallel_groups` rỗng và giới hạn `running_agents` tối đa 1 phần tử.
  - Triển khai tệp khóa độc quyền `.agents/runtime/orchestrator.lock` chứa các thông tin: `lock_owner`, `work_item_id`, `skill`, `pid`, `started_at`, `heartbeat_at`.
  - Từ chối thực thi khi phát hiện khóa còn hiệu lực với thông báo: `"Sequential mode active. Another workflow task is already running. Resume or wait for it to finish."`
  - Tự động chuẩn hóa trạng thái cũ từ `"parallel"` sang `"sequential"` khi load session.
- **Out of Scope**:
  - Không thiết kế lại hệ thống chạy song song hay hàng đợi bất đồng bộ nâng cao.
  - Không chỉnh sửa mở rộng giao diện UI phức tạp.
