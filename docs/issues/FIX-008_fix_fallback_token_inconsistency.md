<!-- File path: docs/issues/FIX-008_fix_fallback_token_inconsistency.md -->

---
artifact_type: fix
issue_id: FIX-008
workflow: quick-fix
architecture_impact: low
adr_required: false
status: approved
---

# Fix Document – Fallback Token Inconsistency in Visualizer Extension

## 1. Issue
Khi mở dự án mới (ví dụ như `SmartMulti-AgentBrowserAutomation` mới chạy bước `initialize-workflow`), hệ thống chưa có dữ liệu usage thực tế (`workflow_usage_summary` chưa được CLI sinh ra). Lúc này, Visualizer Extension tự động sử dụng chế độ ước lượng dự phòng (Fallback Estimation) nhưng hiển thị số liệu không nhất quán:
- Thanh tiến độ hiển thị `23.2K` tokens.
- Các trường chi tiết bên dưới (Input, Output, Cache, Thinking) cộng lại vượt xa `23.2K` (Input hiển thị `42.4K`).

## 2. Root Cause
- Trong tệp `extensions/visualizer/src/extension.ts`, hàm `estimateContextUsage()` ước lượng số token từ tệp nhật ký `transcript.jsonl`:
  ```typescript
  active_tokens = Math.min(Math.round(fileSize / 3), limit_tokens);
  total_tokens = Math.min(active_tokens + 20000, limit_tokens);
  ```
- Tuy nhiên, trong tệp `webview.html`, tổng số tokens hiển thị ở thanh tiến độ và nhãn chính lại sử dụng:
  ```javascript
  const totalVal = (hasWf && (wf.active_tokens || wf.total_tokens)) ? (wf.active_tokens || wf.total_tokens) : 0;
  ```
  Do `wf.active_tokens` (`23.2K`) được ưu tiên hơn `wf.total_tokens` (`43.2K`), giao diện hiển thị tổng số tokens là `23.2K`.
- Trong khi đó, các trường chi tiết (Input, Output, Cache, Thinking) được tính toán dựa trên `wf.input_tokens` và các trường tương ứng lấy trực tiếp từ ước tính của `total_tokens` (nên Input ra `42.4K`). Sự mâu thuẫn này gây bối rối cho người dùng.

## 3. Scope
- **In Scope**:
  - Đồng bộ `active_tokens` và `total_tokens` trong hàm `estimateContextUsage` của `extension.ts` để chúng luôn bằng nhau (không cộng thêm 20000 bừa bãi).
  - Cập nhật Webview render để luôn đồng bộ hiển thị.
- **Out of Scope**: Không thay đổi cơ chế tính token thực tế của CLI.

## 4. Expected Files
| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | `extensions/visualizer/src/extension.ts` | Đồng bộ `total_tokens` và `active_tokens` trong ước lượng dự phòng |
| Modify | `extensions/visualizer/src/webviewHtml.ts` | Đồng bộ tệp HTML biên dịch |

## 5. Proposed Changes

### [extension.ts](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/src/extension.ts)
Sửa đổi logic gán token trong `estimateContextUsage`:
```typescript
                if (latestFile) {
                    const fileSize = fs.statSync(latestFile).size;
                    total_tokens = Math.min(Math.round(fileSize / 3), limit_tokens);
                    active_tokens = total_tokens;
                }
```

## 6. Risks
- Không có rủi ro hệ thống vì đây chỉ là logic ước lượng hiển thị dự phòng (Fallback UI).

## 7. Acceptance Criteria
- [x] Số liệu tổng tokens và Input/Output/Cache/Thinking trên giao diện đồng bộ 100%.
- [x] Không còn hiện tượng Input vượt quá tổng số tokens trên thanh tiến độ.
