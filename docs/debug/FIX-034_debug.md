<!-- File path: docs/debug/FIX-034_debug.md -->

---
artifact_type: debug
feature_id: FIX-034
workflow: standard
status: PASS
---

# Debug Report – Incorrect Active Context Percentage Fix

## 1. Summary
Con đã sửa đổi và xác thực thành công sự sai lệch toán học trên biểu đồ Active Context:
1. **Backend**: Thay thế `total_tokens` (tích lũy) bằng `active_tokens` trong tệp cấu hình `context_usage` tại `workflow_runtime.py`.
2. **Frontend Webview**: Chỉnh sửa fallback trong `webview.html` để ưu tiên trường `active_tokens` khi dựng giao diện, tránh bị fallback tự động sang tổng tích lũy.

## 2. Diagnostics
- **Build Status**: PASS (Command used: `node build.js` & `npx vsce package`)
- **Lint Status**: PASS (Command used: `npm run compile` typecheck)
- **Unit Tests Status**: PASS (Command used: `python -m unittest skills/workflow-runtime/tests/test_mathematical_percentage.py`)

## 3. Issues Found & Resolved
| Issue Description | Root Cause | Fix Summary | Files Affected |
| :--- | :--- | :--- | :--- |
| Sai lệch số lượng token hoạt động trên biểu đồ (ví dụ: `363.1M / 2.0M` -> `37.1%`) | Mismatch trường dữ liệu: gán tổng token tích lũy cho active context total | Chuyển sang sử dụng chính xác `active_tokens` ở cả backend và frontend | `workflow_runtime.py`, `webview.html` |

## 4. Remaining Risks
- **None**.

## 5. Debug Status
**Status**: PASS
