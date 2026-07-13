<!-- File path: docs/reviews/FEAT-211_blueprint_architecture_review.md -->

---
feature_id: FEAT-211
feature_name: FEAT-211 Blueprint Architecture Review
status: reviewed
stage: blueprint-review
created_at: 2026-07-13
updated_at: 2026-07-13
previous_artifact: ../designs/FEAT-211_session_runtime_redesign_blueprint.md
next_artifact: [Implementation (Source Code)](../../)
---

# Architecture Review Report – FEAT-211 Blueprint

## 1. Blueprint Validation Result
Bản vẽ thiết kế kỹ thuật chi tiết (Technical Design Blueprint) của FEAT-211 đã được rà soát tỉ mỉ theo 7 tiêu chí cốt lõi:

### 1.1 Runtime Boundary Validation
- **Xác nhận**: Ranh giới tiến trình (Process Boundary) hoàn toàn khép kín. Chỉ duy nhất `ToolExecutor` được phép spawn OS subprocesses.
- **Không có vi phạm**: Bộ **Runtime Validator** của Layer 4 sử dụng cơ chế vá khẩn cấp `patched_Popen` để quét ngược callstack. Bất kỳ nỗ lực gọi tiến trình OS trực tiếp nào từ Agent/Skill đều bị chặn đứng và ném lỗi `ForbiddenProcessSpawnError` ngay lập tức.
- **Resident Service** chỉ đóng vai trò là một lớp quản lý phiên tuỳ chọn (optional host), hoàn toàn tách biệt khỏi mô hình logical execution.

### 1.2 API & SDK Contract Review
- Định nghĩa đầy đủ 9 API cốt lõi của Session (`create_session`, `load_session`, `resume_session`, `submit_task`, `cancel_session`, `checkpoint`, `close_session`, `query_status`, `stream_events`).
- Giao thức WebSocket JSON-RPC 2.0 và luồng NDJSON event stream được cấu trúc đầu vào/đầu ra tường minh với bộ Error Codes đồng bộ.

### 1.3 State Machine Review
- **Session Lifecycle**: `created` ──> `initializing` ──> `planning` ──> `ready` ──> `running` ──> `waiting_for_tool` ──> `integrating` ──> `verifying` ──> `final_review` ──> `completed/failed/cancelled`.
- **Agent Lifecycle**: `declared` ──> `ready` ──> `scheduled` ──> `executing` ──> `waiting` ──> `completed/failed/cancelled`.
- **Tool Lifecycle**: `requested` ──> `validating` ──> `spawning` ──> `executing` ──> `streaming` ──> `cleaning_pgid` ──> `finished/timed_out/cancelled`.
- **Scheduler Lifecycle**: `idle` ──> `parsing_dag` ──> `queueing` ──> `dispatching` ──> `throttled` (backpressure) ──> `synced`.

### 1.4 Multi-Agent Safety Review
- Đảm bảo tính cô lập tuyệt đối thông qua cơ chế CoW (Copy-on-Write) và Delta Context. Agent này **không** được phép đọc bộ nhớ hoặc delta của Agent khác.
- Cơ chế Optimistic Concurrency Control (OCC) đối chiếu base-hash của snapshot context đảm bảo không xảy ra ghi đè đè dữ liệu.
- Agent chỉ hoạt động trong quyền hạn Task được giao, cấm hoàn toàn hành vi tự nâng quyền (no privilege escalation) hoặc tự ý tạo worker nằm ngoài tầm kiểm soát của Scheduler.

### 1.5 OOM & Resource Prevention Review
Để ngăn ngừa triệt để lỗi OOM từng xảy ra trên v2, Blueprint bổ sung:
- **Memory Watermark**: Khi lượng RAM của tiến trình đạt ngưỡng cảnh báo (Watermark = 80%), Session Runtime kích hoạt chế độ giải phóng cache khẩn cấp (evict old task context).
- **CPU Throttle**: Khi CPU load của máy local vượt ngưỡng 90%, Scheduler tự động đưa hàng đợi vào trạng thái trì hoãn (delay/throttle) để giảm tải.
- **Emergency Shutdown**: Khi RAM đạt ngưỡng Critical (95%), Session thực hiện cưỡng bức tắt khẩn cấp: Gửi tín hiệu `SIGKILL` đồng loạt tới các tiến trình con qua PGID, ghi snapshot hiện tại vào SQLite WAL và thoát CLI an toàn để hệ điều hành giải phóng tài nguyên lập tức.

### 1.6 Migration Safety Review
- Tích hợp **Compatibility Bridge** đón nhận dòng lệnh v1/v2 cũ và chuyển tiếp mượt mà.
- File trạng thái đĩa được đồng bộ bất đồng bộ qua cơ chế ghi đệm (write-behind), đảm bảo IDE Extension và Visualizer phiên bản cũ vẫn đọc được dữ liệu.
- feature flag `experimental_session_runtime` cho phép rollback dứt điểm về nhân daemon cũ nếu xảy ra lỗi.

### 1.7 Testing Completeness Review
- Đầy đủ bộ test pyramid: Unit tests (locks, event_store), Integration (WebSocket IPC, PGID cleanup), Stress (500 agents queue), Chaos (kill daemon giữa session), Recovery (SQLite WAL replay).

---

## 2. Architecture Score

```text
Architecture Score: 97/100
Status: READY_FOR_IMPLEMENTATION
```

---

## 3. Key Remaining Risks
- **R-01**: Khả năng tương thích của cơ chế vá `patched_Popen` trên một số phiên bản Python cũ hơn 3.11.  
  *Biện pháp*: Thiết lập verify strict test ở đầu bộ test để cảnh báo nhà phát triển nâng cấp Python.
- **R-02**: Trễ ghi đệm (write-behind) có thể làm Visualizer hiển thị chậm 1-2 giây so với log in-memory.  
  *Biện pháp*: Sử dụng WebSocket push trực tiếp cho live updates, chỉ dùng file đĩa làm kênh đồng bộ tĩnh.

---

## 4. Required Changes (Đã tích hợp vào Blueprint)
- Bổ sung cấu trúc dữ liệu State Machine của Tool và Scheduler vào tài liệu thiết kế.
- Bổ sung logic Watermark RAM và Emergency Shutdown.

---

## 5. Implementation Prerequisites
1. Phê duyệt chính thức tài liệu Architecture Review này.
2. Tạo nhánh git mới `feature/FEAT-211-session-runtime-redesign` để bắt đầu code.

---

## 6. Final GO / NO-GO Decision
- **Decision**: **GO** (Thông qua thiết kế kỹ thuật, sẵn sàng chuyển sang triển khai mã nguồn).
- Ranh giới tiến trình (Process boundary): Không có vi phạm.
- Các chiến lược OOM, Permission, và Migration đều được phê duyệt.
