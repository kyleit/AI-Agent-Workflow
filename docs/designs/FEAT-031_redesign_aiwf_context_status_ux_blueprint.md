<!-- File path: docs/designs/FEAT-031_redesign_aiwf_context_status_ux_blueprint.md -->

---
feature_id: FEAT-031
feature_name: Redesign AIWF Context Status UX
status: draft
stage: blueprint
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../plans/FEAT-031_redesign_aiwf_context_status_ux_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint – Redesign AIWF Context Status UX

## 1. Proposed Code Changes

### [workflow.config.json](file:///e:/AgentsProject/.agents/workflow.config.json) & [workflow.config.json.template](file:///e:/AgentsProject/templates/workflow.config.json.template)
- **Operation**: MODIFY
- **Responsibility**: Khai báo cấu hình `telemetry` chứa các định nghĩa style động và ngưỡng phần trăm/chi phí.
- **Changes**:
  - Bổ sung trường `context_styles` chứa màu sắc, nền, viền và emoji biểu tượng cho 4 cấp độ cảnh báo (healthy, warning, high, critical).

### [workflow_runtime.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) & [workflow_runtime.py (active)](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/workflow_runtime.py)
- **Operation**: MODIFY
- **Responsibility**: Nạp cấu hình style telemetry từ `workflow.config.json` đưa vào session state.
- **Changes**:
  - Gán trường `telemetry_config` đầy đủ các thông số `context_thresholds`, `context_styles` và `cost_thresholds`.

### [state_sync.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/state_sync.py) & [state_sync.py (active)](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/state_sync.py)
- **Operation**: MODIFY
- **Responsibility**: Đảm bảo đồng bộ hóa `telemetry_config` đầy đủ giữa Python session dict và tệp `runtime.json`.

### [webview.html](file:///e:/AgentsProject/extensions/visualizer/resources/webview.html)
- **Operation**: MODIFY
- **Responsibility**: Tách biệt giao diện footer thành 3 khối card riêng biệt và áp dụng logic theme cấu hình động.
- **Changes**:
  - Sửa đổi cấu trúc HTML: Loại bỏ `workflow-usage-card` cũ, thêm 3 thẻ `<section>` mới:
    - `#workflow-context-card` (Context Analytics)
    - `#workflow-api-usage-card` (API Usage)
    - `#workflow-efficiency-card` (Efficiency & Optimization)
  - Thêm phần tử `#context-status-badge` bên trong header của card Context để hiển thị nhãn trạng thái động.
  - Sửa đổi hàm Javascript cập nhật giao diện:
    - Nạp `telemetry_config` chứa `context_styles` động.
    - Tô màu thanh progress bar theo màu của trạng thái hiện tại (`style.backgroundColor` tương ứng với style cấu hình).
    - Cập nhật `#context-status-badge` với màu nền, màu chữ và icon cấu hình của trạng thái Context.
    - Hiển thị `#context-alert-box` chứa thông điệp tương ứng của Context khi ở trạng thái Warning/High/Critical. Ẩn đi khi ở trạng thái Healthy.
    - Hiển thị `#cost-alert-box` chứa thông điệp về hiệu suất chi phí (Cost Warning, Redundant Reads, v.v.) bên trong card Efficiency.

### [test_runtime.py](file:///e:/AgentsProject/skills/workflow-runtime/tests/test_runtime.py) & [test_runtime.py (active)](file:///e:/AgentsProject/.agents/skills/workflow-runtime/tests/test_runtime.py)
- **Operation**: MODIFY
- **Responsibility**: Viết unit test tự động kiểm chứng việc nạp và gán style cấu hình telemetry.

---

## 2. Target Folder Structure
Giữ nguyên bố cục thư mục hiện tại.

---

## 3. Interface & Data Contracts

### Bổ sung cấu hình Telemetry & Styles
```json
  "telemetry": {
    "context_thresholds": {
      "warning": 60,
      "high": 80,
      "critical": 95
    },
    "context_styles": {
      "healthy": {
        "color": "#10b981",
        "bg": "rgba(16, 185, 129, 0.1)",
        "border": "rgba(16, 185, 129, 0.3)",
        "icon": "🟢",
        "label": "Healthy"
      },
      "warning": {
        "color": "#f59e0b",
        "bg": "rgba(245, 158, 11, 0.1)",
        "border": "rgba(245, 158, 11, 0.3)",
        "icon": "🟡",
        "label": "Warning"
      },
      "high": {
        "color": "#f97316",
        "bg": "rgba(249, 115, 22, 0.1)",
        "border": "rgba(249, 115, 22, 0.3)",
        "icon": "🟠",
        "label": "High"
      },
      "critical": {
        "color": "#ef4444",
        "bg": "rgba(239, 68, 68, 0.1)",
        "border": "rgba(239, 68, 68, 0.3)",
        "icon": "🔴",
        "label": "Critical"
      }
    },
    "cost_thresholds": {
      "warning_usd": 10.0,
      "critical_usd": 50.0
    }
  }
```

---

## 4. Algorithms & Key Logic

### Logic render động trong Webview JS
```javascript
// 1. Phân loại trạng thái Context dựa trên ngưỡng phần trăm
const tc = data.telemetry_config || {};
const contextThresholds = tc.context_thresholds || { warning: 60, high: 80, critical: 95 };
const styles = tc.context_styles || {
    healthy: { color: "#10b981", bg: "rgba(16, 185, 129, 0.1)", border: "rgba(16, 185, 129, 0.3)", icon: "🟢", label: "Healthy" },
    // ... warning, high, critical
};

let statusKey = "healthy";
if (activePercentage >= contextThresholds.critical) statusKey = "critical";
else if (activePercentage >= contextThresholds.high) statusKey = "high";
else if (activePercentage >= contextThresholds.warning) statusKey = "warning";

const currentStyle = styles[statusKey];

// 2. Cập nhật Status Badge của Context
const badge = document.getElementById("context-status-badge");
if (badge) {
    badge.style.color = currentStyle.color;
    badge.style.background = currentStyle.bg;
    badge.style.border = `1px solid ${currentStyle.border}`;
    badge.innerHTML = `<span>${currentStyle.icon}</span> <span>${currentStyle.label}</span>`;
}

// 3. Tô màu thanh progress bar
const progressBar = document.getElementById("workflow-usage-progress-bar");
if (progressBar) {
    progressBar.style.width = activePercentage + "%";
    progressBar.style.backgroundColor = currentStyle.color;
}

// 4. Hiển thị cảnh báo Context (chỉ warning/high/critical)
const contextAlertBox = document.getElementById("context-alert-box");
const contextAlertText = document.getElementById("context-alert-text");
const contextAlertIcon = document.getElementById("context-alert-icon");
if (contextAlertBox && contextAlertText && contextAlertIcon) {
    if (statusKey !== "healthy") {
        let alertMsg = "";
        if (statusKey === "critical") {
            alertMsg = `Context usage is critical (<strong>${activePercentage.toFixed(1)}%</strong>). Next request may exceed the model limit.`;
        } else if (statusKey === "high") {
            alertMsg = `Context usage is high (<strong>${activePercentage.toFixed(1)}%</strong>). Prompt compression recommended.`;
        } else {
            alertMsg = `Context usage is warning (<strong>${activePercentage.toFixed(1)}%</strong>). Consider reducing context.`;
        }
        contextAlertText.innerHTML = alertMsg;
        contextAlertIcon.innerText = currentStyle.icon;
        contextAlertBox.style.background = currentStyle.bg;
        contextAlertBox.style.borderColor = currentStyle.border;
        contextAlertBox.style.color = currentStyle.color;
        contextAlertBox.style.display = "flex";
    } else {
        contextAlertBox.style.display = "none";
    }
}
```

---

## 5. Verification & Test Plan

### Unit Test
Bổ sung xác minh trường `context_styles` trong `test_telemetry_config_loading_and_fallback`:
- Xác nhận các khóa màu sắc, icon, và nhãn hiển thị được nạp thành công từ tệp cấu hình động và có cấu trúc fallback hợp lệ khi chạy unit test.
- Đảm bảo toàn bộ test suite chạy thành công vượt qua.
