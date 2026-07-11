<!-- File path: docs/quick/QUICK-029_permanent_testing_rules_and_ci_validation.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-029
workflow: quick-feature
status: pending
---
# Mini Plan & Feature Specification – Permanent Testing Rules and CI Validation

## 1. Feature Goal
Thiết lập Quy định Kiểm thử Vĩnh viễn (Permanent Testing Rules) cho toàn bộ dự án AIWF. Toàn bộ các kiểm thử (test) mới và cũ bắt buộc phải tuân thủ phân loại thư mục, khai báo marker pytest và định nghĩa ánh xạ ảnh hưởng (impact mapping). Triển khai bước xác thực CI Validation tự động quét và báo cáo các vi phạm cấu trúc kiểm thử.

## 2. Quick Feature Justification
- **Estimated Complexity**: Medium (cần sắp xếp lại vị trí tệp tin và cài đặt luật quét phân tích tĩnh).
- **Implementation Scope**: Thay đổi cấu trúc thư mục chứa các tệp tin kiểm thử dưới `skills/` và bổ sung thêm hàm xác thực trong `tia_engine.py` / CLI.

## 3. Specification & Requirements

### 3.1. Standard Test Directory Structure
Toàn bộ các tệp tin test Python (ngoại trừ tệp cấu hình chia sẻ `conftest.py`) BẮT BUỘC phải nằm trong một trong các thư mục con đã được phê duyệt trực thuộc thư mục `tests/`:
```text
tests/
├── smoke/
├── unit/
├── integration/
├── concurrency/
├── e2e/
├── stateful/
└── performance/
```

### 3.2. Mandatory Classification & Pytest Markers
Mỗi tệp tin test phải tương ứng trực tiếp với tên thư mục chứa nó và phải được trang bị duy nhất 1 primary decorator marker tương ứng trong pytest (ví dụ: `@pytest.mark.unit` cho thư mục `unit/`). Các bài test không được phân loại hoặc nằm ngoài thư mục trên sẽ bị coi là vi phạm.

### 3.3. Test Impact Mapping Alignment
Mỗi tệp mã nguồn Python thực thi của framework phải được định nghĩa liên kết kiểm thử trong `SOURCE_TO_TEST_MAP` tại `tia_engine.py` (hoặc có liên kết hợp lệ). Nếu có tệp mã nguồn mới không được map, hoặc có tệp map đến test không tồn tại (obsolete mappings), CI sẽ thất bại.

### 3.4. CI Validation Subcommand
Tích hợp lệnh:
```bash
aiwf test validate
```
Lệnh này sẽ tự động chạy xác thực các quy tắc cấu trúc trên và trả về mã lỗi 1 nếu:
- Có tệp kiểm thử nằm trực tiếp dưới thư mục `tests/` hoặc thư mục không được phê duyệt.
- Có tệp kiểm thử thiếu marker phân loại.
- Có tệp mã nguồn (`.py` dưới `scripts/`) thiếu ánh xạ ảnh hưởng trong `SOURCE_TO_TEST_MAP`.
- Có tệp kiểm thử bị trùng lặp.
- Có ánh xạ lỗi thời (obsolete mapping) trỏ tới tệp test không tồn tại.
