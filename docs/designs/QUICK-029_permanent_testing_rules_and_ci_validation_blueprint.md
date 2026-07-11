<!-- File path: docs/designs/QUICK-029_permanent_testing_rules_and_ci_validation_blueprint.md -->
---
artifact_type: quick-feature-blueprint
feature_id: QUICK-029
workflow: quick-feature
status: pending
---
# Technical Design Blueprint – Permanent Testing Rules and CI Validation

## Summary
Thiết lập Quy định Kiểm thử Vĩnh viễn (Permanent Testing Rules) cho dự án AIWF. Di chuyển toàn bộ các tệp tin kiểm thử hiện tại vào các thư mục con phân loại tương ứng và bổ sung tính năng tự động xác thực kiến trúc kiểm thử thông qua lệnh CLI `aiwf test validate`.

## Scope
- Di chuyển 30 tệp test của `workflow-runtime` và 5 tệp test của `knowledge-runtime` vào các thư mục tương ứng (`smoke/`, `unit/`, `integration/`, `concurrency/`).
- Bổ sung hàm `validate_test_architecture` kiểm tra thư mục kiểm thử hợp lệ, sự hiện diện của marker tương ứng, tính đầy đủ của impact mapping, trùng lặp tên file và obsolete mappings.
- Bổ sung lệnh CLI `aiwf test validate` để xác thực trong CI.

## Technical Design

### 1. Test Folder Organization
Phân chia các tệp kiểm thử hiện tại theo mô hình thư mục:
- `concurrency/`: `test_lock.py`
- `smoke/`: `test_smoke.py`, `test_runtime_api.py`
- `integration/`: `test_agents_merge.py`, `test_refactoring.py`, `test_script_first.py`, `test_runtime.py`, `test_state_engine.py`, `test_choice.py`, `test_provider_manager.py`
- `unit/`: Tất cả các tệp test còn lại.

### 2. CI Validation Rules
Trong `tia_engine.py`, triển khai hàm `validate_test_architecture(workspace_root)` thực hiện các quy trình sau:
1. **Directory Verification**: Quét tất cả các tệp `test_*.py` trong `skills/`. Thư mục trực tiếp chứa tệp tin kiểm thử phải thuộc tập hợp: `{"smoke", "unit", "integration", "concurrency", "e2e", "stateful", "performance"}`.
2. **Pytest Marker Check**: Đọc nội dung tệp kiểm thử và kiểm tra sự tồn tại của chuỗi `"pytest.mark.<folder_name>"` hoặc `"pytestmark = pytest.mark.<folder_name>"`.
3. **Obsolete Mapping Check**: Quét `SOURCE_TO_TEST_MAP` và đảm bảo tất cả các tệp kiểm thử đích đều tồn tại trên đĩa.
4. **Duplicate Tests Check**: Kiểm tra xem có 2 tệp kiểm thử nào trùng tên được đặt trong 2 thư mục khác nhau hay không.
5. **Source File Mapping Check**: Đảm bảo toàn bộ các file `.py` nguồn trong các thư mục `scripts/` (trừ `__init__.py`) đều được định nghĩa tối thiểu 1 mapping trong `SOURCE_TO_TEST_MAP`.

## Files to Change

### [MODIFY] [tia_engine.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/tia_engine.py)
- Cập nhật `SOURCE_TO_TEST_MAP` trỏ tới tất cả các tệp mã nguồn hiện tại bao gồm cả các tệp mới/phụ trợ.
- Triển khai hàm `validate_test_architecture(workspace_root)`.

### [MODIFY] [workflow_runtime.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py)
- Thêm subaction `validate` vào CLI subcommand `test`.

## Implementation Steps

### Bước 1: Di chuyển các tệp tin kiểm thử vào thư mục phân loại tương ứng
- Tạo các thư mục con trong `skills/workflow-runtime/tests/` và `skills/knowledge-runtime/tests/`.
- Thực hiện di chuyển các tệp tin tương ứng.

### Bước 2: Cập nhật `tia_engine.py` và triển khai `validate_test_architecture`
- Viết mã nguồn kiểm tra các ràng buộc tĩnh của kiến trúc kiểm thử.

### Bước 3: Đăng ký subaction `validate` vào CLI `test`
- Chỉnh sửa `workflow_runtime.py` để tích hợp logic gọi hàm kiểm tra.

## Validation Plan

### Automated Tests
- Chạy thử lệnh:
  ```bash
  python skills/workflow-runtime/scripts/workflow_runtime.py test validate
  ```
  Xác minh đầu ra trả về thành công (Exit code 0).
- Tạo thử một tệp tin test vi phạm (ví dụ đặt sai thư mục) và kiểm tra xem lệnh trên có trả về lỗi (Exit code 1) hay không.

## Rollback Plan
- Di chuyển các tệp test trở lại thư mục gốc của `tests/`.
- Khôi phục `tia_engine.py` và `workflow_runtime.py` từ Git stash/checkout.
