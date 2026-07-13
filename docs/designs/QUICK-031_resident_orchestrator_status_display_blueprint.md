<!-- File path: docs/designs/QUICK-031_resident_orchestrator_status_display_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-031
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – Resident Orchestrator Status Display in VS Code Visualizer Extension

## 1. Proposed Code Changes
Chỉ thay đổi giao diện frontend Webview của Extension để hiển thị các dữ liệu trạng thái Resident Orchestrator sẵn có.

### `extensions/visualizer/resources/webview.html`
- **Operation**: MODIFY
- **Responsibility**: Bổ sung thẻ HTML hiển thị thông tin Resident Orchestrator và viết logic gán dữ liệu DOM khi nhận tin nhắn `UPDATE_SESSION`.
- **Changes**:
  - Chèn một Section HTML `Resident Orchestrator Status` vào tab `Concurrency / Team` (id="panel-team") ngay phía trước thẻ Adaptive Team Plan.
  - Cập nhật hàm xử lý `UPDATE_SESSION` trong thẻ `<script>` để tìm các thẻ DOM mới và gán giá trị tương ứng (`orchestrator_status`, `orchestrator_pid`, `attach_mode`, `last_heartbeat`).

---

## 2. Target Folder Structure
```text
.
└── extensions/
    └── visualizer/
        ├── resources/
        │   └── webview.html (Modified)
        └── src/
            ├── extension.ts (Unchanged - already has watchers and parsers)
            └── webviewHtml.ts (Auto-generated via build.js)
```

---

## 3. Interface & Data Contracts
### Webview IPC Contract (UPDATE_SESSION payload)
Dữ liệu gửi từ Extension Backend sang Webview chứa các trường thông tin Orchestrator sau (đã có sẵn trong logic aggregate của `extension.ts`):
- `orchestrator_status`: `RUNNING` | `STOPPED` | `UNHEALTHY (stale heartbeat)`
- `orchestrator_pid`: PID của tiến trình (ví dụ: `20306`) hoặc `N/A`
- `attach_mode`: `started` | `attached` | `N/A`
- `last_heartbeat`: Khoảng thời gian từ heartbeat cuối cùng (ví dụ: `3.5s ago`) hoặc `N/A`

---

## 4. Algorithms & Key Logic
### A. Thêm Widget hiển thị trên UI
Chèn vào `panel-team` (ở dòng 1728) đoạn HTML sau:
```html
<!-- Resident Orchestrator Status Section -->
<section class="glass" style="padding: 12px; border-radius: 6px; margin-bottom: 12px; border: 1px solid var(--line); background: var(--panel-soft);">
    <h3 style="margin: 0 0 8px 0; font-size: 13px; color: var(--cyan); font-weight: bold; display: flex; align-items: center; gap: 6px;">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
        Resident Orchestrator Status
    </h3>
    <div style="display: flex; flex-direction: column; gap: 6px; font-size: 11px;">
        <div style="display: flex; justify-content: space-between;">
            <span>Orchestrator Status:</span>
            <strong id="orch-status" style="color: var(--muted);">UNKNOWN</strong>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span>Orchestrator PID:</span>
            <strong id="orch-pid" style="color: #cbd5e1;">N/A</strong>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span>Attach Mode:</span>
            <strong id="orch-attach" style="color: #cbd5e1;">N/A</strong>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span>Last Heartbeat:</span>
            <strong id="orch-heartbeat" style="color: #cbd5e1;">N/A</strong>
        </div>
    </div>
</section>
```

### B. Logic cập nhật DOM
Cập nhật JS trong hàm `UPDATE_SESSION`:
```javascript
// Render Resident Orchestrator Status
const orchStatusEl = document.getElementById("orch-status");
const orchPidEl = document.getElementById("orch-pid");
const orchAttachEl = document.getElementById("orch-attach");
const orchHeartbeatEl = document.getElementById("orch-heartbeat");

if (orchStatusEl) {
    const status = data.orchestrator_status || "STOPPED";
    orchStatusEl.innerText = status;
    if (status === "RUNNING") {
        orchStatusEl.style.color = "var(--green)";
    } else if (status.startsWith("UNHEALTHY")) {
        orchStatusEl.style.color = "var(--orange)";
    } else {
        orchStatusEl.style.color = "var(--red)";
    }
}
if (orchPidEl) {
    orchPidEl.innerText = data.orchestrator_pid || "N/A";
}
if (orchAttachEl) {
    orchAttachEl.innerText = data.attach_mode || "N/A";
}
if (orchHeartbeatEl) {
    orchHeartbeatEl.innerText = data.last_heartbeat || "N/A";
}
```

---

## 5. Validation Rules
- **No Null Pointer Errors**: Phải kiểm tra sự tồn tại của các thành phần DOM (`if (orchStatusEl)...`) trước khi thực hiện gán giá trị để tránh lỗi JS làm đứng màn hình Webview.

---

## 6. Implementation Checklist
- [ ] Bổ sung mã HTML vào `extensions/visualizer/resources/webview.html` tại vị trí tab `panel-team`.
- [ ] Bổ sung mã cập nhật JS trong hàm nhận `UPDATE_SESSION` trong `webview.html`.
- [ ] Chạy lệnh biên dịch giao diện: `node build.js` tại thư mục `extensions/visualizer`.

---

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - Mở giao diện Visualizer và chuyển sang tab `Concurrency / Team`.
  - Kiểm tra Resident Orchestrator Status widget hiển thị đúng thông tin của tiến trình hiện tại.
  - Dừng orchestrator (`python skills/workflow-runtime/scripts/workflow_runtime.py orchestrator stop`) và xác nhận UI đổi sang màu đỏ `STOPPED`.
  - Khởi động lại orchestrator và xác nhận UI đổi sang màu xanh `RUNNING`.
