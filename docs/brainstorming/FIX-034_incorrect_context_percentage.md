<!-- docs/brainstorming/FIX-034_incorrect_context_percentage.md -->

---
feature_id: FIX-034
feature_name: Incorrect Active Context Percentage
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FIX-034_incorrect_context_percentage_plan.md
---

# Master Requirement Document – Incorrect Active Context Percentage

## 1. Feature ID & Name
- **Feature ID**: FIX-034
- **Feature Name**: Incorrect Active Context Percentage Fix

## 2. Original Idea / Problem
Bảng điều khiển Visualizer hiển thị sai lệch toán học giữa lượng token hoạt động (active tokens) và phần trăm tương ứng.
Ví dụ:
- `349.2K / 2.0M active tokens` -> Hiển thị `36.5%` (Trong khi thực tế `349.2K / 2.0M ≈ 17.46%`).
- `363.1M / 2.0M active tokens` -> Hiển thị `37.1%` (Trong khi thực tế `363.1M` lớn hơn nhiều so với `2.0M` limit).

---

## 3. Root Cause Investigation & Pipeline Trace
Con đã rà soát toàn bộ chuỗi tính toán (calculation pipeline) từ backend đến frontend:

1. **Provider & Runtime Parser (`context.py` / `parse_transcript`)**:
   - `active_tokens` được tính bằng độ dài của transcript cuối cùng chia cho 3: `active_tokens = int(current_history_chars / 3)`. (Kết quả: đúng thực tế context hoạt động, ví dụ: ~742K).
   - `total_tokens` được tính bằng tổng số token nhập và xuất lũy kế qua toàn bộ các bước: `total_tokens = input_tokens + output_tokens`. (Kết quả: tăng lũy kế theo cấp số cộng của các lượt chat, ví dụ: ~363.1M).
2. **Context Analyzer (`workflow_runtime.py`)**:
   - Khi tạo đối tượng `session["context_usage"]`:
     ```python
     session["context_usage"] = {
         "total_tokens": usage.get("total_tokens", 0), # LỖI: Gán bằng total_tokens (lũy kế), đáng lẽ phải là active_tokens
         "limit_tokens": usage.get("limit_tokens", 2000000),
         "percentage": usage.get("percentage", 0.0) # Đúng: Tính từ active_tokens
     }
     ```
3. **Webview Binding (`webview.html`)**:
   - Khi render lượng token hoạt động:
     ```javascript
     const activeTotal = active.total_tokens !== undefined ? active.total_tokens : (wf.total_tokens || 0);
     ```
     Do `active.total_tokens` là `undefined`, UI rơi vào fallback sử dụng `wf.total_tokens` (đang chứa giá trị `total_tokens` lũy kế từ `context_usage`).

**FIRST LAYER WHERE VALUES DIVERGE:**
- **`workflow_runtime.py` line 154**: Gán giá trị `total_tokens` (lũy kế) cho biến hiển thị `total_tokens` của active context window thay vì `active_tokens`.
- **`webview.html` line 1985**: Fallback ưu tiên hiển thị `wf.total_tokens` lũy kế thay vì ưu tiên `wf.active_tokens`.

---

## 4. Requirement Discovery
- **Functional Requirements**:
  * **FR-01**: Sửa đổi `workflow_runtime.py` để gán `"total_tokens": usage.get("active_tokens", 0)` cho `context_usage`.
  * **FR-02**: Sửa đổi `webview.html` để prioritze hiển thị `active_tokens` từ workflow summary/context usage.
  * **FR-03**: Đảm bảo tất cả 8 diagnostic metrics hiển thị đồng bộ phần trăm dựa trên công thức `active_tokens / limit_tokens`.
- **Technical Constraints**:
  * Đảm bảo tính toán hoàn toàn ở backend/extension host, không tự tính toán lại không đồng bộ ở Webview để giữ Single Source of Truth.

---

## 5. Solution Options Evaluated

### Option A: Sửa gán biến ở `workflow_runtime.py` & Sửa fallback trong `webview.html` (Khuyên dùng)
- **Ưu điểm**: Sửa đúng gốc rễ ở cả 2 đầu pipeline, đảm bảo dữ liệu truyền đi chính xác và giao diện binding đúng trường dữ liệu mong muốn.
- **Complexity**: Low.
- **Risk**: None.

---

## 6. Selected Solution
Con đề xuất chọn **Option A**. Giải quyết triệt để lỗi hiển thị toán học sai lệch.

---

## 7. Acceptance Criteria
- [ ] Phần trăm hiển thị trong Active Context Card luôn bằng `active_context_tokens / context_limit` chính xác trong khoảng sai số 0.1%.
- [ ] Label hiển thị dạng K/M khớp chuẩn (ví dụ: ~742.0K / 2.0M).

---

## 8. User Confirmation Gate
```text
────────────────────────────────────────────────────
Bug Investigation Complete

Bug:                      FIX-034: Incorrect Active Context Percentage
Root Cause:               mismatch binding variables (total_tokens vs active_tokens)
Recommended Solution:     Option A — Fix python assignment & html binding fallback

Continue generating Brainstorming document?

  [Y] Yes — Generate docs/brainstorming/FIX-034_incorrect_context_percentage.md
  [N] No  — Stop.
────────────────────────────────────────────────────
```
Con xin phản hồi từ Ba. Ba gõ `Y` để con tiếp tục nhé!
