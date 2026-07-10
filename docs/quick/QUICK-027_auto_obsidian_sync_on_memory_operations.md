<!-- File path: docs/quick/QUICK-027_auto_obsidian_sync_on_memory_operations.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-027
workflow: quick-feature
status: approved
---
# Mini Plan & Feature Specification – Auto Obsidian Sync on Memory Operations

## 1. Feature Goal
Tự động kích hoạt đồng bộ hóa tri thức Obsidian (`sync`) sau khi chạy các lệnh khởi tạo (`bootstrap`) và cập nhật (`update`) bộ nhớ dự án thông qua CLI của Project Memory.

## 2. Quick Feature Justification
Giải thích lý do tác vụ đủ điều kiện phát triển nhanh thay vì chu trình SDLC đầy đủ:
- **Estimated Complexity**: Low
- **Implementation Scope**: Single module or local change (thêm logic gọi hàm sync của `knowledge-runtime` vào cuối hai script `bootstrap.py` và `update.py`).
- **Architectural Impact**: Low / Purely additive (không ảnh hưởng tới cấu trúc lõi của Project Memory hay Knowledge Runtime).
- **Risk Level**: Low (nếu có lỗi khi import hoặc chạy đồng bộ Obsidian, hệ thống chỉ đưa ra cảnh báo `log_warn` và vẫn hoàn thành tiến trình chính của bộ nhớ).
- **Justification**: Yêu cầu mang tính mở rộng cục bộ và tự động hóa ngầm, không đòi hỏi thay đổi thiết kế cơ sở dữ liệu hay thay đổi lớn về kiến trúc.

## 3. Scope Boundary
Phân định ranh giới phạm vi rõ ràng để tránh mơ hồ:
- **In Scope**:
  - Tự động gọi ngầm `knowledge_runtime.sync("obsidian")` ở cuối hàm `run_bootstrap` của `bootstrap.py`.
  - Tự động gọi ngầm `knowledge_runtime.sync("obsidian")` ở cuối hàm `run_update` của `update.py`.
  - Đảm bảo xử lý ngoại lệ an toàn nếu `knowledge-runtime` chưa được cài đặt hoặc cấu hình Obsidian bị tắt.
- **Out of Scope**:
  - Viết lại cơ chế nén hay cơ chế chuyển dịch liên kết của Obsidian.
- **Not Modified**:
  - Giao diện CLI và core API của `knowledge-runtime`.
- **Future Work**:
  - Hỗ trợ đồng bộ hóa các provider khác (như Notion, GitHub...) tự động.

## 4. Trigger / Execution Flow
- **Entry Point**: `run_bootstrap()` trong `bootstrap.py` hoặc `run_update()` trong `update.py`.
- **Trigger Source**: Người dùng chạy CLI `cli.py bootstrap` hoặc `cli.py update` (hoặc thông qua các skill tương ứng `project-memory-bootstrap`, `project-memory-update`).
- **Execution Order**: Sau khi Project Memory lưu trạng thái thành công (`update_memory_state`) -> Tiến hành nạp động và gọi đồng bộ hóa Obsidian -> Trả về kết quả JSON chính của bộ nhớ.
- **Completion Condition**: Hoàn thành tiến trình bộ nhớ và trả về JSON kết quả thành công, kèm thông báo thành công hoặc cảnh báo trong log stdout/stderr.

## 5. Runtime Sequence
Chuỗi hoạt động runtime của tiến trình tích hợp:
```text
Project Memory Update / Bootstrap
       ↓
Chỉ mục SQLite được cập nhật
       ↓
Cấu trúc JSON & Markdown được ghi nhận
       ↓
Cập nhật trạng thái (update_memory_state)
       ↓
Kiểm tra & nạp gói "knowledge_runtime" qua sys.path (nếu chưa nạp)
       ↓
Gọi knowledge_runtime.sync("obsidian")
       ↓
In thông báo Log (Success / Warn)
       ↓
Hoàn thành phiên làm việc (session_complete)
```

## 6. Dependency Contract
- **Required Dependencies**: Gói Python `knowledge-runtime` (đặt tại `skills/knowledge-runtime/scripts`).
- **Optional Dependencies**: Cấu hình nhà cung cấp Obsidian được bật (`enabled: true`) trong `memory.config.json` hoặc cấu hình máy toàn cục.
- **External Runtime**: Không có.
- **Expected Contracts**: Hàm `knowledge_runtime.sync` trả về một `dict` có định dạng `{"status": "success" | "failure", "message": "..."}`.
- **Detection Method**: Thử import `knowledge_runtime` sau khi chèn đường dẫn động `skills/knowledge-runtime/scripts` vào `sys.path`.
- **Failure Behavior**: Bỏ qua ngầm nếu không tìm thấy gói hoặc gặp lỗi trong quá trình thực thi đồng bộ, in log warning và tiếp tục hoàn thành tiến trình chính.

## 7. Error Matrix
| Condition | Expected Behavior | User Visibility | Recovery Action |
|---|---|---|---|
| Dependency Missing | Ghi nhận lỗi `ImportError`, bỏ qua đồng bộ | Cảnh báo in ra log stdout/stderr | Tiến trình chính hoàn thành bình thường |
| Timeout | Bỏ qua hoặc báo lỗi kết nối nếu dùng API REST | Cảnh báo in ra log | Tiếp tục chạy bình thường |
| Configuration Disabled | Bỏ qua đồng bộ | Không hiển thị gì (hoặc log thông tin) | Tiếp tục chạy bình thường |
| Invalid config | Báo lỗi cấu hình không hợp lệ | Cảnh báo in ra log | Tiếp tục chạy bình thường |
| Partial Sync Failure | Tiếp tục đồng bộ các tệp khác | In log cảnh báo tệp bị lỗi | Tiếp tục chạy bình thường |

## 8. Non-functional Requirements
- **Performance Expectations**: Tiến trình đồng bộ Obsidian chạy dưới 2 giây đối với các thay đổi tăng cường thông thường.
- **Blocking vs Asynchronous**: Chạy đồng bộ (blocking) trong CLI chính để đảm bảo tính nhất quán của tri thức trước khi đóng phiên làm việc.
- **Timeouts**: Tối đa 30 giây cho toàn bộ tiến trình đồng bộ.
- **Retry Policy**: Không thử lại tự động ở tầng CLI bộ nhớ.
- **Resource Usage**: Rất thấp (chỉ đọc tệp tin và tính toán MD5 hash).
- **Thread Safety**: Sử dụng cơ chế khóa tệp tin chuẩn để đảm bảo an toàn khi ghi đồng thời.
- **Idempotency**: Có tính idempotency cao nhờ so sánh MD5 hash của các tệp tin nguồn và đích.
- **User Interaction**: Không yêu cầu bất kỳ tương tác hoặc phê duyệt nào của người dùng khi chạy CLI.

## 9. Logging Requirements
- **Start**: Không log lúc bắt đầu chạy ngầm để giữ giao diện sạch.
- **Progress**: Không hiển thị log tiến độ chạy ngầm.
- **Warning**: `Auto-sync Obsidian skipped: [Error]` hoặc `Obsidian auto-sync returned status: [Msg]`.
- **Skipped**: Log dạng warn khi bị bỏ qua do tắt cấu hình hoặc lỗi.
- **Success**: `Obsidian sync completed automatically after memory [bootstrap / update].`.
- **Failure**: Ghi log lỗi chi tiết nếu sync ném ra ngoại lệ.
- **Completion**: In ra JSON kết quả chính của tiến trình bộ nhớ dự án.

## 10. Configuration Impact
- **Existing Configs Reused**: Cấu hình `obsidian` trong tệp `memory.config.json` hoặc cấu hình máy toàn cục.
- **New Configs Required**: Không có.
- **Migration Required**: Không.
- **Default Behavior**: Nếu cấu hình bị thiếu hoặc disable, tính năng tự động đồng bộ sẽ bị bỏ qua.
- **Backward Compatibility**: Tương thích ngược hoàn toàn với tất cả các dự án cũ không sử dụng Obsidian.

## 11. Design Constraints
- **CLI/API Constraints**: Không thêm CLI lệnh mới vào Project Memory; không thay đổi API giao tiếp của `knowledge-runtime`.
- **Database Constraints**: Không thay đổi schema SQLite của Project Memory.
- **Architectural Constraints**: Tái sử dụng gói `knowledge-runtime` hiện tại, tuyệt đối không sao chép hoặc viết lại logic đồng bộ hóa Obsidian bên trong gói `project_memory`.

## 12. Blast Radius
Xác định các thành phần bị ảnh hưởng và đánh giá mức độ tác động:
- **Affected Skills**: project-memory-bootstrap, project-memory-update
- **Affected Runtime**: project_memory CLI scripts (`bootstrap.py`, `update.py`)
- **Affected Extension**: None
- **Affected Memory**: None
- **Affected Documentation**: None
- **Affected Scripts**: None
- **Impact Level**: Low

## 13. File Change Scope
Biên giới tác động mã nguồn thực tế:
- **Modify**:
  - `runtime/scripts/project_memory/bootstrap.py`
  - `runtime/scripts/project_memory/update.py`
- **Do Not Modify**:
  - `skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py`

## 14. Success Metrics
Các chỉ số đo lường hiệu quả thành công:
- **Regression free**: Yes
- **Backward compatible**: Yes
- **Implementation completeness**: 100%

## 15. Rollback Strategy
- **Files Affected**: `runtime/scripts/project_memory/bootstrap.py`, `runtime/scripts/project_memory/update.py`.
- **Safe Rollback Steps**: Sử dụng lệnh `git checkout` để khôi phục trạng thái cũ của hai tệp này.
- **Migration Rollback**: Không có.
- **Behavior After Rollback**: Hệ thống hoạt động bình thường, không tự động đồng bộ sang Obsidian khi chạy lệnh bộ nhớ.

## 16. Expanded Acceptance Criteria
- [ ] AC-01 (Success Path): Chạy lệnh `cli.py update` hiển thị thông báo log `Obsidian sync completed automatically after memory update.`.
- [ ] AC-02 (Success Path): Chạy lệnh `cli.py bootstrap` hiển thị thông báo log `Obsidian sync completed automatically after memory bootstrap.`.
- [ ] AC-03 (Failure Path): Xóa tạm thời thư mục `skills/knowledge-runtime`, chạy lệnh bộ nhớ vẫn chạy thành công và in ra cảnh báo `Auto-sync Obsidian skipped: ...`.
- [ ] AC-04 (Backward Compatibility): Dự án không cấu hình Obsidian chạy lệnh bộ nhớ thành công mà không gây crash.
- [ ] AC-05 (Regression): Đảm bảo các tệp markdown tri thức và file-map được cập nhật chính xác như cũ.
- [ ] AC-06 (No duplicate execution): Chạy liên tiếp lệnh bộ nhớ không làm tăng số lượng tệp được sao chép sang Obsidian.
- [ ] AC-07 (No behavior change outside scope): Các lệnh của `knowledge-runtime` (như sync thủ công) hoạt động không đổi.

## 17. Self Verification
Xác minh tự động bắt buộc sau triển khai:
- [ ] So sánh Trước vs Sau (Before vs After comparison).
- [ ] Kiểm thử không hồi quy (Regression testing) bằng cách chạy lại test suite của `project-memory`.
- [ ] Kiểm tra các tệp tin trong vault Obsidian dự án `/Volumes/Kyle/Knowledge/AIWF-Knowledge-AI-Skill-Framework` được cập nhật đồng nhất ngay sau khi chạy lệnh.

## 18. Open Questions
- Không có câu hỏi nào cần giải quyết.

## 19. Blueprint Handoff
Bản thiết kế kỹ thuật (Technical Design Blueprint) ở Phase 2 bắt buộc phải quyết định và làm rõ:
- Vị trí chèn khối lệnh gọi sync cụ thể trong mã nguồn của hai tệp `bootstrap.py` và `update.py`.
- Cách thức giải quyết đường dẫn động đến `skills/knowledge-runtime/scripts` từ `runtime/scripts/project_memory/` thông qua `sys.path`.
- Các cấp độ log chi tiết khi đồng bộ thành công hoặc bỏ qua.
- Cách thiết lập kiểm thử đơn vị mô phỏng việc import `knowledge_runtime` để bảo vệ test suite không phụ thuộc tệp thật.
