<!-- File path: docs/quick/QUICK-031_resident_orchestrator_status_display.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-031
workflow: quick-feature
status: pending
---
# Mini Plan & Feature Specification – Resident Orchestrator Status Display in VS Code Visualizer Extension

## 1. Feature Goal
Hiển thị trạng thái hoạt động của Resident Orchestrator (Daemon chạy nền) trực tiếp trên giao diện của Visualizer VS Code Extension, giúp Ba dễ dàng theo dõi hệ thống đang `RUNNING`, `STOPPED` hay `DRAINING` kèm các thông tin như PID, Heartbeat gần nhất mà không cần chạy dòng lệnh CLI thủ công.

## 2. Quick Feature Justification
Giải thích lý do tác vụ đủ điều kiện phát triển nhanh thay vì chu trình SDLC đầy đủ:
- **Estimated Complexity**: Low (Chỉ thêm một component hiển thị nhỏ trên UI Webview của Extension và bổ sung hàm đọc file trạng thái tĩnh ở Backend Extension).
- **Implementation Scope**: Single module (Visualizer VS Code Extension).
- **Architectural Impact**: Low (Tận dụng cơ chế đọc file JSON trạng thái sẵn có của Extension, không thay đổi cấu trúc dữ liệu hay logic của Core Runtime).
- **Risk Level**: Low (Không can thiệp vào tiến trình Resident Orchestrator gốc).
- **Justification**: Tính năng bổ sung UI hiển thị trạng thái tĩnh nhẹ nhàng, phạm vi ảnh hưởng hẹp và cực kỳ an toàn.

## 3. Scope Boundary
- **In Scope**:
  - Đọc tệp trạng thái tĩnh `.agents/state/orchestrator.json` từ VS Code Extension Backend (`extension.ts`).
  - Gửi thông tin trạng thái qua Webview IPC (`postMessage`).
  - Hiển thị widget trạng thái Resident Orchestrator trên Webview UI (`webview.html`) bao gồm: Trạng thái (Running/Stopped), PID, thời gian Heartbeat cuối cùng.
  - Sử dụng cơ chế lắng nghe sự kiện thay đổi file của VS Code (`vscode.workspace.createFileSystemWatcher`) hoặc Polling tần suất thấp (3 giây/lần) để cập nhật trạng thái thời gian thực mà không làm tăng CPU/RAM.
- **Out of Scope**:
  - Không cho phép Start/Stop Orchestrator từ giao diện Visualizer (để tránh rủi ro bảo mật và quyền hạn).
  - Không thay đổi logic ghi log hoặc cơ chế heartbeat của Resident Orchestrator daemon.
- **Not Modified**:
  - Core Python Runtime (`workflow_runtime.py`, `autonomous_orchestrator.py`).
- **Future Work**:
  - Bổ sung nút restart/stop an toàn từ Extension nếu Ba cấp quyền cụ thể.

## 4. Trigger / Execution Flow
- **Entry Point**: Khi Webview Visualizer được mở (active) hoặc refresh.
- **Trigger Source**: Sự kiện thay đổi của file `.agents/state/orchestrator.json` được hệ điều hành báo qua `FileSystemWatcher`.
- **Execution Order**:
  1. Webview Visualizer được khởi chạy -> Extension Backend kích hoạt.
  2. Extension Backend đọc trạng thái ban đầu của Resident Orchestrator từ `.agents/state/orchestrator.json` (nếu file không tồn tại hoặc stale quá 10 giây -> trạng thái `STOPPED`).
  3. Extension Backend gửi dữ liệu trạng thái ban đầu sang Webview thông qua IPC.
  4. Đăng ký một `FileSystemWatcher` lắng nghe file `orchestrator.json`. Khi file thay đổi, Backend đọc lại dữ liệu và gửi cập nhật sang Webview.
- **Completion Condition**: Widget hiển thị trạng thái chính xác và đồng bộ theo thời gian thực trên Visualizer panel.

## 5. Runtime Sequence
```
Extension Webview                Extension Backend            OS File System
      │                                  │                           │
      ├─────── Ready Event ─────────────>│                           │
      │                                  ├────── Read File ─────────>│
      │                                  │<───── json content ───────┤
      │<────── Send Status Msg ──────────┤                           │
      │                                  │                           │
      │                                  ├────── Watch File ────────>│
      │                                  │                           │ (Orchestrator writes new heartbeat)
      │                                  │<───── File Changed ───────┤
      │                                  ├────── Read File ─────────>│
      │                                  │<───── json content ───────┤
      │<────── Send Status Msg ──────────┤                           │
```

## 6. Dependency Contract
- **Required Dependencies**: VS Code API (`vscode`).
- **Optional Dependencies**: None.
- **External Runtime**: Tệp tin `.agents/state/orchestrator.json` do Python Resident Orchestrator ghi nhận.
- **Expected Contracts**:
  - Cấu trúc `orchestrator.json`:
    ```json
    {
      "status": "running",
      "pid": 20306,
      "last_heartbeat": "2026-07-13T13:01:04.358664+07:00"
    }
    ```
- **Detection Method**: Kiểm tra sự tồn tại của file `orchestrator.json` và thuộc tính `status`.
- **Failure Behavior**: Nếu file không tồn tại hoặc bị lỗi cú pháp JSON, hiển thị trạng thái Resident Orchestrator là `STOPPED`.

## 7. Error Matrix
| Condition | Expected Behavior | User Visibility | Recovery Action |
|---|---|---|---|
| File `orchestrator.json` không tồn tại | Mặc định coi là `STOPPED` | Trạng thái hiển thị `STOPPED (No PID)` | Tiếp tục lắng nghe file khi nào được tạo ra |
| Lỗi parse JSON | Báo lỗi parse, hiển thị `UNKNOWN` | Trạng thái hiển thị `UNKNOWN (Error)` | Thử đọc lại ở chu kỳ tiếp theo |
| Heartbeat bị quá hạn (stale > 15s) | Hiển thị trạng thái `ZOMBIE` hoặc `STOPPED` | Trạng thái hiển thị `STOPPED (Stale)` | Tiếp tục theo dõi |

## 8. Non-functional Requirements
- **Performance Expectations**:
  - Đọc file tĩnh trực tiếp cực nhanh, độ trễ < 5ms.
  - Sử dụng `FileSystemWatcher` của VS Code giúp tiết kiệm tài nguyên CPU/RAM tuyệt đối, tránh chạy vòng lặp polling vô hạn.
- **Blocking vs Asynchronous**: Bất đồng bộ hoàn toàn (`fs.promises.readFile`), không chặn giao diện render của VS Code.
- **Timeouts**: Đọc file có giới hạn thời gian (timeout 500ms).
- **Resource Usage**: CPU tăng trưởng < 0.1%, RAM tăng thêm < 1MB.
- **Thread Safety**: Chỉ đọc (`Read-only`), không ghi đè nên không sợ xung đột khóa file với Daemon.

## 9. Logging Requirements
- **Start**: Ghi log debug "Watching Resident Orchestrator state at .agents/state/orchestrator.json".
- **Warning**: Ghi log khi file không tồn tại hoặc parse lỗi.
- **Success**: Ghi log gửi trạng thái thành công sang Webview.

## 10. Configuration Impact
- Không yêu cầu cấu hình mới. Tự động nhận diện thư mục workspace.

## 11. Design Constraints
- Tuyệt đối không gọi lệnh CLI `aiwf orchestrator status` để lấy dữ liệu vì việc spawn tiến trình Python tiêu tốn rất nhiều CPU/RAM. Chỉ được đọc file JSON tĩnh.
- Tuân thủ quy tắc đồng bộ tệp Visualizer Extension: Biên tập tệp `webview.html`, chạy `node build.js` để tự động sinh `webviewHtml.ts`.

## 12. Blast Radius
- **Affected Extension**: Bổ sung widget hiển thị trên panel Visualizer, không ảnh hưởng đến các chức năng khác của Extension.
- **Impact Level**: Low.

## 13. File Change Scope
- **Modify**:
  - `extensions/visualizer/resources/webview.html` (Thêm HTML/CSS/JS hiển thị trạng thái)
  - `extensions/visualizer/src/extension.ts` (Thêm hàm đọc và watch file `orchestrator.json`)
- **Create**:
  - `docs/quick/QUICK-031_resident_orchestrator_status_display.md` (Mini Spec)
  - `docs/designs/QUICK-031_resident_orchestrator_status_display_blueprint.md` (Technical Blueprint - Phase 2)
- **Do Not Modify**:
  - Bất kỳ tệp nguồn Python nào khác.

## 1success. Success Metrics
- **Regression free**: Yes.
- **Resource safety**: Đảm bảo CPU/RAM sử dụng của extension không tăng bất thường trong suốt quá trình watch file.
- **Implementation completeness**: 100%.

## 15. Rollback Strategy
- Chỉ cần chạy `git checkout -- extensions/visualizer/` để khôi phục trạng thái ban đầu của Extension.

## 16. Expanded Acceptance Criteria
- [ ] AC-01 (Success Path): Khi Resident Orchestrator đang chạy, Extension Visualizer hiển thị đúng trạng thái `RUNNING`, đúng PID và thời gian cập nhật Heartbeat thời gian thực.
- [ ] AC-02 (Failure Path): Khi Resident Orchestrator bị tắt, Extension tự động phát hiện và chuyển hiển thị sang `STOPPED`.
- [ ] AC-03 (Performance Check): Extension không tạo ra thêm bất kỳ tiến trình con nào (no child process spawn) và không tăng CPU/RAM trong vòng 10 phút mở liên tục.

## 17. Self Verification
- Kiểm tra bằng Activity Monitor (trên Mac) hoặc Task Manager để so sánh lượng CPU/RAM tiêu thụ của VS Code Helper (Renderer) trước và sau khi mở Visualizer.

## 18. Open Questions
- Không có.

## 19. Blueprint Handoff
Bản thiết kế kỹ thuật ở Phase 2 sẽ xác định chi tiết:
- Cấu trúc DOM và CSS của widget hiển thị trạng thái Resident Orchestrator.
- Cú pháp đăng ký `vscode.workspace.createFileSystemWatcher` và cơ chế truyền tin IPC.
