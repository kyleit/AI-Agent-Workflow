---
artifact_type: fix-spec
issue_id: FIX-026
workflow: quick-fix
status: pending
---
# Mini Plan & Fix Specification – Add Init and Test Commands to AIWF CLI

## 🔒 QUICK-FIX MODE ACTIVE

| 🔒 QUICK-FIX MODE ACTIVE |
| :--- |
| This Skill runs in a **three-phase model** with strict Blueprint enforcement. |
| **Phase 1 (Specification)**: Analyze and write the FIX specification. |
| **Phase 2 (Blueprint)**: Design the technical solution and write the Design Blueprint. |
| **Phase 3 (Implementation)**: Implement code only after explicit Blueprint approval. |
| NO SOURCE CODE will be modified during Phase 1 or Phase 2. |
| Specification path: `docs/issues/FIX-XXX_issue_name.md` |
| Design Blueprint path: `docs/designs/FIX-XXX_issue_name_blueprint.md` |

## 1. Issue Description
Người dùng phản ánh không thấy lệnh `init` và muốn hỗ trợ thêm lệnh `bootstrap` khi sử dụng công cụ dòng lệnh toàn cục `aiwf` (wrapper `aiwf` CLI). Hiện tại, wrapper `aiwf` (`bootstrap.ps1`) chỉ chuyển tiếp các lệnh như `install`, `update`, `uninstall`, `doctor`, `version`, `memory`, `blueprint`, `registry`, `provider`, và `sync`, nhưng thiếu lệnh `init`, `test` (vừa mới được giới thiệu trong QUICK-029) và lệnh `bootstrap`.

## 2. Scope
- **In Scope**:
  - Cấu hình thêm ba nhánh lệnh `init`, `test` và `bootstrap` trong switch-case của `bootstrap.ps1`.
  - Cập nhật hướng dẫn `Show-Help` của `bootstrap.ps1` để phản ánh ba lệnh này.
  - Tải và cài đặt lại wrapper toàn cục sau khi sửa đổi bằng cách chạy `bootstrap.ps1` cục bộ.
- **Out of Scope**:
  - Không sửa đổi cấu trúc hoặc logic lõi của `workflow_runtime.py` cho `init` hoặc `test`.

## 3. Quick Fix Justification
- **Estimated Complexity**: Low (chỉ cấu hình thêm case-branch và cập nhật help trong script wrapper).
- **Implementation Scope**: Thêm nhánh lệnh trong `bootstrap.ps1`.
- **Architectural Impact**: Low (không ảnh hưởng tới logic nghiệp vụ).
- **Risk Level**: Low.
- **Justification**: Đây là một thay đổi nhỏ về giao diện dòng lệnh (CLI wrapper forwarding) hoàn toàn độc lập và không ảnh hưởng tới kiến trúc hệ thống.

## 4. Trigger / Execution Flow
- **Entry Point**: Người dùng chạy lệnh `aiwf init` hoặc `aiwf test` trên terminal.
- **Trigger Source**: Lệnh gõ trực tiếp từ người dùng.
- **Execution Order**:
  1. Wrapper `aiwf` bắt lệnh con `init` hoặc `test`.
  2. Wrapper thực thi chuyển tiếp các đối số bằng cách gọi kịch bản Python `workflow_runtime.py`.
- **Completion Condition**: Lệnh chuyển tiếp thực thi hoàn tất và trả về exit code của kịch bản Python.

## 5. Runtime Sequence
```
User Command (e.g. aiwf test smoke)
       ↓
aiwf PowerShell Wrapper
       ↓
Forward arguments to: python skills/workflow-runtime/scripts/workflow_runtime.py test smoke
       ↓
Execution output & Exit Code returned to User
```

## 6. Dependency Contract
- **Required Dependencies**: Tệp `workflow_runtime.py` phải tồn tại.
- **External Runtime**: PowerShell (Windows).
- **Expected Contracts**: Wrapper phải chuyển tiếp đúng 100% tất cả các đối số phía sau `$args`.

## 7. Error Matrix
| Condition | Expected Behavior | User Visibility | Recovery Action |
|---|---|---|---|
| Gọi ngoài thư mục dự án | Báo lỗi tệp kịch bản Python không tìm thấy | Lỗi đường dẫn từ python | Di chuyển vào thư mục dự án |
| Sai cú pháp lệnh con | Trả lỗi cú pháp của `workflow_runtime` | Thông báo `--help` của action tương ứng | Nhập đúng cú pháp |

## 8. Non-functional Requirements
- **Performance Expectations**: Chuyển tiếp tham số ngay lập tức (< 10ms).
- **Blocking vs Asynchronous**: Đồng bộ (Blocking).
- **Timeouts**: Phụ thuộc vào lệnh gốc.
- **Idempotency**: An toàn khi gọi nhiều lần.

## 9. Logging Requirements
- **Start**: Không ghi log bổ sung từ wrapper (ủy quyền cho Python core).
- **Success**: Output trực tiếp của lệnh.
- **Failure**: Trả về exit code phi 0 nếu lệnh Python thất bại.

## 10. Configuration Impact
- **Existing Configs Reused**: Không có.
- **New Configs Required**: Không có.
- **Backward Compatibility**: Tương thích hoàn toàn 100% với các lệnh `aiwf` hiện có.

## 11. Design Constraints
- **CLI/API Constraints**: Bổ sung `init`, `test`, và `bootstrap` vào CLI wrapper.
- **Architectural Constraints**: Giữ nguyên kiến trúc wrapper hiện tại trong `bootstrap.ps1`.

## 12. Blast Radius
- **Affected Skills**: Không có.
- **Affected Runtime**: Không có.
- **Affected Documentation**: `bootstrap.ps1`.
- **Affected Scripts**: Tệp wrapper `$env:LOCALAPPDATA/aiwf/bin/aiwf.ps1`.
- **Impact Level**: Low.

## 13. File Change Scope
- **Modify**:
  - `bootstrap.ps1`

## 14. Success Metrics
- Chạy `aiwf bootstrap` kích hoạt trình cài đặt môi trường của framework.
- Chạy `aiwf init` hiển thị kết quả khởi tạo thành công hoặc bỏ qua.
- Chạy `aiwf test validate` hiển thị kết quả xác thực thành công.
