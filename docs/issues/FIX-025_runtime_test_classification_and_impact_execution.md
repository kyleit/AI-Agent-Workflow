<!-- File path: docs/issues/FIX-025_runtime_test_classification_and_impact_execution.md -->
---
artifact_type: fix-spec
issue_id: FIX-025
workflow: quick-fix
status: pending
---
# Mini Plan & Fix Specification – Refactor Runtime Test Strategy with Test Classification and Impact-Based Execution

## 1. Issue Description
Hiện tại, bộ test suite chạy toàn bộ các bài kiểm thử (hơn 50 test case) mỗi khi có sự thay đổi mã nguồn. Điều này gây tốn thời gian chạy (hơn 1-2 phút) và hao tốn tài nguyên CPU vô ích. Cần thiết kế và triển khai cơ chế Phân tích ảnh hưởng của Kiểm thử (Test Impact Analysis - TIA) và phân loại kiểm thử thông minh để chỉ chạy các bài kiểm thử bị ảnh hưởng bởi file mã nguồn thay đổi, kết hợp bộ kiểm thử khói (smoke suite) cực nhẹ để xác thực nhanh.

## 2. Scope
- **In Scope**:
  - Tạo tệp tin cấu hình `pytest.ini` với đầy đủ các marker phân loại.
  - Phân loại toàn bộ các tệp test Python hiện có thông qua marker pytest hoặc đặt trong `conftest.py` / decorator.
  - Xây dựng module phân tích ảnh hưởng thay đổi tệp tin (`tia_engine.py`) để map giữa file thay đổi và test case tương ứng.
  - Thêm CLI subcommand `aiwf test` hỗ trợ chạy: `affected`, `unit`, `integration`, `concurrency`, `smoke`, `full`.
- **Out of Scope**:
  - Viết lại toàn bộ nội dung của các test case cũ không liên quan đến kiểm thử TIA.

## 3. Quick Fix Justification
- **Estimated Complexity**: Medium
- **Implementation Scope**: Chỉ ảnh hưởng đến hạ tầng cấu hình test của Workflow Runtime và cấu hình `pytest.ini`.
- **Architectural Impact**: Thấp, không thay đổi logic SDLC chính mà bổ sung các lệnh kiểm thử thông minh.
- **Risk Level**: Thấp (chỉ ảnh hưởng đến lệnh test).
- **Justification**: Hoạt động tối ưu hóa hạ tầng test là cải tiến mang tính cục bộ hỗ trợ năng suất làm việc của Coder và Agent.

## 4. Trigger / Execution Flow
- **Entry Point**: CLI subcommand `python workflow_runtime.py test <mode>`
- **Trigger Source**: Ba chạy trực tiếp từ terminal hoặc do Agent kích hoạt trong các pha kiểm thử tự động.
- **Execution Order**:
  1. Detect changed files (sử dụng git diff hoặc so sánh timestamp).
  2. Map changed files sang affected test files.
  3. Bổ sung bắt buộc các tệp smoke test.
  4. Chạy `pytest` nhắm mục tiêu vào các tệp đã lọc.

## 5. Runtime Sequence
```
User / Agent CLI run test affected
↓
Get Git Diff / Changed files
↓
Run TIA Resolver mapping to tests
↓
Combine with Smoke tests
↓
Execute pytest with arguments
↓
Report execution time and saved time
```

## 6. Dependency Contract
- **Required Dependencies**: `pytest`
- **Optional Dependencies**: None
- **External Runtime**: Python và pytest.
- **Expected Contracts**: Lệnh CLI in ra báo cáo thống kê tóm tắt định dạng JSON hoặc text dễ đọc.

## 7. Error Matrix
| Condition | Expected Behavior | User Visibility | Recovery Action |
|---|---|---|---|
| Không có file thay đổi | Báo cáo không có thay đổi và chỉ chạy suite smoke | Thông tin hiển thị trên terminal | Tiến hành chạy smoke test |
| Lỗi cú pháp pytest.ini | Pytest báo lỗi parser | In trực tiếp ra terminal | Sửa lại định dạng cấu hình |
| Lỗi TIA mapping | Trả về toàn bộ danh sách test (fallback full suite) | Cảnh báo fallback | Chạy full test suite |

## 8. Non-functional Requirements
- **Performance Expectations**: TIA mapping hoàn thành dưới **50ms**. Thời gian chạy test affected trung bình dưới **5 giây** thay vì hơn **60 giây** của full suite.
- **Thread Safety**: Không chạy các test concurrency song song.

## 9. Logging Requirements
- **Start**: `[INFO] Initializing Test Impact Analysis...`
- **Warning**: `[WARN] Cannot resolve file mapping, falling back to all tests.`
- **Success**: `[SUCCESS] Tests executed successfully. Saved estimate: X seconds.`

## 10. Configuration Impact
- **Existing Configs Reused**: Tải cấu hình từ `pytest.ini` mới tạo.

## 11. Design Constraints
- Không sửa đổi mã nguồn các modules chạy chính của hệ thống trừ việc đăng ký CLI subcommand `test` trong `workflow_runtime.py`.

## 12. Blast Radius
- **Affected Skills**: `workflow-runtime`, `knowledge-runtime`
- **Impact Level**: Low

## 13. File Change Scope
- **Create**:
  - `pytest.ini`
  - `skills/workflow-runtime/scripts/tia_engine.py`
  - `skills/workflow-runtime/tests/test_smoke.py`
- **Modify**:
  - `skills/workflow-runtime/scripts/workflow_runtime.py`

## 14. Success Metrics
- **Regression free**: Yes
- **Token reduction**: None
- **Latency improvement**: Chạy test nhanh hơn **80%** trong quá trình phát triển thông thường.

## 15. Rollback Strategy
- **Safe Rollback Steps**: `git checkout` các file đã chỉnh sửa và xóa `pytest.ini` cùng `tia_engine.py`.

##Expanded Acceptance Criteria
- [ ] AC-01: Chạy `aiwf test smoke` kiểm tra khởi động cli thành công dưới 2 giây.
- [ ] AC-02: Thay đổi một tệp tin (ví dụ `db.py`) và chạy `aiwf test affected` sẽ chỉ kích hoạt chạy các test liên quan tới db và smoke test.
- [ ] AC-03: Thay đổi tệp tin tài liệu (`.md`) không kích hoạt chạy bất kỳ test case Python nào.

## 17. Self Verification
- Kiểm tra danh sách các marker đã đăng ký bằng lệnh `pytest --markers`.
- Chạy thử nghiệm các subcommand kiểm thử qua CLI và so sánh kết quả.

## 18. Open Questions
Không có câu hỏi nào.

## 19. Blueprint Handoff
Tài liệu Blueprint ở Phase 2 sẽ làm rõ:
- Tên tệp tin ánh xạ TIA mapping cụ thể.
- Cơ cấu ghi log kết quả so sánh thời gian chạy và thời gian tiết kiệm được.
