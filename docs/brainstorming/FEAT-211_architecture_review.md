<!-- File path: docs/brainstorming/FEAT-211_architecture_review.md -->

---
feature_id: FEAT-211
feature_name: Session Runtime Redesign Architecture Review
status: reviewed
stage: brainstorming
created_at: 2026-07-13
updated_at: 2026-07-13
previous_artifact: ./FEAT-211_session_runtime_redesign.md
next_artifact: ../plans/FEAT-211_session_runtime_redesign_plan.md
---

# Architecture Review Report – Session Runtime Redesign (FEAT-211)

## 1. Executive Summary
- **Review Date**: 2026-07-13
- **Feature ID**: FEAT-211
- **Review Target**: Session Runtime Redesign v2.0.0
- **Status**: **READY_FOR_PLANNING**
- **Architecture Consistency Score**: **95/100**
- **Final Requirement Readiness Score**: **92/100**

---

## 2. Core Architecture Validation
Kiến trúc phân lớp gồm 6 Layers đã được rà soát và xác nhận tính đúng đắn:
1. **Session Runtime Core** là nhân thực thi chính (In-process execution core), quản lý vòng đời đóng mở của một workflow session.
2. **Resident Service** và **Background Job Host** nằm hoàn toàn ở Layer 6 (Optional Host Layer). Chúng hoạt động như các adapters/controllers và không can thiệp vào mô hình chạy đơn phiên in-process mặc định.
3. **Daemon không còn là dependency bắt buộc**: Nhà phát triển có thể chạy trọn vẹn workflow AIWF đa agent trực tiếp qua CLI/IDE mà không cần khởi động bất kỳ daemon nào chạy ngầm.
4. **Logical Agent**: Đã xác nhận Agent là đối tượng in-memory nhẹ, chạy bất đồng bộ trên Event Loop, không tạo thêm OS process hay thread nào độc lập.

---

## 3. FEAT Boundary & Dependency Assessment
Bộ phân rã 14 tính năng (`FEAT-211` đến `FEAT-224`) được đánh giá là hợp lý và mạch lạc:

### Đồ thị phụ thuộc (Dependency Graph):
```text
FEAT-211 (Session Core) ──> FEAT-212 (State WAL)
                              │
                              ▼
                        FEAT-213 (Logical Agent) & FEAT-214 (Context Engine)
                              │
                              ▼
                        FEAT-215 (Scheduler & Pool) ──> FEAT-216 (Tool Executor)
                                                          │
                                                          ▼
                                                    FEAT-217 (Permission Boundary)
                                                          │
                                                          ▼
                                                    FEAT-218 & 219 (API & SDK v3)
                                                          │
                                                          ▼
                                                    FEAT-220 & 221 (Migration Layer & CLI)
                                                          │
                                                          ▼
                                                    FEAT-222 & 223 (Bg & Resident Hosts)
                                                          │
                                                          ▼
                                                    FEAT-224 (Certification Suite)
```
- **Đánh giá ranh giới**: Không có FEAT nào bị phình to quá mức hoặc có dependency vòng tròn (circular dependency). `FEAT-224` (Certification Suite) nằm ở bước cuối cùng là điểm chốt chặn tích hợp tự động cho toàn bộ hệ thống mới.

---

## 4. Migration Strategy Validation
- **Compatibility Layer**: SDK và API cũ (v1/v2) giao tiếp với CLI sẽ được định tuyến thông qua một **Compatibility Bridge** sử dụng JSON-RPC cục bộ.
- **Visualizer & CLI**: Hỗ trợ cơ chế tự động spawn một ephemeral session nếu không phát hiện daemon đang hoạt động, tránh breaking changes cho các phiên bản visualizer cũ.
- **State Files**: Các tệp JSON tĩnh đĩa (`context.json`, `workflow.json`) tiếp tục được đồng bộ định kỳ (write-behind flush) để giữ tính tương thích dữ liệu đĩa.

---

## 5. Resource Safety & Boundary Enforcement
- **Process Boundary**: Chốt chặn `patched_Popen` tại Layer 4 (Tool Executor) sẽ quét và kiểm duyệt stacktrace của toàn bộ lệnh gọi subprocess ngoài. Nếu phát hiện luồng gọi trực tiếp từ Agent/Skill khác, Runtime lập tức dừng phiên để bảo vệ sandbox.
- **Conocurency Limits**: Worker Pool kiểm soát nghiêm ngặt qua asyncio Semaphore (max active tasks = M) để tránh cạn kiệt CPU/RAM.
- **Subprocess Cleanup**: Sử dụng Process Group ID (PGID) chuyên biệt thông qua `os.setsid()` để dọn dẹp sạch 100% child process tree con cháu khi gặp timeout hoặc cancel.

---

## 6. Key Remaining Risks & Mitigation

| ID | Risk Description | Level | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **R-01** | Treo Event Loop do CPU-heavy tasks của Python | High | Bắt buộc offload các hàm parse AST/hash sang ThreadPool. |
| **R-02** | Xung đột ghi đè dữ liệu (Multi-session write conflict) | Medium | Áp dụng khóa tệp tin vật lý ngắn hạn kết hợp SQLite WAL journaling. |
| **R-03** | Lỗi rò rỉ phân quyền (Permission Mode Leakage) | Medium | Sử dụng scoped context và task-level token, cấm ghi đè file session chung. |

---

## 7. Required Architectural Decisions (Decided)
- **IPC Protocol**: Thống nhất sử dụng cổng local WebSocket/HTTP (`127.0.0.1:8765`) để giao tiếp CLI/Visualizer thay thế cho Unix Domain Sockets để đảm bảo chạy mượt mà trên cả Windows.
- **Worker Pool Core**: Chọn **Option B (Async + ThreadPool)** làm nhân cốt lõi cho các Agent nội bộ tin cậy, kết hợp **Option C (Process Isolation)** động cho các Plugins/Scripts không tin cậy.

---

## 8. Planning Prerequisites (Tiền đề cho Planning)
Trước khi tiến hành tạo Implementation Plan cho `FEAT-211`:
1. Phê duyệt chính thức báo cáo Architecture Review này.
2. Đóng băng các API v1/v2 hiện tại trong codebase để phục vụ việc thiết lập bộ test suite đối sánh.
3. Chuẩn bị file thiết kế schema SQLite WAL phục vụ Event Store.

---
**Review Decision**: **APPROVED FOR PLANNING**  
*Hệ thống đã đạt độ chín kiến trúc và sẵn sàng bước vào Phase 3 (Planning).*
