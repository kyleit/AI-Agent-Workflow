# Pipeline Investigation & Mathematical Validation Report – FIX-034

## 1. Root Cause Analysis
- **Problem**: Biểu đồ hiển thị sự sai lệch lớn giữa số lượng token hiển thị bên cạnh thanh trượt và tỷ lệ phần trăm (ví dụ: hiển thị `363.1M / 2.0M active tokens` -> `37.1%`).
- **Root Cause**: Có sự lẫn lộn giữa lượng token hoạt động tại bước hiện tại (`active_tokens` khoảng ~736K-828K) và tổng số lượng token tích lũy lũy kế của toàn bộ cuộc trò chuyện (`total_tokens` khoảng ~363M-450M).
  * **Backend**: Biến `total_tokens` của active context được gán sai bằng `usage.get("total_tokens", 0)` thay vì `active_tokens` trong `workflow_runtime.py`.
  * **Frontend**: Phép fallback `activeTotal` trong `webview.html` ưu tiên `wf.total_tokens` (tích lũy) thay vì `wf.active_tokens`.

---

## 2. Pipeline Trace Report
Dưới đây là hành trình vết của giá trị token qua từng tầng kiến trúc trước và sau khi sửa lỗi:

### Before Fix:
- **Context Analyzer** (`context.py`):
  * `active_tokens` = `828,671` (đúng).
  * `total_tokens` = `450,666,771` (đúng, tính lũy kế).
- **SQLite** (`usage_records` table):
  * Lưu trữ chính xác cả hai cột: `active_tokens = 828671`, `total_tokens = 450666771`.
- **JSON Payload / State** (`usage.json`):
  * `session["context_usage"]["total_tokens"]` = `450,666,771` (sai lệch do gán nhầm từ `total_tokens` lũy kế).
  * `session["context_usage"]["percentage"]` = `41.43` (đúng, tính trên `active_tokens`).
- **Webview UI**:
  * Đọc `activeTotal` = `450,666,771`. Định dạng qua `formatTokens` -> `450.7M`.
  * Đọc `activePercentage` = `41.43`. Định dạng -> `41.4%`.
  * Kết quả hiển thị: `450.7M / 2.0M` -> `41.4%` (Sai lệch toán học: 450.7M > 2.0M).

### After Fix:
- **JSON Payload / State** (`usage.json`):
  * `session["context_usage"]["total_tokens"]` = `828,671` (sửa thành `active_tokens`).
  * `session["context_usage"]["percentage"]` = `41.43` (đúng).
- **Webview UI**:
  * Đọc `activeTotal` = `828,671`. Định dạng qua `formatTokens` -> `828.7K`.
  * Đọc `activePercentage` = `41.43`. Định dạng -> `41.4%`.
  * Kết quả hiển thị: `828.7K / 2.0M` -> `41.4%` (Đúng toán học: 828,671 / 2,000,000 = 41.43%).

---

## 3. Formula Validation Report
Công thức tính toán phần trăm duy nhất (Single Source of Truth) tại Backend:
$$\text{percentage} = \frac{\text{active\_tokens}}{\text{limit\_tokens}} \times 100$$
Frontend (Webview) chỉ nhận dữ liệu tính toán sẵn này qua các biến JSON state, tuyệt đối không tự tính toán lại.

---

## 4. Unit Conversion Audit
- **Raw unit**: Số nguyên đếm số lượng token thực tế (raw tokens).
- **Formatter**: Hàm `formatTokens` trong `webview.html` chia cho `1,000,000` để lấy hậu tố `M` nếu >= 1,000,000; chia cho `1,000` lấy hậu tố `K` nếu >= 1,000; giữ nguyên nếu nhỏ hơn.
- Phép chia và làm tròn chỉ diễn ra ở bước hiển thị (after calculation), không làm thay đổi hay suy hao giá trị số nguyên gốc khi tính tỷ lệ phần trăm.

---

## 5. JSON Mapping Audit
- **`context_usage`**:
  * `total_tokens` map sang trường `active_tokens` của backend.
  * `limit_tokens` map sang trường `limit_tokens` của backend.
  * `percentage` map sang trường `percentage` của backend.

---

## 6. Before vs After Comparison
- **Trước khi sửa**:
  * Đồ thị hiển thị: `363.1M / 2.0M` -> `37.1%`.
  * Sai số toán học: ~18100% (phi lý).
- **Sau khi sửa**:
  * Đồ thị hiển thị: `742.0K / 2.0M` -> `37.1%` (Ví dụ thực tế).
  * Sai số toán học: 0.0% (Khớp hoàn hảo).

---

## 7. Automated Mathematical Test Report
- **Test File**: `skills/workflow-runtime/tests/test_mathematical_percentage.py`
- **Các trường hợp thử nghiệm**:
  * `100K / 2M` -> `5.0%` (OK)
  * `250K / 2M` -> `12.5%` (OK)
  * `349.2K / 2M` -> `17.46%` (OK)
  * `500K / 2M` -> `25.0%` (OK)
  * `1M / 2M` -> `50.0%` (OK)
  * `1.9M / 2M` -> `95.0%` (OK)
  * `2M / 2M` -> `100.0%` (OK)
- **Kết quả chạy thử**: `Ran 2 tests in 0.000s - OK`.

---

## 8. Final Verification Report
Tất cả các bài kiểm tra toán học và kiểu dữ liệu đều đạt điểm tuyệt đối. Visualizer sidebar giờ đây hiển thị tỷ lệ phần trăm đồng bộ khớp chuẩn xác với lượng token hoạt động.
Báo cáo gỡ lỗi chính thức đã được ghi nhận tại `docs/debug/FIX-034_debug.md`.
