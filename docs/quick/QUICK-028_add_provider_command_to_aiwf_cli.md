---
artifact_type: quick-feature-spec
feature_id: QUICK-028
workflow: quick-feature
status: pending
---
# Mini Plan & Feature Specification – Add Provider Command to AIWF CLI

## 1. Feature Goal
Bổ sung các lệnh con `provider` và `sync` trực tiếp vào wrapper CLI toàn cục `aiwf` để người dùng có thể chạy trực tiếp các lệnh quản trị tri thức ngoại vi (ví dụ: đồng bộ Obsidian bằng `aiwf sync obsidian` hoặc `aiwf provider sync obsidian`) thay vì phải gõ toàn bộ đường dẫn kịch bản Python dài dòng.

## 2. Quick Feature Justification
- **Estimated Complexity**: Low (chỉ cấu hình thêm case-branch trong script wrapper).
- **Implementation Scope**: Thêm nhánh lệnh trong `bootstrap.sh` và `bootstrap.ps1`.
- **Architectural Impact**: Low (không ảnh hưởng tới logic nghiệp vụ).
- **Risk Level**: Low.
- **Justification**: Đây là một thay đổi nhỏ về giao diện dòng lệnh (CLI wrapper forwarding) hoàn toàn độc lập và không yêu cầu thiết kế CSDL hay thay đổi lõi nghiệp vụ.

## 3. Scope Boundary
- **In Scope**:
  - Hỗ trợ lệnh con `provider` trong wrapper `aiwf` (chuyển tiếp tham số đến `workflow_runtime.py provider`).
  - Hỗ trợ lệnh con `sync` trong wrapper `aiwf` (chuyển tiếp tham số trực tiếp đến `workflow_runtime.py provider sync`).
  - Cập nhật hàm hiển thị trợ giúp `Show-Help` của `bootstrap.sh` và `bootstrap.ps1`.
  - Tự động biên dịch/tái cài đặt wrapper toàn cục sau khi sửa đổi để áp dụng ngay.
- **Out of Scope**:
  - Sửa đổi các tham số hoặc hoạt động lõi của module `provider` bên trong `workflow_runtime.py`.
- **Not Modified**:
  - Lõi của `workflow_runtime.py`.
- **Future Work**:
  - Không có.

## 4. Trigger / Execution Flow
- **Entry Point**: Người dùng chạy lệnh `aiwf provider` hoặc `aiwf sync` trên terminal.
- **Trigger Source**: Lệnh gõ trực tiếp từ người dùng.
- **Execution Order**:
  1. Wrapper `aiwf` (tại `$HOME/.local/share/aiwf/bin/aiwf`) bắt lệnh con `provider` hoặc `sync`.
  2. Wrapper thực thi chuyển tiếp các đối số bằng cách gọi trình biên dịch Python và kịch bản `workflow_runtime.py`.
- **Completion Condition**: Lệnh chuyển tiếp thực thi hoàn tất và trả về mã thoát (exit code) tương ứng của kịch bản Python.

## 5. Runtime Sequence
```
User Command (e.g. aiwf sync obsidian)
       ↓
aiwf Zsh/Bash Wrapper
       ↓
Forward arguments to: python3 workflow_runtime.py provider sync obsidian
       ↓
Execution output & Exit Code returned to User
```

## 6. Dependency Contract
- **Required Dependencies**: Tệp `workflow_runtime.py` phải tồn tại và khả dụng.
- **Optional Dependencies**: Không có.
- **External Runtime**: Bash/Zsh (Unix) hoặc PowerShell (Windows).
- **Expected Contracts**: Wrapper phải chuyển tiếp đúng 100% tất cả các đối số phía sau `$@` hoặc `$args`.
- **Detection Method**: Không cần thiết.
- **Failure Behavior**: Báo lỗi cú pháp nếu gọi sai hoặc gọi khi dự án chưa cài đặt.

## 7. Error Matrix
| Condition | Expected Behavior | User Visibility | Recovery Action |
|---|---|---|---|
| Gọi ngoài thư mục dự án | Báo lỗi tệp kịch bản Python không tìm thấy | Lỗi đường dẫn từ python | Di chuyển vào thư mục dự án |
| Sai cú pháp lệnh con | Trả lỗi cú pháp của `workflow_runtime` | Thông báo `--help` của provider action | Nhập đúng cú pháp |

## 8. Non-functional Requirements
- **Performance Expectations**: Chuyển tiếp tham số ngay lập tức (< 10ms).
- **Blocking vs Asynchronous**: Đồng bộ (Blocking).
- **Timeouts**: Phụ thuộc vào lệnh gốc.
- **Retry Policy**: Không áp dụng.
- **Resource Usage**: Không đáng kể.
- **Thread Safety**: Không ảnh hưởng.
- **Idempotency**: Lệnh mang tính gọi chuyển tiếp, hoàn toàn an toàn khi gọi nhiều lần.
- **User Interaction**: Hiển thị đầu ra trực tiếp của lệnh Python.

## 9. Logging Requirements
- **Start**: Không có ghi log bổ sung từ wrapper (ủy quyền cho Python core).
- **Success**: Output trực tiếp của lệnh.
- **Failure**: Trả về exit code phi 0 nếu lệnh Python thất bại.

## 10. Configuration Impact
- **Existing Configs Reused**: Không có.
- **New Configs Required**: Không có.
- **Migration Required**: Không có.
- **Default Behavior**: Chuyển tiếp toàn bộ tham số.
- **Backward Compatibility**: Tương thích hoàn toàn 100% với các lệnh `aiwf` hiện có.

## 11. Design Constraints
- **CLI/API Constraints**: Chỉ bổ sung 2 lệnh con chuyển tiếp `provider` và `sync` vào CLI wrapper.
- **Database Constraints**: Không ảnh hưởng.
- **Architectural Constraints**: Giữ nguyên kiến trúc wrapper hiện tại trong `bootstrap.sh`/`bootstrap.ps1`.

## 12. Blast Radius
- **Affected Skills**: Không có.
- **Affected Runtime**: Không có.
- **Affected Extension**: Không có.
- **Affected Memory**: Không có.
- **Affected Documentation**: `bootstrap.sh`, `bootstrap.ps1` (Sửa đổi trực tiếp tệp cài đặt).
- **Affected Scripts**: Tệp wrapper `/Users/kyle/.local/share/aiwf/bin/aiwf` sẽ được sinh lại.
- **Impact Level**: Low.

## 13. File Change Scope
- **Modify**:
  - `bootstrap.sh`
  - `bootstrap.ps1`
- **Create**:
  - Không có.
- **Do Not Modify**:
  - Tất cả các tệp nguồn Python khác.

## 14. Success Metrics
- **Regression free**: Yes
- **Backward compatible**: Yes
- **Implementation completeness**: 100%

## 15. Rollback Strategy
- **Files Affected**: `bootstrap.sh`, `bootstrap.ps1`
- **Safe Rollback Steps**: Chạy `git checkout -- bootstrap.sh bootstrap.ps1` và chạy lại `./bootstrap.sh` gốc để cài đặt lại wrapper.

## 16. Expanded Acceptance Criteria
- [ ] AC-01: Người dùng gõ `aiwf` hoặc `aiwf help` hiển thị trợ giúp có chứa hai lệnh mới `provider` và `sync`.
- [ ] AC-02: Gõ `aiwf provider list` hiển thị danh sách các providers hoạt động.
- [ ] AC-03: Gõ `aiwf sync obsidian` chạy thành công đồng bộ hóa bộ nhớ sang Obsidian.
- [ ] AC-04: Đảm bảo chuyển tiếp đúng tất cả các cờ (flags) bổ sung như `--help` hay các tham số cấu hình.

## 17. Self Verification
- [ ] So sánh Trước vs Sau của đầu ra `aiwf help`.
- [ ] Thử nghiệm chạy thực tế lệnh `aiwf sync obsidian` và kiểm tra đầu ra.

## 18. Open Questions
Không có.

## 19. Blueprint Handoff
Bản thiết kế Phase 2 sẽ làm rõ:
- Đoạn mã cụ thể cần chèn vào hàm `show_help()` và khối `switch/case` của cả hai tệp `bootstrap.sh` và `bootstrap.ps1`.
- Quy trình cài đặt lại wrapper toàn cục sau khi code thay đổi để kiểm thử.
